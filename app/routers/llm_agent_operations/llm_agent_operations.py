import os

from fastapi import APIRouter
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, validator

from app.core.controllers.llm_agent_controller import LLMAgentController
from app.settings.config import settings

_llm_agent_router = APIRouter(
    prefix="/v1/llm_agent_operations", tags=["llm_agent_operations"]
)

os.environ["LANGCHAIN_TRACING_V2"] = settings.get("LANGCHAIN_TRACING_V2")
os.environ["LANGCHAIN_API_KEY"] = settings.get("LANGCHAIN_API_KEY")


class ChatBotRequest(BaseModel):
    question: str
    model: str = "groq"
    embedding_model: str = "hugging_face"

    @validator("question")
    def validate_company_name(cls, v: str):
        if not v:
            raise ValueError("question must be a non-empty string")
        return v


@_llm_agent_router.post("/ask_agent/")
async def ask_agent(request: ChatBotRequest):
    response = LLMAgentController(request.model, request.embedding_model)
    for s in response().stream(
        {
            "question": request.question,
            "chat_history": [],
            "answer": "",
            "messages": HumanMessage(content=request.question),
        },
        {"recursion_limit": 15},
    ):
        if "__end__" not in s:
            print(s)
            print("---")
