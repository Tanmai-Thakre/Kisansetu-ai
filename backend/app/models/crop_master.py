"""
Crop master data model — stores supported crop metadata.
"""
from sqlalchemy import Column, Integer, String, Boolean
from app.database.base import Base


class CropMaster(Base):
    """
    Master table for supported crops.
    Extensible — add new crops without code changes.
    """
    __tablename__ = "crop_master"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)    # "cotton"
    display_name = Column(String(100), nullable=False)         # "Cotton"
    unit = Column(String(50), nullable=False, default="quintal")
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "unit": self.unit,
            "description": self.description,
        }
