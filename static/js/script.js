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

// Chart instances
let priorityChart = null;
let stateChart = null;
let emptyFirstResponseChart = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

function initializeEventListeners() {
    // File input change event
    fileInput.addEventListener('change', handleFileSelect);
    
    // Form submit event
    uploadForm.addEventListener('submit', handleFormSubmit);
    
    // Export buttons
    exportExcelBtn.addEventListener('click', handleExportExcel);
    exportTxtBtn.addEventListener('click', handleExportTxt);
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        // Validate file type
        const validExtensions = ['.xlsx', '.xls'];
        const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        
        if (!validExtensions.includes(fileExtension)) {
            showError('请选择Excel文件 (.xlsx 或 .xls 格式)');
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
        showError('请先选择Excel文件');
        return;
    }
    
    // Show loading state
    showLoading();
    
    // Create FormData for file upload
    const formData = new FormData();
    formData.append('file', file);
    
    // Send AJAX request
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => {
                throw new Error(errorData.error || '上传失败');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            analysisData = data;
            showResults(data);
        } else {
            throw new Error(data.error || '分析失败');
        }
    })
    .catch(error => {
        showError(error.message);
    });
}

function handleExportExcel() {
    if (!analysisData) {
        showError('没有可导出的数据');
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
                throw new Error(errorData.error || '导出失败');
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
        showError('没有可导出的数据');
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
                throw new Error(errorData.error || '导出失败');
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
    
    // Create charts
    createCharts(data.stats);
    
    // Show results section with animation
    resultsSection.style.display = 'block';
    resultsSection.classList.add('fade-in');
}

function updateDailyTable(stats) {
    const tableBody = document.querySelector('#dailyTable tbody');
    tableBody.innerHTML = '';
    
    if (stats.daily_new && stats.daily_closed) {
        const allDates = Array.from(
            new Set([...Object.keys(stats.daily_new), ...Object.keys(stats.daily_closed)])
        ).sort();
        
        allDates.forEach(date => {
            const newCount = stats.daily_new[date] || 0;
            const closedCount = stats.daily_closed[date] || 0;
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${date}</td>
                <td>${newCount}</td>
                <td>${closedCount}</td>
            `;
            tableBody.appendChild(row);
        });
    } else {
        tableBody.innerHTML = '<tr><td colspan="3" style="text-align: center;">无每日统计数据</td></tr>';
    }
}

function createCharts(stats) {
    // Destroy existing charts if they exist
    if (priorityChart) priorityChart.destroy();
    if (stateChart) stateChart.destroy();
    if (emptyFirstResponseChart) emptyFirstResponseChart.destroy();
    
    // Priority Distribution Chart
    if (stats.priority_distribution) {
        const priorityCtx = document.getElementById('priorityChart').getContext('2d');
        priorityChart = new Chart(priorityCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(stats.priority_distribution),
                datasets: [{
                    data: Object.values(stats.priority_distribution),
                    backgroundColor: [
                        '#ff6b6b', '#feca57', '#48dbfb', '#1dd1a1', '#ff9ff3'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }
    
    // State Distribution Chart
    if (stats.state_distribution) {
        const stateCtx = document.getElementById('stateChart').getContext('2d');
        stateChart = new Chart(stateCtx, {
            type: 'pie',
            data: {
                labels: Object.keys(stats.state_distribution),
                datasets: [{
                    data: Object.values(stats.state_distribution),
                    backgroundColor: [
                        '#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }
    
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
