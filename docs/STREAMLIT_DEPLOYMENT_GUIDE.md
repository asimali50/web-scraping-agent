# Streamlit Cloud Deployment Guide

## Step-by-Step Deployment Instructions

### Prerequisites
- GitHub account (repository already set up)
- Streamlit Cloud account (free: https://streamlit.io/cloud)
- All files committed and pushed to GitHub

### Step 1: Prepare Repository for Streamlit Cloud

The repository structure should look like:
```
web-scraping-agent/
├── app.py                          # Main Streamlit app
├── requirements-streamlit.txt      # Dependencies
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
├── src/                            # Source code
├── docs/                           # Documentation
└── config.yaml                     # App configuration
```

### Step 2: Create Streamlit Configuration File

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[client]
showErrorDetails = true
toolbarMode = "viewer"

[server]
port = 8501
headless = true
runOnSave = true
maxUploadSize = 200

[logger]
level = "info"

[client.toolbarMode]
value = "viewer"
```

### Step 3: Set Up Environment Variables

Create `.streamlit/secrets.toml` locally (NOT committed to GitHub):

```toml
# Required API Keys
CLAUDE_API_KEY = "your-claude-api-key"
GOOGLE_SHEETS_API_KEY = "your-google-sheets-api-key"

# Optional settings
BROWSER_TIMEOUT_MS = 30000
MAX_WORKERS = 3
ENABLE_BROWSER = true
```

**IMPORTANT:** This file should be in `.gitignore` and never committed.

### Step 4: Update .gitignore

Add to `.gitignore`:

```
.streamlit/secrets.toml
.streamlit/sessions/
*.db
__pycache__/
.env
.env.local
```

### Step 5: Commit All Changes

```bash
git add app.py requirements-streamlit.txt .streamlit/config.toml
git commit -m "Add Streamlit Cloud deployment files

- Create Streamlit web app (app.py) for Excel upload and processing
- Add Streamlit configuration (.streamlit/config.toml)
- Add requirements-streamlit.txt with all dependencies
- Ready for Streamlit Cloud deployment"
git push origin main
```

### Step 6: Deploy on Streamlit Cloud

1. **Visit Streamlit Cloud**: https://share.streamlit.io/

2. **Sign in with GitHub** (or create account)

3. **Click "New app"**

4. **Fill in deployment details**:
   - **Repository**: `asimali50/web-scraping-agent`
   - **Branch**: `main`
   - **Main file path**: `app.py`

5. **Click "Deploy"**

Streamlit Cloud will:
- Clone your repository
- Install dependencies from `requirements-streamlit.txt`
- Start the app
- Provide you with a unique URL (e.g., `https://web-scraping-agent.streamlit.app`)

### Step 7: Configure Secrets in Streamlit Cloud

1. Go to your app dashboard
2. Click the **hamburger menu** (☰) → **Settings**
3. Scroll to **Secrets**
4. Paste your secrets (from `.streamlit/secrets.toml`):

```
CLAUDE_API_KEY = "your-key-here"
GOOGLE_SHEETS_API_KEY = "your-key-here"
```

5. **Save**

The app will automatically redeploy with the secrets.

### Step 8: Monitor & Manage

- **Logs**: Streamlit Cloud shows real-time logs
- **Redeploy**: Push changes to `main` branch → auto-redeploys
- **Performance**: Monitor usage in the app dashboard

---

## Troubleshooting

### Issue: "Module not found" errors

**Solution**: Ensure all dependencies are in `requirements-streamlit.txt`:
```bash
pip freeze > requirements-streamlit.txt
```

### Issue: Playwright browser not available

**Solution**: Streamlit Cloud has limited browser support. For this app:
- Keep `enable_browser` option in sidebar
- App gracefully degrades without browser
- Consider using headless mode or API-based alternatives

### Issue: Timeout errors during processing

**Solution**: Adjust in `config.yaml`:
```yaml
browser:
  timeout_ms: 60000  # Increase timeout

scraping:
  amazon:
    timeout_seconds: 15
  google:
    timeout_seconds: 20
```

### Issue: Memory issues with large files

**Solution**:
- Limit concurrent workers in sidebar
- Process smaller batches
- Increase Streamlit Cloud resources (paid tier)

---

## Deployment Checklist

- [ ] All code committed to `main` branch
- [ ] `app.py` created and working locally
- [ ] `requirements-streamlit.txt` contains all dependencies
- [ ] `.streamlit/config.toml` created
- [ ] `.streamlit/secrets.toml` added to `.gitignore`
- [ ] GitHub repository is public
- [ ] Streamlit Cloud account created
- [ ] App deployed on Streamlit Cloud
- [ ] Secrets configured in Streamlit Cloud dashboard
- [ ] App tested with sample data
- [ ] URL shared with users

---

## Usage Instructions for End Users

### Accessing Your App

1. Visit: **[Your Streamlit Cloud URL]**

2. **Upload Excel File**:
   - Click "Choose an Excel file"
   - Select your product file with columns: ASIN, Brand, Amazon Link
   - Or use sample data to test

3. **Configure Settings** (optional):
   - Adjust concurrent workers (1-10)
   - Enable/disable browser automation
   - Choose report generation

4. **Process**: Click "▶️ Process Now"

5. **Download Results**:
   - Excel file with brand website URLs
   - CSV export
   - Execution logs

### Expected Output

For each product:
- ✅ **Found**: Brand website detected and verified
- ❓ **Needs Review**: Multiple potential matches
- ❌ **Not Found**: No suitable website found
- ⚠️ **Error**: Processing failed

---

## Advanced Configuration

### Custom Domain

1. In Streamlit Cloud dashboard
2. **Settings** → **Custom domain**
3. Add your domain (requires CNAME record)

### Scale Up (Premium Features)

- **Tier**: Streamlit Cloud offers paid tiers
- **Resources**: Increase CPU, memory, and workers
- **Support**: Priority support included

### Local Development

```bash
# Test app locally before deploying
streamlit run app.py

# With custom config
streamlit run app.py --config.toml .streamlit/config.toml
```

---

## Security Best Practices

✅ **DO:**
- Store API keys in Streamlit Cloud secrets
- Use environment variables for sensitive data
- Keep dependencies updated
- Enable HTTPS (automatic on Streamlit Cloud)

❌ **DON'T:**
- Commit `.streamlit/secrets.toml`
- Hardcode API keys in code
- Use deprecated dependencies
- Log sensitive information

---

## Support & Resources

- **Streamlit Docs**: https://docs.streamlit.io/
- **Deployment Guide**: https://docs.streamlit.io/streamlit-cloud/get-started
- **GitHub Issues**: https://github.com/asimali50/web-scraping-agent/issues
- **Community Forum**: https://discuss.streamlit.io/

---

## Next Steps

After deployment:
1. Share the app URL with stakeholders
2. Gather feedback
3. Monitor logs for issues
4. Scale resources if needed
5. Add additional features based on usage
