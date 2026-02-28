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
const genrePills = document.getElementById('genre-pills');
const genreCustom = document.getElementById('genre-custom');
const experiencePills = document.getElementById('experience-pills');
const experienceCustom = document.getElementById('experience-custom');

let isRunning = false;
let pollInterval = null;
let selectedGenre = '';
let selectedExperience = '';

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
    // Ensure genre/experience are applied before starting playback
    if (selectedGenre || selectedExperience) {
        await sendPreferences();
    }
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

let prefDebounce = null;
function debouncedSendPreferences() {
    clearTimeout(prefDebounce);
    prefDebounce = setTimeout(sendPreferences, 400);
}

function setupPillRow(container, customInput, getSetter, setSetter) {
    container.addEventListener('click', (e) => {
        const pill = e.target.closest('.pill');
        if (!pill) return;
        const wasActive = pill.classList.contains('active');
        container.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
        if (wasActive) {
            setSetter('');
        } else {
            pill.classList.add('active');
            setSetter(pill.dataset.value);
            customInput.value = '';
        }
        sendPreferences();
    });
    customInput.addEventListener('input', () => {
        container.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
        setSetter(customInput.value);
        debouncedSendPreferences();
    });
}

setupPillRow(genrePills, genreCustom, () => selectedGenre, v => { selectedGenre = v; });
setupPillRow(experiencePills, experienceCustom, () => selectedExperience, v => { selectedExperience = v; });

async function sendPreferences() {
    await fetch('/api/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ genre: selectedGenre, experience: selectedExperience })
    });
    updateStatus();
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
            body: JSON.stringify({ lat, lon, genre: selectedGenre, experience: selectedExperience })
        });
        if (!response.ok) throw new Error('Could not fetch weather for coordinates');
        updateCityBtn.textContent = 'Update';
        updateStatus();
    } catch (e) {
        alert('Could not fetch weather for coordinates.');
        updateCityBtn.textContent = 'Update';
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

// Initial poll
updateStatus();
pollInterval = setInterval(updateStatus, 1000);
