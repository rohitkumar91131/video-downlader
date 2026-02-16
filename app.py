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

    # Step 1: Get Stream URLs using yt-dlp
    try:
        # Get direct URLs for video and audio
        # We ask for the specific format + best audio
        get_url_cmd = [
            'yt-dlp',
            '-f', f"{format_id}+bestaudio/best",
            '--get-url',
            url
        ]
        
        urls_output = subprocess.check_output(get_url_cmd).decode('utf-8').strip().split('\n')
        
        if not urls_output:
            return "Failed to extract stream URLs", 500

        video_url = urls_output[0]
        audio_url = urls_output[1] if len(urls_output) > 1 else None

        # Step 2: Construct FFmpeg command to stream and merge
        # -i video_url -i audio_url (if exists) -c copy -f matroska -
        ffmpeg_cmd = ['./ffmpeg']
        
        # Add User-Agent to avoid 403 Forbidden from YouTube
        # (Naive approach, usually works for signed URLs temporarily)
        ffmpeg_cmd.extend(['-headers', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36\r\n'])
        ffmpeg_cmd.extend(['-i', video_url])
        
        if audio_url:
            ffmpeg_cmd.extend(['-headers', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36\r\n'])
            ffmpeg_cmd.extend(['-i', audio_url])
            # Map video and audio streams
            ffmpeg_cmd.extend(['-map', '0:v', '-map', '1:a'])
            # Copy codecs (no re-encoding) for speed and quality
            ffmpeg_cmd.extend(['-c:v', 'copy', '-c:a', 'aac']) # Convert audio to aac if needed for mkv compatibility or just copy? 
            # MKV supports almost anything. '-c copy' is safest/fastest.
            # But sometimes audio codec in separate stream might overlap?
            # Safest is -c copy.
            ffmpeg_cmd.extend(['-c', 'copy'])
        else:
            ffmpeg_cmd.extend(['-c', 'copy'])

        # Output to stdout in matroska format
        ffmpeg_cmd.extend(['-f', 'matroska', '-'])
        # Add moving flags for robustness? Not needed for MKV stream.

    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting URLs: {e}")
        return "Failed to resolve stream", 500

    def generate():
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE # Capture stderr to avoid polluting stream, log if needed
        )
        
        try:
            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    break
                yield chunk
            process.wait()
        except GeneratorExit:
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
