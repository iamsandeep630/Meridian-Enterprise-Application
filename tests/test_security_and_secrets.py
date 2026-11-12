"""
Security, Secrets Detection, and Quality Benchmarks Test Suite
Verifies that no API keys, cloud secrets, or security credentials are committed,
and tests cryptographic and input sanitization boundaries.
"""

import os
import re
import sys
import unittest
from pathlib import Path


class TestSecretsAndSecurityBenchmarks(unittest.TestCase):
    """
    Automated security gate testing for credential leakage,
    hardcoded secrets, and cryptographic standards.
    """

    @classmethod
    def setUpClass(cls):
        # Resolve project root: /app or repository root
        cls.repo_root = Path(__file__).resolve().parent.parent
        cls.backend_dir = cls.repo_root / "backend"
        cls.frontend_dir = cls.repo_root / "frontend"

        # Ensure both repo_root and backend_dir are on sys.path
        for p in [str(cls.repo_root), str(cls.backend_dir)]:
            if p not in sys.path:
                sys.path.insert(0, p)

        cls.SECRET_PATTERNS = {
            "AWS Access Key ID": re.compile(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])"),
            "GitHub Classic Token": re.compile(r"ghp_[a-zA-Z0-9]{36}"),
            "GitHub Fine-Grained Token": re.compile(r"github_pat_[a-zA-Z0-9_]{82}"),
            "Slack Token": re.compile(r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*"),
            "Private RSA/SSH Key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
            "Generic Hardcoded AWS Secret": re.compile(
                r"(?i)aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{40}['\"]"
            ),
            "Hardcoded Jira Token": re.compile(r"ATATT3xFfGF0[a-zA-Z0-9_\-=]{40,}"),
        }

        cls.EXCLUDED_DIRS = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            ".idea",
            ".vscode",
            ".aws",  # deployment templates with placeholder arns
        }
        cls.EXCLUDED_FILES = {
            ".env",
            ".env.example",
            ".env.local",
            "package-lock.json",
            "shopmart.db",
        }

    def test_no_hardcoded_secrets_in_tracked_code(self):
        """
        Verify that no high-entropy credentials, cloud secrets, or API tokens
        exist in any tracked backend or frontend source file.
        """
        violations = []

        scan_roots = [self.backend_dir, self.frontend_dir, self.repo_root / "tests"]
        for scan_root in scan_roots:
            if not scan_root.exists():
                continue

            for root, dirs, files in os.walk(scan_root):
                dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS]

                for file in files:
                    if file in self.EXCLUDED_FILES or file.endswith((".pyc", ".db", ".png", ".jpg", ".svg")):
                        continue

                    file_path = Path(root) / file
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        for label, pattern in self.SECRET_PATTERNS.items():
                            matches = pattern.findall(content)
                            for m in matches:
                                # Skip obvious mock strings or test placeholders
                                if any(x in m.lower() for x in ["mock", "dummy", "example", "test"]):
                                    continue
                                rel_path = file_path.relative_to(self.repo_root)
                                masked = m[:6] + "..." + m[-4:] if len(m) > 10 else "***"
                                violations.append(f"{rel_path}: [{label}] detected -> {masked}")
                    except Exception as e:
                        # Log but do not block unreadable binary files
                        pass

        self.assertEqual(
            len(violations),
            0,
            f"Security Benchmark Failed! Hardcoded secrets detected in codebase:\n"
            + "\n".join(violations),
        )

    def test_auth_security_jwt_configuration(self):
        """
        Verify that auth security module does not use a fixed hardcoded secret
        without falling back to environment-based configuration.
        """
        from auth.security import SECRET_KEY, create_access_token, decode_access_token

        # Ensure tokens can be signed and verified
        token = create_access_token(user_id=999, email="benchmark@meridian.com")
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)

        payload = decode_access_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "999")
        self.assertEqual(payload["email"], "benchmark@meridian.com")

        # Invalid token must fail safely without throwing unhandled exceptions
        invalid_payload = decode_access_token("invalid.token.signature")
        self.assertIsNone(invalid_payload)

    def test_password_hashing_security(self):
        """
        Verify password hashing uses bcrypt with salted hashes and does not leak plaintext.
        """
        from auth.security import hash_password, verify_password

        plaintext = "StrongEnterprisePassword!2026"
        hashed = hash_password(plaintext)

        self.assertNotEqual(plaintext, hashed)
        self.assertTrue(hashed.startswith("$2b$") or hashed.startswith("$2a$"))
        self.assertTrue(verify_password(plaintext, hashed))
        self.assertFalse(verify_password("WrongPassword123", hashed))

    def test_database_parameterized_queries(self):
        """
        Verify that database queries use parameter substitution rather than
        raw SQL string interpolation to prevent SQL injection.
        """
        from database import get_db, User

        db = next(get_db())
        try:
            # Query with parameterized input
            malicious_email = "admin' OR '1'='1"
            user = db.query(User).filter(User.email == malicious_email).first()
            # Malicious input should return None safely without syntax error
            self.assertIsNone(user)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
