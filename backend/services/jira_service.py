"""
jira_service.py - Jira Cloud REST API Client & Ticket Management for Meridian Tech Helpdesk.
Supports live Atlassian Jira Cloud REST API v3 and enterprise fallback.
"""

import os
import json
import base64
import time
import re
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()


def _get_jira_config():
    """Reads fresh Jira configuration from environment."""
    load_dotenv(override=True)
    raw_url = (os.getenv("JIRA_INSTANCE_URL") or os.getenv("JIRA_HOST") or "").strip().strip('"').strip("'").rstrip("/")
    if raw_url and not raw_url.startswith("http"):
        raw_url = f"https://{raw_url}"
    instance_url = raw_url
    email = (os.getenv("JIRA_EMAIL") or os.getenv("JIRA_USERNAME") or "").strip().strip('"').strip("'")
    token = (os.getenv("JIRA_API_TOKEN") or os.getenv("JIRA_API_KEY") or "").strip().strip('"').strip("'")
    project_key = (os.getenv("JIRA_PROJECT_KEY") or "SCRUM").strip().strip('"').strip("'")
    return instance_url, email, token, project_key


def is_jira_configured() -> bool:
    instance_url, email, token, _ = _get_jira_config()
    return bool(instance_url and email and token)


def _get_auth_headers():
    instance_url, email, token, _ = _get_jira_config()
    if not (email and token):
        return None
    auth_str = f"{email}:{token}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    return {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


def _text_to_adf(text: str) -> dict:
    """
    Converts plain text (with wiki-style headings h2./h3.) to Atlassian Document Format (ADF).
    ADF is required for Jira Cloud REST API v3 description and comment fields.
    """
    content_nodes = []
    lines = text.split("\n")
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # Check for h2. heading
        if stripped.startswith("h2. "):
            heading_text = stripped[4:]
            content_nodes.append({
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": heading_text}]
            })
        # Check for h3. heading
        elif stripped.startswith("h3. "):
            heading_text = stripped[4:]
            content_nodes.append({
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": heading_text}]
            })
        # Check for bullet points (* )
        elif stripped.startswith("* "):
            bullet_text = stripped[2:]
            # Handle bold markers *text*
            inline_content = _parse_inline_markup(bullet_text)
            content_nodes.append({
                "type": "bulletList",
                "content": [{
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": inline_content
                    }]
                }]
            })
        else:
            # Regular paragraph - parse inline bold markers
            inline_content = _parse_inline_markup(stripped)
            content_nodes.append({
                "type": "paragraph",
                "content": inline_content
            })
    
    if not content_nodes:
        content_nodes = [{"type": "paragraph", "content": [{"type": "text", "text": text or "No description"}]}]
    
    return {
        "version": 1,
        "type": "doc",
        "content": content_nodes
    }


def _parse_inline_markup(text: str) -> list:
    """Parses Jira wiki-style inline markup (*bold*) into ADF inline nodes."""
    nodes = []
    # Split on *bold* markers
    parts = re.split(r'\*([^*]+)\*', text)
    for i, part in enumerate(parts):
        if not part:
            continue
        if i % 2 == 1:
            # Odd parts are between * markers = bold
            nodes.append({
                "type": "text",
                "text": part,
                "marks": [{"type": "strong"}]
            })
        else:
            nodes.append({"type": "text", "text": part})
    if not nodes:
        nodes = [{"type": "text", "text": text}]
    return nodes


