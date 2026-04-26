(function () {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const folderInput = document.getElementById('folderInput');
    const fileCountSpan = document.getElementById('fileCount');
    const submitBtn = document.getElementById('submitBtn');
    const statusDiv = document.getElementById('status');
    const previewArea = document.getElementById('previewArea');
    const previewGrid = document.getElementById('previewGrid');
    const addMoreBtn = document.getElementById('addMoreBtn');
    const clearAllBtn = document.getElementById('clearAllBtn');
    const apiUrl = window.photoTimestampConfig?.apiUrl;

    let selectedFiles = [];
    let objectUrls = [];

    function updateFileList() {
        fileCountSpan.innerText = `已选择 ${selectedFiles.length} 个文件`;
        submitBtn.disabled = selectedFiles.length === 0;
        generatePreviews();
    }

    function generatePreviews() {
        objectUrls.forEach((url) => URL.revokeObjectURL(url));
        objectUrls = [];

        previewGrid.innerHTML = '';
        if (selectedFiles.length === 0) {
            previewArea.style.display = 'none';
            return;
        }
        previewArea.style.display = 'block';

        const maxPreview = Math.min(selectedFiles.length, 50);
        for (let i = 0; i < maxPreview; i++) {
            const file = selectedFiles[i];
            const col = document.createElement('div');
            col.className = 'col-md-3 col-6';
            col.dataset.index = i;

            const card = document.createElement('div');
            card.className = 'card h-100 border-0 shadow-sm position-relative';

            const deleteBtn = document.createElement('span');
            deleteBtn.className = 'btn-delete position-absolute top-0 end-0 m-1';
            deleteBtn.innerHTML = '<i class="bi bi-x-lg"></i>';
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                removeFile(parseInt(col.dataset.index, 10));
            });

            const img = document.createElement('img');
            img.className = 'card-img-top';
            img.style.objectFit = 'cover';
            img.style.height = '100px';
            img.alt = file.name;

            if (file.type.startsWith('image/')) {
                const url = URL.createObjectURL(file);
                objectUrls.push(url);
                img.src = url;
            } else img.src = 'https://via.placeholder.com/100?text=No+Preview';

            const cardBody = document.createElement('div');
            cardBody.className = 'card-body p-2';
            cardBody.innerHTML = `<small class="text-truncate d-block" title="${file.name}">${file.name}</small>`;

            card.appendChild(deleteBtn);
            card.appendChild(img);
            card.appendChild(cardBody);
            col.appendChild(card);
            previewGrid.appendChild(col);
        }

        if (selectedFiles.length > 50) {
            const more = document.createElement('div');
            more.className = 'col-12 text-muted small mt-2';
            more.innerText = `... 还有 ${selectedFiles.length - 50} 个文件未显示`;
            previewGrid.appendChild(more);
        }
    }

    function removeFile(index) {
        if (index >= 0 && index < selectedFiles.length) {
            selectedFiles.splice(index, 1);
            updateFileList();
        }
    }

    function clearAll() {
        selectedFiles = [];
        updateFileList();
    }

    function appendFiles(newFiles) {
        for (const file of newFiles) {
            if (file.type.startsWith('image/')) selectedFiles.push(file);
        }
        updateFileList();
    }

    async function handleFileAppend(fileList) {
        const files = [];
        for (let i = 0; i < fileList.length; i++) files.push(fileList[i]);
        appendFiles(files);
    }

    function traverseDirectory(entry, files) {
        return new Promise((resolve) => {
            const reader = entry.createReader();
            const readEntries = () => {
                reader.readEntries((entries) => {
                    if (entries.length === 0) resolve();
                    else {
                        const promises = [];
                        for (const e of entries) {
                            if (e.isFile) {
                                promises.push(new Promise((res) => {
                                    e.file((file) => {
                                        files.push(file);
                                        res();
                                    });
                                }));
                            } else if (e.isDirectory) promises.push(traverseDirectory(e, files));
                        }
                        Promise.all(promises).then(readEntries);
                    }
                });
            };
            readEntries();
        });
    }

    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        handleFileAppend(e.target.files);
        fileInput.value = '';
    });
    folderInput.addEventListener('change', async (e) => {
        await handleFileAppend(e.target.files);
        folderInput.value = '';
    });
    addMoreBtn.addEventListener('click', () => fileInput.click());
    clearAllBtn.addEventListener('click', clearAll);

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.background = '#e9f0ff';
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.background = '';
    });
    dropZone.addEventListener('drop', async (e) => {
        e.preventDefault();
        dropZone.style.background = '';

        const items = e.dataTransfer.items;
        if (items) {
            const files = [];
            const promises = [];
            for (let i = 0; i < items.length; i++) {
                const entry = items[i].webkitGetAsEntry();
                if (!entry) continue;
                if (entry.isFile) {
                    promises.push(new Promise((resolve) => {
                        entry.file((file) => {
                            files.push(file);
                            resolve();
                        });
                    }));
                } else if (entry.isDirectory) promises.push(traverseDirectory(entry, files));
            }
            await Promise.all(promises);
            appendFiles(files);
        } else appendFiles(e.dataTransfer.files);
    });

    submitBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) return;
        const formData = new FormData();
        for (const file of selectedFiles) formData.append('photos', file);

        const originalHTML = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>处理中...';
        submitBtn.disabled = true;
        statusDiv.innerText = '正在处理，请稍候...';

        try {
            const result = await apiRequest(apiUrl, formData);
            if (result.type === 'file') {
                downloadBlob(result.blob, result.filename);
                statusDiv.innerText = '处理完成，文件已下载';
            } else if (result.type === 'json') statusDiv.innerText = '处理成功';
        } catch (error) {
            statusDiv.innerText = '处理失败，请重试';
        } finally {
            submitBtn.innerHTML = originalHTML;
            submitBtn.disabled = false;
        }
    });
})();
