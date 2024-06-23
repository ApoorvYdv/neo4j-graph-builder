from fastapi import APIRouter

from .llm_agent_operations import _llm_agent_router

llm_agent_router = APIRouter()
llm_agent_router.include_router(router=_llm_agent_router)
