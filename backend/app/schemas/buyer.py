"""
Pydantic schemas for Buyer and BuyerRequirement.
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel


class BuyerRequirementBase(BaseModel):
    crop: str
    min_quantity: Optional[float] = None
    max_quantity: Optional[float] = None
    quality_requirement: Optional[str] = None
    offered_price: Optional[float] = None
    delivery_date: Optional[date] = None


class BuyerRequirementCreate(BuyerRequirementBase):
    pass


class BuyerRequirementOut(BuyerRequirementBase):
    id: int
    buyer_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BuyerBase(BaseModel):
    company_name: str
    location: Optional[str] = None
    verified: bool = False


class BuyerCreate(BuyerBase):
    pass


class BuyerOut(BuyerBase):
    id: int
    user_id: int
    requirements: List[BuyerRequirementOut] = []

    class Config:
        from_attributes = True


class BuyerListItem(BaseModel):
    id: int
    company_name: str
    location: Optional[str]
    verified: bool
    crop: str
    offered_price: Optional[float]
    min_quantity: Optional[float]
    max_quantity: Optional[float]
    quality_requirement: Optional[str]
    note: str = "DEMO DATA"
