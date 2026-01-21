# 🚀 Quick Start Guide - Taiwan Government Subsidy Chatbot

## ✅ What Has Been Set Up

I've created the complete database structure for your Taiwan Government Subsidy chatbot project:

### 📁 Files Created:

1. **`backend/models.py`** (Updated)
   - Added `SubsidyConsultation` model for storing consultation data
   - Removed legacy company onboarding models
   - Updated imports to support BigInteger for large financial values

2. **`backend/config.py`** (Updated)
   - Changed from OpenAI to Gemini API configuration
   - Now uses `GEMINI_API_KEY` and `GEMINI_MODEL`

3. **`backend/subsidy_calculator.py`** (New)
   - Complete Python implementation of the subsidy calculation logic
   - Includes `SubsidyCalculator` class and helper functions
   - Ready to integrate with your chatbot

4. **`backend/init_db.py`** (New)
   - Python script to automatically create all database tables
   - Uses SQLAlchemy ORM

5. **`backend/schema.sql`** (New)
   - Raw SQL schema for manual database creation
   - Can be executed directly in Supabase SQL Editor

6. **`.env.example`** (New)
   - Example environment configuration file
   - Shows all required environment variables

7. **`DATABASE_SETUP.md`** (New)
   - Comprehensive database setup documentation
   - Includes table structures and calculation logic reference

## 🎯 Next Steps

### Step 1: Create Your .env File

```bash
# Copy the example file
cp .env.example .env

# Then edit .env and fill in your actual values
```

Your `.env` file should contain:

```bash
# Supabase Database
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres

# JWT Secret (for authentication)
EXTERNAL_JWT_SECRET=your-jwt-secret-here

# Gemini API
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

### Step 2: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Create Database Tables

**Option A: Using Python Script (Recommended)**
```bash
cd backend
python init_db.py
```

**Option B: Using Supabase SQL Editor**
1. Open your Supabase project
2. Go to SQL Editor
3. Copy contents of `backend/schema.sql`
4. Execute the SQL

### Step 4: Test the Subsidy Calculator

```bash
cd backend
python subsidy_calculator.py
```

This will run the example calculations and verify the logic is working.

## 📊 Database Table Structure

### Main Table: `subsidy_consultations`

Stores all Taiwan government subsidy consultation data:

- **Basic Info**: source, project_type (研發/行銷)
- **Financial Data**: budget, people, capital, revenue
- **Project Info**: marketing_type, growth_revenue
- **Bonus Items**: bonus_count, bonus_details
- **Results**: grant_min, grant_max, recommended_plans
- **Tracking**: timestamp, created_at, updated_at

## 💡 Calculation Logic Overview

```python
from backend.subsidy_calculator import calculate_subsidy

result = calculate_subsidy(
    budget=5000000,      # 500萬預算
    people=20,           # 20位員工
    capital=10000000,    # 1000萬資本額
    revenue=30000000,    # 3000萬營收
    bonus_count=3,       # 3個加分項目
    project_type="研發"  # 研發類型
)

print(f"補助範圍: NT${result['grant_min']:,} ~ NT${result['grant_max']:,}")
print(f"推薦方案: {', '.join(result['recommended_plans'])}")
```

## 🎨 Recommended Plans

### For 研發 (R&D) Projects:
- **地方SBIR** - Local SBIR program
- **CITD** - Commercial Innovation and Technology Development
- **中央SBIR** - Central SBIR program

### For 行銷 (Marketing) Projects:
- **開拓海外市場計畫** - Export market development
- **內銷行銷推廣計畫** - Domestic marketing (reserved)

After showing recommendations, the chatbot should also recommend **補助引擎** app for writing government subsidy proposals.

## 🔄 Next Development Steps

After database setup, you'll need to:

1. **Create Gemini Chatbot Handler**
   - Similar to `ai_chatbot_handler.py` but using Gemini API
   - Collect user information through conversation
   - Call `subsidy_calculator` to compute results

2. **Create API Endpoints**
   - `/api/subsidy/calculate` - Calculate subsidy
   - `/api/subsidy/chat` - Chat with AI assistant
   - `/api/subsidy/consultation/{id}` - Get consultation details

3. **Build Frontend**
   - Chat interface for user interaction
   - Display calculation results
   - Show recommended subsidy programs
   - Recommend "補助引擎" app

## 📞 Need Help?

- **Database Setup**: See `DATABASE_SETUP.md`
- **Calculation Logic**: See `backend/subsidy_calculator.py`
- **Environment Config**: See `.env.example`

## ✨ Features Implemented

- ✅ Database schema for subsidy consultations
- ✅ Subsidy calculation engine
- ✅ Gemini API configuration
- ✅ Support for both 研發 and 行銷 projects
- ✅ Bonus items logic (with discounts)
- ✅ Revenue-based bonuses
- ✅ Plan recommendation system
- ✅ Guest and authenticated user support

---

**Ready to proceed?** Start with Step 1 above! 🚀
