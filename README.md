# McBOT - Manufacturing Chatbot

A full-stack AI chatbot application with RAG (Retrieval-Augmented Generation) for querying manufacturing data. Built with React frontend and FastAPI backend, powered by local Ollama models and Oracle database.

## Features

### Backend
- **FastAPI** REST API
- **Oracle Database** for data persistence
- **Ollama Integration** for local AI models
- **JWT Authentication** with role-based access control
- **Session Management** with chat history
- **Multiple AI Models** support

### Frontend
- **React** with Vite
- **Tailwind CSS** for styling
- **Real-time Chat** interface
- **Session Management** with sidebar
- **Model Selection** dropdown
- **Admin Dashboard** for system management

### RAG (Retrieval-Augmented Generation)
- **Database Query Access** - AI can query live manufacturing data
- **Semantic Metadata** - YAML-based schema understanding
- **Natural Language** - Converts user questions to SQL automatically
- **Interactive Clarification** - AI asks for clarification when questions are ambiguous
  - Clickable suggestion buttons
  - Custom text input for user responses
  - Context-aware follow-up queries
- **Auto-Execution** - SQL queries run automatically, results summarized naturally
- **Oracle Syntax** - Auto-fixes common PostgreSQL→Oracle syntax differences
- **Security Hardened** - Only SELECT queries allowed (no INSERT, UPDATE, DELETE, DROP, etc.)
  - SQL injection prevention
  - Read-only database access
  - Multiple statement blocking
  - Comprehensive keyword filtering

### User Roles
- **User** (access_level=0): Can chat and manage own sessions
- **Moderator** (access_level=1): Reserved for future features
- **Admin** (access_level=2): Full access including admin dashboard

## Prerequisites

- Python 3.10+
- Node.js 18+
- Oracle Database (XE or higher)
- Ollama running locally

## Installation

### 1. Clone and Setup Python Environment

```powershell
cd app
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` in the project root and update:

```env
# Database Configuration
DB_username=your_oracle_username
DB_password=your_oracle_password
DB_host=localhost
DB_port=1521
DB_service_name=XEPDB1

# JWT Secret - Generate a strong key
SECRET_KEY=your_generated_secret_key_here

# CORS Origins
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8000

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
```

**⚠️ SECURITY: Generate a strong SECRET_KEY:**
```powershell
python app/scripts/generate_secret_key.py
```

Copy the output to your `.env` file.

```env
# Database Configuration
DB_username=your_db_user
DB_password=your_db_password
DB_host=localhost
DB_port=1521
DB_service_name=XEPDB1

# JWT Secret
SECRET_KEY=your-secret-key-here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Initialize Database

```powershell
# Create tables
python .\backend\database\initialized_db.py

# Create admin user
python .\backend\database\admin_users.py
```

### 4. Install Frontend Dependencies

```powershell
cd frontend
npm install
```

## Development

### Quick Start (Recommended)

From the project root directory:

```powershell
# Run the start script
.\start.ps1
```

This will:
1. Activate the virtual environment
2. Test database connection
3. Start the FastAPI server on http://localhost:8000
4. Serve the frontend (already built)

### Manual Start

**Backend only:**
```powershell
# From project root
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend development mode:**
```powershell
cd app/frontend
npm run dev
```

- Backend API: http://localhost:8000
- Backend Docs: http://localhost:8000/docs
- Frontend (dev): http://localhost:5173

## Production

### Build and Deploy

```powershell
# Build frontend
cd app/frontend
npm run build
cd ../..

# Start production server
.\start.ps1
```

Application: http://localhost:8000

## Project Structure

