import requests

from app.config import settings
from app.db.mongo import messages_collection


class AIFallbackService:
    def generate_reply(self, user_message: str, session_id: str) -> str:
        if not settings.openai_api_key:
            return "I am not fully confident. Please share more details or request a human agent."

        try:
            # Fetch recent messages for context to make the bot actually helpful
            recent_docs = list(messages_collection.find({"session_id": session_id}).sort("_id", 1).limit(10))
            messages = [
                {
                    "role": "system",
                    "content": "You are a concise and helpful customer support assistant.",
                }
            ]
            
            for doc in recent_docs:
                role = "assistant" if doc.get("sender") == "bot" else "user"
                if doc.get("text"):
                    messages.append({"role": role, "content": doc["text"]})
            
            # If the current user_message isn't already in the DB (though it should be), add it just in case
            if not any(m.get("content") == user_message and m.get("role") == "user" for m in messages):
                messages.append({"role": "user", "content": user_message})

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.openai_model,
                    "messages": messages,
                    "temperature": 0.2,
                },
                timeout=10,
            )
            
            data = response.json()
            if response.status_code != 200:
                error_msg = data.get("error", {}).get("message", "Unknown API error")
                if "quota" in error_msg.lower():
                    return "Sorry, the AI service is currently unavailable due to quota limits. Please try again later or request a human agent."
                return f"Sorry, an error occurred with the AI service: {error_msg}"
                
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"I am not fully confident. Please share more details or request a human agent. (Error: {str(e)})"
