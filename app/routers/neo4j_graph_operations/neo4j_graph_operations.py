from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.controllers.neo4j_graph_controller import (Neo4JAsk,
                                                         Neo4JGraphBuilder)

_neo4j_graph_router = APIRouter(
    prefix="/v1/neo4j_graph_operations", tags=["neo4j_graph_operations"]
)


@_neo4j_graph_router.post("/load_documents/")
async def upload_file(
    neo4j_graph_controller: Annotated[Neo4JGraphBuilder, Depends()],
    file: UploadFile = File(...),
):
    contents = await file.read()
    results = neo4j_graph_controller.upload_to_neo4j_database(contents)
    return results


@_neo4j_graph_router.post("/ask_question/")
async def ask_question(
    neo4j_graph_controller: Annotated[Neo4JAsk, Depends()], question: str
):
    results = neo4j_graph_controller.ask_question(question)
    return results
