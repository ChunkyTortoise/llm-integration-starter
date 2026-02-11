# Streamlit Cloud Deployment Guide

This guide covers deploying the LLM Integration Starter to Streamlit Cloud.

## Prerequisites

- GitHub account
- Repository pushed to GitHub (`ChunkyTortoise/llm-integration-starter`)
- Streamlit Cloud account (free tier available)

## Quick Deploy

[![Deploy to Streamlit Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=ChunkyTortoise/llm-integration-starter&branch=main&fileName=app.py)

## Manual Deployment Steps

### 1. Push to GitHub

Ensure your code is pushed to the GitHub repository:

```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### 2. Create Streamlit Cloud App

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Select:
   - **Repository**: `ChunkyTortoise/llm-integration-starter`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **Custom subdomain**: `ct-llm-starter`
5. Click "Deploy"

## Project Structure for Deployment

```
llm-integration-starter/
├── app.py                # Entry point for Streamlit Cloud
├── requirements.txt      # Python dependencies (includes -e . for local package)
├── pyproject.toml        # Package configuration
├── .streamlit/
│   └── config.toml       # Streamlit configuration
├── llm_starter/          # Core package used by app.py
│   ├── __init__.py
│   ├── completion.py
│   ├── streaming.py
│   ├── function_calling.py
│   ├── rag_pipeline.py
│   ├── mock_llm.py
│   ├── cost_tracker.py
│   └── latency_tracker.py
├── llm_integration_starter/  # Extended modules
│   ├── __init__.py
│   └── ...
└── demo_data/            # Sample documents for RAG demo
    ├── api_reference.txt
    ├── faq.txt
    └── policy.txt
```

## How It Works

1. **Entry Point**: Streamlit Cloud runs `app.py`
2. **Dependencies**: `requirements.txt` installs core deps; `-e .` installs local packages
3. **No API Keys Required**: Uses MockLLM with preset responses for all 5 tabs
4. **Features**: Completion, SSE streaming, function calling, RAG pipeline, cost/latency dashboard
5. **Demo Data**: `demo_data/` provides sample documents for the RAG tab

## Local Development

```bash
# Clone the repository
git clone https://github.com/ChunkyTortoise/llm-integration-starter.git
cd llm-integration-starter

# Install dependencies
pip install -e ".[dev]"

# Run the Streamlit app
streamlit run app.py
```

## Troubleshooting

### App won't start
- Check that `app.py` exists in the root directory
- Verify `requirements.txt` has `-e .` to install local packages
- Check Streamlit Cloud logs for import errors

### Import errors
- Ensure `llm_starter/` directory has `__init__.py`
- The package is installed via `-e .` in requirements.txt

### RAG tab shows no documents
- Verify `demo_data/` directory exists with .txt files
- The directory must be in the repo root (not gitignored)

## Updating the Deployment

Any push to the `main` branch automatically triggers a redeploy on Streamlit Cloud.

```bash
git add .
git commit -m "Update app"
git push origin main
```

## Resources

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-cloud)
- [LLM Integration Starter README](./README.md)
- [Streamlit App URL](https://ct-llm-starter.streamlit.app)
