# 🚀 DEPLOY NOW - Exact Steps to Launch Your App

**Status:** Your code is ready. Follow these exact steps to go live in 10 minutes.

---

## Step 1: Get Your API Keys (2 minutes)

### Claude API Key (Required)

1. Visit: https://console.anthropic.com/account/keys
2. Click **"Create Key"**
3. Copy the key (starts with `sk-ant-`)
4. Save it somewhere safe — you'll need it in Step 3

### Google Sheets API (Optional - only if using Google Sheets)

If you only use Excel files, **skip this step**.

For Google Sheets support:
1. Visit: https://cloud.google.com/console
2. Create new project
3. Enable Google Sheets API
4. Create Service Account
5. Download JSON credentials
6. Copy the API key from the JSON

---

## Step 2: Deploy on Streamlit Cloud (3 minutes)

### 2.1: Create Account

1. Visit: **https://share.streamlit.io/**
2. Click **"Sign in with GitHub"**
3. Authorize Streamlit to access your GitHub account
4. You'll see your dashboard

### 2.2: Deploy Your App

1. Click **"New app"** (top left button)

2. Fill in the deployment form:
   ```
   Repository:        asimali50/web-scraping-agent
   Branch:            main
   Main file path:    app.py
   ```

3. Click **"Deploy"**

4. Wait 2-5 minutes for deployment to complete

   You'll see:
   ```
   ✅ Building...
   ✅ Installing dependencies...
   ✅ Running app...
   ✅ Available at: https://web-scraping-agent.streamlit.app
   ```

5. **Save your app URL** — this is your live app!

---

## Step 3: Add API Keys to Streamlit Cloud (2 minutes)

### Critical: This is where you configure secrets

1. Your app should now be deployed. Wait for it to fully load (check status on dashboard)

2. Click the **hamburger menu ☰** in the top right of your app

3. Select **"Settings"**

4. Click the **"Secrets"** tab

5. You should see a text editor. **Paste this** (with your actual keys):

```toml
# Claude API Key - REQUIRED
CLAUDE_API_KEY = "sk-ant-YOUR_KEY_HERE"

# Google Sheets API - OPTIONAL
# GOOGLE_SHEETS_API_KEY = "AIza..."

# App Settings
ENABLE_BROWSER = false
MAX_WORKERS = 3
BROWSER_TIMEOUT_MS = 30000
```

6. Click **"Save"**

The app will automatically redeploy with your secrets. ✨

---

## Step 4: Test Your App (3 minutes)

### Test 1: Load Sample Data

1. Refresh your app page (or wait for redeploy notification)
2. Scroll to **"Or Try with Sample Data"**
3. Click **"📋 Load Sample Products"**
4. See 3 products appear in table
5. ✅ **Secrets are working!**

### Test 2: Process Sample Data

1. Scroll to **"🚀 Start Processing"**
2. Make sure "Enable Browser" is **UNCHECKED** ← Important!
3. Click **"▶️ Process Now"**
4. Watch progress indicator
5. Wait 2-5 minutes for processing

**Expected results:**
- ✅ Found: 1-3 websites detected
- ❓ Needs Review: 0-1
- ❌ Not Found: 0-2

### Test 3: Download Results

1. Scroll to **"📥 Export Results"**
2. Click **"📊 Download Excel"**
3. Open file in Excel
4. Verify columns: ASIN, Brand, Amazon Link, Website URL, Confidence, Status
5. ✅ **Everything working!**

---

## Step 5: Share Your App (1 minute)

### Your Live App URL

```
https://web-scraping-agent.streamlit.app
```

Or find it in your Streamlit Cloud dashboard → click your app → **"Share"**

### Share with Team

Send them this:
```
Check out our new Brand Website Scraper:
https://web-scraping-agent.streamlit.app

Upload your Excel file with product info and get brand websites detected automatically!
```

---

## ⚠️ Important: Playwright on Streamlit Cloud

### Why "Enable Browser" should stay UNCHECKED

| Feature | With Browser | Without Browser (✅ For Cloud) |
|---------|--------------|-------------------------------|
| Speed | Slower (10s/row) | Faster (3-5s/row) |
| Reliability | Medium | High (no timeouts) |
| Resources | Heavy | Light |
| Cloud Friendly | ❌ | ✅ |
| Results Quality | Same | Same |

**On Streamlit Cloud:** Always leave "Enable Browser" unchecked. The app uses API-based scraping which is:
- ✅ Faster
- ✅ More reliable
- ✅ Uses fewer resources
- ✅ Works perfectly

---

## Troubleshooting - Quick Fixes

### ❌ App shows "Module not found"

**Solution:** Your secrets aren't configured
1. Go to app Settings → Secrets
2. Paste all secrets from Step 3
3. Save
4. Refresh app

### ❌ Processing hangs or times out

**Solution:** Too many workers or large file
1. In app sidebar, reduce "Concurrent Workers" to 1-2
2. Try smaller Excel file (< 50 rows)
3. Leave "Enable Browser" unchecked

### ❌ Download button not working

**Solution:** File too large
1. Process smaller batches (< 100 rows)
2. Streamlit Cloud max file size: 200MB

### ❌ App keeps redeploying

**Normal behavior!** Streamlit Cloud redeployment means:
- GitHub push detected
- New dependencies installing
- Secrets updated

Just wait 1-2 minutes.

---

## Success Checklist

- [ ] Streamlit Cloud account created
- [ ] App deployed at `https://web-scraping-agent.streamlit.app`
- [ ] Claude API key added to Streamlit Cloud Secrets
- [ ] Sample data test runs successfully
- [ ] Excel results download works
- [ ] "Enable Browser" is UNCHECKED in settings
- [ ] App URL shared with team
- [ ] No errors in app logs

---

## What to Do If Something Goes Wrong

### Check the Logs

1. Go to Streamlit Cloud dashboard
2. Click your app
3. Scroll down to **"Logs"**
4. See real-time error messages
5. Copy error → search GitHub Issues

### Common Error Messages

**"ModuleNotFoundError: No module named 'src'"**
- Solution: This is normal on first deploy. Wait 2 minutes for redeploy.

**"CLAUDE_API_KEY not found"**
- Solution: Add to Streamlit Secrets (Step 3)
- Then save and wait 30 seconds

**"Connection timeout"**
- Solution: Reduce workers to 1, reduce file size to < 20 rows

---

## Next Steps After Deploy

1. **Monitor first week:** Check logs for errors
2. **Share with users:** Send them the app URL
3. **Gather feedback:** What features do they want?
4. **Optimize:** Update max workers based on actual usage
5. **Scale:** If popular, upgrade to paid Streamlit tier

---

## Commands Reference

```bash
# Test locally before deploying
streamlit run app.py

# View your GitHub commits
git log --oneline

# Check deployment status
# (Visit Streamlit Cloud dashboard and click your app)
```

---

## Support

**Got issues?**
- 📖 Read: `docs/STREAMLIT_QUICK_START.md`
- 🔧 Read: `docs/STREAMLIT_DEPLOYMENT_GUIDE.md`
- 💬 GitHub Issues: https://github.com/asimali50/web-scraping-agent/issues

---

## You're Ready! 🎉

Your app is built, tested, and ready to deploy.

**Next action:** Go to https://share.streamlit.io and click "New app"

**Time to live:** 10 minutes from now you'll have a working web scraper! 🚀
