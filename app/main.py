import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from pathlib import Path
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.api.tools import router as tools_router
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

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception):
        logging.getLogger(__name__).error("Request failed: %s", request.url.path, exc_info=error)
        return JSONResponse(status_code=500, content={"detail": "تعذر إكمال التحليل. تحقق من تجهيز النماذج وسجل الخادم."})

    application.include_router(health_router)
    application.include_router(verify_router)

    application.include_router(tools_router)
    frontend = Path(__file__).resolve().parents[1] / "Frontend " / "baseerah-separated"
    application.mount("/ui", StaticFiles(directory=frontend, html=True), name="ui")

    @application.get("/", include_in_schema=False)
    def frontend_redirect():
        return RedirectResponse("/ui/")

    return application


app = create_app()