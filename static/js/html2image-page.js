(function () {
    const form = document.getElementById('toolForm');
    if (!form) return;

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const formData = new FormData(form);
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>转换中...';
        submitBtn.disabled = true;

        try {
            const result = await apiRequest(form.dataset.apiUrl, formData);
            if (result.type === 'file') downloadBlob(result.blob, result.filename);
            else if (result.type === 'json') console.log('转换成功:', result.data);
        } catch (error) {
            console.error(error);
        } finally {
            submitBtn.innerHTML = '<i class="bi bi-play-circle me-1"></i>开始转换';
            submitBtn.disabled = false;
        }
    });
})();
