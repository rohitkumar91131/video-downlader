# YouTube Video Downloader (Python Edition)

A production-ready YouTube video downloader using Python (Flask) and yt-dlp.

## Features
- **All Formats**: 144p to 4K, MP3, etc.
- **Streaming**: Downloads convert/stream directly to client.
- **Security**: Strict URL validation.
- **Deployment**: Ready for Render.com.

## Prerequisites
- Python 3.8+
- pip

## Local Setup

1. **Create Virtual Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Server**
   ```bash
   python app.py
   ```
   Server runs on `http://localhost:3000`.

## Deployment (Render)

1. Push this repo to GitHub/GitLab.
2. Create a new **Web Service** on Render.
3. Connect your repo.
4. Render will automatically detect `render.yaml` (Python environment).

## Troubleshooting
- **Error: "Module not found"**: Ensure you activated the virtual environment before running.
- **Private Videos**: Not supported in this version.
