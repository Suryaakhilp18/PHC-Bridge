from typing import Optional
from pydantic import BaseModel, ConfigDict

class LoginRequest(BaseModel):
    username: str
    password: Optional[str] = "demo123"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    full_name: str
    role: str
    facility_id: Optional[str] = None
    facility_name: Optional[str] = None
    is_active: bool

TokenResponse.model_rebuild()
