// static/js/common.js
async function apiRequest(url, formData) {
    const response = await fetch(url, {
        method: 'POST',
        body: formData
    });

    const contentType = response.headers.get('content-type') || '';

    // 如果是文件下载（常见 MIME 类型）
    if (contentType.includes('application/octet-stream') ||
        contentType.includes('audio/') ||
        contentType.includes('video/') ||
        contentType.includes('image/') ||
        contentType.includes('application/zip') ||
        contentType.includes('application/x-zip-compressed')) {

        // 尝试从 Content-Disposition 获取文件名
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'download';
        if (contentDisposition) {
            const matchFilenameStar = contentDisposition.match(/filename\*=(?:UTF-8|utf-8)''([^;]+)/);
            if (matchFilenameStar && matchFilenameStar[1]) {
                filename = decodeURIComponent(matchFilenameStar[1]);
            } else {
                const matchFilename = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (matchFilename && matchFilename[1]) {
                    filename = matchFilename[1].replace(/['"]/g, '');
                }
            }
        }
        const blob = await response.blob();
        return { type: 'file', blob, filename };
    }
    // 如果是 JSON 响应
    else if (contentType.includes('application/json')) {
        const result = await response.json();
        if (!result.success) {
            alert(result.message);
            throw new Error(result.message);
        }
        return { type: 'json', data: result.data };
    }
    // 其他情况（如纯文本错误）
    else {
        const text = await response.text();
        alert(text);
        throw new Error(text);
    }
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