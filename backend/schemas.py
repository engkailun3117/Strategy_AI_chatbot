from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============== Authentication Schemas ==============

class UserResponse(BaseModel):
    """Schema for user response (synced from external JWT)"""
    id: int
    external_user_id: str
    username: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Chatbot Schemas ==============

class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message"""
    message: str = Field(..., min_length=1, description="User's message")
    session_id: Optional[int] = Field(None, description="Session ID (if continuing an existing session)")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "我想申請研發補助",
                "session_id": None
            }
        }


class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Schema for chatbot response"""
    session_id: int
    message: str
    completed: bool = False
    progress: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": 1,
                "message": "您好！我是台灣政府補助診斷助理。我將協助您評估適合的補助方案。請問您的計畫類型是研發還是行銷？",
                "completed": False,
                "progress": {
                    "fields_completed": 0,
                    "total_fields": 6
                }
            }
        }


class ChatSessionResponse(BaseModel):
    """Schema for chat session response"""
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============== Subsidy Consultation Schemas ==============

class SubsidyConsultationCreate(BaseModel):
    """Schema for creating a subsidy consultation"""
    project_type: Optional[str] = Field(None, description="研發 or 行銷")
    budget: Optional[int] = Field(None, description="預計所需經費 (元)")
    people: Optional[int] = Field(None, description="公司投保人數 (人)")
    capital: Optional[int] = Field(None, description="公司實收資本額 (元)")
    revenue: Optional[int] = Field(None, description="公司大約年度營業額 (元)")
    growth_revenue: Optional[int] = Field(None, description="預計行銷活動可帶來營業額成長 (元)")
    bonus_count: Optional[int] = Field(0, description="加分項目數量 (0-5)")
    bonus_details: Optional[str] = Field(None, description="加分項目詳情")
    marketing_type: Optional[str] = Field(None, description="行銷方向: 內銷, 外銷")

    class Config:
        json_schema_extra = {
            "example": {
                "project_type": "研發",
                "budget": 5000000,
                "people": 20,
                "capital": 10000000,
                "revenue": 30000000,
                "bonus_count": 3,
                "bonus_details": "專利, 認證, 技術創新"
            }
        }


class SubsidyCalculationResult(BaseModel):
    """Schema for subsidy calculation result"""
    grant_min: int = Field(..., description="補助最低值 (元)")
    grant_max: int = Field(..., description="補助最高值 (元)")
    recommended_plans: List[str] = Field(..., description="推薦方案")
    breakdown: Optional[dict] = Field(None, description="計算明細")

    class Config:
        json_schema_extra = {
            "example": {
                "grant_min": 2887500,
                "grant_max": 3850000,
                "recommended_plans": ["地方SBIR", "CITD", "中央SBIR"],
                "breakdown": {
                    "grant_employee": 3000000,
                    "grant_revenue_bonus": 500000,
                    "bonus_amount": 350000
                }
            }
        }


class SubsidyConsultationResponse(BaseModel):
    """Schema for subsidy consultation response"""
    id: int
    chat_session_id: Optional[int]
    user_id: Optional[int]
    source: str
    project_type: Optional[str]
    budget: Optional[int]
    people: Optional[int]
    capital: Optional[int]
    revenue: Optional[int]
    growth_revenue: Optional[int]
    bonus_count: Optional[int]
    bonus_details: Optional[str]
    marketing_type: Optional[str]
    grant_min: Optional[int]
    grant_max: Optional[int]
    recommended_plans: Optional[str]
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

