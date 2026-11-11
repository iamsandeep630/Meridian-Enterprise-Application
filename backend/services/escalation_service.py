"""
escalation_service.py - Real-Time Support Escalation, SSE Streams, and Live Chat Handoff
for Meridian Tech Helpdesk.
"""

import os
import json
import asyncio
import time
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

try:
    from . import meshcentral_service, jira_service
except ImportError:
    import meshcentral_service
    import jira_service

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

ESCALATIONS_FILE = os.path.join(DATA_DIR, "escalations.json")
CONVERSATIONS_FILE = os.path.join(DATA_DIR, "conversations.json")

# In-memory stores
escalation_store: list[dict] = []
conversation_store: dict[str, dict] = {}

# SSE Queues
dashboard_subscribers: set[asyncio.Queue] = set()
conversation_subscribers: dict[str, set[asyncio.Queue]] = {}


def save_stores():
    try:
        with open(ESCALATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(escalation_store, f, indent=2)
    except Exception as e:
        print(f"[EscalationService] Error saving escalations: {e}")

    try:
        serialized = []
        for cid, conv in conversation_store.items():
            serialized.append({
                "id": cid,
                "messages": conv.get("messages", []),
                "status": conv.get("status", "active"),
                "title": conv.get("title"),
                "ticketId": conv.get("ticketId"),
                "jiraKey": conv.get("jiraKey"),
                "issueSummary": conv.get("issueSummary"),
                "sharingLink": conv.get("sharingLink"),
                "chatLink": conv.get("chatLink"),
                "engineerJoined": conv.get("engineerJoined", False),
                "engineerJoinedAt": conv.get("engineerJoinedAt"),
                "engineerName": conv.get("engineerName"),
                "createdAt": conv.get("createdAt")
            })
        with open(CONVERSATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2)
    except Exception as e:
        print(f"[EscalationService] Error saving conversations: {e}")


def load_stores():
    global escalation_store, conversation_store
    try:
        if os.path.exists(ESCALATIONS_FILE):
            with open(ESCALATIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    escalation_store.clear()
                    escalation_store.extend(data)
                    print(f"[EscalationService] Loaded {len(escalation_store)} escalations from disk.")
    except Exception as e:
        print(f"[EscalationService] Error loading escalations: {e}")

    try:
        if os.path.exists(CONVERSATIONS_FILE):
            with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    conversation_store.clear()
                    for item in data:
                        cid = str(item.get("id"))
                        conversation_store[cid] = item
                    print(f"[EscalationService] Loaded {len(conversation_store)} conversations from disk.")
    except Exception as e:
        print(f"[EscalationService] Error loading conversations: {e}")


load_stores()


# ---------------- SSE Broadcasts ----------------
async def broadcast_dashboard(payload: dict):
    """Pushes a live event to all connected Support Engineer Dashboard clients."""
    msg = f"data: {json.dumps(payload)}\n\n"
    dead = []
    for q in list(dashboard_subscribers):
        try:
            await q.put(msg)
        except Exception:
            dead.append(q)
    for q in dead:
        dashboard_subscribers.discard(q)


async def broadcast_conversation(conv_id: str, payload: dict):
    """Pushes a live event to all clients connected to a specific conversation."""
    cid = str(conv_id)
    subs = conversation_subscribers.get(cid, set())
    msg = f"data: {json.dumps(payload)}\n\n"
    dead = []
    for q in list(subs):
        try:
            await q.put(msg)
        except Exception:
            dead.append(q)
    for q in dead:
        subs.discard(q)


def subscribe_dashboard() -> asyncio.Queue:
    q = asyncio.Queue()
    dashboard_subscribers.add(q)
    return q


def unsubscribe_dashboard(q: asyncio.Queue):
    dashboard_subscribers.discard(q)


def subscribe_conversation(conv_id: str) -> asyncio.Queue:
    cid = str(conv_id)
    if cid not in conversation_subscribers:
        conversation_subscribers[cid] = set()
    q = asyncio.Queue()
    conversation_subscribers[cid].add(q)
    return q


def unsubscribe_conversation(conv_id: str, q: asyncio.Queue):
    cid = str(conv_id)
    if cid in conversation_subscribers:
        conversation_subscribers[cid].discard(q)


# ---------------- Core Escalation Operations ----------------
async def get_dashboard_tickets() -> list[dict]:
    """
    Returns all escalation tickets, merging Jira tickets with local store data
    (remote desktop sharing links, device info, 30-min timers, and chat links).
    """
    now = datetime.utcnow()

    # Cleanse any expired status to real ticket status (tickets do not expire when remote links expire)
    for t in escalation_store:
        if t.get("status") == "expired":
            t["status"] = t.get("jiraStatus") or "L2 Confirmed"

    jira_tickets = jira_service.list_jira_tickets(limit=50)

    # Merge
    merged = list(jira_tickets)
    for local in escalation_store:
        match = next(
            (j for j in merged if (local.get("jiraKey") and j.get("key") == local.get("jiraKey")) or
                                  (local.get("id") and (j.get("id") == local.get("id") or j.get("key") == local.get("id")))),
            None
        )
        if match:
            # Synchronize status and assignee from local store
            if local.get("status"):
                match["status"] = local["status"]
            if local.get("assignedTo"):
                match["assignedTo"] = local["assignedTo"]
            if local.get("assignee"):
                match["assignee"] = local["assignee"]
            if local.get("notes"):
                match["notes"] = local["notes"]
            if local.get("resolvedAt"):
                match["resolvedAt"] = local["resolvedAt"]

            if not match.get("sharingLink") and local.get("sharingLink"):
                match["sharingLink"] = local["sharingLink"]
            if not match.get("chatLink") and local.get("chatLink"):
                match["chatLink"] = local["chatLink"]
            if not match.get("conversationId") and local.get("conversationId"):
                match["conversationId"] = local["conversationId"]
            if not match.get("linkExpiresAt") and (local.get("linkExpiresAt") or local.get("expiresAt")):
                match["linkExpiresAt"] = local.get("linkExpiresAt") or local.get("expiresAt")
            if not match.get("deviceName") and local.get("deviceName"):
                match["deviceName"] = local["deviceName"]
            if not match.get("deviceOs") and local.get("deviceOs"):
                match["deviceOs"] = local["deviceOs"]
            if not match.get("currentUsers") and local.get("currentUsers"):
                match["currentUsers"] = local["currentUsers"]
            if not match.get("executionDetails") and local.get("executionDetails"):
                match["executionDetails"] = local["executionDetails"]
        else:
            merged.append(local)

    # Secondary pass to ensure all have chatLink and expiry
    for t in merged:
        cid = t.get("conversationId")
        if not cid:
            # check conversation store
            for c_id, conv in conversation_store.items():
                if (t.get("jiraKey") and conv.get("jiraKey") == t.get("jiraKey")) or (t.get("id") and conv.get("ticketId") == t.get("id")):
                    t["conversationId"] = c_id
                    t["chatLink"] = f"http://localhost:8001/support/chat/{c_id}"
                    break
        elif not t.get("chatLink"):
            t["chatLink"] = f"http://localhost:8001/support/chat/{cid}"

        if t.get("sharingLink") and not t.get("linkExpiresAt") and t.get("createdAt"):
            try:
                base = datetime.fromisoformat(t["createdAt"].replace("Z", "+00:00")).replace(tzinfo=None)
                t["linkExpiresAt"] = (base + timedelta(minutes=30)).isoformat() + "Z"
                t["expiresAt"] = t["linkExpiresAt"]
            except Exception:
                pass

    # Sort descending by createdAt
    def parse_time(item):
        s = item.get("createdAt") or ""
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
        except Exception:
            return 0.0

    merged.sort(key=parse_time, reverse=True)
    return merged


async def escalate_session(
    session_id: int,
    user_email: str,
    issue_summary: str,
    execution_details: str = "",
    device_id: str | None = None,
    requires_remote_desktop: bool | None = None
) -> dict:
    """
    Escalates an issue to L2 Support:
      1. Generates 30-min MeshCentral remote desktop sharing link
      2. Creates / attaches Jira Cloud ticket in project KAN
      3. Sets ticket to 'L2 Confirmed' assigned to Support Engineer
      4. Links conversation for Alex <-> Maya human handoff
      5. Pushes live SSE update to Support Engineer Dashboard
    """
    cid = str(session_id)
    now = datetime.utcnow()
    now_iso = now.isoformat() + "Z"
    chat_link = f"http://localhost:8001/support/chat/{cid}"

    # Part 2 & Part 3: Evaluate LLM classification with Python safety net fallback
    if requires_remote_desktop is False:
        is_enterprise_issue = True
    elif requires_remote_desktop is True:
        is_enterprise_issue = False
    else:
        # Fallback safety net (Part 3 Guardrail): Keyword inspection
        enterprise_keywords = [
            "invoice", "dropdown", "product", "catalog", "tax", "gst",
            "leave", "ledger", "billing", "policy", "webcam pro", "4k webcam",
            "checkbox", "check box", "tick", "ticked", "button", "functionality",
            "un-operational", "unoperational", "bug", "crash", "application", "portal", "ui"
        ]
        is_enterprise_issue = any(k in (issue_summary or "").lower() for k in enterprise_keywords)

    if is_enterprise_issue:
        # Enterprise application / catalog issues do NOT require a device remote desktop link
        sharing_info = {"deviceId": "enterprise-cloud"}
        sharing_link = None
        expires_at = None
        device_name = "Enterprise Cloud Services"
        device_os = "Web Platform"
        device_ip = "127.0.0.1"
        current_users = [user_email]
        dev_diag = {
            "name": device_name,
            "os": device_os,
            "ip": device_ip,
            "currentUsers": current_users,
            "category": "Enterprise Application"
        }
    else:
        # 1. MeshCentral 30-min sharing link for device/hardware issues
        sharing_info = meshcentral_service.create_device_sharing_link(device_id=device_id, duration_minutes=30)
        sharing_link = sharing_info.get("sharingLink", "")
        expires_at = sharing_info.get("expiresAt", (now + timedelta(minutes=30)).isoformat() + "Z")
        device_name = sharing_info.get("deviceName", "AVDGLS5-4")
        device_os = sharing_info.get("deviceOs", "Microsoft Windows 11 Enterprise")
        device_ip = sharing_info.get("deviceIp", "10.73.87.230")
        current_users = sharing_info.get("currentUsers", ["AzureAD\\SANDEEPDUBEY"])
        dev_diag = {
            "name": device_name,
            "os": device_os,
            "ip": device_ip,
            "currentUsers": current_users
        }
    chat_history = []
    if cid in conversation_store:
        chat_history = conversation_store[cid].get("messages", [])

    jira_res = jira_service.create_jira_issue(
        session_id=session_id,
        user_email=user_email,
        user_query=issue_summary,
        chat_history=chat_history,
        device_info=dev_diag,
        sharing_link=sharing_link,
        chat_link=chat_link
    )
    instance_url, _, _, project_key = jira_service._get_jira_config()
    jira_key = jira_res.get("ticket_key", f"{project_key}-{session_id}")
    jira_url = jira_res.get("ticket_url", f"{instance_url}/browse/{jira_key}")

    # 3. Create Ticket Record
    esc_id = f"ESC-{session_id}-{uuid.uuid4().hex[:4].upper()}"
    ticket = {
        "id": esc_id,
        "jiraKey": jira_key,
        "jiraUrl": jira_url,
        "jiraStatus": "L2 Confirmed",
        "deviceId": sharing_info.get("deviceId", "default"),
        "deviceName": device_name,
        "deviceOs": device_os,
        "deviceIp": device_ip,
        "currentUsers": current_users,
        "issueSummary": issue_summary,
        "summary": issue_summary,
        "executionDetails": execution_details or "Remediation session escalated to L2 Support Engineer.",
        "sharingLink": sharing_link,
        "conversationId": cid,
        "chatLink": chat_link,
        "status": "new",
        "assignedTo": "Support Engineer",
        "assignee": "Support Engineer",
        "createdAt": now_iso,
        "linkExpiresAt": expires_at,
        "expiresAt": expires_at,
        "resolvedAt": None,
        "notes": ""
    }

    # Add to escalation store
    escalation_store.insert(0, ticket)

    # Update conversation store
    if cid not in conversation_store:
        conversation_store[cid] = {"messages": [], "status": "active", "title": issue_summary}
    conv = conversation_store[cid]
    conv["status"] = "escalated"
    conv["escalatedAt"] = now_iso
    conv["ticketId"] = esc_id
    conv["jiraKey"] = jira_key
    conv["issueSummary"] = issue_summary
    conv["sharingLink"] = sharing_link
    conv["chatLink"] = chat_link

    handoff_text = f"Live Handoff Initiated: Issue escalated to L2 Support Engineer (Alex Turner). Jira: {jira_key}."
    conv.setdefault("messages", []).append({
        "id": f"handoff-{cid}-{int(now.timestamp())}",
        "role": "system",
        "kind": "handoff",
        "type": "handoff",
        "content": handoff_text,
        "jiraKey": jira_key,
        "jiraUrl": jira_url,
        "sharingLink": sharing_link,
        "timestamp": now_iso
    })

    save_stores()

    # Broadcast live handoff event to conversation clients
    await broadcast_conversation(cid, {
        "type": "handoff",
        "message": handoff_text,
        "jiraKey": jira_key,
        "sharingLink": sharing_link,
        "time": now_iso
    })

    # Broadcast live update to Support Engineer Dashboard
    await broadcast_dashboard({
        "type": "live_update",
        "payload": ticket,
        "time": now_iso
    })

    link_preview = sharing_link[:40] if sharing_link else "None (Enterprise Software)"
    print(f"[EscalationService] Escalated session #{session_id} -> {jira_key} (Link: {link_preview})")
    return ticket


async def create_remediation_ticket(
    session_id: int,
    user_email: str,
    issue_summary: str,
    device_info: dict | None = None,
    execution_details: str = "Automated remediation initiated."
) -> dict:
    """
    Creates a Jira ticket and registers it in the escalation/dashboard store BEFORE
    executing an automated remote action (e.g. Zoom cache clear).
    Initial status: 'In Progress', Assignee: 'Bot'.
    """
    cid = str(session_id)
    now = datetime.utcnow()
    now_iso = now.isoformat() + "Z"
    chat_link = f"http://localhost:8001/support/chat/{cid}"

    device_name = (device_info or {}).get("name", "AVDGLS5-4")
    device_os = (device_info or {}).get("os", "Microsoft Windows 11 Enterprise")
    device_ip = (device_info or {}).get("ip", "10.73.87.230")
    current_users = (device_info or {}).get("currentUsers", ["AzureAD\\SANDEEPDUBEY"])
    device_id = (device_info or {}).get("id", "default")

    chat_history = []
    if cid in conversation_store:
        chat_history = conversation_store[cid].get("messages", [])

    # Create ticket in Jira Cloud with initial_status='In Progress' and assignee='Bot'
    jira_res = jira_service.create_jira_issue(
        session_id=session_id,
        user_email=user_email,
        user_query=issue_summary,
        chat_history=chat_history,
        device_info=device_info,
        sharing_link="",
        chat_link=chat_link,
        initial_status="In Progress",
        assignee_type="Bot"
    )
    instance_url, _, _, project_key = jira_service._get_jira_config()
    jira_key = jira_res.get("ticket_key", f"{project_key}-{session_id}")
    jira_url = jira_res.get("ticket_url", f"{instance_url}/browse/{jira_key}")

    # Ensure Jira status is transitioned to 'In Progress' and assigned to 'Bot'
    jira_service.transition_jira_ticket(jira_key, "In Progress")
    jira_service.set_jira_assignee(jira_key, "Bot")

    esc_id = f"ESC-{session_id}-{uuid.uuid4().hex[:4].upper()}"
    ticket = {
        "id": esc_id,
        "jiraKey": jira_key,
        "jiraUrl": jira_url,
        "jiraStatus": "In Progress",
        "status": "In Progress",
        "deviceId": device_id,
        "deviceName": device_name,
        "deviceOs": device_os,
        "deviceIp": device_ip,
        "currentUsers": current_users,
        "issueSummary": issue_summary,
        "summary": issue_summary,
        "executionDetails": execution_details,
        "sharingLink": "",
        "conversationId": cid,
        "chatLink": chat_link,
        "assignedTo": "Bot",
        "assignee": "Bot",
        "createdAt": now_iso,
        "linkExpiresAt": None,
        "expiresAt": None,
        "resolvedAt": None,
        "notes": "Automated remote action initiated by Bot."
    }

    escalation_store.insert(0, ticket)

    if cid not in conversation_store:
        conversation_store[cid] = {"messages": [], "status": "active", "title": issue_summary}
    conv = conversation_store[cid]
    conv["ticketId"] = esc_id
    conv["jiraKey"] = jira_key
    conv["issueSummary"] = issue_summary
    conv["chatLink"] = chat_link
    conv["assignedTo"] = "Bot"
    conv["status"] = "in_progress"

    save_stores()

    # Broadcast live update to Support Engineer Dashboard
    await broadcast_dashboard({
        "type": "live_update",
        "payload": ticket,
        "time": now_iso
    })

    print(f"[EscalationService] Created remediation ticket {esc_id} (Jira: {jira_key}, status: In Progress)")
    return ticket


async def mark_ticket_bot_resolved(session_id_or_key: str | int, comment: str = "") -> dict:
    """
    Marks a ticket as 'Bot Resolved' across Jira Cloud and local dashboard store.
    Broadcasts the resolution event to the Support Engineer Dashboard.
    """
    cid = str(session_id_or_key)
    local_ticket = next((
        t for t in escalation_store
        if t.get("id") == cid or t.get("jiraKey") == cid or str(t.get("conversationId")) == cid
    ), None)

    # Resolve target Jira issue key across any project key format (e.g. SCRUM-12, KAN-5)
    target_key = None
    if local_ticket and local_ticket.get("jiraKey"):
        target_key = local_ticket.get("jiraKey")
    elif "-" in cid and not cid.startswith("ESC-"):
        target_key = cid
    elif cid in conversation_store and conversation_store[cid].get("jiraKey"):
        target_key = conversation_store[cid].get("jiraKey")
    else:
        for t in escalation_store:
            if (str(t.get("conversationId")) == cid or t.get("id") == cid) and t.get("jiraKey"):
                target_key = t.get("jiraKey")
                local_ticket = t
                break

    now_iso = datetime.utcnow().isoformat() + "Z"
    resolution_comment = comment or "✅ Issue confirmed resolved by user after automated Bot remediation."

    if target_key:
        print(f"[EscalationService] Updating Jira ticket {target_key} to 'Bot Resolved'...")
        jira_service.update_jira_ticket(
            ticket_key=target_key,
            status="Bot Resolved",
            comment=resolution_comment
        )

    if local_ticket:
        local_ticket["status"] = "Bot Resolved"
        local_ticket["jiraStatus"] = "Bot Resolved"
        local_ticket["assignedTo"] = "Bot"
        local_ticket["assignee"] = "Bot"
        local_ticket["resolvedAt"] = now_iso
        local_ticket["notes"] = resolution_comment
    else:
        local_ticket = {
            "id": f"ESC-{cid}",
            "jiraKey": target_key or cid,
            "status": "Bot Resolved",
            "jiraStatus": "Bot Resolved",
            "assignedTo": "Bot",
            "assignee": "Bot",
            "notes": resolution_comment,
            "conversationId": cid,
            "createdAt": now_iso,
            "resolvedAt": now_iso
        }
        escalation_store.insert(0, local_ticket)

    if cid in conversation_store:
        conversation_store[cid]["status"] = "resolved"

    save_stores()

    await broadcast_dashboard({
        "type": "ticket_updated",
        "id": local_ticket.get("id") or cid,
        "jiraKey": target_key,
        "status": "Bot Resolved",
        "assignedTo": "Bot",
        "time": now_iso
    })

    print(f"[EscalationService] Ticket for session/key {cid} (Jira: {target_key}) marked as 'Bot Resolved'")
    return {"success": True, "status": "Bot Resolved", "jiraKey": target_key}


async def update_ticket_status(
    ticket_id_or_key: str,
    status: str,
    assigned_to: str = "Support Engineer",
    notes: str = ""
) -> dict:
    """Updates status in Jira and local store, broadcasts to dashboard SSE."""
    local_ticket = next((t for t in escalation_store if t.get("id") == ticket_id_or_key or t.get("jiraKey") == ticket_id_or_key), None)
    target_jira_key = ticket_id_or_key if ("-" in ticket_id_or_key and not ticket_id_or_key.startswith("ESC-")) else (local_ticket.get("jiraKey") if local_ticket else None)

    updated_status = status
    if target_jira_key:
        trans_res = jira_service.transition_jira_ticket(target_jira_key, status)
        updated_status = trans_res.get("status", status)

        comment = f"🛠️ *L2 Support Update:* Status changed to *{updated_status}* by {assigned_to}."
        if notes:
            comment += f"\n*Notes:* {notes}"
        jira_service.add_jira_comment(target_jira_key, comment)
        if assigned_to:
            jira_service.set_jira_assignee(target_jira_key, assigned_to)

    if local_ticket:
        local_ticket["status"] = status
        local_ticket["jiraStatus"] = updated_status
        local_ticket["assignedTo"] = assigned_to
        local_ticket["assignee"] = assigned_to
        if notes:
            local_ticket["notes"] = notes
        if "resolve" in status.lower():
            local_ticket["resolvedAt"] = datetime.utcnow().isoformat() + "Z"
    else:
        local_ticket = {
            "id": ticket_id_or_key,
            "jiraKey": target_jira_key or ticket_id_or_key,
            "status": status,
            "jiraStatus": updated_status,
            "assignedTo": assigned_to,
            "assignee": assigned_to,
            "notes": notes,
            "createdAt": datetime.utcnow().isoformat() + "Z"
        }
        if "resolve" in status.lower():
            local_ticket["resolvedAt"] = datetime.utcnow().isoformat() + "Z"
        escalation_store.insert(0, local_ticket)

    save_stores()

    # Broadcast
    await broadcast_dashboard({
        "type": "ticket_updated",
        "id": ticket_id_or_key,
        "jiraKey": target_jira_key,
        "status": updated_status,
        "assignedTo": assigned_to,
        "time": datetime.utcnow().isoformat() + "Z"
    })

    return {
        "success": True,
        "id": ticket_id_or_key,
        "jiraKey": target_jira_key,
        "status": updated_status,
        "ticket": local_ticket or {"id": ticket_id_or_key, "status": updated_status, "assignedTo": assigned_to}
    }


async def engineer_join_conversation(conv_id: str, engineer_name: str = "Alex (Support Engineer)") -> dict:
    """Announces Support Engineer joining the chat session."""
    cid = str(conv_id)
    if cid not in conversation_store:
        conversation_store[cid] = {"messages": [], "status": "active", "title": "Support Escalation"}

    conv = conversation_store[cid]
    conv["status"] = "engineer_joined"
    conv["engineerJoined"] = True
    conv["engineerJoinedAt"] = datetime.utcnow().isoformat() + "Z"
    conv["engineerName"] = engineer_name

    join_text = f"{engineer_name} has connected to this support chat session."
    if not any(m.get("kind") == "engineer_joined" or "has connected" in m.get("content", "") for m in conv.setdefault("messages", [])):
        conv["messages"].append({
            "id": f"join-{cid}-{int(time.time()*1000)}",
            "role": "system",
            "kind": "engineer_joined",
            "type": "engineer_joined",
            "engineerName": engineer_name,
            "content": join_text,
            "timestamp": conv["engineerJoinedAt"]
        })

    save_stores()

    # Broadcast to conversation clients
    payload = {
        "type": "engineer_joined",
        "engineerName": engineer_name,
        "time": conv["engineerJoinedAt"]
    }
    await broadcast_conversation(cid, payload)

    # Broadcast to dashboard
    await broadcast_dashboard({
        "type": "engineer_joined",
        "conversationId": cid,
        "engineerName": engineer_name,
        "time": conv["engineerJoinedAt"]
    })

    print(f"[Chat {cid}] Support Engineer ({engineer_name}) joined.")
    return {"success": True, "status": "engineer_joined", "engineerName": engineer_name}


async def post_conversation_message(conv_id: str, sender: str, content: str) -> dict:
    """Sends a message into a conversation (used by Alex or Maya)."""
    cid = str(conv_id)
    if cid not in conversation_store:
        conversation_store[cid] = {"messages": [], "status": "active", "title": "Support Escalation"}

    conv = conversation_store[cid]
    role = "user" if sender == "user" else "engineer"
    msg = {
        "id": f"{role}-{int(time.time()*1000)}-{uuid.uuid4().hex[:4]}",
        "role": role,
        "content": content.strip(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    conv["messages"].append(msg)
    if role == "engineer":
        conv["status"] = "engineer_joined"
        conv["engineerJoined"] = True

    save_stores()

    # Broadcast via SSE
    await broadcast_conversation(cid, {"type": "message", "message": msg})
    return {"success": True, "message": msg}

# Backward compatibility aliases
get_escalations = get_dashboard_tickets
update_escalation_status = update_ticket_status


async def delete_escalation_ticket(ticket_id_or_key: str) -> bool:
    """Removes an escalation ticket by ID or Jira key from local store."""
    global escalation_store, conversation_store
    key = str(ticket_id_or_key).strip()
    idx = -1
    for i, t in enumerate(escalation_store):
        if str(t.get("id")) == key or str(t.get("jiraKey")) == key or str(t.get("conversationId")) == key:
            idx = i
            break
    if idx != -1:
        escalation_store.pop(idx)
        save_stores()
        await broadcast_dashboard({"type": "ticket_deleted", "ticketId": key})
        print(f"[EscalationService] Deleted escalation ticket: {key}")
        return True
    return False
