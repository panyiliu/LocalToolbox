(function () {
    const CITIES = [
        { city: 'Los Angeles', country: 'USA', tz: 'America/Los_Angeles', lat: 34.0522, lon: -118.2437 },
        { city: 'New York', country: 'USA', tz: 'America/New_York', lat: 40.7128, lon: -74.0060 },
        { city: 'São Paulo', country: 'Brazil', tz: 'America/Sao_Paulo', lat: -23.5505, lon: -46.6333 },
        { city: 'London', country: 'UK', tz: 'Europe/London', lat: 51.5074, lon: -0.1278 },
        { city: 'Paris', country: 'France', tz: 'Europe/Paris', lat: 48.8566, lon: 2.3522 },
        { city: 'Berlin', country: 'Germany', tz: 'Europe/Berlin', lat: 52.5200, lon: 13.4050 },
        { city: 'Moscow', country: 'Russia', tz: 'Europe/Moscow', lat: 55.7558, lon: 37.6173 },
        { city: 'Cairo', country: 'Egypt', tz: 'Africa/Cairo', lat: 30.0444, lon: 31.2357 },
        { city: 'Nairobi', country: 'Kenya', tz: 'Africa/Nairobi', lat: -1.2921, lon: 36.8219 },
        { city: 'Dubai', country: 'UAE', tz: 'Asia/Dubai', lat: 25.2048, lon: 55.2708 },
        { city: 'Beijing', country: 'China', tz: 'Asia/Shanghai', lat: 39.9042, lon: 116.4074 },
        { city: 'Hong Kong', country: 'China', tz: 'Asia/Hong_Kong', lat: 22.3193, lon: 114.1694 },
        { city: 'Singapore', country: 'Singapore', tz: 'Asia/Singapore', lat: 1.3521, lon: 103.8198 },
        { city: 'Bangkok', country: 'Thailand', tz: 'Asia/Bangkok', lat: 13.7563, lon: 100.5018 },
        { city: 'Mumbai', country: 'India', tz: 'Asia/Kolkata', lat: 19.0760, lon: 72.8777 },
        { city: 'Tokyo', country: 'Japan', tz: 'Asia/Tokyo', lat: 35.6762, lon: 139.6503 },
        { city: 'Seoul', country: 'South Korea', tz: 'Asia/Seoul', lat: 37.5665, lon: 126.9780 },
        { city: 'Sydney', country: 'Australia', tz: 'Australia/Sydney', lat: -33.8688, lon: 151.2093 },
        { city: 'Auckland', country: 'New Zealand', tz: 'Pacific/Auckland', lat: -36.8485, lon: 174.7633 },
    ];

    const utils = window.worldTimeUtils;
    let showSeconds = false;
    let filterText = '';
    let timer = null;
    let map = null;
    let markers = [];

    function buildPopupHtml(now, cityData) {
        const ok = utils.supportsTimeZone(cityData.tz);
        if (!ok) {
            return `<div style="min-width: 240px;"><div class="fw-semibold text-dark">${utils.escapeHtml(cityData.city)} · ${utils.escapeHtml(cityData.country)}</div><div class="text-muted small">${utils.escapeHtml(cityData.tz)}</div><div class="mt-2 text-warning small">该浏览器不支持此时区</div></div>`;
        }
        const value = utils.formatInZone(now, cityData.tz, showSeconds);
        const offset = utils.tryGetOffsetLabel(now, cityData.tz) || '--';
        return `<div style="min-width: 260px;"><div class="d-flex align-items-start justify-content-between gap-2"><div><div class="fw-semibold text-dark">${utils.escapeHtml(cityData.city)} · ${utils.escapeHtml(cityData.country)}</div><div class="text-muted small">${utils.escapeHtml(cityData.tz)}</div></div><span class="badge rounded-pill tb-badge-outline">${utils.escapeHtml(offset)}</span></div><div class="mt-2 tb-clock-time-lg" style="font-size: 1.3rem;">${utils.escapeHtml(value.time)}</div><div class="text-muted small">${utils.escapeHtml(value.date)}</div></div>`;
    }

    function initMap() {
        map = L.map('map', { worldCopyJump: true, zoomControl: true }).setView([20, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, attribution: '&copy; OpenStreetMap' }).addTo(map);
    }

    function rebuildMarkers() {
        const safeFilter = filterText.trim().toLowerCase();
        const now = new Date();
        markers.forEach((marker) => marker.remove());
        markers = [];

        CITIES.filter((city) => !safeFilter || `${city.city} ${city.country} ${city.tz}`.toLowerCase().includes(safeFilter))
            .forEach((cityData) => {
                const marker = L.marker([cityData.lat, cityData.lon], { title: `${cityData.city}, ${cityData.country}` }).addTo(map);
                marker.bindPopup(buildPopupHtml(now, cityData));
                marker._cityData = cityData;
                markers.push(marker);
            });
    }

    function tick() {
        const now = new Date();
        document.getElementById('localTime').innerText = new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit', second: showSeconds ? '2-digit' : undefined, hour12: false }).format(now);
        document.getElementById('localDate').innerText = new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short' }).format(now);
        document.getElementById('utcTime').innerText = new Intl.DateTimeFormat('zh-CN', { timeZone: 'UTC', hour: '2-digit', minute: '2-digit', second: showSeconds ? '2-digit' : undefined, hour12: false }).format(now);
        document.getElementById('utcDate').innerText = new Intl.DateTimeFormat('zh-CN', { timeZone: 'UTC', year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short' }).format(now);
        markers.forEach((marker) => {
            if (marker.isPopupOpen && marker.isPopupOpen()) marker.setPopupContent(buildPopupHtml(now, marker._cityData));
        });
    }

    function start() {
        if (timer) clearInterval(timer);
        tick();
        timer = setInterval(tick, showSeconds ? 250 : 1000);
    }

    document.getElementById('filterInput').addEventListener('input', (e) => {
        filterText = e.target.value || '';
        rebuildMarkers();
    });
    document.getElementById('toggleSecondsBtn').addEventListener('click', () => {
        showSeconds = !showSeconds;
        document.getElementById('toggleSecondsBtn').innerText = showSeconds ? '隐藏秒' : '显示秒';
        start();
    });
    document.getElementById('resetBtn').addEventListener('click', () => {
        showSeconds = false;
        filterText = '';
        document.getElementById('toggleSecondsBtn').innerText = '显示秒';
        document.getElementById('filterInput').value = '';
        rebuildMarkers();
        start();
    });

    initMap();
    rebuildMarkers();
    start();
})();
