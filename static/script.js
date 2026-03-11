const fetchBtn = document.getElementById('fetchBtn');
const btnText = document.getElementById('btnText');
const spinner = document.getElementById('spinner');
const urlInput = document.getElementById('urlInput');
const errorMsg = document.getElementById('error-msg');
const videoInfo = document.getElementById('video-info');
const formatsTableBody = document.querySelector('#formats-table tbody');

fetchBtn.addEventListener('click', fetchVideoInfo);

function setLoading(isLoading) {
    if (isLoading) {
        spinner.style.display = 'block';
        btnText.style.display = 'none';
        fetchBtn.disabled = true;
        errorMsg.classList.add('hidden');
        videoInfo.classList.add('hidden');
    } else {
        spinner.style.display = 'none';
        btnText.style.display = 'block';
        fetchBtn.disabled = false;
    }
}

function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

async function fetchVideoInfo() {
    const url = urlInput.value.trim();
    if (!url || !isValidUrl(url)) {
        showError('Please enter a valid YouTube URL.');
        return;
    }

    setLoading(true);

    try {
        const response = await fetch('/info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch video info');
        }

        renderVideoInfo(data);
    } catch (err) {
        showError(err.message);
    } finally {
        setLoading(false);
    }
}

function renderVideoInfo(data) {
    document.getElementById('thumb').src = data.thumbnail;
    document.getElementById('video-title').textContent = data.title;
    document.getElementById('video-duration').textContent = `Duration: ${data.duration}`;

    formatsTableBody.innerHTML = '';

    data.formats.forEach(fmt => {
        const row = document.createElement('tr');

        let details = [];
        if (fmt.has_video) details.push('Video');
        if (fmt.has_audio) details.push('Audio');
        if (!fmt.has_audio && fmt.has_video) details.push('Muted');

        row.innerHTML = `
            <td>${fmt.resolution}</td>
            <td>${fmt.ext}</td>
            <td>${fmt.filesize}</td>
            <td>${details.join(' + ')}</td>
            <td>
                <button class="download-btn" onclick="downloadVideo('${data.title.replace(/'/g, "\\'")}', '${fmt.format_id}')">
                    ⬇ FFmpeg
                </button>
            </td>
            <td>
                <button class="download-btn direct-btn" onclick="directDownload('${fmt.format_id}', this)">
                    ⚡ Direct
                </button>
            </td>
        `;
        formatsTableBody.appendChild(row);
    });

    videoInfo.classList.remove('hidden');
}

function downloadVideo(title, formatId) {
    const url = urlInput.value.trim();
    if (!url) return;

    const downloadUrl = `/download?url=${encodeURIComponent(url)}&format_id=${encodeURIComponent(formatId)}&title=${encodeURIComponent(title)}`;
    window.location.href = downloadUrl;
}

async function directDownload(formatId, btn) {
    const url = urlInput.value.trim();
    if (!url) return;

    const originalText = btn.textContent;
    btn.textContent = '…';
    btn.disabled = true;

    try {
        const response = await fetch(`/get-url?url=${encodeURIComponent(url)}&format_id=${encodeURIComponent(formatId)}`);
        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || 'Failed to get direct URL');
        }

        window.open(data.url, '_blank');
    } catch (err) {
        showError('Direct download failed: ' + err.message);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.classList.remove('hidden');
}

urlInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        fetchVideoInfo();
    }
});
