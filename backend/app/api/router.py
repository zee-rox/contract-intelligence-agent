from fastapi import APIRouter

from app.api.routes import clauses, documents, questions

api_router = APIRouter()


@api_router.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(clauses.router)
api_router.include_router(questions.router)
