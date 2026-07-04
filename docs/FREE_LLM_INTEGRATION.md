# Free LLM Integration - Groq Setup Guide

**Status:** Updated from Claude (paid) to Groq (free tier)  
**Date:** 2026-07-04  
**Cost:** $0 (free tier)

---

## Quick Overview

Your web scraper now supports **three LLM providers**:

| Provider | Cost | Speed | Model | Setup |
|----------|------|-------|-------|-------|
| **Groq** ⭐ | Free | Very Fast | Mixtral, Llama 3 | 2 min |
| **Google Gemini** | Free | Fast | Gemini Pro | 3 min |
| **Claude** | Paid | Good | Claude 3 | Requires subscription |

**Recommended for testing:** Groq (free tier, unlimited requests, fastest)

---

## Step 1: Get Your Groq API Key (2 minutes)

### Sign Up
1. Visit: **https://console.groq.com**
2. Click "Sign up" (or sign in if you have an account)
3. Create account with email or GitHub

### Get API Key
1. After signup, go to **API Keys** section
2. Click **"Create API Key"**
3. Copy the key (looks like `gsk_...`)
4. Save it somewhere safe

**Note:** Groq free tier includes:
- ✅ Unlimited API requests
- ✅ No credit card required
- ✅ Very fast inference (perfect for testing)

---

## Step 2: Set Up Environment Variable Locally

### Add to .env file (local testing only)

Create or edit `.env` in your project root:

```
# Groq API (Free tier - recommended for testing)
GROQ_API_KEY=gsk_YOUR_KEY_HERE

# Alternative: Google Gemini
# GEMINI_API_KEY=AIza...

# Alternative: Claude (if using paid tier)
# CLAUDE_API_KEY=sk-ant-...
```

**Important:** `.env` is in `.gitignore` — never commit it

### Load the .env file
The app automatically loads `.env` via `python-dotenv`

---

## Step 3: Configure LLM Provider

### Option A: Use Groq (Recommended)

In `config.yaml`, the LLM section is already configured for Groq:

```yaml
llm:
  provider: "groq"  # Use Groq (free)
  model: "mixtral-8x7b-32768"  # Fast, high quality
  max_tokens: 500
  use_only_when: "ambiguous"  # Only use LLM when confidence is unclear
```

No changes needed — it's already set!

### Option B: Switch to Google Gemini

Edit `config.yaml`:

```yaml
llm:
  provider: "gemini"
  model: "gemini-pro"  # or "gemini-1.5-pro"
  max_tokens: 500
  use_only_when: "ambiguous"
```

Get API key from: https://ai.google.dev/

### Option C: Use Claude (Paid)

Edit `config.yaml`:

```yaml
llm:
  provider: "claude"
  model: "claude-opus-4-7"
  max_tokens: 500
  use_only_when: "ambiguous"
```

Requires Claude API subscription.

---

## Step 4: Streamlit Cloud Setup

### Add Secret to Streamlit Cloud Dashboard

1. Deploy your app to Streamlit Cloud (if not already done)
2. Click the **☰ hamburger menu** (top right)
3. Select **"Settings"**
4. Click **"Secrets"** tab
5. Add your API key:

```toml
# For Groq (recommended)
GROQ_API_KEY = "gsk_YOUR_KEY_HERE"

# Or for Gemini
# GEMINI_API_KEY = "AIza..."

# Or for Claude
# CLAUDE_API_KEY = "sk-ant-..."
```

6. Click **"Save"**

The app will automatically redeploy with the secret. ✨

---

## Step 5: Test It Works

### Test Locally

```bash
# Start the app
streamlit run app.py

# Upload a file or load sample data
# Process a few products
# Check logs for LLM queries
```

**Expected logs:**
```
INFO: LLM Service initialized with provider: groq, model: mixtral-8x7b-32768
INFO: Groq client initialized successfully
INFO: LLM verification for BrandName: {'verified': true, 'reason': '...'}
```

### Test on Streamlit Cloud

1. Visit your deployed app
2. Load sample data
3. Process products
4. Check app logs for LLM messages

If no errors, Groq is working! ✅

---

## How LLM Integration Works

### When Is LLM Used?

The app uses a **two-stage matching process**:

