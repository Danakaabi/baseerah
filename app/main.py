from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.verify import router as verify_router


def create_app() -> FastAPI:
    """
    Create and configure the BASEERAH FastAPI application.
    """

    application = FastAPI(
        title="BASEERAH API",
        description=(
            "AI-assisted retrieval, verification, "
            "and context tracing for trusted Islamic content."
        ),
        version="0.1.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5500",
            "http://localhost:5500",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health_router)
    application.include_router(verify_router)

    return application


app = create_app()