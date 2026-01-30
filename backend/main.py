from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db, engine, Base
from models import User, ChatSession, ChatMessage, SubsidyConsultation, ChatSessionStatus
from schemas import (
    UserResponse,
    ChatMessageCreate, ChatResponse, ChatSessionResponse, ChatMessageResponse,
    SubsidyConsultationCreate, SubsidyCalculationResult, SubsidyConsultationResponse
)
from config import get_settings
from auth import get_current_active_user
from subsidy_chatbot_handler import SubsidyChatbotHandler
from subsidy_calculator import calculate_subsidy

# Create database tables
Base.metadata.create_all(bind=engine)

# Debug: Print configuration on startup
settings = get_settings()
print("=" * 60)
print("🔧 Backend Configuration:")
print(f"   Database: {settings.database_url[:30]}...")
print(f"   API Host: {settings.api_host}")
print(f"   API Port: {settings.api_port}")
print(f"   External JWT Secret: {settings.external_jwt_secret[:20]}... (length: {len(settings.external_jwt_secret)})")
print(f"   Gemini Model: {settings.gemini_model}")
print("=" * 60)

# Initialize FastAPI app
app = FastAPI(
    title="Taiwan Government Subsidy Chatbot API",
    description="AI-powered chatbot for Taiwan government subsidy consultation and recommendation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Health Check ==============

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Taiwan Government Subsidy Chatbot API is running",
        "version": "1.0.0",
        "features": ["external_jwt_auth", "gemini_ai_chatbot", "subsidy_calculation", "session_management"]
    }


# ============== Authentication Endpoints ==============

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information

    Requires: Valid JWT token from main system in Authorization header

    This endpoint automatically syncs user data from the JWT token to the local database.
    If the user doesn't exist locally, it will be created automatically.
    """
    return current_user.to_dict()


# ============== Subsidy Chatbot Endpoints ==============

@app.post("/api/subsidy/chat", response_model=ChatResponse)
async def send_subsidy_chatbot_message(
    chat_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send a message to the subsidy consultation chatbot

    - **message**: User's message to the chatbot
    - **session_id**: Optional session ID to continue an existing conversation

    Requires: Authentication
    Returns: Chatbot response with session information
    """
    try:
        # Initialize handler
        handler = SubsidyChatbotHandler(db, current_user.id, chat_data.session_id)

        # Create new session if needed
        if not handler.session:
            session = handler.create_session()

            welcome_message = (
                "您好！我是新手戰略指引的 AI 助理 👋\n\n"
                "我將協助您評估適合的政府補助方案，包括：\n"
                "• 研發類：地方SBIR、CITD、中央SBIR\n"
                "• 行銷類：開拓海外市場計畫、內銷推廣計畫\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📌 **為什麼需要填寫公司資料？**\n\n"
                "填寫公司資料有利於系統了解公司屬性與優勢，平台未來能：\n"
                "✨ 推薦合適的政府補助方案\n"
                "✨ 推薦適合您公司的產品與服務\n"
                "✨ 偵察潛在合作夥伴\n"
                "✨ 協助企業申請政府補助案\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "📝 接下來我會問您幾個問題（大約需要2-3分鐘）\n\n"
                "讓我們開始吧！請問您的計畫類型是「研發」還是「行銷」？"
            )

            handler.add_message("assistant", welcome_message)

            return ChatResponse(
                session_id=session.id,
                message=welcome_message,
                completed=False,
                progress=handler.get_progress()
            )

        # Save user message
        handler.add_message("user", chat_data.message)

        # Process message and get response
        bot_response, is_completed = handler.process_message(chat_data.message)

        # Save bot response
        handler.add_message("assistant", bot_response)

        return ChatResponse(
            session_id=handler.session.id,
            message=bot_response,
            completed=is_completed,
            progress=handler.get_progress()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your message: {str(e)}"
        )


