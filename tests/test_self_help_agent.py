"""
Unit tests for SelfHelpAgent (Strands Agents + Fake Bedrock Converse).
Verifies:
1. Greeting detection and capability intro generation.
2. Grounded RAG inquiry response generation with Strands.
3. Tool calling execution (clear_zoom_cache, escalate_to_l2_support) via Strands Agent.
4. Intent & confirmation detection helpers.
"""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agents.self_help_agent import SelfHelpAgent


class TestSelfHelpAgentStrands(unittest.TestCase):

    def setUp(self):
        self.agent = SelfHelpAgent()

    def test_greeting_detection(self):
        """Verify greeting identification without misclassifying technical issues."""
        self.assertTrue(self.agent.is_greeting("Hello"))
        self.assertTrue(self.agent.is_greeting("Hi there"))
        self.assertTrue(self.agent.is_greeting("good morning"))
        self.assertFalse(self.agent.is_greeting("Zoom is freezing and crashing"))
        self.assertFalse(self.agent.is_greeting("My camera is not working in Teams"))
        self.assertFalse(self.agent.is_greeting("Invoice tax code question"))

    @patch("boto3.Session")
    def test_generate_greeting_reply(self, mock_boto_session):
        """Verify greeting reply generated through Strands Agent."""
        mock_bedrock = MagicMock()
        mock_bedrock.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Hello Maya! I'm your Self Help Assistant for Meridian Enterprise IT Helpdesk. How can I help you today?"}]
                }
            },
            "stopReason": "end_turn"
        }
        sess_inst = MagicMock()
        sess_inst.client.return_value = mock_bedrock
        mock_boto_session.return_value = sess_inst

        agent = SelfHelpAgent()
        agent.aws_key = "test_key"
        agent.aws_secret = "test_secret"

        reply = agent.generate_greeting_reply("Hi")
        self.assertIn("Self Help Assistant", reply)
        mock_bedrock.converse.assert_called_once()

    @patch("boto3.Session")
    def test_generate_grounded_response_with_strands(self, mock_boto_session):
        """Verify standard grounded response generation with Confluence context."""
        mock_bedrock = MagicMock()
        mock_bedrock.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "To resolve Zoom performance issues, restart Zoom and verify your network connection."}]
                }
            },
            "stopReason": "end_turn"
        }
        sess_inst = MagicMock()
        sess_inst.client.return_value = mock_bedrock
        mock_boto_session.return_value = sess_inst

        agent = SelfHelpAgent()
        agent.aws_key = "test_key"
        agent.aws_secret = "test_secret"

        matches = [
            {"title": "Zoom Troubleshooting Guide", "text": "Clear cache or restart.", "score": 0.85}
        ]

        result = agent.generate_response(
            user_query="How do I troubleshoot Zoom?",
            chat_history=[],
            matches=matches
        )

        self.assertIn("restart Zoom", result["reply"])
        self.assertIsNone(result["action"])
        mock_bedrock.converse.assert_called_once()

    @patch("boto3.Session")
    def test_tool_calling_clear_zoom_cache_with_strands(self, mock_boto_session):
        """Verify Strands Agent executes clear_zoom_cache tool and records the action."""
        mock_bedrock = MagicMock()
        mock_bedrock.converse.side_effect = [
            # Turn 1: Bedrock requests clear_zoom_cache tool use
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "tool_zoom_1",
                                    "name": "clear_zoom_cache",
                                    "input": {"device_id": "maya-laptop"}
                                }
                            }
                        ]
                    }
                },
                "stopReason": "tool_use"
            },
            # Turn 2: Bedrock synthesizes final response after tool execution
            {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "I have executed the remote Zoom cache clear on your device. Please restart Zoom and log back in."}]
                    }
                },
                "stopReason": "end_turn"
            }
        ]
        sess_inst = MagicMock()
        sess_inst.client.return_value = mock_bedrock
        mock_boto_session.return_value = sess_inst

        agent = SelfHelpAgent()
        agent.aws_key = "test_key"
        agent.aws_secret = "test_secret"

        history = [
            {"role": "user", "content": "Zoom keeps freezing."},
            {"role": "assistant", "content": "I can run a remote Zoom fix to clear the Zoom cache. Would you like me to proceed?"}
        ]

        result = agent.generate_response(
            user_query="Yes, please go ahead and do it",
            chat_history=history,
            matches=[]
        )

        self.assertEqual(result["action"], "clear_zoom_cache")
        self.assertEqual(result["action_params"], {"device_id": "maya-laptop"})
        self.assertIn("executed the remote Zoom cache clear", result["reply"])
        self.assertEqual(mock_bedrock.converse.call_count, 2)

    def test_confirmation_helpers(self):
        """Verify confirmation and intent evaluation logic."""
        self.assertTrue(self.agent.is_escalation_confirmation("Please raise a ticket for me"))
        self.assertTrue(self.agent.is_escalation_confirmation("Can you escalate to human support?"))
        self.assertTrue(self.agent.is_resolved_signal("It works now, thanks!"))
        self.assertTrue(self.agent.is_resolved_signal("All good now, fixed!"))


if __name__ == "__main__":
    unittest.main()

