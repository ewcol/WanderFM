const bpmSlider = document.getElementById('bpm-slider');
const bpmValue = document.getElementById('bpm-value');
const chunksValue = document.getElementById('chunks-value');
const latInput = document.getElementById('lat-input');
const lonInput = document.getElementById('lon-input');
const updateCityBtn = document.getElementById('update-city-btn');
const playBtn = document.getElementById('play-btn');
const stopBtn = document.getElementById('stop-btn');
const statusBadge = document.getElementById('running-status');
const statusText = statusBadge.querySelector('.status-text');
const promptsBox = document.getElementById('prompts-box');
const syncSpotifyBtn = document.getElementById('sync-spotify-btn');
const spotifyStatus = document.getElementById('spotify-status');

let isRunning = false;
let pollInterval = null;

async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        isRunning = data.running;
        bpmSlider.value = data.bpm;
        bpmValue.textContent = data.bpm;
        chunksValue.textContent = data.chunks_received;
        
        if (data.running) {
            statusBadge.classList.add('running');
            statusText.textContent = 'Live';
            playBtn.classList.add('hidden');
            stopBtn.classList.remove('hidden');
        } else {
            statusBadge.classList.remove('running');
            statusText.textContent = 'Idle';
            playBtn.classList.remove('hidden');
            stopBtn.classList.add('hidden');
        }

        if (data.prompts && data.prompts.length > 0) {
            promptsBox.textContent = data.prompts.map(p => `${p[0]} (${p[1].toFixed(1)})`).join(' • ');
        } else {
            promptsBox.textContent = 'Ready to play...';
        }

        if (data.error) {
            console.error('State error:', data.error);
        }
    } catch (e) {
        console.error('Failed to poll status', e);
    }
}

async function startMusic() {
    await fetch('/api/start', { method: 'POST' });
    updateStatus();
    if (!pollInterval) {
        pollInterval = setInterval(updateStatus, 1000);
    }
}

async function stopMusic() {
    await fetch('/api/stop', { method: 'POST' });
    updateStatus();
}

async function updateBpm(bpm) {
    bpmValue.textContent = bpm;
    await fetch('/api/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bpm: parseInt(bpm) })
    });
}

async function updateCity() {
    const lat = parseFloat(latInput.value);
    const lon = parseFloat(lonInput.value);
    if (isNaN(lat) || isNaN(lon)) {
        alert('Please enter valid latitude and longitude.');
        return;
    }
    updateCityBtn.textContent = '...';
    try {
        const response = await fetch('/api/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat, lon })
        });
        if (!response.ok) throw new Error('Could not fetch weather for coordinates');
        updateCityBtn.textContent = 'Update';
        updateStatus();
    } catch (e) {
        alert('Could not fetch weather for coordinates.');
        updateCityBtn.textContent = 'Update';
    }
}

async function syncSpotify() {
    syncSpotifyBtn.disabled = true;
    syncSpotifyBtn.textContent = '🔄 Syncing...';
    spotifyStatus.textContent = 'Authenticating and analyzing taste...';
    
    try {
        const response = await fetch('/api/spotify/sync', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            if (data.status === 'success') {
                syncSpotifyBtn.textContent = '✅ Synced';
                spotifyStatus.textContent = `Applied styles: ${data.styles.join(', ')}`;
                updateStatus();
            } else if (data.status === 'needs_auth') {
                spotifyStatus.textContent = 'Please authorize in the new window...';
                // Open auth URL in a new window
                const authWindow = window.open(data.auth_url, 'Spotify Auth', 'width=600,height=800');
                
                // Poll for completion
                const checkAuth = setInterval(async () => {
                    const statusRes = await fetch('/api/status');
                    const statusData = await statusRes.json();
                    if (statusData.prompts && statusData.prompts.length > 0) {
                        // Assuming prompts changed means sync finished
                        clearInterval(checkAuth);
                        syncSpotifyBtn.textContent = '✅ Synced';
                        spotifyStatus.textContent = 'Taste synchronized!';
                        if (authWindow) authWindow.close();
                        updateStatus();
                    }
                }, 2000);
            } else {
                throw new Error(data.message);
            }
        } else {
            throw new Error(data.detail || data.message);
        }
    } catch (e) {
        alert('Spotify Sync Failed: ' + e.message);
        syncSpotifyBtn.disabled = false;
        syncSpotifyBtn.textContent = '🎧 Sync Spotify Taste';
        spotifyStatus.textContent = 'Authentication failed or timed out.';
    }
}

bpmSlider.addEventListener('input', (e) => {
    bpmValue.textContent = e.target.value;
});

bpmSlider.addEventListener('change', (e) => {
    updateBpm(e.target.value);
});

playBtn.addEventListener('click', startMusic);
stopBtn.addEventListener('click', stopMusic);
updateCityBtn.addEventListener('click', updateCity);
syncSpotifyBtn.addEventListener('click', syncSpotify);

// Initial poll
updateStatus();
pollInterval = setInterval(updateStatus, 1000);
