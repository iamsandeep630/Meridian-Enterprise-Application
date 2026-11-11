"""
Support Engineer Escalations & Live Ticket Streams
"""
import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from services import escalation_service

router = APIRouter(tags=["Support"])

@router.get("/api/escalations")
async def get_escalations():
    """Returns active escalations with live 30-min countdowns."""
    tickets = await escalation_service.get_dashboard_tickets()
    return {"success": True, "count": len(tickets), "tickets": tickets}

@router.get("/api/tickets/live")
async def sse_tickets():
    """Real-time SSE stream for Support Engineer Dashboard."""
    q = escalation_service.subscribe_dashboard()
    async def event_generator():
        try:
            connected_data = json.dumps({"type": "connected", "time": datetime.utcnow().isoformat()})
            yield "data: " + connected_data + "\n\n"
            while True:
                msg = await q.get()
                yield msg
        except asyncio.CancelledError:
            pass
        finally:
            escalation_service.unsubscribe_dashboard(q)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/api/escalations/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, req: dict):
    new_status = req.get("status")
    assigned_to = req.get("assignedTo", "Support Engineer")
    notes = req.get("notes", "")
    if not new_status:
        raise HTTPException(status_code=400, detail="Missing status")
    res = await escalation_service.update_ticket_status(ticket_id, new_status, assigned_to=assigned_to, notes=notes)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail="Ticket not found")
    return res
