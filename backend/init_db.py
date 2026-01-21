#!/usr/bin/env python3
"""
Database Initialization Script
Creates all tables in the Supabase PostgreSQL database

Usage:
    python init_db.py
"""

from database import Base, engine
from models import (
    User,
    ChatSession,
    ChatMessage,
    SubsidyConsultation
)
from config import get_settings


def init_database():
    """Initialize database tables"""
    print("=" * 60)
    print("🚀 Taiwan Government Subsidy Chatbot - Database Initialization")
    print("=" * 60)

    settings = get_settings()
    print(f"\n📊 Database: {settings.database_url[:30]}...")

    print("\n🔧 Creating database tables...")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)

        print("\n✅ Database tables created successfully!")
        print("\n📋 Created tables:")
        print("   1. users - User authentication and management")
        print("   2. chat_sessions - Chat session tracking")
        print("   3. chat_messages - Conversation history")
        print("   4. subsidy_consultations - Taiwan government subsidy consultation data")

        print("\n" + "=" * 60)
        print("✨ Database initialization complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error creating database tables: {e}")
        print("\nPlease check your database connection and credentials.")
        raise


if __name__ == "__main__":
    init_database()
