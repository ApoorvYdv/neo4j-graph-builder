from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.routers import llm_agent_operations, neo4j_graph_operations
from app.settings.config import settings

description = """
Neo4j With LLM
"""

app = FastAPI(
    title="Neo4J App",
    description=description,
    version="0.0.1",
    # openapi_tags=tags_metadata,
    responses={404: {"description": "Not found"}},
)


origins = settings.get("ALLOWED_ORIGINS") or []

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"],
    allow_headers=[
        "Access-Control-Allow-Headers",
        "Content-Type",
        "Authorization",
        "Access-Control-Allow-Origin",
    ],
)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


app.include_router(neo4j_graph_operations.neo4j_graph_router)
app.include_router(llm_agent_operations.llm_agent_router)