@app.get("/api/subsidy/sessions", response_model=List[ChatSessionResponse])
async def get_user_subsidy_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all subsidy consultation sessions for the current user

    Requires: Authentication
    Returns: List of user's chat sessions
    """
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).all()

    return [session.to_dict() for session in sessions]


@app.get("/api/subsidy/sessions/latest")
async def get_latest_active_subsidy_session(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the latest subsidy consultation session for the current user

    This endpoint helps avoid creating duplicate sessions on page refresh.
    It returns the most recent session (ACTIVE or COMPLETED) to preserve
    conversation history and allow users to view completed consultations.

    Priority:
    1. Return ACTIVE session if exists (conversation in progress)
    2. Otherwise return most recent COMPLETED session (show results)
    3. Return null if no sessions exist (first-time user)

    Requires: Authentication
    Returns: Latest session or null if none exists
    """
    # First, try to find an active session
    active_session = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatSession.status == ChatSessionStatus.ACTIVE
    ).order_by(ChatSession.created_at.desc()).first()

    if active_session:
        return {
            "session_id": active_session.id,
            "status": active_session.status.value,
            "created_at": active_session.created_at.isoformat() if active_session.created_at else None,
            "completed_at": active_session.completed_at.isoformat() if active_session.completed_at else None
        }

    # If no active session, return the most recent completed session
    latest_session = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).first()

    if latest_session:
        return {
            "session_id": latest_session.id,
            "status": latest_session.status.value,
            "created_at": latest_session.created_at.isoformat() if latest_session.created_at else None,
            "completed_at": latest_session.completed_at.isoformat() if latest_session.completed_at else None
        }

    return {"session_id": None}


@app.post("/api/subsidy/sessions/new")
async def create_new_subsidy_session(
    previous_session_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new subsidy consultation session

    This endpoint is called when user explicitly clicks "New Session".
    Can optionally copy data from a previous session to preserve memory.

    - **previous_session_id**: Optional ID of previous session to copy data from

    Requires: Authentication
    Returns: New session ID with welcome message
    """
    handler = SubsidyChatbotHandler(db, current_user.id, None)

    # Create new session
    new_session = handler.create_session()

    # If previous_session_id provided, copy consultation data to preserve memory
    if previous_session_id:
        try:
            # Get previous consultation data
            previous_consultation = db.query(SubsidyConsultation).filter(
                SubsidyConsultation.chat_session_id == previous_session_id
            ).first()

            if previous_consultation:
                # Copy data to new consultation
                new_consultation = handler.consultation_data
                new_consultation.project_type = previous_consultation.project_type
                new_consultation.budget = previous_consultation.budget
                new_consultation.people = previous_consultation.people
                new_consultation.capital = previous_consultation.capital
                new_consultation.revenue = previous_consultation.revenue
                new_consultation.has_certification = previous_consultation.has_certification
                new_consultation.has_gov_award = previous_consultation.has_gov_award
                new_consultation.is_mit = previous_consultation.is_mit
                new_consultation.has_industry_academia = previous_consultation.has_industry_academia
                new_consultation.has_factory_registration = previous_consultation.has_factory_registration
                new_consultation.bonus_count = previous_consultation.bonus_count
                new_consultation.bonus_details = previous_consultation.bonus_details
                new_consultation.marketing_type = previous_consultation.marketing_type
                new_consultation.growth_revenue = previous_consultation.growth_revenue
                db.commit()
                print(f"✓ Copied consultation data from session {previous_session_id} to new session {new_session.id}")
        except Exception as e:
            print(f"⚠️ Warning: Could not copy previous session data: {e}")
            # Continue anyway, don't fail the session creation

    welcome_message = (
        "您好！我是新手戰略指引的 AI 助理 👋\n\n"
        "我將協助您評估適合的政府補助方案，包括：\n"
        "• 研發類：地方SBIR、CITD、中央SBIR\n"
        "• 行銷類：開拓海外市場計畫、內銷推廣計畫\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 **為什麼需要填寫公司資料？**\n\n"
        "填寫公司資料有利於系統了解公司屬性與優勢，平台未來能：\n"
        "✨ 推薦合適的政府補助方案\n"
        "✨ 推薦適合您公司的產品與服務\n"
        "✨ 偵察潛在合作夥伴\n"
        "✨ 協助企業申請政府補助案\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 接下來我會問您幾個問題（大約需要2-3分鐘）\n\n"
        "讓我們開始吧！請問您的計畫類型是「研發」還是「行銷」？"
    )

    handler.add_message("assistant", welcome_message)

    return {
        "session_id": new_session.id,
        "message": welcome_message,
        "progress": handler.get_progress()
    }


@app.get("/api/subsidy/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_subsidy_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all messages for a specific subsidy consultation session

    - **session_id**: The ID of the chat session

    Requires: Authentication
    Authorization: Users can only view their own sessions
    """
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).all()

    return [msg.to_dict() for msg in messages]


