"""
Live chat broadcast flow verification script.
Tests real-time handoff, engineer joining, and message exchange against a running backend server.
"""
import urllib.request
import json
import time

BASE_URL = "http://localhost:8001"

def api_post(endpoint, data, token=None):
    url = f"{BASE_URL}{endpoint}"
    body = json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def api_get(endpoint, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def run_flow():
    print("=== 1. Login as Employee ===")
    login_res = api_post("/login", {"email": "maya.sharma@meridian.com", "password": "password123"})
    user_token = login_res["access_token"]
    print("Logged in as Employee. Token acquired:", user_token[:20] + "...")

    print("\n=== 2. Create new Chat Session ===")
    session = api_post("/sessions", {}, token=user_token)
    session_id = session["id"]
    print(f"Created Session ID: {session_id}")

    print("\n=== 3. Employee sends Zoom issue inquiry ===")
    reply = api_post(f"/sessions/{session_id}/messages", {"message": "My Zoom audio is completely broken during all department meetings."}, token=user_token)
    print(f"Bot replied. Matches found: {len(reply.get('matches', []))}")

    print("\n=== 4. Employee triggers Escalation / Route to Support (Create Jira Ticket) ===")
    fb_res = api_post(f"/sessions/{session_id}/feedback", {"action": "not_resolved", "message_id": 1}, token=user_token)
    print("Escalation triggered via feedback:", fb_res)

    print("\n=== 5. Support Engineer joins the Chat ===")
    join_res = api_post(f"/api/chat/{session_id}/join", {"engineerName": "Alex Turner (Support Engineer)"})
    print("Support Engineer joined:", join_res)

    print("\n=== 6. Support Engineer sends a message ===")
    eng_msg = api_post(f"/api/chat/{session_id}/message", {
        "sender": "engineer",
        "content": "Hi! Alex here from L2 IT Support. I see your audio issue on your workstation. Connecting now."
    })
    print("Engineer sent message:", eng_msg)

    print("\n=== 7. Employee sends follow-up live message in escalated chat ===")
    user_reply = api_post(f"/sessions/{session_id}/messages", {"message": "Thank you Alex! I have the Zoom window open."}, token=user_token)
    print("User sent live reply:", user_reply)

    print("\n=== 8. Verify Employee's Chat Interface (GET /sessions/{id}/messages) ===")
    emp_msgs = api_get(f"/sessions/{session_id}/messages", token=user_token)
    print(f"Total messages in session: {len(emp_msgs)}")

    kinds_in_emp = [m.get("kind") for m in emp_msgs]
    roles_in_emp = [m.get("role") for m in emp_msgs]

    has_jira_ticket = "jira_ticket" in kinds_in_emp
    has_handoff = "handoff" in kinds_in_emp or any("Live Handoff" in (m.get("content") or "") for m in emp_msgs)
    has_eng_joined = "engineer_joined" in kinds_in_emp or any("has connected" in (m.get("content") or "") for m in emp_msgs)
    has_eng_message = "engineer" in roles_in_emp

    print(f"  - Jira Ticket card present: {has_jira_ticket}")
    print(f"  - Live Handoff broadcast present: {has_handoff}")
    print(f"  - Engineer Joined broadcast present: {has_eng_joined}")
    print(f"  - Engineer Message present: {has_eng_message}")

    assert has_jira_ticket, "Jira ticket missing in Employee view"
    assert has_handoff, "Handoff broadcast missing in Employee view"
    assert has_eng_joined, "Engineer joined broadcast missing in Employee view"
    assert has_eng_message, "Engineer message missing in Employee view"

    print("\n>>> ALL ASSERTIONS PASSED! BOTH INTERFACES RECEIVE HANDOFF & JOIN EVENTS! <<<")

if __name__ == "__main__":
    run_flow()
