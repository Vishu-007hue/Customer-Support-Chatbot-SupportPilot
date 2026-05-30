import requests

from app.config import settings
from app.models.schemas import NLPResult
from app.nlp.base import NLPProvider


class RasaProvider(NLPProvider):
    def parse(self, text: str, session_id: str) -> NLPResult:
        payload = {"text": text, "message_id": session_id}
        response = requests.post(settings.rasa_endpoint, json=payload, timeout=8)
        response.raise_for_status()
        data = response.json()

        intent_data = data.get("intent") or {}
        entities = data.get("entities") or []

        normalized_entities = {}
        for entity in entities:
            key = entity.get("entity", "unknown")
            normalized_entities[key] = entity.get("value")

        return NLPResult(
            intent=intent_data.get("name", "Fallback"),
            confidence=float(intent_data.get("confidence", 0.0)),
            entities=normalized_entities,
            raw_text=text,
        )
