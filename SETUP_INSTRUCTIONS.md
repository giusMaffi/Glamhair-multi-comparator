# 🚀 Setup Instructions - Glamhairshop Assistant

Complete guide to initialize the project on GitHub and local environment.

---

## 📋 Prerequisites

- Git installed
- GitHub account
- Python 3.9+ installed
- Anthropic API key

---

## 1️⃣ GitHub Repository Setup

### Create Repository on GitHub

1. Go to https://github.com/new
2. **Repository name**: `glamhairshop-assistant`
3. **Description**: "AI-powered conversational product finder for Glamhairshop"
4. **Visibility**: Private (recommended) or Public
5. ✅ **Do NOT** initialize with README, .gitignore, or license (we have them)
6. Click "Create repository"

### Copy Repository URL

After creation, copy the URL (example):
```
https://github.com/your-username/glamhairshop-assistant.git
```

---

## 2️⃣ Local Project Initialization

### Create Project Structure

```bash
# Create main directory
mkdir glamhairshop-assistant
cd glamhairshop-assistant

# Initialize git
git init
```

### Create Directory Structure

```bash
# Create all directories
mkdir -p {app,src,data,scripts,tests,docs,logs,deploy}
mkdir -p app/{routes,static/{css,js,images},templates}
mkdir -p src/{api/prompts,rag/matchers,routing,utils}
mkdir -p data/{products,embeddings,raw}
mkdir -p scripts/scraping
mkdir -p deploy

# Create __init__.py files for Python packages
touch src/__init__.py
touch src/api/__init__.py
touch src/api/prompts/__init__.py
touch src/rag/__init__.py
touch src/rag/matchers/__init__.py
touch src/routing/__init__.py
touch src/utils/__init__.py
touch app/__init__.py
touch app/routes/__init__.py
touch scripts/__init__.py
touch scripts/scraping/__init__.py
touch tests/__init__.py

# Create .gitkeep for empty directories
touch data/.gitkeep
touch data/products/.gitkeep
touch data/embeddings/.gitkeep
touch data/raw/.gitkeep
touch logs/.gitkeep
```

### Add Base Files

Copy the files I provided into the root directory:
- `README.md`
- `.gitignore`
- `.env.example`
- `requirements.txt`
- `src/config.py` (rename from `config.py`)

---

## 3️⃣ Git Configuration

### Configure Git (if not done globally)

```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### Add Files to Git

```bash
# Add all files
git add .

# Check status
git status

# Commit
git commit -m "Initial project structure - Glamhairshop Assistant"
```

### Connect to GitHub

```bash
# Add remote (replace with your actual URL)
git remote add origin https://github.com/your-username/glamhairshop-assistant.git

# Verify remote
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## 4️⃣ Local Development Setup

### Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Configure Environment

```bash
# Copy .env template
cp .env.example .env

# Edit .env with your values
nano .env  # or use your preferred editor

# CRITICAL: Add your Anthropic API key!
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxx
```

---

## 5️⃣ Verify Installation

### Test Configuration

```bash
# Test config loading
python -c "from src.config import *; print('Config loaded successfully!')"

# Expected output:
# ============================================================
# GLAMHAIRSHOP ASSISTANT - Configuration Loaded
# ============================================================
# Environment: development
# Model: claude-sonnet-4-20250514
# Categories: haircare, parrucchiere
# Port: 5000
# ============================================================
# Config loaded successfully!
```

---

## 6️⃣ Claude Integration Setup

To enable me (Claude) to access your GitHub repository:

### Option A: Share Repository Access

1. Go to your GitHub repo
2. Settings → Collaborators
3. Add collaborator (if working with team)
4. Share repository URL in our chat

### Option B: Share Key Files

When you want me to review/edit code:
1. Share the GitHub repo URL: `https://github.com/your-username/glamhairshop-assistant`
2. I can guide you on what to add/modify
3. You commit and push changes
4. Share updated files if needed

---

## 7️⃣ Next Steps - Development Workflow

### Daily Workflow

```bash
# 1. Pull latest changes
git pull origin main

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Work on your feature
# ... code ...

# 4. Commit changes
git add .
git commit -m "feat: your feature description"

# 5. Push to GitHub
git push origin feature/your-feature-name

# 6. Create Pull Request on GitHub
# (optional for solo work, merge directly)

# 7. Merge to main
git checkout main
git merge feature/your-feature-name
git push origin main
```

### Git Commit Convention

Use semantic commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Maintenance

Examples:
```bash
git commit -m "feat: add haircare product matcher"
git commit -m "fix: resolve category detection bug"
git commit -m "docs: update API documentation"
```

---

## 8️⃣ Claude Collaboration Workflow

### When Working Together

**You:**
1. Share GitHub repo URL
2. Tell me what you want to work on
3. I'll provide code/files

**Me (Claude):**
1. I'll create/modify files
2. Provide them for download
3. Guide you on where to place them

**You:**
1. Add files to project
2. Test locally
3. Commit and push

**Repeat cycle!**

### Sharing Updates with Claude

When you want me to review code:

```bash
# Share specific file
cat src/rag/retriever.py

# Or share via GitHub URL
# https://github.com/your-username/glamhairshop-assistant/blob/main/src/rag/retriever.py
```

I can then review and suggest improvements!

---

## 9️⃣ Troubleshooting

### "Module not found" Error

```bash
# Ensure venv is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt
```

### "ANTHROPIC_API_KEY not found"

```bash
# Check .env file exists
ls -la .env

# Verify content
cat .env | grep ANTHROPIC_API_KEY

# If missing, add it:
echo "ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxx" >> .env
```

### Git Push Rejected

```bash
# Pull latest changes first
git pull origin main

# Resolve conflicts if any
# Then push again
git push origin main
```

---

## 🎉 You're Ready!

Project structure is set up. Now we can start building:

**Next tasks:**
1. ✅ Project structure (DONE)
2. 🔄 RAG system development
3. 🔄 Category detection
4. 🔄 Product matchers
5. 🔄 Flask API
6. 🔄 Frontend

Let me know when you're ready to start coding! 🚀

---

## 📞 Need Help?

Share:
- Error messages
- Output of `git status`
- Screenshots
- Repository URL

I'm here to help! 😊
