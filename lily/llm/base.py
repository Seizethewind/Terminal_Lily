"""What every LLM provider must offer."""
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Reply:
    data: dict            # the raw JSON answer from the server
    routed_via: str = ""  # X-Routed-Via header: which provider/model really answered


class Provider(Protocol):
    def chat(self, payload: dict) -> Reply:
        """Send a chat-completions payload and return the server's reply."""
