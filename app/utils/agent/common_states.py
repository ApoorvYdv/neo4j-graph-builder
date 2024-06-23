from typing import Annotated, List, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class BaseTeamState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    chat_history: str
    question: str
    answer: str


class CypherTeamState(BaseTeamState, TypedDict):
    next: str
    generation: str
    documents: List
