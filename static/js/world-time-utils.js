(function () {
    const tzSupportCache = new Map();

    function escapeHtml(str) {
        return String(str)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }

    function supportsTimeZone(tz) {
        if (tzSupportCache.has(tz)) return tzSupportCache.get(tz);
        try {
            new Intl.DateTimeFormat('zh-CN', { timeZone: tz }).format(new Date());
            tzSupportCache.set(tz, true);
            return true;
        } catch (e) {
            tzSupportCache.set(tz, false);
            return false;
        }
    }

    function tryGetOffsetLabel(now, tz) {
        const tryOptions = [
            { locale: 'en-US', options: { timeZone: tz, timeZoneName: 'shortOffset', hour: '2-digit', minute: '2-digit', hour12: false } },
            { locale: 'en-US', options: { timeZone: tz, timeZoneName: 'short', hour: '2-digit', minute: '2-digit', hour12: false } },
            { locale: 'zh-CN', options: { timeZone: tz, timeZoneName: 'short', hour: '2-digit', minute: '2-digit', hour12: false } },
        ];
        for (const item of tryOptions) {
            try {
                const parts = new Intl.DateTimeFormat(item.locale, item.options).formatToParts(now);
                const tzName = parts.find((p) => p.type === 'timeZoneName')?.value || '';
                if (!tzName) continue;
                const normalized = tzName.replace('GMT', 'UTC');
                if (/UTC[+-]\d/.test(normalized) || /UTC[+-]\d{2}:?\d{0,2}/.test(normalized) || /UTC/.test(normalized)) {
                    return normalized;
                }
            } catch (e) {
                // noop
            }
        }
        return '';
    }

    function formatInZone(now, tz, showSeconds) {
        const timeFormatter = new Intl.DateTimeFormat('zh-CN', {
            timeZone: tz,
            hour: '2-digit',
            minute: '2-digit',
            second: showSeconds ? '2-digit' : undefined,
            hour12: false
        });
        const dateFormatter = new Intl.DateTimeFormat('zh-CN', {
            timeZone: tz,
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            weekday: 'short'
        });
        return { time: timeFormatter.format(now), date: dateFormatter.format(now) };
    }

    async function copyText(text) {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
            return;
        }
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly', '');
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        ta.style.top = '-9999px';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        const ok = document.execCommand('copy');
        document.body.removeChild(ta);
        if (!ok) throw new Error('copy-failed');
    }

    window.worldTimeUtils = {
        escapeHtml,
        supportsTimeZone,
        tryGetOffsetLabel,
        formatInZone,
        copyText,
    };
})();
