const FILE_MIME_PATTERNS = [
    'application/octet-stream',
    'audio/',
    'video/',
    'image/',
    'application/zip',
    'application/x-zip-compressed'
];

function extractFilename(contentDisposition) {
    let filename = 'download';
    if (!contentDisposition) return filename;

    const matchFilenameStar = contentDisposition.match(/filename\*=(?:UTF-8|utf-8)''([^;]+)/);
    if (matchFilenameStar && matchFilenameStar[1]) return decodeURIComponent(matchFilenameStar[1]);

    const matchFilename = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
    if (matchFilename && matchFilename[1]) filename = matchFilename[1].replace(/['"]/g, '');
    return filename;
}

function isFileResponse(contentType) {
    return FILE_MIME_PATTERNS.some((pattern) => contentType.includes(pattern));
}

function normalizeErrorMessage(text) {
    return text || '请求失败';
}

async function parseApiResponse(response) {
    const contentType = response.headers.get('content-type') || '';
    if (isFileResponse(contentType)) {
        const filename = extractFilename(response.headers.get('content-disposition'));
        const blob = await response.blob();
        return { type: 'file', blob, filename };
    }

    if (contentType.includes('application/json')) {
        const result = await response.json();
        if (!result.success) {
            const message = normalizeErrorMessage(result.message);
            alert(message);
            throw new Error(message);
        }
        return { type: 'json', data: result.data };
    }

    const text = await response.text();
    const message = normalizeErrorMessage(text);
    alert(message);
    throw new Error(message);
}

async function apiRequest(url, formData) {
    const response = await fetch(url, { method: 'POST', body: formData });
    return parseApiResponse(response);
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

window.apiRequest = apiRequest;
window.downloadBlob = downloadBlob;
window.ToolboxApiClient = { apiRequest, downloadBlob, parseApiResponse, extractFilename, isFileResponse };