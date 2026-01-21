# 🇹🇼 Taiwan Government Subsidy Chatbot API

AI-powered chatbot for Taiwan government subsidy consultation and recommendation using **Google Gemini AI**.

## 🎯 Features

- ✅ **AI-Powered Conversation**: Uses Google Gemini 2.5 Flash for natural dialogue
- ✅ **Subsidy Calculation**: Automatic calculation of subsidy grant ranges
- ✅ **Program Recommendation**: Recommends suitable government programs (SBIR, CITD, etc.)
- ✅ **Session Management**: Track and resume consultation sessions
- ✅ **Data Export**: Export consultation results in Chinese format
- ✅ **JWT Authentication**: Secure authentication with external JWT tokens

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend App                         │
│              (Your Nuxt/React/Vue App)                  │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP + JWT
                   ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Subsidy Chatbot Handler (Gemini AI)           │   │
│  │  - Conversation Management                      │   │
│  │  - Data Extraction                              │   │
│  │  - Subsidy Calculation                          │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  API Endpoints                                  │   │
│  │  - /api/subsidy/chat                            │   │
│  │  - /api/subsidy/calculate                       │   │
│  │  - /api/subsidy/sessions                        │   │
│  └─────────────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│           Supabase PostgreSQL Database                  │
│  - users                                                │
│  - chat_sessions                                        │
│  - chat_messages                                        │
│  - subsidy_consultations                                │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- PostgreSQL database (Supabase recommended)
- Google Gemini API key
- JWT secret from your main authentication system

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/engkailun3117/Strategy_AI_chatbot.git
cd Strategy_AI_chatbot

# Install Python dependencies
cd backend
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the `backend/` directory:

```bash
# Supabase Database
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres

# JWT Secret (from your main auth system)
EXTERNAL_JWT_SECRET=your-jwt-secret-here

# Gemini API
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Database Setup

**Option A: Using Python script**
```bash
cd backend
python init_db.py
```

**Option B: Using Supabase SQL Editor**
1. Open Supabase SQL Editor
2. Copy contents of `backend/schema.sql`
3. Execute the SQL

### 5. Run the Server

```bash
cd backend
python main.py
```

Or using uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 6. API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

Or see [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for detailed endpoint information.

## 📊 Subsidy Calculation Logic

### 1. Employee-based Grant
```
grantEmployee = MIN(people × 150,000, 3,000,000)
```

### 2. Revenue Bonus
```
IF revenue >= 10,000,000:
    grantRevenueBonus = 500,000
IF revenue >= grantEmployee × 5:
    grantRevenueBonus = budget × 0.1
```

### 3. Bonus Items
- Base amounts: [100,000, 200,000, 50,000, 50,000, 50,000]
- 4 items: total × 0.9
- 5 items: total × 0.8

### 4. Maximum Grant
```
grantMax = grantEmployee + grantRevenueBonus + bonusAmount
upperLimit = MIN(4,500,000, revenue × 0.2)
grantMax = MIN(grantMax, upperLimit)
```

### 5. Minimum Grant
```
grantMin = grantMax × 0.75
```

## 🎯 Recommended Programs

### Research & Development (研發)
- **地方SBIR** - Local SBIR program (threshold >= 0)
- **CITD** - Commercial Innovation (threshold >= 1.5M)
- **中央SBIR** - Central SBIR (threshold >= 2M)

### Marketing (行銷)
- **開拓海外市場計畫** - Export market development
- **內銷行銷推廣計畫** - Domestic marketing

*Threshold = grantMax × 0.8*

## 📁 Project Structure

```
Strategy_AI_chatbot/
├── backend/
│   ├── main.py                      # FastAPI application
│   ├── subsidy_chatbot_handler.py   # Gemini AI chatbot handler
│   ├── subsidy_calculator.py        # Subsidy calculation logic
│   ├── models.py                    # Database models
│   ├── schemas.py                   # Pydantic schemas
│   ├── auth.py                      # JWT authentication
│   ├── database.py                  # Database connection
│   ├── config.py                    # Configuration
│   ├── init_db.py                   # Database initialization
│   ├── schema.sql                   # SQL schema
│   └── requirements.txt             # Python dependencies
├── API_DOCUMENTATION.md             # API documentation
├── DATABASE_SETUP.md                # Database setup guide
├── QUICK_START.md                   # Quick start guide
└── README.md                        # This file
```

## 🔧 Development

### Run Tests

```bash
cd backend
python subsidy_calculator.py
```

This will run example calculations and verify the logic.

### View Logs

The server prints configuration and logs to stdout:

```
============================================================
🔧 Backend Configuration:
   Database: postgresql://postgres...
   API Host: 0.0.0.0
   API Port: 8000
   External JWT Secret: your-jwt-secret... (length: 32)
   Gemini Model: gemini-2.5-flash
============================================================
```

## 🌐 API Endpoints

### Core Endpoints

- `POST /api/subsidy/chat` - Chat with AI assistant
- `POST /api/subsidy/calculate` - Direct calculation
- `GET /api/subsidy/sessions` - Get user sessions
- `GET /api/subsidy/consultations/{id}` - Get consultation data
- `GET /api/subsidy/consultations/{id}/export` - Export data

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete API reference.

## 🛡️ Security

- JWT-based authentication
- User data isolation (users can only access their own data)
- SQL injection protection via SQLAlchemy ORM
- CORS configuration for production deployment
- Secure credential management via environment variables

## 📝 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host/db` |
| `EXTERNAL_JWT_SECRET` | JWT secret from main system | `your-secret-key` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSy...` |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.5-flash` |
| `API_HOST` | API server host | `0.0.0.0` |
| `API_PORT` | API server port | `8000` |

## 🤝 Contributing

This is a specialized project for Taiwan government subsidy consultation. If you have suggestions or improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is proprietary software. All rights reserved.

## 📞 Support

For issues or questions:
- Check the [API Documentation](./API_DOCUMENTATION.md)
- Review the [Database Setup Guide](./DATABASE_SETUP.md)
- See the [Quick Start Guide](./QUICK_START.md)

## 🎉 Acknowledgments

- **Google Gemini AI** - Natural language processing
- **FastAPI** - Modern Python web framework
- **Supabase** - PostgreSQL database hosting
- **SQLAlchemy** - Python SQL toolkit and ORM

---

**Version**: 1.0.0
**Last Updated**: 2026-01-21
**AI Model**: Google Gemini 2.5 Flash
