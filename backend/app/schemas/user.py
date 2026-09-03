"""
Pydantic schemas for User and FarmerProfile.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class FarmerProfileBase(BaseModel):
    village: Optional[str] = None
    district: Optional[str] = None
    state: str = "Gujarat"
    land_area: Optional[float] = None


class FarmerProfileCreate(FarmerProfileBase):
    pass


class FarmerProfileOut(FarmerProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    role: str = "farmer"
    language: str = "en"


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
    created_at: datetime
    farmer_profile: Optional[FarmerProfileOut] = None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
