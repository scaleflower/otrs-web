// Global variables
let analysisData = null;

// DOM Elements
const fileInput = document.getElementById('fileInput');
const uploadForm = document.getElementById('uploadForm');
const uploadBtn = document.querySelector('.upload-btn');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const exportExcelBtn = document.getElementById('exportExcel');
const exportTxtBtn = document.getElementById('exportTxt');
const reuploadBtn = document.getElementById('reuploadBtn');

// Update notification elements
const updateIconButton = document.getElementById('updateIconButton');
const updateIconBadge = document.getElementById('updateIconBadge');
const updateModal = document.getElementById('updateModal');
const updateModalClose = document.getElementById('updateModalClose');
const updateModalCancelBtn = document.getElementById('updateModalCancelBtn');
const updateModalConfirmBtn = document.getElementById('updateModalConfirmBtn');
const updateModalNotes = document.getElementById('updateModalNotes');
const updateModalStatus = document.getElementById('updateModalStatus');
const updateModalLink = document.getElementById('updateModalReleaseLink');
const updateModalPassword = document.getElementById('updatePasswordInput');
const updateModalFeedback = document.getElementById('updateModalFeedback');
const updateModalCurrentVersion = document.getElementById('updateModalCurrentVersion');
const updateModalLatestVersion = document.getElementById('updateModalLatestVersion');
const updateModalPublished = document.getElementById('updateModalPublished');
const updateModalRemindBtn = document.getElementById('updateModalRemindBtn');

let updateStatusData = null;
let updateStatusTimer = null;
let restartNoticeShown = false;

// Chart instances
let emptyFirstResponseChart = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    loadLatestUploadInfo();
    initializeUpdateNotifications();
});

function initializeEventListeners() {
    // File input change event
    fileInput.addEventListener('change', handleFileSelect);
    
    // Form submit event
    uploadForm.addEventListener('submit', handleFormSubmit);
    
    // Export buttons
    exportExcelBtn.addEventListener('click', handleExportExcel);
    exportTxtBtn.addEventListener('click', handleExportTxt);
    
    // Re-upload button
    reuploadBtn.addEventListener('click', handleReupload);
    
    // Age segment click events
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('age-clickable')) {
            const ageSegment = e.target.getAttribute('data-age-segment');
            handleAgeSegmentClick(ageSegment);
        }
    });
    
    // Sort order change event
    const sortOrderSelect = document.getElementById('sortOrder');
    if (sortOrderSelect) {
        sortOrderSelect.addEventListener('change', function() {
            if (analysisData && analysisData.stats) {
                updateDailyTable(analysisData.stats);
            }
        });
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        // Validate file type
        const validExtensions = ['.xlsx', '.xls'];
        const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        
        if (!validExtensions.includes(fileExtension)) {
            showError('Please select an Excel file (.xlsx or .xls format)');
            resetFileInput();
            return;
        }
        
        // Update UI
        fileName.textContent = file.name;
        fileInfo.style.display = 'flex';
        uploadBtn.disabled = false;
        
        // Add animation
        fileInfo.classList.add('fade-in');
    }
}

function handleFormSubmit(event) {
    event.preventDefault();
    
    const file = fileInput.files[0];
    if (!file) {
        showError('Please select an Excel file first');
        return;
    }
    
    // Show loading state
    showLoading();
    
    // Create FormData for file upload
    const formData = new FormData();
    formData.append('file', file);
    
    // Function to update progress display
    const updateProgressDisplay = (progressData) => {
        const progressPercentage = Math.max(0, Math.min(100, (progressData.current_step / progressData.total_steps) * 100));
        
        document.getElementById('progressBar').style.width = `${progressPercentage}%`;
        document.getElementById('progressText').textContent = `${Math.round(progressPercentage)}%`;
        
        const statusElement = document.getElementById('currentStatus');
        const detailsElement = document.getElementById('statusDetails');
        
        statusElement.textContent = progressData.message || '处理中...';
        detailsElement.textContent = progressData.details || '';
        
        // Add animation
        statusElement.classList.add('fade-in');
        setTimeout(() => statusElement.classList.remove('fade-in'), 500);
    };
    
    // Function to poll progress from server
    let isUploadCompleted = false;
    const pollProgress = () => {
        if (isUploadCompleted) return;
        
        fetch('/processing-status')
            .then(response => response.json())
            .then(progressData => {
                // Update progress display
                updateProgressDisplay(progressData);
                
                // Continue polling until progress is complete or upload is finished
                if (progressData.current_step < progressData.total_steps && !isUploadCompleted) {
                    setTimeout(pollProgress, 500); // More frequent updates for better responsiveness
                }
            })
            .catch(error => {
                console.error('Error polling progress:', error);
                // Continue polling even if there's an error, but less frequently
                if (!isUploadCompleted) {
                    setTimeout(pollProgress, 2000);
                }
            });
    };
    
    // Start polling progress immediately
    setTimeout(pollProgress, 200);
    
    // Initial progress display
    updateProgressDisplay({
        current_step: 0,
        total_steps: 7,
        message: '开始处理Excel文件...',
        details: '正在读取文件信息'
    });
    
    // Send AJAX request
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => {
                throw new Error(errorData.error || 'Upload failed');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Mark upload as completed to stop polling
            isUploadCompleted = true;
            
            // Final progress update
            updateProgressDisplay({
                current_step: 7,
                total_steps: 7,
                message: '处理完成！',
                details: `成功导入 ${data.new_records_count} 条记录`
            });
            
            // Small delay to show completion
            setTimeout(() => {
                analysisData = data;
                showResults(data);
            }, 1000);
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
    })
    .catch(error => {
        isUploadCompleted = true; // Stop polling on error
        showError(error.message);
    });
}

