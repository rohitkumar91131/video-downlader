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
- **"Sign in to confirm you're not a bot"**: YouTube bot-detection is blocking the request.
  Fix by providing one of the following (in order of reliability):

  1. **Cookies file** – Export your YouTube cookies from a logged-in browser session using the
     [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
     extension (Netscape format). Then:
     - **Render.com**: Upload as a Secret File (`Dashboard → Environment → Secret Files`) and
       set `YOUTUBE_COOKIES_FILE` to its mount path (e.g. `/etc/secrets/cookies.txt`).
     - **Local**: Set the environment variable before starting: `export YOUTUBE_COOKIES_FILE=/path/to/cookies.txt`

  2. **Proof of Origin (PO) token** – Obtain a `visitor_data` + `po_token` pair following the
     [yt-dlp Extractors guide](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#youtube).
     Then set the environment variables:
     ```
     YOUTUBE_PO_TOKEN=web+<your_token>
     YOUTUBE_VISITOR_DATA=<your_visitor_data>
     ```
     On Render.com, add these under `Dashboard → Environment → Environment Variables`.
