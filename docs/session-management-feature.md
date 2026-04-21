# Session Management Feature

## Overview

The Natural Language Query interface now supports proper session management, allowing users to create new conversation sessions and maintain context isolation between different query conversations.

## Problem Statement

Previously, the system maintained a single session throughout the application lifetime using a hardcoded default session ID (`00000000-0000-0000-0000-000000000000`). This caused:

1. **Context Confusion**: The query service struggled to differentiate between fresh queries and follow-up questions
2. **No Session Isolation**: All queries were treated as part of the same conversation
3. **Poor User Experience**: Users couldn't start fresh conversations without clearing browser storage

## Solution

### Backend Changes

#### 1. New Session Creation Endpoint

**Endpoint**: `POST /api/v1/query/session/new`

**Request Body** (optional):
```json
{
  "user_id": "optional-user-identifier"
}
```

**Response**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-04-21T09:00:00.000Z"
}
```

**Implementation**: [`backend/app/api/v1/query.py`](../backend/app/api/v1/query.py:113-148)

#### 2. Session-Aware Query Processing

The existing query endpoint now properly handles session IDs:

**Endpoint**: `POST /api/v1/query`

**Request Body**:
```json
{
  "query_text": "Show me all APIs",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "use_ai_agents": true
}
```

The `session_id` parameter is now properly utilized to maintain conversation context and isolate queries between different sessions.

### Frontend Changes

#### 1. Enhanced useQuerySession Hook

**Location**: [`frontend/src/hooks/useQuerySession.ts`](../frontend/src/hooks/useQuerySession.ts)

**New Function**: `createNewSession()`

```typescript
const createNewSession = async () => {
  // Calls backend API to create new session
  // Updates local state and localStorage
  // Clears current query history
  // Falls back to local UUID generation if API fails
}
```

**Updated Interface**:
```typescript
interface UseQuerySessionReturn {
  sessionId: string;
  queries: Query[];
  isLoading: boolean;
  error: string | null;
  executeQuery: (queryText: string) => Promise<QueryResponse | null>;
  clearSession: () => void;
  createNewSession: () => Promise<void>;  // NEW
  loadSessionHistory: () => Promise<void>;
}
```

#### 2. New Session Button in UI

**Location**: [`frontend/src/pages/Query.tsx`](../frontend/src/pages/Query.tsx)

A new "New Session" button has been added to the query interface header:

- **Position**: Next to the session ID display
- **Behavior**: 
  - If queries exist: Prompts user for confirmation before creating new session
  - If no queries: Creates new session immediately
- **State**: Disabled while loading to prevent duplicate requests

**UI Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Natural Language Query                                   │
│ Ask questions about your APIs in plain English          │
│                                                          │
│ [Session: 550e8400...] [New Session] [Clear History]   │
└─────────────────────────────────────────────────────────┘
```

## Usage

### For Users

1. **Starting a New Conversation**:
   - Click the "New Session" button in the query interface
   - If you have existing queries, confirm you want to start fresh
   - Your previous conversation is saved and can be accessed via session history

2. **Session Persistence**:
   - Sessions are stored in browser localStorage
   - Refreshing the page maintains your current session
   - Each browser tab can have its own session

3. **Session Isolation**:
   - Each session maintains its own conversation context
   - Follow-up questions only reference queries within the same session
   - Different sessions don't interfere with each other

### For Developers

#### Creating a New Session (API)

