from app.config import settings
from app.nlp.base import NLPProvider
from app.nlp.dialogflow_provider import DialogflowProvider
from app.nlp.rasa_provider import RasaProvider
from app.nlp.local_provider import LocalNLPProvider


def get_nlp_provider() -> NLPProvider:
    provider = settings.nlp_provider.strip().lower()
    if provider == "rasa":
        return RasaProvider()
    if provider == "local":
        return LocalNLPProvider()
    return DialogflowProvider()

