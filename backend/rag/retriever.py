"""
Knowledge Base Hybrid Retriever with AWS Bedrock Knowledge Base Integration
Provides primary search grounded on AWS Bedrock Knowledge Base (BAB6KXZLG6 in ap-south-1)
with automatic fallback to local FAISS dense semantic embeddings and BM25 lexical keyword matching.
"""
import json
import os
import pickle
import re

import boto3

MODEL_NAME = "all-MiniLM-L6-v2"
CANDIDATE_K = 10
TOP_K = 5
DENSE_WEIGHT = 0.65
LEXICAL_WEIGHT = 0.35
CONFIDENCE_THRESHOLD = 0.45


class HybridRetriever:
    _instance = None

    def __init__(self, data_dir: str | None = None):
        if not data_dir:
            base = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(base))
            candidate_dirs = [
                os.path.join(project_root, "data", "vector_indices"),
                os.path.join(base, "data"),
                os.path.join(os.path.dirname(base), "knowledge_base", "data"),
                os.path.dirname(base),
            ]
            data_dir = next((d for d in candidate_dirs if os.path.exists(os.path.join(d, "knowledge.index"))), candidate_dirs[0])

        self.data_dir = data_dir
        self.meta_p = os.path.join(data_dir, "knowledge_meta.json")
        self.index_p = os.path.join(data_dir, "knowledge.index")
        self.bm25_p = os.path.join(data_dir, "bm25_index.pkl")

        # Lazy loaded local ML models
        self._local_initialized = False
        self.model = None
        self.index = None
        self.bm25 = None

        if os.path.exists(self.meta_p):
            with open(self.meta_p, "r", encoding="utf-8") as f:
                self.meta = json.load(f)
        else:
            self.meta = []

        # Build document lookup map for resolving titles and canonical Confluence URLs
        self.doc_lookup = {}
        for chunk in self.meta:
            t = chunk.get("title", "")
            text = chunk.get("text", "")
            m = re.search(r'\*\*Confluence URL:\*\*\s*(https://[^\s\n\r]+)', text)
            c_url = m.group(1).strip() if m else chunk.get("url", "")
            if t:
                norm_title = re.sub(r'[^a-z0-9]', '', t.lower())
                if norm_title not in self.doc_lookup:
                    self.doc_lookup[norm_title] = {"title": t, "url": c_url}

        # AWS Bedrock Knowledge Base Configuration
        self.aws_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region_name = os.getenv("AWS_REGION", "ap-south-1")
        self.kb_id = os.getenv("AWS_BEDROCK_KB_ID", "BAB6KXZLG6")
        self._bedrock_client = None

        if self.kb_id and self.aws_key and self.aws_secret:
            print(f"[HybridRetriever] Initialized with AWS Bedrock KB (ID: {self.kb_id}, Region: {self.region_name})")

    @classmethod
    def get_instance(cls, data_dir: str | None = None):
        if cls._instance is None:
            cls._instance = cls(data_dir)
        return cls._instance

    def _init_local_models(self):
        """Lazily initialize local sentence-transformers, FAISS, and BM25 index on demand."""
        if self._local_initialized:
            return

        print("[HybridRetriever] Initializing local FAISS + BM25 embeddings...")
        try:
            import faiss
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(MODEL_NAME)
            if os.path.exists(self.index_p):
                self.index = faiss.read_index(self.index_p)

            if os.path.exists(self.bm25_p):
                with open(self.bm25_p, "rb") as f:
                    self.bm25 = pickle.load(f)["bm25"]
        except Exception as e:
            print(f"[HybridRetriever] Warning: Could not initialize local FAISS models: {e}")

        self._local_initialized = True

    def _get_bedrock_client(self):
        if self._bedrock_client is None:
            in_ecs = bool(os.getenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI"))
            if in_ecs:
                os.environ.pop("AWS_ACCESS_KEY_ID", None)
                os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
                os.environ.pop("AWS_SESSION_TOKEN", None)
                self._bedrock_client = boto3.client(
                    "bedrock-agent-runtime",
                    region_name=self.region_name
                )
            elif self.aws_key and self.aws_secret:
                self._bedrock_client = boto3.client(
                    "bedrock-agent-runtime",
                    aws_access_key_id=self.aws_key,
                    aws_secret_access_key=self.aws_secret,
                    region_name=self.region_name
                )
        return self._bedrock_client

    def bedrock_kb_search(self, query: str, top_k: int = TOP_K) -> list[dict]:
        """
        Queries AWS Bedrock Knowledge Base (BAB6KXZLG6) via bedrock-agent-runtime.
        Returns ranked documents normalized to {title, url, text, score}.
        """
        client = self._get_bedrock_client()
        if not client or not self.kb_id:
            return []

        try:
            response = client.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={"text": query},
                retrievalConfiguration={
                    "vectorSearchConfiguration": {
                        "numberOfResults": top_k
                    }
                }
            )
            raw_results = response.get("retrievalResults", [])
            results = []

            for item in raw_results:
                content = item.get("content", {}).get("text", "")
                score = round(float(item.get("score", 0.0)), 4)
                loc = item.get("location", {})
                s3_uri = loc.get("s3Location", {}).get("uri", "")
                confluence_loc = loc.get("confluenceLocation", {}).get("url", "")

                fname = s3_uri.split("/")[-1].replace(".md", "") if s3_uri else ""
                norm_fname = re.sub(r'[^a-z0-9]', '', fname.lower())

                title = None
                url = confluence_loc

                if norm_fname in self.doc_lookup:
                    title = self.doc_lookup[norm_fname]["title"]
                    if not url:
                        url = self.doc_lookup[norm_fname]["url"]

                if not title:
                    m_head = re.search(r'^#\s+([^\n]+)', content)
                    if m_head:
                        clean_head = m_head.group(1).split("**")[0].strip()
                        title = clean_head
                    elif fname:
                        title = re.sub(r'__+', ' & ', fname).replace("_", " ").title()
                    else:
                        title = "AWS Bedrock Knowledge Base"

                if not url:
                    m_url = re.search(r'\*\*Confluence URL:\*\*\s*(https://[^\s\n\r]+)', content)
                    if m_url:
                        url = m_url.group(1).strip()
                    else:
                        url = "https://agnishpaul2002.atlassian.net/wiki/spaces/SELFHELP"

                results.append({
                    "title": title,
                    "url": url,
                    "text": content,
                    "score": score
                })

            return results
        except Exception as e:
            print(f"[HybridRetriever] Warning: AWS Bedrock KB retrieval failed ({e}). Falling back to local retriever.")
            return []

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r'\w+', text.lower())

    def dense_search(self, query: str, top_k: int = CANDIDATE_K) -> list[tuple[int, float]]:
        self._init_local_models()
        if not self.index or self.index.ntotal == 0 or not self.model:
            return []
        import faiss
        vec = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(vec)
        scores, indices = self.index.search(vec, top_k)
        return [(int(idx), float(score)) for idx, score in zip(indices[0], scores[0]) if idx != -1]

    def lexical_search(self, query: str, top_k: int = CANDIDATE_K) -> list[tuple[int, float]]:
        self._init_local_models()
        if not self.bm25:
            return []
        scores = self.bm25.get_scores(self._tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        max_score = ranked[0][1] if ranked and ranked[0][1] > 0 else 1.0
        return [(idx, float(score / max_score)) for idx, score in ranked if score > 0]

    def local_hybrid_search(self, query: str, top_k: int = TOP_K) -> list[dict]:
        """
        Local hybrid search combining Dense Cosine Similarity + BM25 Lexical Score.
        """
        dense_results = dict(self.dense_search(query))
        lexical_results = dict(self.lexical_search(query))

        all_candidates = set(dense_results.keys()) | set(lexical_results.keys())
        scored = []

        for idx in all_candidates:
            d_score = dense_results.get(idx, 0.0)
            l_score = lexical_results.get(idx, 0.0)
            hybrid_score = (d_score * DENSE_WEIGHT) + (l_score * LEXICAL_WEIGHT)
            scored.append((idx, hybrid_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_matches = scored[:top_k]

        results = []
        for idx, score in top_matches:
            if idx < len(self.meta):
                chunk = self.meta[idx]
                results.append({
                    "title": chunk.get("title", "Confluence Knowledge Base"),
                    "url": chunk.get("url") or "https://agnishpaul2002.atlassian.net/wiki/spaces/SELFHELP",
                    "text": chunk.get("text", ""),
                    "score": round(score, 4)
                })
        return results

    def search(self, query: str, top_k: int = TOP_K) -> list[dict]:
        """
        Primary search using AWS Bedrock Knowledge Base (BAB6KXZLG6).
        Automatically falls back to local FAISS + BM25 hybrid search if needed.
        """
        if self.kb_id and self.aws_key and self.aws_secret:
            bedrock_results = self.bedrock_kb_search(query, top_k=top_k)
            if bedrock_results:
                print(f"[HybridRetriever] Retrieved {len(bedrock_results)} chunks from AWS Bedrock KB (top score: {bedrock_results[0]['score']})")
                return bedrock_results

        # Fallback to local index
        return self.local_hybrid_search(query, top_k=top_k)

    def is_escalation_needed(self, results: list[dict]) -> tuple[bool, float]:
        top_score = results[0]["score"] if results else 0.0
        escalate = (not results) or (top_score < CONFIDENCE_THRESHOLD)
        return escalate, top_score
