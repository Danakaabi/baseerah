from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
async def health_check() -> dict[str, str]:
    """
    Check whether the BASEERAH API is running.

    Returns:
        Basic API health information.
    """
    return {
        "status": "ok",
        "service": "BASEERAH API",
        "version": "0.1.0",
    }