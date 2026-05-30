import os
from uuid import uuid4

from app.config import settings
from app.models.schemas import NLPResult
from app.nlp.base import NLPProvider


class DialogflowProvider(NLPProvider):
    def __init__(self) -> None:
        if settings.dialogflow_credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.dialogflow_credentials_path

        from google.cloud import dialogflow_v2 as dialogflow

        self.dialogflow = dialogflow
        self.session_client = dialogflow.SessionsClient()

    def parse(self, text: str, session_id: str) -> NLPResult:
        session = self.session_client.session_path(
            settings.dialogflow_project_id, session_id or str(uuid4())
        )
        text_input = self.dialogflow.TextInput(
            text=text, language_code=settings.dialogflow_language_code
        )
        query_input = self.dialogflow.QueryInput(text=text_input)
        response = self.session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )

        result = response.query_result
        params = dict(result.parameters) if result.parameters else {}
        intent = result.intent.display_name if result.intent else "Fallback"
        confidence = float(result.intent_detection_confidence or 0.0)

        return NLPResult(
            intent=intent,
            confidence=confidence,
            entities=params,
            raw_text=result.query_text or text,
        )
