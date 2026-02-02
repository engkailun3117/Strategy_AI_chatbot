-- Clear all data from the three tables
-- Execute in the correct order to respect foreign key constraints

-- Delete chat_messages (references chat_sessions)
DELETE FROM chat_messages;

-- Delete subsidy_consultations (references chat_sessions and users)
DELETE FROM subsidy_consultations;

-- Delete chat_sessions (parent table)
DELETE FROM chat_sessions;

-- Display confirmation
SELECT
    'Database cleared successfully!' as message,
    (SELECT COUNT(*) FROM chat_messages) as chat_messages_count,
    (SELECT COUNT(*) FROM chat_sessions) as chat_sessions_count,
    (SELECT COUNT(*) FROM subsidy_consultations) as subsidy_consultations_count;
