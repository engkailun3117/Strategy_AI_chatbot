from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey, Enum, Text, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class UserRole(str, enum.Enum):
    """User role enumeration - Updated to match DB case"""
    USER = "USER"  # Change this to uppercase
    ADMIN = "ADMIN" # Change this to uppercase to be safe


class ChatSessionStatus(str, enum.Enum):
    """Chat session status enumeration - Updated to match DB case"""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class User(Base):
    """User table for external JWT authentication (synced from main system)"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    external_user_id = Column(String(100), unique=True, nullable=False, index=True)  # Maps to main system's user ID
    username = Column(String(50), nullable=False, index=True)
    role = Column(
        Enum(UserRole, native_enum=True, values_callable=lambda obj: [e.value for e in obj]),
        default=UserRole.USER,
        nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "external_user_id": self.external_user_id,
            "username": self.username,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ChatSession(Base):
    """Chat session table for managing user chatbot conversations"""

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(
        Enum(ChatSessionStatus, native_enum=True, values_callable=lambda obj: [e.value for e in obj]),
        default=ChatSessionStatus.ACTIVE,
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class ChatMessage(Base):
    """Chat message table for storing conversation history"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class SubsidyConsultation(Base):
    """台灣政府補助方案診斷與推薦資料"""

    __tablename__ = "subsidy_consultations"

    id = Column(Integer, primary_key=True, index=True)
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Optional for guest users

    # Basic Info
    source = Column(String(100), default="補助診斷士", nullable=False)
    project_type = Column(String(50), nullable=True)  # 研發 or 行銷
    data_confirmed = Column(Boolean, default=False, nullable=True)  # 使用者是否確認資料正確

    # Financial Data (stored in 元/TWD)
    budget = Column(BigInteger, nullable=True)  # 預計所需經費 (元)
    people = Column(Integer, nullable=True)  # 公司投保人數 (人)
    capital = Column(BigInteger, nullable=True)  # 公司實收資本額 (元)
    revenue = Column(BigInteger, nullable=True)  # 公司大約年度營業額 (元)
    growth_revenue = Column(BigInteger, nullable=True)  # 預計行銷活動可帶來營業額成長 (元)

    # Bonus Items (加分項目) - Individual boolean flags
    has_certification = Column(Boolean, nullable=True)  # 是否產品／服務取得第三方認證
    has_gov_award = Column(Boolean, nullable=True)  # 是否取得政府相關獎項
    is_mit = Column(Boolean, nullable=True)  # 產品是否為 MIT 生產
    has_industry_academia = Column(Boolean, nullable=True)  # 是否有做產學合作
    has_factory_registration = Column(Boolean, nullable=True)  # 是否有工廠登記證

    # Legacy bonus fields (kept for backward compatibility)
    bonus_count = Column(Integer, default=0, nullable=True)  # 加分項目數量 (0-5)
    bonus_details = Column(Text, nullable=True)  # 加分項目詳情 (comma separated)

    # Marketing Type (for 行銷 projects)
    marketing_type = Column(Text, nullable=True)  # 行銷方向 (comma separated: 內銷, 外銷)

    # Calculation Results (stored in 元/TWD)
    grant_min = Column(BigInteger, nullable=True)  # 補助最低值 (元)
    grant_max = Column(BigInteger, nullable=True)  # 補助最高值 (元)
    recommended_plans = Column(Text, nullable=True)  # 推薦方案名稱 (comma separated)

    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    chat_session = relationship("ChatSession", foreign_keys=[chat_session_id])

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "chat_session_id": self.chat_session_id,
            "user_id": self.user_id,
            "source": self.source,
            "project_type": self.project_type,
            "data_confirmed": self.data_confirmed,
            "budget": self.budget,
            "people": self.people,
            "capital": self.capital,
            "revenue": self.revenue,
            "growth_revenue": self.growth_revenue,
            "has_certification": self.has_certification,
            "has_gov_award": self.has_gov_award,
            "is_mit": self.is_mit,
            "has_industry_academia": self.has_industry_academia,
            "has_factory_registration": self.has_factory_registration,
            "bonus_count": self.bonus_count,
            "bonus_details": self.bonus_details,
            "marketing_type": self.marketing_type,
            "grant_min": self.grant_min,
            "grant_max": self.grant_max,
            "recommended_plans": self.recommended_plans,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def to_export_format(self):
        """Convert to export format with Chinese field names"""
        return {
            "時間戳": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None,
            "來源": self.source,
            "類型選擇": self.project_type,
            "預計所需經費(元)": self.budget,
            "公司投保人數(人)": self.people,
            "公司實收資本額(元)": self.capital,
            "公司大約年度營業額(元)": self.revenue,
            "產品／服務取得第三方認證": "是" if self.has_certification else "否",
            "取得政府相關獎項": "是" if self.has_gov_award else "否",
            "產品為 MIT 生產": "是" if self.is_mit else "否",
            "有做產學合作": "是" if self.has_industry_academia else "否",
            "有工廠登記證": "是" if self.has_factory_registration else "否",
            "加分項目數量": self.bonus_count,
            "加分項目詳情": self.bonus_details,
            "行銷方向": self.marketing_type,
            "預計行銷活動可帶來營業額成長(元)": self.growth_revenue,
            "補助最低值(元)": self.grant_min,
            "補助最高值(元)": self.grant_max,
            "推薦方案名稱": self.recommended_plans
        }