function handleExportExcel() {
    if (!analysisData) {
        showError('No data available for export');
        return;
    }
    
    // Show loading state for export
    const originalText = exportExcelBtn.innerHTML;
    exportExcelBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在导出...';
    exportExcelBtn.disabled = true;
    
    fetch('/export/excel', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(analysisData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => {
                throw new Error(errorData.error || 'Export failed');
            });
        }
        return response.blob();
    })
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `otrs_analysis_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    })
    .catch(error => {
        showError(error.message);
    })
    .finally(() => {
        // Restore button state
        exportExcelBtn.innerHTML = originalText;
        exportExcelBtn.disabled = false;
    });
}

function handleExportTxt() {
    if (!analysisData) {
        showError('No data available for export');
        return;
    }
    
    // Show loading state for export
    const originalText = exportTxtBtn.innerHTML;
    exportTxtBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在导出...';
    exportTxtBtn.disabled = true;
    
    fetch('/export/txt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(analysisData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => {
                throw new Error(errorData.error || 'Export failed');
            });
        }
        return response.blob();
    })
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `otrs_analysis_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    })
    .catch(error => {
        showError(error.message);
    })
    .finally(() => {
        // Restore button state
        exportTxtBtn.innerHTML = originalText;
        exportTxtBtn.disabled = false;
    });
}

