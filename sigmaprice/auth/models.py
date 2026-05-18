"""Pydantic models for auth requests and responses"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    TRUSTED_USER = "trusted_user"
    USER = "user"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    role: UserRoleEnum = UserRoleEnum.USER
    display_name: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[UserRoleEnum] = None
    display_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRoleEnum
    display_name: Optional[str] = None
    is_active: bool = True
    is_trusted: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PermissionCreate(BaseModel):
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None


class PermissionResponse(BaseModel):
    id: int
    user_id: int
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