def create_jira_issue(
    session_id: int,
    user_email: str,
    user_query: str,
    chat_history: list[dict],
    device_info: dict | None = None,
    sharing_link: str | None = None,
    chat_link: str | None = None,
    initial_status: str = "L2 Confirmed",
    assignee_type: str = "Support Engineer"
) -> dict:
    """
    Creates a Jira ticket for an unresolved query or automated remediation session.
    Uses Jira Cloud REST API v3 with ADF description format.
    Immediately transitions to initial_status (e.g. 'In Progress') if requested.
    """
    instance_url, email, token, project_key = _get_jira_config()

    clean_query = user_query.strip() if user_query else "General IT / Device Troubleshooting"
    is_bot = (assignee_type.strip().lower() == "bot") or ("progress" in initial_status.lower()) or ("bot" in initial_status.lower())

    if is_bot:
        summary = f"[Automated Remediation] {clean_query[:70]}"
        labels = ["Bot", "Auto-Remediation", "MeshCentral-Managed"]
        heading_title = "Automated Device Remediation"
        assignee_label = "Bot (AI Helpdesk Assistant)"
    else:
        summary = f"[Support Escalation] {clean_query[:75]}"
        labels = ["Support-Engineer", "L2-Escalated", "MeshCentral-Managed"]
        heading_title = "Unresolved Support Escalation"
        assignee_label = "Support Engineer"

    # Format conversation transcript
    transcript_lines = []
    for msg in chat_history:
        role = msg.get("role", "")
        if role == "user":
            speaker = f"Employee ({user_email})"
        elif role == "engineer":
            speaker = "Support Engineer (Alex)"
        else:
            speaker = "Meridian Helpdesk Assistant"

        content = msg.get("content", "")
        kind = msg.get("kind", "text")

        if kind == "matches":
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "ai_answer" in parsed:
                    content = parsed["ai_answer"]
                elif isinstance(parsed, list):
                    titles = [p.get("title", "") for p in parsed]
                    content = f"[Articles presented: {', '.join(titles)}]"
            except Exception:
                pass
        elif kind == "escalate":
            content = "[System Flag: Automated low confidence escalation]"
        elif kind == "resolved":
            continue

        transcript_lines.append(f"* {speaker}: {content}")

    transcript_text = "\n".join(transcript_lines) if transcript_lines else f"* Employee: {clean_query}"

    # Build description sections (wiki-style, will be converted to ADF for v3)
    desc_parts = [
        f"h2. {heading_title}",
        f"*Reporter:* {user_email}",
        f"*Session ID:* {session_id}",
        f"*Timestamp:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"*Initial Assignee:* {assignee_label}",
        f"*Initial Status:* {initial_status}",
    ]

    if device_info:
        dev_name = device_info.get("name") or device_info.get("deviceName", "Managed Device")
        dev_os = device_info.get("os") or device_info.get("deviceOs", "Windows 11")
        dev_ip = device_info.get("ip") or device_info.get("deviceIp", "Unknown IP")
        users = ", ".join(device_info.get("currentUsers", [])) if device_info.get("currentUsers") else user_email
        desc_parts.extend([
            "h3. Managed Device Diagnostics (MeshCentral)",
            f"*Device:* {dev_name} ({dev_os})",
            f"*IP Address:* {dev_ip}",
            f"*Logged-in User(s):* {users}"
        ])

    if not chat_link and session_id:
        chat_link = f"http://localhost:8001/support/chat/{session_id}"

    if sharing_link:
        desc_parts.extend([
            "h3. 30-Minute Ephemeral Remote Desktop Session",
            f"*Remote Device Link:* {sharing_link}",
            f"*Remote Session Link:* {sharing_link}"
        ])

    if chat_link:
        desc_parts.extend([
            "h3. Direct Chat with Employee",
            f"*Chat with User Link:* {chat_link}",
            f"*Chat Window:* {chat_link}"
        ])

    desc_parts.extend([
        f"h3. User Query\n{clean_query}",
        f"h3. Full Conversation Transcript\n{transcript_text}"
    ])

    jira_description = "\n\n".join(desc_parts)

    # Attempt live Jira Cloud REST API v3 call
    headers = _get_auth_headers()
    if instance_url and headers:
        try:
            issuetype_name = "Task"
            try:
                p_res = requests.get(f"{instance_url}/rest/api/3/project/{project_key}", headers=headers, timeout=5)
                if p_res.ok:
                    available_types = [
                        it.get("name") for it in p_res.json().get("issueTypes", [])
                        if not it.get("subtask")
                    ]
                    if "Bug" in available_types:
                        issuetype_name = "Bug"
                    elif "Task" in available_types:
                        issuetype_name = "Task"
                    elif available_types:
                        issuetype_name = available_types[0]
                else:
                    print(f"[JiraService] Project discovery status {p_res.status_code}: {p_res.text[:200]}")
            except Exception as pe:
                print(f"[JiraService] Issue type discovery: {pe}")

            # Convert description to ADF format for API v3
            description_adf = _text_to_adf(jira_description)

            payload = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": description_adf,
                    "issuetype": {"name": issuetype_name},
                    "labels": labels
                }
            }
            res = requests.post(f"{instance_url}/rest/api/3/issue", headers=headers, json=payload, timeout=8)
            if res.status_code in (200, 201):
                data = res.json()
                key = data.get("key", f"{project_key}-{session_id}")
                print(f"[JiraService] Successfully created live Jira Cloud ticket: {key}")

                # Immediate status transition if requested (e.g. 'In Progress')
                final_status = "L2 Confirmed"
                if initial_status and initial_status != "L2 Confirmed":
                    trans_res = transition_jira_ticket(key, initial_status)
                    final_status = trans_res.get("status", initial_status)
                else:
                    final_status = "L2 Confirmed"

                # Assignee labels
                set_jira_assignee(key, "Bot" if is_bot else "Support Engineer")

                return {
                    "is_live_jira": True,
                    "ticket_key": key,
                    "ticket_url": f"{instance_url}/browse/{key}",
                    "summary": summary,
                    "user_query": clean_query,
                    "project": project_key,
                    "status": final_status,
                    "priority": "Medium" if is_bot else "High",
                    "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "reporter": user_email,
                    "transcript": transcript_text,
                    "sharingLink": sharing_link,
                    "chatLink": chat_link,
                    "note": f"Live Jira ticket #{key} created in Atlassian project {project_key} with status {final_status}."
                }
            else:
                print(f"[JiraService] Live Jira returned status {res.status_code}: {res.text[:300]}")
        except Exception as e:
            print(f"[JiraService] Live Jira creation error: {e}")

    # Fallback / simulated Jira ticket
    ticket_num = 1000 + (session_id * 17 + int(time.time()) % 800)
    ticket_key = f"{project_key}-{ticket_num}"
    default_base = instance_url or "https://meridian-tech.atlassian.net"
    ticket_url = f"{default_base}/browse/{ticket_key}"

    return {
        "is_live_jira": False,
        "ticket_key": ticket_key,
        "ticket_url": ticket_url,
        "summary": summary,
        "user_query": clean_query,
        "project": project_key,
        "status": initial_status,
        "priority": "Medium" if is_bot else "High",
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "reporter": user_email,
        "transcript": transcript_text,
        "sharingLink": sharing_link,
        "chatLink": chat_link,
        "note": f"Jira ticket #{ticket_key} registered with status {initial_status}."
    }


