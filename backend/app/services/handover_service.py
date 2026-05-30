from datetime import datetime

from app.db.mongo import handover_collection
from app.models.schemas import HandoverRequest, HandoverResponse


class HandoverService:
    def create_handover(self, payload: HandoverRequest) -> HandoverResponse:
        document = {
            "session_id": payload.session_id,
            "reason": payload.reason,
            "transcript": payload.transcript or [],
            "status": "open",
            "created_at": datetime.utcnow(),
        }
        result = handover_collection.insert_one(document)
        return HandoverResponse(status="queued", handover_id=str(result.inserted_id))
