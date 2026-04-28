(function () {
    const form = document.getElementById('toolForm');
    if (!form) return;

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const formData = new FormData(form);
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>导出中...';
        submitBtn.disabled = true;

        if (!formData.has('remove_outer_background')) formData.set('remove_outer_background', 'false');
        if (!formData.has('print_background')) formData.set('print_background', 'false');
        if (!formData.has('landscape')) formData.set('landscape', 'false');

        try {
            const result = await apiRequest(form.dataset.apiUrl, formData);
            if (result.type === 'file') downloadBlob(result.blob, result.filename);
            else if (result.type === 'json') console.log('导出成功:', result.data);
        } catch (error) {
            console.error(error);
        } finally {
            submitBtn.innerHTML = '<i class="bi bi-play-circle me-1"></i>开始导出';
            submitBtn.disabled = false;
        }
    });
})();