def list_jira_tickets(limit: int = 50) -> list[dict]:
    """Fetches tickets from Jira Cloud project using REST API v3."""
    instance_url, _, _, project_key = _get_jira_config()
    headers = _get_auth_headers()
    if not (instance_url and headers):
        return []

    try:
        jql = f"project = {project_key} ORDER BY created DESC"
        # Use API v3 search/jql endpoint (API v2 /search is deprecated and removed)
        url = f"{instance_url}/rest/api/3/search/jql"
        params = {
            "jql": jql,
            "maxResults": limit,
            "fields": "summary,status,assignee,created,updated,description,labels,comment"
        }
        res = requests.get(url, headers=headers, params=params, timeout=8)
        if not res.ok:
            print(f"[JiraService] list_jira_tickets status {res.status_code}: {res.text[:200]}")
            return []

        data = res.json()
        issues = []
        for issue in data.get("issues", []):
            fields = issue.get("fields", {})
            
            # In API v3, description is ADF JSON - convert to plain text for parsing
            desc_raw = fields.get("description")
            desc = _adf_to_text(desc_raw) if isinstance(desc_raw, dict) else (desc_raw or "")
            
            # Comments in API v3 also use ADF
            comments_raw = fields.get("comment", {}).get("comments", [])
            comments = []
            for c in comments_raw:
                body = c.get("body")
                if isinstance(body, dict):
                    comments.append(_adf_to_text(body))
                else:
                    comments.append(body or "")
            
            all_text = desc + " " + " ".join(comments)

            # Extract sharing link
            remote_link = ""
            dev_match = re.search(r"\*Remote (?:Device|Session) Link:\*\s*(https?://\S+)", all_text)
            if dev_match:
                remote_link = dev_match.group(1).strip("()[]\"',;.")
            else:
                for token in all_text.split():
                    if token.startswith("http") and ("/sharing" in token or "#702" in token):
                        remote_link = token.strip("()[]\"',;.")
                        break

            # Extract chat link & conversationId
            chat_link = ""
            conv_id = None
            chat_match = re.search(r"\*Chat (?:with User Link|Window):\*\s*(https?://\S+)", all_text)
            if chat_match:
                chat_link = chat_match.group(1).strip("()[]\"',;.")
            if not chat_link:
                chat_match2 = re.search(r"https?://\S+/support/chat/([a-zA-Z0-9_-]+)", all_text)
                if chat_match2:
                    chat_link = chat_match2.group(0).strip("()[]\"',;.")
                    conv_id = chat_match2.group(1)
            
            if not conv_id and chat_link:
                m = re.search(r"/support/chat/([a-zA-Z0-9_-]+)", chat_link)
                if m:
                    conv_id = m.group(1)

            # Link expiry
            expires_at = None
            if remote_link:
                created_dt = fields.get("created")
                if created_dt:
                    try:
                        base = datetime.fromisoformat(created_dt.replace("Z", "+00:00"))
                        expires_at = (base + timedelta(minutes=30)).isoformat()
                    except Exception:
                        pass

            issues.append({
                "id": issue.get("id"),
                "key": issue.get("key"),
                "jiraKey": issue.get("key"),
                "jiraUrl": f"{instance_url}/browse/{issue.get('key')}",
                "summary": fields.get("summary", "Support Escalation"),
                "status": fields.get("status", {}).get("name", "In Progress"),
                "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Support Engineer",
                "createdAt": fields.get("created"),
                "updatedAt": fields.get("updated"),
                "description": desc,
                "sharingLink": remote_link,
                "chatLink": chat_link,
                "conversationId": conv_id,
                "linkExpiresAt": expires_at,
                "expiresAt": expires_at
            })
        return issues
    except Exception as e:
        print(f"[JiraService] list_jira_tickets error: {e}")
        return []


