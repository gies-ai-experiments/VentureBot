# VentureBots Quick Start Guide 🚀

> **Quick reference for getting VentureBots running locally**

## Prerequisites
- Python 3.8+
- Anthropic API key

## 1. Environment Setup
```bash
# Clone and enter directory
cd /Users/vishal/Desktop/VentureBot

# Copy environment template
cp .env.example .env

# Add your API key to .env
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

## 2. Installation & Testing
```bash
# Activate virtual environment
source agent_venv/bin/activate

# Test system components
python tests/test_imports.py              # Verify imports
python tests/test_enhanced_analysis.py    # Test market intelligence
```

## 3. Start Services
```bash
# Terminal 1: Start backend (port 8000)
PORT=8000 python main.py

# Terminal 2: Start frontend (port 8501)
chainlit run chainlit_app.py --port 8501
```

## 4. Access Application
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000/docs

## 5. Test Workflow
1. Open http://localhost:8501
2. Type "hello" to start onboarding
3. Complete user profile
4. Generate and select an idea
5. **Watch enhanced validation** (15-30 seconds)
6. See comprehensive market intelligence dashboard

## Expected Validation Output
```
🎯 MARKET ANALYSIS: [Your Idea]
📊 OVERALL ASSESSMENT: X.X/10 🟢
🔍 Analysis Confidence: ████████░░░░ (0.8/1.0)

📈 DETAILED SCORES:
├── Market Opportunity: ████████████ 0.8/1.0 🟢
├── Competitive Position: ██████░░░░░░ 0.6/1.0 🟡
├── Execution Feasibility: █████████░░░ 0.7/1.0 🟡
└── Innovation Potential: ████████████ 0.9/1.0 🟢

🏢 KEY COMPETITORS IDENTIFIED:
• [Competitor details with funding/users]

💡 MARKET OPPORTUNITIES IDENTIFIED:
• [Specific market gaps]

🚀 STRATEGIC RECOMMENDATIONS:
• [Prioritized action items]
```

## Troubleshooting
| Issue | Solution |
|-------|----------|
| No validation results | Check backend running: `curl http://localhost:8000/docs` |
| Import errors | Run: `python tests/test_imports.py` |
| Backend won't start | Check: API key in .env, port 8000 available |
| "No text response" | Restart backend: `PORT=8000 python main.py` |

## Documentation Map
- **README.md**: Complete project overview
- **docs/CLAUDE.md**: Development memory for Claude Code
- **docs/DEVELOPMENT_GUIDE.md**: Comprehensive troubleshooting
- **docs/VENTUREBOT_AGENT_ANALYSIS.md**: Technical system analysis

---
**✅ Success Indicator**: Validation shows rich visual dashboard with market intelligence in 15-30 seconds