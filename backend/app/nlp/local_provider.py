from app.models.schemas import NLPResult
from app.nlp.base import NLPProvider


class LocalNLPProvider(NLPProvider):
    def __init__(self):
        # Basic keyword mapping for the seeded intents
        self.intent_keywords = {
            "Greeting": ["hello", "hi", "hey", "greetings"],
            "Order_Status": ["order", "status", "track", "where", "package"],
            "Refund_Request": ["refund", "return", "money", "back"],
            "Complaint_Product": ["broken", "defect", "complain", "issue", "problem", "wrong"],
            "Goodbye": ["bye", "goodbye", "see you", "exit"],
        }

    def parse(self, text: str, session_id: str) -> NLPResult:
        text_lower = text.lower()
        
        best_intent = "Fallback"
        best_score = 0.0
        
        for intent, keywords in self.intent_keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                # Calculate a rudimentary confidence score based on matches
                # If it matches 1 keyword it gets 0.8, 2 keywords gets 0.9, etc.
                score = min(0.7 + (matches * 0.1), 1.0)
                if score > best_score:
                    best_score = score
                    best_intent = intent
                    
        return NLPResult(
            intent=best_intent,
            confidence=best_score if best_score > 0 else 0.0,
            entities={},
            raw_text=text,
        )
