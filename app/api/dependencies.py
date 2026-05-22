
from fastapi import Header, HTTPException


async def verify_content_type_json(
    content_type: str = Header(default="application/json")
):
    """
    Ensures the request content type is JSON.
    Used for endpoints that expect JSON body.
    """
    if "application/json" not in content_type:
        raise HTTPException(
            status_code=415,
            detail="Content-Type must be application/json",
        )


async def get_pagination_params(
    page: int = 1,
    limit: int = 10,
):
    """
    Shared pagination parameters for list endpoints.
    """
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page number must be greater than 0",
        )
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100",
        )
    return {
        "page": page,
        "limit": limit,
        "offset": (page - 1) * limit,
    }