-- =====================================================
-- Taiwan Government Subsidy Chatbot - Database Schema
-- =====================================================
-- This SQL script creates all necessary tables for the
-- Taiwan government subsidy recommendation chatbot system
--
-- Execute this in your Supabase SQL Editor to create tables
-- =====================================================

-- Create ENUM types first
DO $$ BEGIN
    CREATE TYPE userrole AS ENUM ('user', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE chatsessionstatus AS ENUM ('active', 'completed', 'abandoned');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- =====================================================
-- Table: users
-- User authentication and management
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    external_user_id VARCHAR(100) UNIQUE NOT NULL,
    username VARCHAR(50) NOT NULL,
    role userrole NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_external_user_id ON users(external_user_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- =====================================================
-- Table: chat_sessions
-- Chat session tracking for conversations
-- =====================================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    status chatsessionstatus NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);

-- =====================================================
-- Table: chat_messages
-- Store conversation history
-- =====================================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);

-- =====================================================
-- Table: company_onboarding (Legacy - from previous project)
-- Company onboarding data
-- =====================================================
CREATE TABLE IF NOT EXISTS company_onboarding (
    id SERIAL PRIMARY KEY,
    chat_session_id INTEGER NOT NULL UNIQUE REFERENCES chat_sessions(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    industry VARCHAR(100),
    capital_amount INTEGER,
    invention_patent_count INTEGER,
    utility_patent_count INTEGER,
    certification_count INTEGER,
    esg_certification_count INTEGER,
    esg_certification TEXT,
    is_current BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_company_onboarding_chat_session_id ON company_onboarding(chat_session_id);
CREATE INDEX IF NOT EXISTS idx_company_onboarding_user_id ON company_onboarding(user_id);
CREATE INDEX IF NOT EXISTS idx_company_onboarding_is_current ON company_onboarding(is_current);

-- =====================================================
-- Table: products (Legacy - from previous project)
-- Product information
-- =====================================================
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    onboarding_id INTEGER NOT NULL REFERENCES company_onboarding(id) ON DELETE CASCADE,
    product_id VARCHAR(100),
    product_name VARCHAR(200),
    price VARCHAR(50),
    main_raw_materials VARCHAR(500),
    product_standard VARCHAR(200),
    technical_advantages TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_onboarding_id ON products(onboarding_id);
CREATE INDEX IF NOT EXISTS idx_products_product_id ON products(product_id);

-- =====================================================
-- Table: subsidy_consultations
-- 台灣政府補助方案診斷與推薦資料
-- Main table for Taiwan government subsidy consultation
-- =====================================================
CREATE TABLE IF NOT EXISTS subsidy_consultations (
    id SERIAL PRIMARY KEY,
    chat_session_id INTEGER REFERENCES chat_sessions(id),
    user_id INTEGER REFERENCES users(id),

    -- Basic Info
    source VARCHAR(100) NOT NULL DEFAULT '補助診斷士',
    project_type VARCHAR(50),  -- 研發 or 行銷

    -- Contact Info
    email VARCHAR(255),
    company_name VARCHAR(255),
    phone VARCHAR(50),
    consult BOOLEAN DEFAULT false,  -- 是否需要諮詢

    -- Financial Data (stored in 元/TWD)
    budget BIGINT,  -- 預計所需經費 (元)
    people INTEGER,  -- 公司投保人數 (人)
    capital BIGINT,  -- 公司實收資本額 (元)
    revenue BIGINT,  -- 公司大約年度營業額 (元)
    growth_revenue BIGINT,  -- 預計行銷活動可帶來營業額成長 (元)

    -- Bonus Items (加分項目)
    bonus_count INTEGER DEFAULT 0,  -- 加分項目數量 (0-5)
    bonus_details TEXT,  -- 加分項目詳情 (comma separated)

    -- Marketing Type (for 行銷 projects)
    marketing_type TEXT,  -- 行銷方向 (comma separated: 內銷, 外銷)

    -- Calculation Results (stored in 元/TWD)
    grant_min BIGINT,  -- 補助最低值 (元)
    grant_max BIGINT,  -- 補助最高值 (元)
    recommended_plans TEXT,  -- 推薦方案名稱 (comma separated)

    -- Device & Tracking Info
    device VARCHAR(50),  -- 裝置類型 (mobile, desktop, tablet)

    -- Timestamps
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subsidy_consultations_chat_session_id ON subsidy_consultations(chat_session_id);
CREATE INDEX IF NOT EXISTS idx_subsidy_consultations_user_id ON subsidy_consultations(user_id);
CREATE INDEX IF NOT EXISTS idx_subsidy_consultations_email ON subsidy_consultations(email);
CREATE INDEX IF NOT EXISTS idx_subsidy_consultations_timestamp ON subsidy_consultations(timestamp);

-- =====================================================
-- Trigger: Update updated_at timestamp automatically
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables with updated_at column
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON chat_sessions;
CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_company_onboarding_updated_at ON company_onboarding;
CREATE TRIGGER update_company_onboarding_updated_at BEFORE UPDATE ON company_onboarding
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_subsidy_consultations_updated_at ON subsidy_consultations;
CREATE TRIGGER update_subsidy_consultations_updated_at BEFORE UPDATE ON subsidy_consultations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Grant permissions (adjust as needed for your Supabase setup)
-- =====================================================
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- =====================================================
-- Verification Query
-- Run this to verify all tables were created successfully
-- =====================================================
-- SELECT table_name
-- FROM information_schema.tables
-- WHERE table_schema = 'public'
-- ORDER BY table_name;

-- =====================================================
-- Complete!
-- All tables created successfully.
-- =====================================================