1. **Stage 1: Deterministic Matching** (always runs)
   - Brand name matching
   - Domain legitimacy
   - Logo detection
   - Product category overlap
   - Generates confidence score (0-100%)

2. **Stage 2: LLM Verification** (if ambiguous)
   - If confidence is between 40-75% (ambiguous)
   - Calls Groq/Gemini/Claude for verification
   - LLM analyzes brand + website content
   - Boosts confidence if match is verified

**Why two stages?**
- ✅ Fast: Most matches done deterministically
- ✅ Cheap: LLM only called for ambiguous cases
- ✅ Accurate: LLM handles edge cases

### Cost Estimate

**For 1000 products:**
- ~80% deterministic matches: 0 LLM calls
- ~20% ambiguous: 200 LLM calls
- **Groq cost:** $0 (free tier)
- **Claude cost:** ~$0.30-0.50 (paid)

---

## Model Options

### Groq Models (Recommended)

```yaml
# Fastest, great for real-time
model: "mixtral-8x7b-32768"

# Most accurate, slightly slower
model: "llama3-70b-8192"

# Balanced, good quality
model: "llama2-70b-4096"
```

### Google Gemini Models

```yaml
model: "gemini-pro"        # Fast, good quality
model: "gemini-1.5-pro"    # More capable, slower
```

### Claude Models

```yaml
model: "claude-opus-4-7"   # Most capable, slowest
model: "claude-3-sonnet"   # Balanced
```

---

## Troubleshooting

### Issue: "GROQ_API_KEY not found"

**Solution:**
1. Check `.env` file has `GROQ_API_KEY = "gsk_..."`
2. For Streamlit Cloud: Settings → Secrets → Add key
3. Restart app or refresh page

### Issue: "Failed to initialize Groq client"

**Solution:**
1. Install groq: `pip install groq`
2. Check API key is correct (no extra spaces)
3. Check internet connection

### Issue: LLM calls are slow

**Solution:**
1. Use Groq instead of other providers (fastest)
2. Reduce `max_tokens` in `config.yaml`
3. Reduce concurrent workers to avoid rate limits

### Issue: "Rate limit exceeded"

**Solution:**
1. Groq free tier: Very generous (unlikely to hit)
2. Reduce concurrent workers (in sidebar)
3. Wait a few minutes and retry

---

## Switching Providers

### From Claude to Groq

**File: `config.yaml`**
```yaml
# Change from:
llm:
  provider: "claude"

# To:
llm:
  provider: "groq"
```

**File: `.env` (local)**
```bash
# Remove:
CLAUDE_API_KEY=...

# Add:
GROQ_API_KEY=gsk_...
```

**File: Streamlit Cloud Secrets**
- Remove: `CLAUDE_API_KEY`
- Add: `GROQ_API_KEY = "gsk_..."`

---

## Performance Comparison

### Matching Speed (per 10 products)

| Provider | Speed | Cost | Quality |
|----------|-------|------|---------|
| Groq | 20-30s | $0 | Excellent |
| Gemini | 25-35s | $0 | Good |
| Claude | 40-50s | $0.05-0.10 | Excellent |

*(Assuming 5 ambiguous products requiring LLM)*

---

## Free Tier Limits

### Groq
- ✅ Unlimited requests
- ✅ No rate limiting
- ✅ No credit card required
- **Limit:** Free tier may have monthly quotas (generous)

### Google Gemini
- ✅ 60 requests per minute
- ✅ 1500 requests per day
- ✅ No credit card required
- **Limit:** Day quota

### Claude
- ❌ Requires paid subscription
- ✅ No limits for paid users

---

## Next Steps

1. **Get Groq API key:** https://console.groq.com
2. **Add to .env locally** for testing
3. **Test app locally:** `streamlit run app.py`
4. **Deploy to Streamlit Cloud** with updated dependencies
5. **Add secret to Streamlit dashboard:** Settings → Secrets
6. **Test in production**

---

## Support

**Questions about Groq?**
- Docs: https://console.groq.com/docs
- Status: https://status.groq.com/

**Questions about your app?**
- Check `docs/` folder for full guides
- GitHub Issues: Report bugs

---

**You're all set! Your app now uses free LLM APIs. Deploy and enjoy!** 🚀