@app.get("/api/subsidy/consultations/{session_id}", response_model=SubsidyConsultationResponse)
async def get_subsidy_consultation_data(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the subsidy consultation data for a specific session

    - **session_id**: The ID of the chat session

    Requires: Authentication
    Authorization: Users can only view their own data
    """
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    consultation_data = db.query(SubsidyConsultation).filter(
        SubsidyConsultation.chat_session_id == session_id
    ).first()

    if not consultation_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No consultation data found for this session"
        )

    return consultation_data.to_dict()


@app.get("/api/subsidy/consultations/{session_id}/export")
async def export_subsidy_consultation_data(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export subsidy consultation data in Chinese field name format

    - **session_id**: The ID of the chat session

    Requires: Authentication
    Authorization: Users can only export their own data
    Returns: Data with Chinese field names
    """
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    consultation_data = db.query(SubsidyConsultation).filter(
        SubsidyConsultation.chat_session_id == session_id
    ).first()

    if not consultation_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No consultation data found for this session"
        )

    # Return data in export format
    return consultation_data.to_export_format()


@app.post("/api/subsidy/calculate", response_model=SubsidyCalculationResult)
async def calculate_subsidy_amount(
    data: SubsidyConsultationCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Calculate subsidy amount based on provided data (without saving to session)

    This is a standalone calculation endpoint that doesn't require a chat session.
    Useful for quick calculations or API integrations.

    Requires: Authentication
    Returns: Calculated subsidy range and recommended plans
    """
    try:
        # Validate required fields
        if not data.project_type:
            raise HTTPException(status_code=400, detail="project_type is required")
        if data.budget is None:
            raise HTTPException(status_code=400, detail="budget is required")
        if data.people is None:
            raise HTTPException(status_code=400, detail="people is required")
        if data.capital is None:
            raise HTTPException(status_code=400, detail="capital is required")
        if data.revenue is None:
            raise HTTPException(status_code=400, detail="revenue is required")

        # Prepare marketing types
        marketing_types = []
        if data.marketing_type:
            marketing_types = [t.strip() for t in data.marketing_type.split(',')]

        # Calculate subsidy
        result = calculate_subsidy(
            budget=data.budget,
            people=data.people,
            capital=data.capital,
            revenue=data.revenue,
            bonus_count=data.bonus_count or 0,
            project_type=data.project_type,
            marketing_types=marketing_types,
            growth_revenue=data.growth_revenue or 0
        )

        return SubsidyCalculationResult(
            grant_min=result["grant_min"],
            grant_max=result["grant_max"],
            recommended_plans=result["recommended_plans"],
            breakdown=result.get("breakdown")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating subsidy: {str(e)}"
        )


# ============================================================================
# BACKWARD COMPATIBILITY ENDPOINTS
# These endpoints provide aliases for /api/chatbot/* -> /api/subsidy/*
# to maintain compatibility with older frontend applications
# ============================================================================

@app.post("/api/chatbot/chat", response_model=ChatResponse)
async def chatbot_send_message_compat(
    chat_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Backward compatibility alias for /api/subsidy/chat"""
    return await send_subsidy_chatbot_message(chat_data, current_user, db)


@app.get("/api/chatbot/sessions/latest")
async def chatbot_get_latest_session_compat(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Backward compatibility alias for /api/subsidy/sessions/latest"""
    return await get_latest_active_subsidy_session(current_user, db)


@app.get("/api/chatbot/sessions", response_model=List[ChatSessionResponse])
async def chatbot_get_sessions_compat(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Backward compatibility alias for /api/subsidy/sessions"""
    return await get_user_subsidy_sessions(current_user, db)


@app.post("/api/chatbot/sessions/new")
async def chatbot_create_new_session_compat(
    previous_session_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Backward compatibility alias for /api/subsidy/sessions/new"""
    return await create_new_subsidy_session(previous_session_id, current_user, db)


@app.get("/api/chatbot/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def chatbot_get_session_messages_compat(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Backward compatibility alias for /api/subsidy/sessions/{session_id}/messages"""
    return await get_subsidy_session_messages(session_id, current_user, db)


@app.get("/api/chatbot/consultations/{session_id}", response_model=SubsidyConsultationResponse)
async def chatbot_get_consultation_compat(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Backward compatibility alias for /api/subsidy/consultations/{session_id}"""
    return await get_subsidy_consultation(session_id, current_user, db)


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
