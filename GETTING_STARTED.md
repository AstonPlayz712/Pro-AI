# 🚀 QUICK START GUIDE - Private AI Assistant

## ⚡ Get Started in 3 Minutes

### Step 1: Install (30 seconds)
```bash
cd /workspaces/Pro-AI
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure (1 minute)
```bash
# Copy template
cp .env.example .env

# Open .env and add API keys (optional - Ollama works without)
# OPENAI_API_KEY=your-key
# ANTHROPIC_API_KEY=your-key
# GOOGLE_API_KEY=your-key
```

### Step 3: Run (30 seconds)
```bash
python main.py
```

### Step 4: Open Browser
Visit: **http://localhost:8000**

---

## 🎯 First Time Using?

1. **Choose a Model**
   - OpenAI: Requires API key, most capable
   - Anthropic: Requires API key, good reasoning
   - Google: Requires API key, good for long text
   - Ollama: No API key, free & private (requires Ollama server)

2. **Adjust Settings**
   - Temperature: 0.0 (focused) to 2.0 (creative)
   - Max Tokens: 100-4000 (higher = longer responses)

3. **Send a Message**
   - Type in the text box
   - Click Send or press Shift+Enter
   - Watch the response appear!

4. **Continue Chatting**
   - Context is preserved automatically
   - History saved in your browser
   - Clear chat anytime with the Clear button

---

## 📍 Where Everything Is

| Component | Location | Purpose |
|-----------|----------|---------|
| Web UI | `http://localhost:8000` | Chat interface |
| API Docs | `http://localhost:8000/docs` | API reference |
| Config | `.env` | API keys & settings |
| Backend | `src/` | Python code |
| Frontend | `ui/` | HTML/CSS/JS |
| Docs | `README.md` | Full documentation |

---

## 🔑 Need API Keys?

### OpenAI
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy to `.env`: `OPENAI_API_KEY=sk-...`

### Anthropic
1. Go to https://console.anthropic.com
2. Get API key
3. Copy to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

### Google Gemini
1. Go to https://ai.google.dev
2. Create API key
3. Copy to `.env`: `GOOGLE_API_KEY=...`

### Ollama (Free & Local)
1. Install from https://ollama.ai
2. Run: `ollama serve`
3. In another terminal: `ollama pull llama2`
4. No API key needed!

---

## 🐛 Troubleshooting

### "Port already in use"
```bash
# Use different port
API_PORT=9000 python main.py
```

### "ModuleNotFoundError"
```bash
# Make sure you're in the venv
source venv/bin/activate
# And installed requirements
pip install -r requirements.txt
```

### "API key not working"
- Check `.env` file exists in project root
- Verify key is correctly copied (no extra spaces)
- Make sure key has proper permissions on the service

### "Can't connect to Ollama"
```bash
# Make sure Ollama server is running
ollama serve

# Check URL in .env
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 📚 Next Steps

### Learn the API
```bash
# Read the comprehensive guide
cat API_USAGE_GUIDE.md

# Or visit interactive docs
http://localhost:8000/docs
```

### Test the Backend
```bash
# In one terminal
python main.py

# In another
python test_api.py
```

### Explore the Code
```bash
# Main entry point
cat main.py

# Backend structure
ls -la src/

# See project docs
python PROJECT_DOCUMENTATION.py
```

### Build on It
- Add new endpoints in `src/backend/routes/`
- Implement tools in `src/tools/`
- Extend memory to database
- Add user authentication
- Deploy to cloud

---

## 💪 Full Documentation

- **README.md** - Overview and setup
- **API_USAGE_GUIDE.md** - API reference with examples
- **QUICK_REFERENCE.md** - Quick lookup
- **FINAL_SUMMARY.md** - Complete project summary
- **ARCHITECTURE.md** - System design
- **PROJECT_DOCUMENTATION.py** - Deep technical docs

---

## ✨ Features at a Glance

✅ Beautiful Web UI
✅ 4 AI Models (OpenAI, Anthropic, Google, Ollama)
✅ Real-time Chat
✅ Auto-save History
✅ Temperature Controls
✅ Token Management
✅ Dark/Light Theme
✅ Mobile Responsive
✅ API Documentation
✅ Production Ready

---

## 🎓 Common Tasks

### Send a Chat Message
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "model": "openai"
  }'
```

### Get Available Models
```bash
curl http://localhost:8000/api/models
```

### Get Chat History
```bash
curl http://localhost:8000/api/memory
```

### Clear Memory
```bash
curl -X DELETE http://localhost:8000/api/memory
```

---

## 🚢 Deploy to Production

### Local Server
```bash
python main.py
```

### Production Server
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Docker
```bash
docker build -t ai-assistant .
docker run -p 8000:8000 ai-assistant
```

### Environment Setup for Production
```bash
# Use production settings
API_DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000

# Add authentication
# Add HTTPS
# Add rate limiting
# Add monitoring
```

---

## 📊 Project Overview

```
Your Project
├── Backend API (FastAPI)
│   ├── OpenAI Support
│   ├── Anthropic Support
│   ├── Google Support
│   └── Ollama Support (Free!)
├── Web UI (HTML/CSS/JS)
│   ├── Chat Interface
│   ├── Model Selector
│   └── Settings Panel
├── Conversation Memory
│   ├── Browser Storage
│   └── Server JSON Storage
└── Complete Documentation
    ├── API Guide
    ├── Architecture
    └── Setup Instructions
```

---

## 🎯 Success Checklist

- [ ] Server running: `python main.py`
- [ ] Web UI opens: `http://localhost:8000`
- [ ] Can type messages
- [ ] Can select different models
- [ ] Response appears in chat
- [ ] Chat history saves
- [ ] API docs work: `http://localhost:8000/docs`

**If all checked: ✅ You're ready to go!**

---

## 🆘 Get Help

1. **Check the docs** - Most answers are in README.md
2. **Run verify_setup.py** - Checks if everything is configured correctly
3. **Check server output** - Error messages are logged
4. **Read API docs** - Visit `/docs` endpoint
5. **Review examples** - Check test_api.py for examples

---

## 🎉 Congratulations!

You now have a **complete, production-ready AI assistant** with:
- ✅ Backend API
- ✅ Web interface
- ✅ Multiple AI models
- ✅ Conversation memory
- ✅ Full documentation

**Start building something amazing! 🚀**

---

**Quick Links:**
- 📖 [README.md](README.md) - Full documentation
- 🔌 [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md) - API reference
- 🏗️ [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- 📋 [MANIFEST.md](MANIFEST.md) - File listing
- 📊 [FINAL_SUMMARY.md](FINAL_SUMMARY.md) - Complete summary

**Server Command:** `python main.py`
**Browser URL:** `http://localhost:8000`
**API Docs:** `http://localhost:8000/docs`
