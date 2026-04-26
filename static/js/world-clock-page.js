(function () {
    const ZONES = [
        { label: '洛杉矶（Pacific）', tz: 'America/Los_Angeles' },
        { label: '纽约（Eastern）', tz: 'America/New_York' },
        { label: '伦敦（GMT）', tz: 'Europe/London' },
        { label: '巴黎（CET）', tz: 'Europe/Paris' },
        { label: '开罗（EET）', tz: 'Africa/Cairo' },
        { label: '迪拜（GST）', tz: 'Asia/Dubai' },
        { label: '孟买（IST）', tz: 'Asia/Kolkata' },
        { label: '曼谷（ICT）', tz: 'Asia/Bangkok' },
        { label: '新加坡（SGT）', tz: 'Asia/Singapore' },
        { label: '香港（HKT）', tz: 'Asia/Hong_Kong' },
        { label: '东京（JST）', tz: 'Asia/Tokyo' },
        { label: '悉尼（AEST）', tz: 'Australia/Sydney' },
        { label: '奥克兰（NZST）', tz: 'Pacific/Auckland' },
    ];

    const utils = window.worldTimeUtils;
    let showSeconds = false;
    let timer = null;
    let filterText = '';

    function buildCards() {
        const grid = document.getElementById('clockGrid');
        const safeFilter = filterText.trim().toLowerCase();

        const zones = ZONES.filter((z) => !safeFilter || (z.label + ' ' + z.tz).toLowerCase().includes(safeFilter));
        if (zones.length === 0) {
            grid.innerHTML = '<div class="col-12"><div class="text-center text-muted py-5 tb-clock-cell">未找到匹配的时区</div></div>';
            return;
        }

        grid.innerHTML = zones.map((z, idx) => {
            const ok = utils.supportsTimeZone(z.tz);
            const badge = ok ? '<span class="badge rounded-pill tb-badge-outline">IANA</span>' : '<span class="badge rounded-pill text-bg-warning">不支持</span>';
            return `<div class="col-md-6"><div class="tb-clock-cell p-3"><div class="d-flex justify-content-between align-items-start gap-2"><div><div class="fw-semibold text-dark">${utils.escapeHtml(z.label)}</div><div class="text-muted small d-flex align-items-center gap-2 flex-wrap"><span>${utils.escapeHtml(z.tz)}</span><span class="badge rounded-pill tb-badge-outline" data-offset="${utils.escapeHtml(z.tz)}">--</span></div></div><div class="d-flex align-items-center gap-2">${badge}<button class="btn btn-sm btn-outline-secondary" data-copy="${utils.escapeHtml(z.tz)}" title="复制时区标识"><i class="bi bi-clipboard"></i></button></div></div><div class="mt-3 d-flex align-items-baseline justify-content-between"><div><div class="clock-time tb-clock-time-lg" data-tz="${utils.escapeHtml(z.tz)}">--</div><div class="clock-date text-muted small" data-tz-date="${utils.escapeHtml(z.tz)}">--</div></div><div class="text-muted small"><span class="badge rounded-pill tb-badge-outline">#${idx + 1}</span></div></div></div></div>`;
        }).join('');

        grid.querySelectorAll('button[data-copy]').forEach((btn) => {
            btn.addEventListener('click', async () => {
                const tz = btn.getAttribute('data-copy');
                try {
                    await utils.copyText(tz);
                    btn.innerHTML = '<i class="bi bi-check2"></i>';
                    setTimeout(() => (btn.innerHTML = '<i class="bi bi-clipboard"></i>'), 900);
                } catch (e) {
                    alert('复制失败，请手动复制：' + tz);
                }
            });
        });
    }

    function tick() {
        const now = new Date();
        const localTimeFmt = new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit', second: showSeconds ? '2-digit' : undefined, hour12: false }).format(now);
        const localDateFmt = new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short' }).format(now);
        document.getElementById('localTime').innerText = localTimeFmt;
        document.getElementById('localDate').innerText = localDateFmt;

        const utcTimeFmt = new Intl.DateTimeFormat('zh-CN', { timeZone: 'UTC', hour: '2-digit', minute: '2-digit', second: showSeconds ? '2-digit' : undefined, hour12: false }).format(now);
        const utcDateFmt = new Intl.DateTimeFormat('zh-CN', { timeZone: 'UTC', year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short' }).format(now);
        document.getElementById('utcTime').innerText = utcTimeFmt;
        document.getElementById('utcDate').innerText = utcDateFmt;

        document.querySelectorAll('.clock-time[data-tz]').forEach((el) => {
            const tz = el.getAttribute('data-tz');
            if (!utils.supportsTimeZone(tz)) el.innerText = '不支持';
            else el.innerText = utils.formatInZone(now, tz, showSeconds).time;
        });
        document.querySelectorAll('.clock-date[data-tz-date]').forEach((el) => {
            const tz = el.getAttribute('data-tz-date');
            if (!utils.supportsTimeZone(tz)) el.innerText = '';
            else el.innerText = utils.formatInZone(now, tz, showSeconds).date;
        });
        document.querySelectorAll('[data-offset]').forEach((el) => {
            const tz = el.getAttribute('data-offset');
            el.innerText = !utils.supportsTimeZone(tz) ? '' : (utils.tryGetOffsetLabel(now, tz) || '--');
        });
    }

    function start() {
        if (timer) clearInterval(timer);
        tick();
        timer = setInterval(tick, showSeconds ? 250 : 1000);
    }

    document.getElementById('filterInput').addEventListener('input', (e) => {
        filterText = e.target.value || '';
        buildCards();
        tick();
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
        buildCards();
        start();
    });

    buildCards();
    start();
})();
