# Session Management & Memory Preservation

## Overview
The chatbot test interface now includes intelligent session management with automatic session detection, chat history loading, and memory preservation across sessions.

## Features

### 1. **Automatic Session Detection**
When the user loads the page, the system automatically:
- Checks for existing active sessions via `/api/subsidy/sessions/latest`
- Detects if the user is a first-time user (no previous sessions)
- Loads the latest session if one exists
- Creates a new session only for first-time users

### 2. **Chat History Loading**
If an existing session is found:
- Loads all previous messages from `/api/subsidy/sessions/{session_id}/messages`
- Displays the full conversation history
- Restores the progress indicator
- Shows an info message: "已載入您的上次對話 (Session #X)"

### 3. **First-Time User Detection**
The system identifies first-time users by:
- Checking if `/api/subsidy/sessions/latest` returns `session_id: null`
- Setting `isFirstTimeUser = true` flag
- Showing a welcome message: "歡迎！這是您第一次使用補助診斷助理。"
- Automatically creating their first session

### 4. **Memory Preservation for New Sessions**
When users click "🆕 New Session", they get a choice:
- **Preserve Data** (確定): Copies all consultation data from current session to new session
- **Fresh Start** (取消): Creates a blank new session

**What Data is Preserved:**
- Project type (研發/行銷)
- Budget (預計所需經費)
- Company size (投保人數)
- Capital (實收資本額)
- Revenue (年度營業額)
- Bonus items (all 5 boolean flags + count + details)
- Marketing type (行銷方向)
- Growth revenue (預計營業額成長)

## API Changes

### Updated Endpoint: `POST /api/subsidy/sessions/new`

**New Parameter:**
- `previous_session_id` (optional, int): ID of previous session to copy data from

**Behavior:**
- If `previous_session_id` is provided, copies all consultation data to new session
- If not provided or null, creates a blank session
- Returns: session_id, welcome message, progress

**Example:**
```javascript
// Create new session with preserved data
POST /api/subsidy/sessions/new?previous_session_id=42

// Create blank new session
POST /api/subsidy/sessions/new
```

## Frontend Implementation

### Key Functions

#### `loadLatestSession()`
- Called on page load
- Fetches latest active session
- Loads chat history if session exists
- Detects first-time users
- Creates new session for first-time users

#### `loadChatHistory(sessionId)`
- Fetches all messages for a session
- Displays them in chronological order
- Scrolls to bottom after loading

#### `loadConsultationData(sessionId)`
- Fetches consultation data
- Calculates and updates progress indicator

#### `handleNewSessionClick()`
- Shows confirmation dialog for data preservation
- Calls `startNewSession(preserve)` with user's choice

#### `startNewSession(preservePreviousData)`
- Creates new session via API
- Optionally includes `previous_session_id` parameter
- Shows appropriate info message
- Clears chat and displays welcome message

### User Experience Flow

**First-Time User:**
```
1. User opens test-chatbot.html
2. System detects: no previous sessions
3. Shows: "歡迎！這是您第一次使用補助診斷助理。"
4. Shows: "已開始新對話 (Session #1)"
5. Displays: Welcome message from chatbot
```

**Returning User:**
```
1. User opens test-chatbot.html
2. System detects: existing active session #5
3. Shows: "已載入您的上次對話 (Session #5)"
4. Loads: All previous messages and conversation history
5. Restores: Progress indicator (e.g., "4/6")
6. User can continue conversation where they left off
```

**Starting New Session (with data preservation):**
```
1. User clicks "🆕 New Session"
2. System shows dialog:
   "是否要將目前填寫的資料帶入新對話？
   • 點「確定」= 保留資料，繼續使用
   • 點「取消」= 清空資料，重新開始"
3. User clicks "確定" (preserve)
4. Shows: "已開始新對話並保留先前資料 (Session #5 → #6)"
5. New session has all consultation data from session #5
6. Chat history is cleared (fresh conversation)
7. User can continue from where they were with preserved data
```

**Starting New Session (fresh start):**
```
1. User clicks "🆕 New Session"
2. System shows dialog
3. User clicks "取消" (fresh start)
4. Shows: "已開始新對話 (Session #7)"
5. All data is cleared
6. Starts from beginning
```

## UI Changes

### New Info Message Style
Added `.info-message` CSS class for informational messages:
- Light blue background (#d1ecf1)
- Dark cyan text (#0c5460)
- Centered text
- Blue left border
- Used for session status messages

### Updated Session Info Display
- Session ID always displayed and updated
- Progress indicator shows current completion status
- New Session button triggers smart preservation dialog

## Benefits

1. **Better UX**: Users don't lose their session on page refresh
2. **Convenience**: Can pick up conversation where they left off
3. **Flexibility**: Choice to preserve or reset data when starting new session
4. **First-Time Experience**: Welcoming message for new users
5. **Transparency**: Clear info messages about what's happening
6. **Memory Preservation**: Don't lose filled data when creating new sessions

## Testing

### Test Case 1: First-Time User
1. Clear all sessions from database (or use new JWT token)
2. Open test-chatbot.html
3. Should see: "歡迎！這是您第一次使用補助診斷助理。"
4. Should see: "已開始新對話 (Session #1)"
5. Should see: Welcome message from AI

### Test Case 2: Returning User
1. Have an existing active session with some messages
2. Open test-chatbot.html
3. Should see: "已載入您的上次對話 (Session #X)"
4. Should see: All previous messages loaded
5. Should see: Progress indicator updated correctly

### Test Case 3: New Session with Data Preservation
1. Fill in some data (e.g., project type, budget, people)
2. Click "🆕 New Session"
3. Click "確定" in dialog
4. Should see: "已開始新對話並保留先前資料 (Session #X → #Y)"
5. Verify: New session has all consultation data from previous session
6. Chat history should be cleared
7. Can query data to verify preservation

### Test Case 4: New Session Fresh Start
1. Have existing session with data
2. Click "🆕 New Session"
3. Click "取消" in dialog
4. Should see: "已開始新對話 (Session #Y)"
5. Verify: New session has no consultation data
6. Starts from beginning

## Implementation Files

- **Backend**: `/backend/main.py` - Updated `/api/subsidy/sessions/new` endpoint
- **Frontend**: `/test-chatbot.html` - Complete session management implementation
- **Documentation**: This file

## Future Enhancements

Potential improvements:
- Session history dropdown to switch between past sessions
- "Resume" button to go back to previous active session
- Session naming/tagging capability
- Export session transcript
- Share session with others
- Session timeout handling