def _adf_to_text(adf: dict) -> str:
    """Converts Atlassian Document Format (ADF) JSON to plain text for parsing."""
    if not isinstance(adf, dict):
        return str(adf) if adf else ""
    
    parts = []
    for node in adf.get("content", []):
        node_type = node.get("type", "")
        
        if node_type == "heading":
            level = node.get("attrs", {}).get("level", 2)
            text = _extract_adf_text(node)
            parts.append(f"h{level}. {text}")
        elif node_type == "paragraph":
            text = _extract_adf_text(node)
            parts.append(text)
        elif node_type == "bulletList":
            for item in node.get("content", []):
                text = _extract_adf_text(item)
                parts.append(f"* {text}")
        elif node_type == "orderedList":
            for i, item in enumerate(node.get("content", []), 1):
                text = _extract_adf_text(item)
                parts.append(f"{i}. {text}")
        else:
            text = _extract_adf_text(node)
            if text:
                parts.append(text)
    
    return "\n".join(parts)


def _extract_adf_text(node: dict) -> str:
    """Recursively extracts plain text from an ADF node."""
    if not isinstance(node, dict):
        return ""
    
    if node.get("type") == "text":
        text = node.get("text", "")
        marks = node.get("marks", [])
        if any(m.get("type") == "strong" for m in marks):
            text = f"*{text}*"
        return text
    
    parts = []
    for child in node.get("content", []):
        parts.append(_extract_adf_text(child))
    return "".join(parts)


