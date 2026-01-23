"""
Script to clear all data from chat_messages, chat_sessions, and subsidy_consultations tables.
This is useful for testing the API from a clean state.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def clear_database_tables(database_url):
    """Clear all data from the specified tables"""

    # Create engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Delete in order to respect foreign key constraints
        # Using raw SQL for simplicity

        # 1. Delete chat_messages (references chat_sessions)
        result = db.execute(text("DELETE FROM chat_messages"))
        chat_messages_count = result.rowcount
        print(f"Deleted {chat_messages_count} records from chat_messages")

        # 2. Delete subsidy_consultations (references chat_sessions and users)
        result = db.execute(text("DELETE FROM subsidy_consultations"))
        subsidy_consultations_count = result.rowcount
        print(f"Deleted {subsidy_consultations_count} records from subsidy_consultations")

        # 3. Delete chat_sessions (parent table)
        result = db.execute(text("DELETE FROM chat_sessions"))
        chat_sessions_count = result.rowcount
        print(f"Deleted {chat_sessions_count} records from chat_sessions")

        # Commit the changes
        db.commit()
        print("\nDatabase tables cleared successfully!")
        print("You can now test your API from a clean state.")

    except Exception as e:
        db.rollback()
        print(f"Error clearing database: {e}")
        raise
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    print("Starting database cleanup...")
    print("This will delete ALL data from:")
    print("  - chat_messages")
    print("  - chat_sessions")
    print("  - subsidy_consultations")
    print()

    # Get database URL from environment variable or command line argument
    database_url = os.getenv("DATABASE_URL")

    if len(sys.argv) > 1:
        database_url = sys.argv[1]

    if not database_url:
        print("Error: DATABASE_URL not provided.")
        print("\nUsage:")
        print("  1. Set DATABASE_URL environment variable:")
        print("     export DATABASE_URL='your_database_url'")
        print("     python3 clear_database.py")
        print("\n  2. Or pass as command line argument:")
        print("     python3 clear_database.py 'your_database_url'")
        sys.exit(1)

    clear_database_tables(database_url)
