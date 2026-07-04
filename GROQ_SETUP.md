# Deploy with Free LLM (Groq) - Quick Setup

**Status:** Codebase updated to support free LLM APIs  
**Recommended:** Groq (free tier, unlimited requests, fastest)  
**Time to deploy:** 15 minutes

---

## 🚀 Quick Action Items

### Step 1: Get Groq API Key (2 minutes)
```
1. Visit: https://console.groq.com/
2. Sign up (free, no credit card)
3. Go to API Keys
4. Create new key
5. Copy the key (gsk_...)
```

### Step 2: Update Streamlit Cloud Secrets (2 minutes)

Replace your old Claude secret with Groq:

**In Streamlit Cloud Dashboard:**
1. Click hamburger ☰ → Settings → Secrets
2. **Remove:** `CLAUDE_API_KEY = "..."`
3. **Add:** `GROQ_API_KEY = "gsk_YOUR_KEY_HERE"`
4. Save

**Your app will auto-redeploy!** ✨

### Step 3: Test (1 minute)
1. Load sample data
2. Process products
3. Check logs for "LLM verification" messages
4. Download results

---

## What Changed in Codebase

✅ **New file:** `src/services/llm_service.py`
- Unified LLM service supporting Groq, Gemini, Claude
- Auto-detects provider from config
- Falls back gracefully if LLM unavailable

✅ **Updated:** `config.yaml`
- Provider: groq (default)
- Model: mixtral-8x7b-32768 (fast)
- use_only_when: ambiguous (cost optimization)

✅ **Updated:** `src/agents/matching_agent.py`
- Integrates LLM service
- Uses LLM for verification when confidence is ambiguous
- Graceful degradation if LLM unavailable

✅ **Updated:** `requirements-streamlit.txt` and `requirements.txt`
- Added: groq>=0.4.1
- Added: google-generativeai>=0.3.0

✅ **Updated:** `app.py`
- Added Groq info to sidebar
- Link to free API console

✅ **New documentation:** `docs/FREE_LLM_INTEGRATION.md`
- Complete setup guide
- Provider comparison
- Troubleshooting
- Model options

---

## Why This Works Better

| Metric | Claude (Paid) | Groq (Free) |
|--------|---------------|------------|
| Cost | $0.50-1.00 per 1000 products | $0.00 ✨ |
| Setup | Requires subscription | Sign up instantly |
| Speed | Moderate | Very fast ⚡ |
| Quality | Excellent | Excellent |
| Credit card | Required | Not needed |

---

## Two-Stage Matching (Smart & Cheap)

**Stage 1: Deterministic** (always)
- Brand name matching
- Domain legitimacy
- Product categories
- Logo detection
- **Cost:** $0

**Stage 2: LLM Verification** (only when ambiguous)
- If confidence between 40-75%
- Call Groq for verification
- ~20% of products
- **Cost:** $0 (free tier)

**Result:** Most matches done deterministically, LLM only for edge cases

---

## Documentation

| File | Purpose |
|------|---------|
| `docs/FREE_LLM_INTEGRATION.md` | Complete setup guide (READ THIS!) |
| `config.yaml` | LLM provider configuration |
| `src/services/llm_service.py` | LLM service implementation |
| `app.py` | Updated sidebar with Groq info |

---

## Next: Deploy to Streamlit Cloud

1. Your code is already pushed to GitHub ✅
2. Get Groq API key (2 min)
3. Update Streamlit Cloud Secrets (2 min)
4. Test (1 min)

**Total: 5 minutes to live with free LLM!** 🚀

---

## Troubleshooting

**"GROQ_API_KEY not found"**
- Add to Streamlit Secrets: Settings → Secrets → Add key

**"Failed to initialize Groq client"**
- Check API key is correct (no extra spaces)
- Make sure you created the key in https://console.groq.com

**"No LLM calls happening"**
- Check logs for "LLM verification" messages
- Make sure confidence is between 40-75% (ambiguous range)
- Verify GROQ_API_KEY is in Streamlit Secrets

---

**Ready to deploy? You have everything you need!** 🎉