```bash
curl -X POST http://localhost:8000/api/v1/query/session/new \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### Executing a Query with Session

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Show me all APIs",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

#### Retrieving Session History

```bash
curl http://localhost:8000/api/v1/query/session/550e8400-e29b-41d4-a716-446655440000
```

## Testing

A comprehensive test script is available to verify session management functionality:

**Location**: [`backend/scripts/test_session_management.py`](../backend/scripts/test_session_management.py)

**Run the test**:
```bash
cd backend
python scripts/test_session_management.py
```

**Test Coverage**:
1. ✓ Create new session via API
2. ✓ Execute query in session 1
3. ✓ Create second session
4. ✓ Execute query in session 2
5. ✓ Verify session 1 history
6. ✓ Verify session 2 history
7. ✓ Verify session isolation

## Benefits

### 1. Improved Context Management
- The query service can now accurately distinguish between fresh queries and follow-ups
- AI agents have better context for generating responses
- Follow-up suggestions are more relevant

### 2. Better User Experience
- Users can start fresh conversations without losing history
- Multiple conversation threads can be maintained
- Clear visual indication of current session

### 3. Enhanced Debugging
- Session IDs make it easier to trace query flows
- Session history provides audit trail
- Isolated sessions simplify troubleshooting

### 4. Scalability
- Supports multiple concurrent users
- Each user can have multiple active sessions
- Session data can be archived or cleaned up independently

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Query.tsx                                      │    │
│  │  - New Session Button                           │    │
│  │  - Session Display                              │    │
│  └────────────────┬───────────────────────────────┘    │
│                   │                                      │
│  ┌────────────────▼───────────────────────────────┐    │
│  │  useQuerySession Hook                           │    │
│  │  - createNewSession()                           │    │
│  │  - executeQuery(sessionId)                      │    │
│  │  - loadSessionHistory(sessionId)                │    │
│  └────────────────┬───────────────────────────────┘    │
└───────────────────┼──────────────────────────────────────┘
                    │
                    │ HTTP/REST
                    │
┌───────────────────▼──────────────────────────────────────┐
│                  Backend (FastAPI)                        │
│                                                           │
│  ┌────────────────────────────────────────────────┐     │
│  │  /api/v1/query/session/new                     │     │
│  │  - Generate UUID                                │     │
│  │  - Return session_id                            │     │
│  └────────────────┬───────────────────────────────┘     │
│                   │                                       │
│  ┌────────────────▼───────────────────────────────┐     │
│  │  /api/v1/query                                  │     │
│  │  - Accept session_id                            │     │
│  │  - Process with context                         │     │
│  └────────────────┬───────────────────────────────┘     │
│                   │                                       │
│  ┌────────────────▼───────────────────────────────┐     │
│  │  QueryService                                   │     │
│  │  - Context management                           │     │
│  │  - Session-aware processing                     │     │
│  └────────────────┬───────────────────────────────┘     │
└───────────────────┼───────────────────────────────────────┘
                    │
                    │
┌───────────────────▼───────────────────────────────────────┐
│                  OpenSearch                                │
│                                                            │
│  - queries index (session_id field)                       │
│  - Session history storage                                │
│  - Query context preservation                             │
└────────────────────────────────────────────────────────────┘
```

## Future Enhancements

1. **Session Management UI**:
   - List all sessions
   - Switch between sessions
   - Rename sessions
   - Delete old sessions

2. **Session Sharing**:
   - Share session URLs
   - Collaborative query sessions
   - Session export/import

3. **Advanced Context**:
   - Cross-session learning
   - User preference persistence
   - Session templates

4. **Analytics**:
   - Session duration tracking
   - Query patterns per session
   - User engagement metrics

## Related Files

- Backend API: [`backend/app/api/v1/query.py`](../backend/app/api/v1/query.py)
- Query Service: [`backend/app/services/query_service.py`](../backend/app/services/query_service.py)
- Frontend Hook: [`frontend/src/hooks/useQuerySession.ts`](../frontend/src/hooks/useQuerySession.ts)
- Frontend UI: [`frontend/src/pages/Query.tsx`](../frontend/src/pages/Query.tsx)
- Test Script: [`backend/scripts/test_session_management.py`](../backend/scripts/test_session_management.py)

## Changelog

- **2026-04-21**: Initial implementation of session management feature
  - Added `/api/v1/query/session/new` endpoint
  - Enhanced `useQuerySession` hook with `createNewSession()`
  - Added "New Session" button to query interface
  - Created test script for session management
  - Updated documentation

---

Made with Bob