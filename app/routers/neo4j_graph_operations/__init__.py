from fastapi import APIRouter

from .neo4j_graph_operations import _neo4j_graph_router

neo4j_graph_router = APIRouter()
neo4j_graph_router.include_router(router=_neo4j_graph_router)
