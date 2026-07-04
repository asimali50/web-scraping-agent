# Streamlit Cloud Deployment - Complete Step-by-Step Guide

**Status:** Ready to deploy  
**Target:** https://streamlit.io/cloud  
**Repository:** https://github.com/asimali50/web-scraping-agent

---

## Quick Start (5 Minutes)

### Phase 1: Pre-Deployment Verification ✅

Before deploying, verify your local setup works:

```bash
# Test the Streamlit app locally
streamlit run app.py

# Test with sample data - should show results
```

If it runs locally without errors, proceed to deployment.

---

## Phase 2: Streamlit Cloud Dashboard Setup

### Step 1: Create Streamlit Cloud Account

1. Visit https://share.streamlit.io/
2. Click **"Sign in with GitHub"**
3. Authorize Streamlit to access your GitHub repositories
4. You'll be redirected to your dashboard

### Step 2: Deploy New App

1. Click **"New app"** button (top left)
2. Fill in the deployment form:

   | Field | Value |
   |-------|-------|
   | **Repository** | `asimali50/web-scraping-agent` |
   | **Branch** | `main` |
   | **Main file path** | `app.py` |

3. Click **"Deploy"**

**Expected behavior:**
- Streamlit Cloud clones your repo
- Installs dependencies from `requirements-streamlit.txt`
- Builds the app (takes 2-5 minutes on first deploy)
- Provides a public URL (e.g., `https://web-scraping-agent.streamlit.app`)

---

## Phase 3: Configure Secrets

### Critical: Add API Keys to Streamlit Cloud

⚠️ **NEVER hardcode secrets in code. Always use Streamlit Secrets.**

1. **Wait for app to deploy** (status shows "Deployed")

2. **Access app settings:**
   - Click the **hamburger menu** (☰) in top right
   - Select **Settings**

3. **Navigate to Secrets:**
   - Click **"Secrets"** tab
   - You'll see a text editor with TOML format

4. **Paste your secrets** (replace with your actual keys):

```toml
# Claude API - REQUIRED for scraping
CLAUDE_API_KEY = "sk-ant-..."  # Get from https://console.anthropic.com

# Google Sheets API - OPTIONAL (only if using Google Sheets feature)
GOOGLE_SHEETS_API_KEY = "AIza..."  # Get from Google Cloud Console

# App Settings - OPTIONAL
BROWSER_TIMEOUT_MS = 30000
MAX_WORKERS = 3
ENABLE_BROWSER = false  # Keep false for Streamlit Cloud
```

5. **Click "Save"**

The app will **automatically redeploy** with the secrets. ✨

---

## Phase 4: Handle Playwright on Streamlit Cloud

### The Challenge
Playwright (browser automation) requires significant resources and browser binaries. Streamlit Cloud has limited resources, so we use a **degraded mode** approach.

### Solution: Disable Browser for Streamlit Cloud

Our app already has a graceful fallback! In the sidebar, you'll see:

```
⚙️ Configuration
├─ Concurrent Workers: 3
├─ ☐ Enable Browser (Playwright)  ← UNCHECK THIS
├─ ☐ Generate Reports
```

**For Streamlit Cloud deployment:**
- Leave "Enable Browser" **UNCHECKED**
- The app will use API-based scraping instead
- Processing is faster and more reliable
- All features work identically

### Why This Works

Our scraping pipeline has two modes:

| Mode | Browser | Speed | Resources | Best For |
|------|---------|-------|-----------|----------|
| **With Browser** | Playwright | Slower | High | Local/Desktop |
| **API-Based** | None | Faster | Low | Streamlit Cloud ✅ |

Both modes use:
- Google Search APIs
- Amazon product data
- Claude AI for matching
- Brand website verification

---

## Phase 5: Testing the Deployed App

### Test 1: Verify Secrets Loaded

1. Open your Streamlit Cloud app URL
2. Look at the page title and layout
3. If it loads without errors → **Secrets are working ✅**

### Test 2: Load Sample Data

1. Scroll to **"Or Try with Sample Data"**
2. Click **"📋 Load Sample Products"**
3. Verify 3 products appear in the table

### Test 3: Process Sample Data

1. Click **"▶️ Process Now"**
2. Watch the progress indicator
3. Processing should complete in 2-5 minutes

**Expected results:**
- ✅ Found: 1-3 results
- ❓ Needs Review: 0-1 results
- ❌ Not Found: 0-2 results

### Test 4: Export Results

1. Scroll to **"📥 Export Results"**
2. Click **"📊 Download Excel"**
3. Open file and verify brand URLs are populated

If all tests pass → **Deployment successful! 🎉**

---

## Phase 6: Production Configuration

### Update for Production Use

In `.streamlit/config.toml`, Streamlit Cloud will use these settings:

```toml
[theme]
primaryColor = "#1f77b4"      # App blue
backgroundColor = "#ffffff"   # Clean white
font = "sans serif"           # Professional

[client]
showErrorDetails = true       # Show errors to help debug
toolbarMode = "viewer"        # Hide code editor from users

[server]
maxUploadSize = 200           # Max 200MB file upload
```

### Optional: Custom Domain