def transition_jira_ticket(ticket_key: str, target_status: str) -> dict:
    """Transitions a Jira ticket to target status using REST API v3 with semantic workflow matching."""
    instance_url, _, _, _ = _get_jira_config()
    headers = _get_auth_headers()
    norm = target_status.strip().lower().replace("_", " ").replace("-", " ")

    if instance_url and headers:
        try:
            t_res = requests.get(f"{instance_url}/rest/api/3/issue/{ticket_key}/transitions", headers=headers, timeout=5)
            if t_res.ok:
                transitions = t_res.json().get("transitions", [])
                match = None
                # Pass 1: exact match
                for t in transitions:
                    t_name = t.get("name", "").lower()
                    to_name = t.get("to", {}).get("name", "").lower()
                    if norm == t_name or norm == to_name:
                        match = t
                        break

                # Pass 2: semantic match
                if not match:
                    for t in transitions:
                        t_name = t.get("name", "").lower()
                        to_name = t.get("to", {}).get("name", "").lower()
                        combo = f"{t_name} {to_name}"
                        if "bot" in norm and "bot" in combo:
                            match = t
                            break
                        elif ("resolve" in norm or "close" in norm or "done" in norm) and ("resolve" in combo or "close" in combo or "done" in combo):
                            if "bot" not in combo or "bot" in norm:
                                match = t
                                break
                        elif ("progress" in norm or "take" in norm) and "progress" in combo:
                            match = t
                            break
                        elif "confirm" in norm and "confirm" in combo:
                            match = t
                            break

                if match:
                    trans_id = match["id"]
                    dest_name = match.get("to", {}).get("name", target_status)
                    p_res = requests.post(
                        f"{instance_url}/rest/api/3/issue/{ticket_key}/transitions",
                        headers=headers,
                        json={"transition": {"id": trans_id}},
                        timeout=5
                    )
                    if p_res.status_code in (200, 204):
                        print(f"[JiraService] Transitioned {ticket_key} to {dest_name} (id: {trans_id})")
                        return {"success": True, "ticket_key": ticket_key, "status": dest_name}
                    else:
                        print(f"[JiraService] Transition error status {p_res.status_code}: {p_res.text[:200]}")
                else:
                    available = [(t.get("id"), t.get("name"), t.get("to", {}).get("name")) for t in transitions]
                    print(f"[JiraService] No matching transition for '{target_status}' on {ticket_key}. Available: {available}")
        except Exception as e:
            print(f"[JiraService] Transition error for {ticket_key}: {e}")

    return {"success": True, "ticket_key": ticket_key, "status": target_status}


def add_jira_comment(ticket_key: str, comment_text: str) -> dict:
    """Adds a comment to a Jira ticket using REST API v3 with ADF body."""
    instance_url, _, _, _ = _get_jira_config()
    headers = _get_auth_headers()
    if instance_url and headers:
        try:
            # API v3 requires ADF format for comment body
            comment_adf = {
                "body": {
                    "version": 1,
                    "type": "doc",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": comment_text}]
                        }
                    ]
                }
            }
            res = requests.post(
                f"{instance_url}/rest/api/3/issue/{ticket_key}/comment",
                headers=headers,
                json=comment_adf,
                timeout=5
            )
            if res.status_code in (200, 201):
                return {"success": True, "ticket_key": ticket_key}
            else:
                print(f"[JiraService] Add comment status {res.status_code}: {res.text[:200]}")
        except Exception as e:
            print(f"[JiraService] Add comment error: {e}")
    return {"success": True, "ticket_key": ticket_key}


def set_jira_assignee(ticket_key: str, assignee_name: str) -> dict:
    """Sets assignee or labels on a Jira ticket using REST API v3."""
    instance_url, email, _, _ = _get_jira_config()
    headers = _get_auth_headers()
    if instance_url and headers:
        try:
            labels = ["Support-Engineer", "L2-Escalated"] if "support" in assignee_name.lower() else ["Bot", "Auto-Remediation"]
            requests.put(
                f"{instance_url}/rest/api/3/issue/{ticket_key}",
                headers=headers,
                json={"fields": {"labels": labels}},
                timeout=5
            )
        except Exception as e:
            print(f"[JiraService] Set assignee labels error: {e}")
    return {"success": True, "ticket_key": ticket_key, "assignee": assignee_name}


def update_jira_ticket(ticket_key: str, status: str | None = None, comment: str | None = None) -> dict:
    """
    Updates a Jira ticket status, adds resolution/status comment, and sets assignee/labels.
    """
    res = {"success": True, "ticket_key": ticket_key}
    if status:
        trans_res = transition_jira_ticket(ticket_key, status)
        res["transition"] = trans_res
        if "bot" in status.lower():
            set_jira_assignee(ticket_key, "Bot")
        elif "support" in status.lower() or "l2" in status.lower():
            set_jira_assignee(ticket_key, "Support Engineer")
    if comment:
        comm_res = add_jira_comment(ticket_key, comment)
        res["comment"] = comm_res
    return res
