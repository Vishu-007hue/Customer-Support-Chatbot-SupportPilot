from app.config import settings
from app.db.mongo import messages_collection, responses_collection
from app.models.schemas import ChatRequest, ChatResponse, MessageDocument, NLPResult
from app.services.ai_fallback_service import AIFallbackService
from app.services.response_cache_service import ResponseCacheService
from app.nlp.factory import get_nlp_provider


class ChatService:
    def __init__(self) -> None:
        self.nlp = get_nlp_provider()
        self.ai_fallback = AIFallbackService()
        self.cache = ResponseCacheService()

    def _get_response_for_intent(self, intent: str) -> str | None:
        cached_reply = self.cache.get(intent)
        if cached_reply:
            return cached_reply

        record = responses_collection.find_one({"intent": intent})
        if not record:
            return None
        variants = record.get("variants", [])
        selected = variants[0] if variants else None
        if selected:
            self.cache.set(intent, selected)
        return selected

    def get_history(self, session_id: str) -> list[MessageDocument]:
        docs = list(messages_collection.find({"session_id": session_id}).sort("created_at", 1))
        # Remove mongo _id before validating
        for d in docs:
            d.pop("_id", None)
        return [MessageDocument(**d) for d in docs]

    def handle_chat(self, payload: ChatRequest) -> ChatResponse:
        user_msg = MessageDocument(
            session_id=payload.session_id,
            sender="user",
            text=payload.message,
        )
        messages_collection.insert_one(user_msg.model_dump())

        try:
            nlp_result = self.nlp.parse(payload.message, payload.session_id)
        except Exception:  # noqa: BLE001
            # Keep chat functional even when external NLP services are offline.
            nlp_result = NLPResult(
                intent="Fallback",
                confidence=0.0,
                entities={},
                raw_text=payload.message,
            )

        handover_suggested = False
        source = "intent-db"

        if nlp_result.confidence >= settings.confidence_threshold:
            reply = self._get_response_for_intent(nlp_result.intent)
            if not reply:
                reply = "I understand your request. A support agent will assist shortly."
                source = "default-high-confidence"
        elif nlp_result.confidence >= settings.low_confidence_threshold:
            reply = "Can you share a bit more detail so I can help better?"
            source = "clarification"
        else:
            reply = self.ai_fallback.generate_reply(payload.message, payload.session_id)
            source = "ai-fallback"
            handover_suggested = True

        bot_msg = MessageDocument(
            session_id=payload.session_id,
            sender="bot",
            text=reply,
            intent=nlp_result.intent,
            confidence=nlp_result.confidence,
        )
        messages_collection.insert_one(bot_msg.model_dump())

        return ChatResponse(
            reply=reply,
            intent=nlp_result.intent,
            confidence=nlp_result.confidence,
            handover_suggested=handover_suggested,
            source=source,
        )
