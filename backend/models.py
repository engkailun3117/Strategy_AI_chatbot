from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey, Enum, Text, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    USER = "user"
    ADMIN = "admin"


class ChatSessionStatus(str, enum.Enum):
    """Chat session status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class User(Base):
    """User table for external JWT authentication (synced from main system)"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    external_user_id = Column(String(100), unique=True, nullable=False, index=True)  # Maps to main system's user ID
    username = Column(String(50), nullable=False, index=True)
    role = Column(Enum(UserRole, native_enum=True, create_constraint=True, name='userrole'), default=UserRole.USER, nullable=False)
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
    status = Column(Enum(ChatSessionStatus, native_enum=True, create_constraint=True, name='chatsessionstatus'),
                    default=ChatSessionStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    onboarding_data = relationship("CompanyOnboarding", back_populates="chat_session", uselist=False)

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


class CompanyOnboarding(Base):
    """Company onboarding data collected through chatbot"""

    __tablename__ = "company_onboarding"

    id = Column(Integer, primary_key=True, index=True)
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Chatbot Data Collection (責任範圍)
    industry = Column(String(100), nullable=True)  # 產業別
    capital_amount = Column(Integer, nullable=True)  # 資本總額（以臺幣為單位）
    invention_patent_count = Column(Integer, nullable=True)  # 發明專利數量 - 權重高
    utility_patent_count = Column(Integer, nullable=True)  # 新型專利數量 - 權重低
    certification_count = Column(Integer, nullable=True)  # 公司認證資料數量
    esg_certification_count = Column(Integer, nullable=True)  # ESG相關認證資料數量
    esg_certification = Column(Text, nullable=True)  # ESG相關認證資料（例如：ISO 14064, ISO 14067, ISO 14046）

    is_current = Column(Boolean, default=True, nullable=False, index=True)  # Whether this is the current/active record for the user

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User")
    chat_session = relationship("ChatSession", back_populates="onboarding_data")
    products = relationship("Product", back_populates="company_onboarding", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "chat_session_id": self.chat_session_id,
            "user_id": self.user_id,
            "industry": self.industry,
            "capital_amount": self.capital_amount,
            "invention_patent_count": self.invention_patent_count,
            "utility_patent_count": self.utility_patent_count,
            "certification_count": self.certification_count,
            "esg_certification_count": self.esg_certification_count,
            "esg_certification": self.esg_certification,
            "is_current": self.is_current,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "products": [p.to_dict() for p in self.products] if self.products else []
        }

    def to_export_format(self):
        """Convert to the export JSON format requested by the user"""
        return {
            "產業別": self.industry,
            "資本總額（以臺幣為單位）": self.capital_amount,
            "發明專利數量": self.invention_patent_count,
            "新型專利數量": self.utility_patent_count,
            "公司認證資料數量": self.certification_count,
            "ESG相關認證資料數量": self.esg_certification_count,
            "ESG相關認證資料": self.esg_certification,
            "產品": [p.to_export_format() for p in self.products] if self.products else []
        }


class Product(Base):
    """Product information table (子欄)"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    onboarding_id = Column(Integer, ForeignKey("company_onboarding.id"), nullable=False, index=True)

    # Product Information (子欄)
    product_id = Column(String(100), nullable=True, index=True)  # 產品ID
    product_name = Column(String(200), nullable=True)  # 產品名稱
    price = Column(String(50), nullable=True)  # 價格
    main_raw_materials = Column(String(500), nullable=True)  # 主要原料
    product_standard = Column(String(200), nullable=True)  # 產品規格(尺寸、精度)
    technical_advantages = Column(Text, nullable=True)  # 技術優勢

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    company_onboarding = relationship("CompanyOnboarding", back_populates="products")

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "onboarding_id": self.onboarding_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "price": self.price,
            "main_raw_materials": self.main_raw_materials,
            "product_standard": self.product_standard,
            "technical_advantages": self.technical_advantages,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def to_export_format(self):
        """Convert to the export JSON format requested by the user"""
        return {
            "產品ID": self.product_id,
            "產品名稱": self.product_name,
            "價格": self.price,
            "主要原料": self.main_raw_materials,
            "產品規格(尺寸、精度)": self.product_standard,
            "技術優勢": self.technical_advantages
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

    # Contact Info
    email = Column(String(255), nullable=True, index=True)
    company_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    consult = Column(Boolean, default=False)  # 是否需要諮詢

    # Financial Data (stored in 元/TWD)
    budget = Column(BigInteger, nullable=True)  # 預計所需經費 (元)
    people = Column(Integer, nullable=True)  # 公司投保人數 (人)
    capital = Column(BigInteger, nullable=True)  # 公司實收資本額 (元)
    revenue = Column(BigInteger, nullable=True)  # 公司大約年度營業額 (元)
    growth_revenue = Column(BigInteger, nullable=True)  # 預計行銷活動可帶來營業額成長 (元)

    # Bonus Items (加分項目)
    bonus_count = Column(Integer, default=0, nullable=True)  # 加分項目數量 (0-5)
    bonus_details = Column(Text, nullable=True)  # 加分項目詳情 (comma separated)

    # Marketing Type (for 行銷 projects)
    marketing_type = Column(Text, nullable=True)  # 行銷方向 (comma separated: 內銷, 外銷)

    # Calculation Results (stored in 元/TWD)
    grant_min = Column(BigInteger, nullable=True)  # 補助最低值 (元)
    grant_max = Column(BigInteger, nullable=True)  # 補助最高值 (元)
    recommended_plans = Column(Text, nullable=True)  # 推薦方案名稱 (comma separated)

    # Device & Tracking Info
    device = Column(String(50), nullable=True)  # 裝置類型 (mobile, desktop, tablet)

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
            "email": self.email,
            "company_name": self.company_name,
            "phone": self.phone,
            "consult": self.consult,
            "budget": self.budget,
            "people": self.people,
            "capital": self.capital,
            "revenue": self.revenue,
            "growth_revenue": self.growth_revenue,
            "bonus_count": self.bonus_count,
            "bonus_details": self.bonus_details,
            "marketing_type": self.marketing_type,
            "grant_min": self.grant_min,
            "grant_max": self.grant_max,
            "recommended_plans": self.recommended_plans,
            "device": self.device,
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
            "Email": self.email,
            "公司行號": self.company_name,
            "預計所需經費(元)": self.budget,
            "公司投保人數(人)": self.people,
            "公司實收資本額(元)": self.capital,
            "公司大約年度營業額(元)": self.revenue,
            "加分項目數量": self.bonus_count,
            "加分項目詳情": self.bonus_details,
            "行銷方向": self.marketing_type,
            "預計行銷活動可帶來營業額成長(元)": self.growth_revenue,
            "補助最低值(元)": self.grant_min,
            "補助最高值(元)": self.grant_max,
            "推薦方案名稱": self.recommended_plans,
            "裝置類型": self.device,
            "是否需要諮詢": self.consult,
            "電話": self.phone
        }