```
simple-ai-chatbot-system/
├── app/
│   ├── backend/
│   │   ├── api/              # API routes (auth, chat, sessions, admin, rag)
│   │   ├── core/             # Config & database connection
│   │   ├── database/         # Models, migrations, user management
│   │   ├── models/           # SQLAlchemy models
│   │   ├── rag/              # RAG schema metadata (YAML)
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── services/         # Business logic services
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/  # React components
│   │   │   ├── context/     # Context providers
│   │   │   ├── pages/       # Page components
│   │   │   └── services/    # API services
│   │   └── dist/            # Built files (production)
│   ├── tests/               # Test scripts
│   │   ├── test_query_security.py      # Security validation tests
│   │   ├── test_query_executor.py      # Query execution tests
│   │   └── test_rag_service.py         # RAG service tests
│   ├── scripts/             # Utility scripts
│   │   ├── create_admin_quick.py       # Quick admin creation
│   │   ├── reset_user_password.py      # Password reset
│   │   ├── update_ollama_models.py     # Sync Ollama models
│   │   └── inspect_rag_table.py        # DB inspection
│   ├── main.py              # FastAPI entry point
│   ├── start.ps1            # Dev startup script
│   └── start-prod.ps1       # Production script
├── start.ps1                # Root startup script (recommended)
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (form data)
- `POST /api/auth/login/json` - Login (JSON)
- `GET /api/auth/me` - Get current user
- `GET /api/auth/verify` - Verify token

### Chat
- `POST /api/chat/send` - Send message
- `POST /api/chat/send/stream` - Send with streaming
- `GET /api/chat/history/{session_id}` - Get history
- `DELETE /api/chat/message/{message_id}` - Delete message
- `GET /api/chat/models` - List models
- `GET /api/chat/ollama/status` - Check Ollama status

### Sessions
- `POST /api/sessions` - Create session
- `GET /api/sessions` - List sessions
- `GET /api/sessions/{id}` - Get session
- `PUT /api/sessions/{id}` - Update session
- `DELETE /api/sessions/{id}` - Soft delete
- `DELETE /api/sessions/{id}/permanent` - Hard delete

## Admin Features

Access admin dashboard at `/admin` (requires admin account)

- View system statistics
- Manage AI models
- View system information
- Monitor Ollama status

## Using RAG Features

### Enable Database Access

1. Start a new chat session
2. Toggle **"Database Access (RAG)"** in the chat interface
3. The AI can now query manufacturing data from `conv_test_pivot_queue_sim` table

### Example Questions

**Direct queries:**
- "How many devices are in November 2024?"
- "What's the average P1 yield for December?"
- "Show me total billed units by month"

**Ambiguous queries (triggers clarification):**
- "Show me devices for November" → AI asks which November (2024? 2025?)
- "What's the yield?" → AI asks which yield type (P1? P2? P3?)
- "How many units?" → AI asks which units (devices? billed_units?)

### Interactive Clarification

When the AI needs clarification:
1. It displays clickable suggestion buttons with options
2. You can click a suggestion to select it
3. Or type a custom response in the text box
4. Your response becomes context for the follow-up query

### SQL Query Handling

- SQL queries are executed automatically
- Results are summarized in natural language
- Raw SQL is hidden from users (logged to INFO level)
- Auto-fixes PostgreSQL syntax to Oracle (DATE_PART→SUBSTR, LIMIT→FETCH FIRST)

### Security Features

**Query Validation:**
- Only SELECT queries are allowed
- Blocks all data modification operations (INSERT, UPDATE, DELETE)
- Blocks all schema modifications (DROP, CREATE, ALTER, TRUNCATE)
- Blocks permission changes (GRANT, REVOKE)
- Prevents multiple statement execution (SQL injection protection)
- Validates queries before execution

**Blocked Keywords:**
`INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`, `TRUNCATE`, `GRANT`, `REVOKE`, `COMMIT`, `ROLLBACK`, `MERGE`, `REPLACE`, `RENAME`, `EXECUTE`, `EXEC`, `CALL`

If a user tries to modify data, they'll see: "⚠️ I cannot execute this query for security reasons. I can only run SELECT queries to retrieve data, not modify or delete it."

## Testing & Utilities

### Running Tests

Test scripts validate system functionality and security:

```powershell
# Test RAG service
python app/tests/test_rag_service.py

# Test query execution
python app/tests/test_query_executor.py

# CRITICAL: Test security validation
python app/tests/test_query_security.py
```

See `app/tests/README.md` for detailed information.

### Utility Scripts

Administrative tools for system management:

```powershell
# Create admin user
python app/backend/database/admin_users.py

# Quick admin creation
python app/scripts/create_admin_quick.py

# Reset user password
python app/scripts/reset_user_password.py <username> <password>

# Update Ollama models in database
python app/scripts/update_ollama_models.py

# Inspect database table
python app/scripts/inspect_rag_table.py
```

See `app/scripts/README.md` for detailed information.

## Troubleshooting

### Database Connection Failed
- Verify Oracle is running
- Check `.env` credentials
- Ensure service name is correct

### Ollama Not Connected
- Start Ollama: `ollama serve`
- Verify URL in `.env`
- Check firewall settings

### Frontend Build Errors
- Clear node_modules: `rm -r node_modules`
- Reinstall: `npm install`
- Rebuild: `npm run build`

## License

MIT

## Support

For issues and questions, please check the documentation or create an issue.
