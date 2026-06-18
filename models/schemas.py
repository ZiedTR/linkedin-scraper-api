from typing import Any, Optional
from pydantic import BaseModel


class APIResponse(BaseModel):
    success: bool = True
    message: str = ""
    cached: bool = False
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_type: str
    details: Optional[dict[str, Any]] = None