In Streamlit Cloud dashboard:
1. Settings → **Custom domain**
2. Add your domain (e.g., `scraper.yourdomain.com`)
3. Add CNAME record to your DNS

---

## Phase 7: Share with Users

### Your Live App URL

Share this with team members:

```
https://web-scraping-agent.streamlit.app
```

Or with custom domain:

```
https://scraper.yourdomain.com
```

### User Instructions

Create a simple guide for end users:

**How to Use:**
1. Download your Excel file with products (columns: ASIN, Brand, Amazon Link)
2. Visit the app link
3. Upload your file
4. Click "▶️ Process Now"
5. Download results Excel file when complete

---

## Common Issues & Solutions

### ❌ Issue: "Module not found" Error

**Cause:** Missing dependency in `requirements-streamlit.txt`

**Solution:**
```bash
# Add missing package locally
pip install <package-name>

# Update requirements
pip freeze > requirements-streamlit.txt

# Commit and push
git add requirements-streamlit.txt
git commit -m "Add missing dependency"
git push origin main
```

Streamlit Cloud will auto-redeploy with new dependencies.

---

### ❌ Issue: "CLAUDE_API_KEY not found"

**Cause:** Secrets not configured in Streamlit Cloud dashboard

**Solution:**
1. Go to app Settings → Secrets
2. Paste your API key: `CLAUDE_API_KEY = "sk-ant-..."`
3. Save
4. Wait 30 seconds for redeploy
5. Refresh the app

---

### ❌ Issue: "Playwright failed to install"

**Cause:** Browser binaries can't be installed on Streamlit Cloud

**Solution:**
- **This is expected and fine!**
- The app automatically falls back to API-based mode
- Leave "Enable Browser" unchecked
- All features work identically

---

### ❌ Issue: Upload button not working

**Cause:** File size exceeds 200MB limit

**Solution:**
- Split large files into smaller batches
- Default Streamlit Cloud limit is 200MB
- Configure in `.streamlit/config.toml`: `maxUploadSize = 200`

---

### ❌ Issue: Processing timeout after 10 minutes

**Cause:** Streamlit Cloud has execution time limits

**Solution:**
- Reduce worker count to 1-2 (in sidebar)
- Process smaller batches (< 100 rows)
- Use premium Streamlit tier for longer executions

---

## Advanced Configuration

### Increase Resources (Premium)

For production scale:

1. Visit Streamlit Cloud dashboard
2. Click your app
3. Settings → **Upgrade**
4. Choose tier:
   - **Starter** (free): 1 shared runner, 1 app
   - **Pro** ($/month): Multiple runners, priority support
   - **Enterprise**: Dedicated resources

### Auto-Reload on GitHub Push

By default, Streamlit Cloud automatically redeploys when you push to GitHub:

```bash
# Make changes locally
git add .
git commit -m "Fix bug in scraping"
git push origin main

# Your Streamlit Cloud app redeploys automatically within 2-3 minutes
```

### View Logs

1. Click your app in Streamlit Cloud dashboard
2. Scroll down to **"Logs"**
3. View real-time execution logs

---

## Security Best Practices

### ✅ DO:
- Store API keys only in Streamlit Cloud **Secrets**
- Use environment variables for sensitive data
- Keep dependencies updated (`pip freeze`)
- Enable HTTPS (automatic on Streamlit Cloud)
- Use GitHub 2FA for repository access

### ❌ DON'T:
- Hardcode API keys in `app.py`, `config.yaml`, or `requirements.txt`
- Commit `.streamlit/secrets.toml` (it's in `.gitignore` for this reason)
- Log sensitive information
- Use deprecated Python versions (< 3.8)

---

## Deployment Checklist

Before considering deployment complete, verify:

- [ ] GitHub account connected to Streamlit Cloud
- [ ] Repository is public (or granted access)
- [ ] App deployed on Streamlit Cloud
- [ ] API keys added to Streamlit Cloud Secrets
- [ ] App accessible via public URL
- [ ] Sample data test runs successfully
- [ ] Excel export works
- [ ] Settings sidebar functions properly
- [ ] No errors in app logs
- [ ] URL shared with team

---

## Next Steps

1. **Share the app URL** with your team
2. **Monitor logs** for errors in first week
3. **Collect feedback** on features and UX
4. **Scale if needed** with paid tier
5. **Add more features** based on usage patterns

---

## Support & Resources

- **Streamlit Docs:** https://docs.streamlit.io/
- **Streamlit Cloud Docs:** https://docs.streamlit.io/streamlit-cloud/get-started
- **Troubleshooting:** https://docs.streamlit.io/streamlit-cloud/troubleshooting
- **Community:** https://discuss.streamlit.io/
- **Project Issues:** https://github.com/asimali50/web-scraping-agent/issues

---

## Quick Command Reference

```bash
# Test app locally
streamlit run app.py

# Update dependencies
pip freeze > requirements-streamlit.txt

# Commit and push (triggers auto-redeploy)
git add .
git commit -m "Your message"
git push origin main

# View git log
git log --oneline

# Check GitHub status
git status
```

---

**You're all set! Deploy now and enjoy your live web app! 🚀**