function handleReupload() {
    // Hide results section
    resultsSection.style.display = 'none';
    
    // Show upload section with animation
    document.querySelector('.upload-section').style.display = 'block';
    document.querySelector('.upload-section').classList.add('fade-in');
    
    // Reset file input and form
    resetFileInput();
    
    // Clear any stored analysis data
    analysisData = null;
    localStorage.removeItem('otrsAnalysisData');
    
    // Scroll to top for better user experience
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showLoading() {
    // Hide other sections
    document.querySelector('.upload-section').style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    // Show loading section
    loadingSection.style.display = 'block';
    loadingSection.classList.add('fade-in');
}

function showResults(data) {
    // Hide loading and other sections
    loadingSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    // Update summary cards
    document.getElementById('totalRecords').textContent = data.total_records.toLocaleString();
    document.getElementById('openTickets').textContent = (data.stats.current_open_count || 0).toLocaleString();
    document.getElementById('emptyFirstResponse').textContent = (data.stats.empty_firstresponse_count || 0).toLocaleString();
    
    // Update daily statistics table
    updateDailyTable(data.stats);
    
    // Update age segments if available
    if (data.stats.age_segments) {
        document.getElementById('age24h').textContent = (data.stats.age_segments.age_24h || 0).toLocaleString();
        document.getElementById('age24_48h').textContent = (data.stats.age_segments.age_24_48h || 0).toLocaleString();
        document.getElementById('age48_72h').textContent = (data.stats.age_segments.age_48_72h || 0).toLocaleString();
        document.getElementById('age72h').textContent = (data.stats.age_segments.age_72h || 0).toLocaleString();
    }
    
    // Create charts
    createCharts(data.stats);

    // Update empty first response table
    updateEmptyFirstResponseTable(data.stats);

    // Show results section with animation
    resultsSection.style.display = 'block';
    resultsSection.classList.add('fade-in');
}

function updateDailyTable(stats) {
    const tableBody = document.querySelector('#dailyTable tbody');
    tableBody.innerHTML = '';
    
    if (stats.daily_new && stats.daily_closed) {
        let allDates = Array.from(
            new Set([...Object.keys(stats.daily_new), ...Object.keys(stats.daily_closed)])
        );
        
        // First, calculate cumulative open tickets correctly from earliest date
        // Sort dates in ascending order for correct cumulative calculation
        const sortedDatesAsc = [...allDates].sort((a, b) => new Date(a) - new Date(b));
        
        // Calculate cumulative open tickets for each date (from earliest to latest)
        const cumulativeByDate = {};
        let cumulativeOpen = 0;
        
        sortedDatesAsc.forEach(date => {
            const newCount = stats.daily_new[date] || 0;
            const closedCount = stats.daily_closed[date] || 0;
            cumulativeOpen = cumulativeOpen + newCount - closedCount;
            cumulativeByDate[date] = cumulativeOpen;
        });
        
        // Now sort dates based on selected display order
        const sortOrderSelect = document.getElementById('sortOrder');
        const sortOrder = sortOrderSelect ? sortOrderSelect.value : 'desc';
        
        allDates.sort((a, b) => {
            const dateA = new Date(a);
            const dateB = new Date(b);
            return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
        });
        
        // Display the table with correct cumulative values
        allDates.forEach(date => {
            const newCount = stats.daily_new[date] || 0;
            const closedCount = stats.daily_closed[date] || 0;
            const cumulativeOpen = cumulativeByDate[date] || 0;
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${date}</td>
                <td>${newCount}</td>
                <td>${closedCount}</td>
                <td>${cumulativeOpen}</td>
            `;
            tableBody.appendChild(row);
        });
    } else {
        tableBody.innerHTML = '<tr><td colspan="4" style="text-align: center;">无每日统计数据</td></tr>';
    }
}

function createCharts(stats) {
    // Destroy existing charts if they exist
    if (emptyFirstResponseChart) emptyFirstResponseChart.destroy();
    
    // Empty FirstResponse Chart
    if (stats.empty_firstresponse_by_priority) {
        const emptyCtx = document.getElementById('emptyFirstResponseChart').getContext('2d');
        emptyFirstResponseChart = new Chart(emptyCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(stats.empty_firstresponse_by_priority),
                datasets: [{
                    label: '空FirstResponse数量',
                    data: Object.values(stats.empty_firstresponse_by_priority),
                    backgroundColor: '#ff9f43',
                    borderColor: '#ff9f43',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

function showError(message) {
    // Hide other sections
    loadingSection.style.display = 'none';
    resultsSection.style.display = 'none';
    
    // Show error message
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
    errorSection.classList.add('fade-in');
}

function hideError() {
    errorSection.style.display = 'none';
    document.querySelector('.upload-section').style.display = 'block';
}

function resetFileInput() {
    fileInput.value = '';
    fileInfo.style.display = 'none';
    uploadBtn.disabled = true;
}

// Utility function to format numbers
function formatNumber(num) {
    return new Intl.NumberFormat('zh-CN').format(num);
}

// Handle age segment click
function handleAgeSegmentClick(ageSegment) {
    if (!analysisData) return;
    
    // Show loading state for details
    const detailsContainer = document.getElementById('ageDetailsContainer');
    const detailsTable = document.getElementById('ageDetailsTable');
    detailsTable.querySelector('tbody').innerHTML = '<tr><td colspan="4" style="text-align: center;">加载中...</td></tr>';
    detailsContainer.style.display = 'block';
    
    // Send request to get age segment details
    fetch('/age-details', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            age_segment: ageSegment,
            analysis_data: analysisData,
            session_id: analysisData.session_id
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('获取明细数据失败');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            updateAgeDetailsTable(data.details);
        } else {
            throw new Error(data.error || '获取明细数据失败');
        }
    })
    .catch(error => {
        detailsTable.querySelector('tbody').innerHTML = `<tr><td colspan="4" style="text-align: center; color: #dc3545;">${error.message}</td></tr>`;
    });
}

// Update age details table
function updateAgeDetailsTable(details) {
    const tableBody = document.querySelector('#ageDetailsTable tbody');
    tableBody.innerHTML = '';
    
    if (details && details.length > 0) {
        details.forEach(ticket => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${ticket.ticket_number || 'N/A'}</td>
                <td>${ticket.age || 'N/A'}</td>
                <td>${ticket.created || 'N/A'}</td>
                <td>${ticket.priority || 'N/A'}</td>
            `;
            tableBody.appendChild(row);
        });
    } else {
        tableBody.innerHTML = '<tr><td colspan="4" style="text-align: center;">无数据</td></tr>';
    }
}

// Update empty first response table with real data
function updateEmptyFirstResponseTable(stats) {
    const tableBody = document.querySelector('#emptyFirstResponseTable tbody');
    tableBody.innerHTML = '<tr><td colspan="4" style="text-align: center;">加载中...</td></tr>';
    
    // Send request to get empty first response details
    fetch('/empty-firstresponse-details', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: analysisData.session_id
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('获取空FirstResponse明细数据失败');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            tableBody.innerHTML = '';
            
            if (data.details && data.details.length > 0) {
                data.details.forEach(ticket => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${ticket.ticket_number || 'N/A'}</td>
                        <td>${ticket.age || 'N/A'}</td>
                        <td>${ticket.created || 'N/A'}</td>
                        <td>${ticket.priority || 'N/A'}</td>
                    `;
                    tableBody.appendChild(row);
                });
            } else {
                tableBody.innerHTML = '<tr><td colspan="4" style="text-align: center;">无空FirstResponse工单</td></tr>';
            }
        } else {
            throw new Error(data.error || '获取空FirstResponse明细数据失败');
        }
    })
    .catch(error => {
        tableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: #dc3545;">${error.message}</td></tr>`;
    });
}
// Load latest upload information
function loadLatestUploadInfo() {
    const latestUploadContent = document.getElementById('latestUploadContent');
    if (!latestUploadContent) return; // Exit if element doesn't exist
    
    fetch('/api/latest-upload-info')
        .then(response => {
            if (!response.ok) {
                throw new Error('获取最新上传信息失败');
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.has_data && data.latest_upload) {
                const info = data.latest_upload;
                latestUploadContent.innerHTML = `
                    <div class="upload-info-grid">
                        <div class="upload-info-item">
                            <h4>上传文件</h4>
                            <p>${info.filename}</p>
                        </div>
                        <div class="upload-info-item">
                            <h4>新增记录数</h4>
                            <p>${info.new_records_count.toLocaleString()} 条</p>
                        </div>
                        <div class="upload-info-item">
                            <h4>上传时间</h4>
                            <p>${info.upload_time}</p>
                        </div>
                        <div class="upload-info-item">
                            <h4>数据库总记录</h4>
                            <p>${info.total_records.toLocaleString()} 条</p>
                        </div>
                    </div>
                `;
            } else {
                latestUploadContent.innerHTML = `
                    <div class="no-upload-message">
                        <i class="fas fa-inbox"></i>
                        <h4>暂无上传记录</h4>
                        <p>请先上传 Excel 文件来查看数据统计</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading latest upload info:', error);
            latestUploadContent.innerHTML = `
                <div class="no-upload-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h4>加载失败</h4>
                    <p>${error.message}</p>
                </div>
            `;
        });
}

// Add some animation effects
function animateValue(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        element.textContent = formatNumber(Math.floor(progress * (end - start) + start));
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// ---------------------------------------------------------------------------
// Application update notifications
// ---------------------------------------------------------------------------

function initializeUpdateNotifications() {
    if (!updateIconButton && !updateModal) {
        return;
    }

    if (updateIconButton) {
        updateIconButton.addEventListener('click', () => openUpdateModal(true));
    }
    if (updateModalRemindBtn) {
        updateModalRemindBtn.addEventListener('click', () => {
            acknowledgeUpdateNotification();
            closeUpdateModal();
        });
    }
    if (updateModalConfirmBtn) {
        updateModalConfirmBtn.addEventListener('click', triggerUpdateFromModal);
    }
    if (updateModalClose) {
        updateModalClose.addEventListener('click', closeUpdateModal);
    }
    if (updateModalCancelBtn) {
        updateModalCancelBtn.addEventListener('click', closeUpdateModal);
    }
    if (updateModal) {
        updateModal.addEventListener('click', (event) => {
            if (event.target === updateModal) {
                closeUpdateModal();
            }
        });
    }

    fetchUpdateStatus();
}

function scheduleUpdateStatusPoll(seconds) {
    if (updateStatusTimer) {
        clearTimeout(updateStatusTimer);
    }
    updateStatusTimer = setTimeout(fetchUpdateStatus, Math.max(seconds, 5) * 1000);
}

async function fetchUpdateStatus() {
    if (!updateIconButton && !updateModal) {
        return;
    }
    try {
        const response = await fetch('/api/update/status');
        if (!response.ok) {
            throw new Error('无法获取更新状态');
        }
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || '读取更新状态失败');
        }
        updateStatusData = data.status || null;
        applyUpdateIndicatorState(updateStatusData);
        const pollSeconds = getUpdatePollInterval(updateStatusData);
        scheduleUpdateStatusPoll(pollSeconds);
    } catch (error) {
        console.error('Error fetching update status:', error);
        scheduleUpdateStatusPoll(180);
    }
}

function getUpdatePollInterval(status) {
    if (!status) return 180;
    switch (status.status) {
        case 'updating':
        case 'restarting':
            return 5;
        case 'update_available':
            return 60;
        case 'update_failed':
        case 'error':
            return 120;
        default:
            return 180;
    }
}

function applyUpdateIndicatorState(status) {
    if (!updateIconButton) return;

    updateIconButton.style.display = 'none';
    updateIconButton.classList.remove('pulse', 'spinning', 'error');
    updateIconButton.disabled = false;

    if (updateIconBadge) {
        updateIconBadge.textContent = '';
    }

    if (!status || status.update_enabled === false) {
        return;
    }

    const statusCode = status.status || 'unknown';

    switch (statusCode) {
        case 'update_available':
            if (status.notified_at) {
                return;
            }
            updateIconButton.style.display = 'inline-flex';
            updateIconButton.classList.add('pulse');
            if (updateIconBadge) updateIconBadge.textContent = '更新';
            break;
        case 'updating':
            updateIconButton.style.display = 'inline-flex';
            updateIconButton.classList.add('spinning');
            if (updateIconBadge) updateIconBadge.textContent = '更新中';
            break;
        case 'restarting':
            updateIconButton.style.display = 'inline-flex';
            updateIconButton.classList.add('spinning');
            updateIconButton.disabled = true;
            if (updateIconBadge) updateIconBadge.textContent = '重启中';
            if (!restartNoticeShown) {
                restartNoticeShown = true;
                setTimeout(() => window.location.reload(), 5000);
            }
            break;
        case 'update_failed':
            updateIconButton.style.display = 'inline-flex';
            updateIconButton.classList.add('error');
            if (updateIconBadge) updateIconBadge.textContent = '失败';
            break;
        default:
            return;
    }
}

function openUpdateModal(focusPassword = false) {
    if (!updateModal) return;
    populateUpdateModal();
    updateModal.classList.add('visible');
    if (focusPassword && updateModalPassword) {
        setTimeout(() => updateModalPassword.focus(), 150);
    }
}

function populateUpdateModal() {
    if (!updateStatusData) {
        if (updateModalNotes) {
            updateModalNotes.innerHTML = '<p>当前没有可用的更新信息。</p>';
        }
        if (updateModalStatus) {
            updateModalStatus.textContent = '';
        }
        if (updateModalLink) {
            updateModalLink.style.display = 'none';
        }
        if (updateModalConfirmBtn) {
            updateModalConfirmBtn.style.display = 'none';
        }
        if (updateModalRemindBtn) {
            updateModalRemindBtn.style.display = 'none';
        }
        return;
    }

    const latest = updateStatusData.latest_version || updateStatusData.current_version || '未知版本';
    const current = updateStatusData.current_version || '未知版本';
    const statusCode = updateStatusData.status || 'unknown';

    if (updateModalCurrentVersion) updateModalCurrentVersion.textContent = current;
    if (updateModalLatestVersion) updateModalLatestVersion.textContent = latest;
    if (updateModalPublished) updateModalPublished.textContent = formatDisplayDate(updateStatusData.published_at);

    if (updateModalNotes) {
        updateModalNotes.innerHTML = formatReleaseNotes(updateStatusData.release_notes);
    }
    if (updateModalLink) {
        if (updateStatusData.release_url) {
            updateModalLink.href = updateStatusData.release_url;
            updateModalLink.style.display = 'inline-flex';
        } else {
            updateModalLink.style.display = 'none';
        }
    }
    if (updateModalStatus) {
        updateModalStatus.textContent = describeUpdateStatus(updateStatusData);
    }
    if (updateModalFeedback) {
        updateModalFeedback.textContent = '';
        updateModalFeedback.className = 'update-modal-feedback';
    }

    const requiresPassword = statusCode === 'update_available' || statusCode === 'update_failed';
    if (updateModalPassword) {
        updateModalPassword.value = '';
        updateModalPassword.disabled = !requiresPassword;
    }

    if (updateModalConfirmBtn) {
        if (statusCode === 'update_available') {
            updateModalConfirmBtn.style.display = 'inline-flex';
            updateModalConfirmBtn.disabled = false;
            updateModalConfirmBtn.innerHTML = '<i class="fas fa-play"></i> 开始更新';
        } else if (statusCode === 'update_failed') {
            updateModalConfirmBtn.style.display = 'inline-flex';
            updateModalConfirmBtn.disabled = false;
            updateModalConfirmBtn.innerHTML = '<i class="fas fa-redo"></i> 重新尝试';
        } else {
            updateModalConfirmBtn.style.display = 'none';
        }
    }

    if (updateModalRemindBtn) {
        if (statusCode === 'update_available') {
            updateModalRemindBtn.style.display = 'inline-flex';
            updateModalRemindBtn.disabled = false;
        } else {
            updateModalRemindBtn.style.display = 'none';
        }
    }
}

function closeUpdateModal() {
    if (!updateModal) return;
    updateModal.classList.remove('visible');
}

async function acknowledgeUpdateNotification() {
    try {
        const response = await fetch('/api/update/ack', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        if (!response.ok) {
            throw new Error('通知服务器失败');
        }
        if (updateStatusData) {
            updateStatusData.notified_at = new Date().toISOString();
        }
        applyUpdateIndicatorState(updateStatusData);
    } catch (error) {
        console.error('Error acknowledging update notification:', error);
    }
}

async function triggerUpdateFromModal() {
    if (!updateStatusData || !updateModalConfirmBtn) return;

    const password = updateModalPassword ? updateModalPassword.value.trim() : '';
    if (!password) {
        if (updateModalFeedback) {
            updateModalFeedback.textContent = '请先输入管理员密码。';
            updateModalFeedback.className = 'update-modal-feedback error';
        }
        if (updateModalPassword) updateModalPassword.focus();
        return;
    }

    updateModalConfirmBtn.disabled = true;
    updateModalConfirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在启动';
    if (updateModalFeedback) {
        updateModalFeedback.textContent = '';
        updateModalFeedback.className = 'update-modal-feedback';
    }

    try {
        const response = await fetch('/api/update/trigger', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                target_version: updateStatusData.latest_version,
                auth_password: password
            })
        });

        const payload = await response.json();

        if (!response.ok || !payload.success) {
            throw new Error(payload.error || '更新启动失败');
        }

        if (updateModalFeedback) {
            updateModalFeedback.textContent = '更新已开始，请稍候。';
            updateModalFeedback.className = 'update-modal-feedback success';
        }
        closeUpdateModal();
        fetchUpdateStatus();
    } catch (error) {
        if (updateModalFeedback) {
            updateModalFeedback.textContent = error.message;
            updateModalFeedback.className = 'update-modal-feedback error';
        }
        if (updateModalConfirmBtn) {
            updateModalConfirmBtn.disabled = false;
            updateModalConfirmBtn.innerHTML = '<i class="fas fa-play"></i> 开始更新';
        }
    }
}


function formatReleaseNotes(notes) {
    if (!notes) {
        return '<p>该版本未提供发布说明。</p>';
    }
    const escaped = escapeHtml(notes);
    return escaped.replace(/\r?\n/g, '<br>');
}

function escapeHtml(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function formatDisplayDate(value) {
    if (!value) return '未知';
    try {
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return value;
        }
        return date.toLocaleString();
    } catch (error) {
        return value;
    }
}

function describeUpdateStatus(status) {
    if (!status) return '';
    const latest = status.latest_version || status.current_version || '';
    switch (status.status) {
        case 'update_available':
            return `即将更新到版本 ${latest}。`;
        case 'updating':
            return '更新正在进行中，请稍候。';
        case 'restarting':
            return '更新已完成，应用即将自动重启。';
        case 'update_failed':
            return `更新失败：${status.last_error || '未知原因'}`;
        case 'error':
            return `检查更新时发生错误：${status.last_error || '未知原因'}`;
        default:
            return '';
    }
}
