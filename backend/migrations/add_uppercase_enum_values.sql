-- Migration: Add uppercase enum values to match Python enum definitions
-- Date: 2026-01-21
-- Purpose: Fix case sensitivity mismatch between Python enums and PostgreSQL enums

-- Allow uppercase values in the database for ChatSessionStatus
ALTER TYPE chatsessionstatus ADD VALUE IF NOT EXISTS 'ACTIVE';
ALTER TYPE chatsessionstatus ADD VALUE IF NOT EXISTS 'COMPLETED';
ALTER TYPE chatsessionstatus ADD VALUE IF NOT EXISTS 'ABANDONED';

-- Allow uppercase values in the database for UserRole
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'USER';
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'ADMIN';

-- Note: PostgreSQL enum values are immutable once added, they cannot be removed
-- Both uppercase and lowercase values will now coexist in the database
-- The application will use uppercase values going forward
