# Utility Scripts

Administrative and maintenance scripts for the AI Chatbot System.

## User Management

**`create_admin_quick.py`**
- Quick admin user creation from command line
- Interactive prompts for username, email, password

```powershell
python app/scripts/create_admin_quick.py
```

**`app/backend/database/admin_users.py`** (main location)
- Full-featured admin user management
- Create, list, and manage users
- More comprehensive than create_admin_quick.py

```powershell
python app/backend/database/admin_users.py
```

**`reset_user_password.py`**
- Reset user password by username
- Useful when users forget passwords

```powershell
python app/scripts/reset_user_password.py <username> <new_password>
```

## System Maintenance

**`update_ollama_models.py`**
- Syncs Ollama models to database
- Updates model availability status
- Run after installing new Ollama models

```powershell
python app/scripts/update_ollama_models.py
```

**`inspect_rag_table.py`**
- Inspects the RAG data table structure and contents
- Shows table schema and sample data
- Useful for debugging data issues

```powershell
python app/scripts/inspect_rag_table.py
```

## Common Tasks

### First Time Setup

```powershell
# 1. Create admin user
python app/backend/database/admin_users.py

# 2. Sync Ollama models
python app/scripts/update_ollama_models.py
```

### Troubleshooting

```powershell
# Check database table structure
python app/scripts/inspect_rag_table.py

# Reset a forgotten password
python app/scripts/reset_user_password.py admin NewPassword123
```

### Regular Maintenance

```powershell
# Update models after installing new ones in Ollama
python app/scripts/update_ollama_models.py
```
