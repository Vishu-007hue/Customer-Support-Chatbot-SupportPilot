from abc import ABC, abstractmethod

from app.models.schemas import NLPResult


class NLPProvider(ABC):
    @abstractmethod
    def parse(self, text: str, session_id: str) -> NLPResult:
        raise NotImplementedError
