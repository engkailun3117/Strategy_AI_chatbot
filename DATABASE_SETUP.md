# 台灣政府補助方案 AI Chatbot - Database Setup Guide

## 📋 Overview

This document explains how to set up the database for the Taiwan Government Subsidy Recommendation Chatbot. The system uses **Supabase (PostgreSQL)** as the database and **Gemini API** for AI capabilities.

## 🗄️ Database Tables

### Core Tables

1. **users** - User authentication and management
2. **chat_sessions** - Chat session tracking
3. **chat_messages** - Conversation history
4. **subsidy_consultations** - Taiwan government subsidy consultation data ⭐ **MAIN TABLE**

## 📊 Main Table: subsidy_consultations

This is the core table for storing Taiwan government subsidy calculation and recommendation data.

### Fields Structure

| Field | Type | Description |
|-------|------|-------------|
| `id` | SERIAL | Primary key |
| `chat_session_id` | INTEGER | Link to chat session (optional) |
| `user_id` | INTEGER | Link to user (optional for guests) |
| `source` | VARCHAR(100) | Data source (default: "補助診斷士") |
| `project_type` | VARCHAR(50) | Project type: "研發" or "行銷" |
| `budget` | BIGINT | Estimated budget (預計所需經費) in 元 |
| `people` | INTEGER | Number of insured employees (投保人數) |
| `capital` | BIGINT | Registered capital (實收資本額) in 元 |
| `revenue` | BIGINT | Annual revenue (年度營業額) in 元 |
| `growth_revenue` | BIGINT | Expected revenue growth from marketing in 元 |
| `bonus_count` | INTEGER | Number of bonus items selected (0-5) |
| `bonus_details` | TEXT | Bonus item details (comma-separated) |
| `marketing_type` | TEXT | Marketing direction: "內銷", "外銷" (comma-separated) |
| `grant_min` | BIGINT | Minimum subsidy amount (補助最低值) in 元 |
| `grant_max` | BIGINT | Maximum subsidy amount (補助最高值) in 元 |
| `recommended_plans` | TEXT | Recommended subsidy plans (comma-separated) |
| `timestamp` | TIMESTAMP | Record timestamp |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

## 🚀 Setup Methods

### Method 1: Using Python Script (Recommended)

1. **Ensure your `.env` file is configured:**

```bash
# Supabase Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database

EXTERNAL_JWT_SECRET=your-jwt-secret

# Gemini API
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

2. **Install required dependencies:**

```bash
cd backend
pip install -r requirements.txt
```

3. **Run the initialization script:**

```bash
python init_db.py
```

This will create all tables automatically using SQLAlchemy.

### Method 2: Using Supabase SQL Editor

1. **Open your Supabase project**
2. **Go to SQL Editor**
3. **Copy and paste the contents of `backend/schema.sql`**
4. **Execute the SQL script**

This method gives you more control and allows you to verify each step.

## 🧪 Verification

After creating the tables, verify they exist by running this query in Supabase SQL Editor:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

You should see all 4 tables listed.

## 📝 Subsidy Calculation Logic Reference

The subsidy calculation follows this logic (from the provided JavaScript code):

### 1. Employee-based Grant (grantEmployee)
```
grantEmployee = MIN(people × 150,000, 3,000,000)
```

### 2. Revenue Bonus (grantRevenueBonus)
```
IF revenue >= 10,000,000:
    grantRevenueBonus = 500,000
IF revenue >= grantEmployee × 5:
    grantRevenueBonus = budget × 0.1
```

### 3. Bonus Items Amount (bonusAmount)
- Base amounts: [100,000, 200,000, 50,000, 50,000, 50,000]
- If 4 items selected: total × 0.9
- If 5 items selected: total × 0.8

### 4. Maximum Grant Calculation
```
grantMax = grantEmployee + grantRevenueBonus + bonusAmount
```

### 5. Upper Limit Cap
```
upperLimit = MIN(4,500,000, revenue × 0.2)
IF grantMax > upperLimit:
    grantMax = upperLimit
```

### 6. Minimum Grant
```
grantMin = grantMax × 0.75
```

## 🎯 Recommended Plans Logic

### For Research & Development (研發):
- **地方SBIR**: threshold >= 0
- **CITD**: threshold >= 1,500,000
- **中央SBIR**: threshold >= 2,000,000

(threshold = grantMax × 0.8)

### For Marketing (行銷):
- **開拓海外市場計畫**: When marketing_type includes "外銷"
- **內銷行銷推廣計畫**: When marketing_type includes "內銷"

## 🔐 Security Notes

1. **User Authentication**: The system supports both authenticated users and guest users
2. **JWT Integration**: Uses `EXTERNAL_JWT_SECRET` for authentication
3. **Data Privacy**: All financial data is stored securely in Supabase
4. **Indexes**: Proper indexes are created for optimal query performance

## 🛠️ Next Steps

After database setup:

1. ✅ Database tables created
2. ⏭️ Create AI chatbot handler for Gemini API
3. ⏭️ Implement subsidy calculation functions
4. ⏭️ Create API endpoints for chatbot interactions
5. ⏭️ Build frontend interface

## 📚 Additional Resources

- **Supabase Docs**: https://supabase.com/docs
- **Gemini API Docs**: https://ai.google.dev/docs
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/

## 🆘 Troubleshooting

### Issue: "relation already exists" error
**Solution**: Tables already exist. Either drop them first or skip table creation.

### Issue: "permission denied" error
**Solution**: Check your Supabase database permissions and ensure the user has CREATE privileges.

### Issue: Connection timeout
**Solution**: Verify your `DATABASE_URL` is correct and the Supabase instance is running.

## 📞 Support

If you encounter any issues, please check:
1. Database connection string is correct
2. Supabase instance is active
3. Required Python packages are installed
4. Environment variables are properly set

---

**Created for**: Taiwan Government Subsidy Recommendation Chatbot
**Database**: Supabase (PostgreSQL)
**AI Model**: Gemini 2.5 Flash
**Last Updated**: 2026-01-21
