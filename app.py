import os
import re
import json
import logging
import subprocess
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import yt_dlp

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Regex for URL validation
URL_REGEX = re.compile(r'^https?://(www\.)?(youtube\.com|youtu\.be)/.+$')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/info', methods=['POST'])
def get_info():
    data = request.get_json()
    url = data.get('url')

    if not url or not URL_REGEX.match(url):
        return jsonify({'error': 'Invalid YouTube URL'}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False, # get full info
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Formats processing
            formats = []
            for f in info.get('formats', []):
                # Filter useful formats
                if f.get('protocol') in ['https', 'http', 'm3u8_native']:
                    resolution = f.get('resolution') or 'audio only'
                    filesize = f.get('filesize')
                    filesize_approx = f.get('filesize_approx')
                    size_str = 'N/A'
                    if filesize:
                        size_str = f"{filesize / 1024 / 1024:.2f} MB"
                    elif filesize_approx:
                        size_str = f"~{filesize_approx / 1024 / 1024:.2f} MB"
                    
                    formats.append({
                        'format_id': f['format_id'],
                        'ext': f['ext'],
                        'resolution': resolution,
                        'filesize': size_str,
                        'has_video': f.get('vcodec') != 'none',
                        'has_audio': f.get('acodec') != 'none',
                        'fps': f.get('fps'),
                        'note': f.get('format_note')
                    })
            
            # Sort by resolution (descending)
            def resolution_key(fmt):
                res = fmt['resolution']
                if res == 'audio only': return 0
                try:
                    return int(res.split('x')[0]) if 'x' in res else 0
                except:
                    return 0

            formats.sort(key=resolution_key, reverse=True)

            return jsonify({
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration_string'),
                'formats': formats
            })

    except Exception as e:
        logging.error(f"Error fetching info: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download')
def download():
    url = request.args.get('url')
    format_id = request.args.get('format_id')
    title = request.args.get('title')

    if not url or not URL_REGEX.match(url):
        return "Invalid URL", 400
    
    if not format_id or not re.match(r'^[a-zA-Z0-9_+]+$', format_id):
        return "Invalid Format ID", 400

    safe_title = re.sub(r'[^a-zA-Z0-9-_]', '_', title or 'video')
    filename = f"{safe_title}.mkv"

    # Absolute path to binaries
    current_dir = os.getcwd()
    yt_dlp_path = os.path.join(current_dir, "yt-dlp")
    ffmpeg_path = os.path.join(current_dir, "ffmpeg") # We will download this to root

    # Verify binaries exist
    if not os.path.exists(yt_dlp_path):
        logging.error(f"yt-dlp not found at {yt_dlp_path}")
        return "Server Error: yt-dlp binary missing", 500

    # Ensure ffmpeg is in PATH for yt-dlp to find it
    # OR pass --ffmpeg-location
    
    cmd = [
        yt_dlp_path,
        '--extractor-args', 'youtube:player_client=android', # Bypass bot check
        '-f', f"{format_id}+bestaudio/best", # Merge
        '--merge-output-format', 'mkv',      # Ensure streamable container
        '--ffmpeg-location', ffmpeg_path,    # Explicitly tell yt-dlp where ffmpeg is
        '-o', '-',                           # Stream to stdout
        url
    ]

    def generate():
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        try:
            # Read chunks
            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    break
                yield chunk
            
            process.wait()
            
            # Check for errors after completion
            if process.returncode != 0:
                stderr = process.stderr.read().decode()
                logging.error(f"yt-dlp error: {stderr}")

        except GeneratorExit:
            # Client disconnected
            logging.info("Client disconnected, killing yt-dlp process")
            process.terminate()
            process.wait()
        except Exception as e:
            logging.error(f"Streaming error: {e}")
            process.terminate()

    return Response(
        stream_with_context(generate()),
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'video/x-matroska',
            'X-Accel-Buffering': 'no'
        }
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
