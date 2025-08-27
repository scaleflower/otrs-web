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

// Chart instances
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
    
    // Re-upload button
    reuploadBtn.addEventListener('click', function() {
        resultsSection.style.display = 'none';
        document.querySelector('.upload-section').style.display = 'block';
        fileInput.value = '';
        fileInfo.style.display = 'none';
        uploadBtn.disabled = true;
    });
    
    // Sort order change event
    const sortOrderSelect = document.getElementById('sortOrder');
    if (sortOrderSelect) {
        sortOrderSelect.addEventListener('change', function() {
            if (analysisData && analysisData.stats.daily_new && analysisData.stats.daily_closed) {
                updateDailyTable(analysisData.stats);
            }
        });
    }
    
    // Age segment click events
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('age-clickable')) {
            const ageSegment = e.target.getAttribute('data-age-segment');
            handleAgeSegmentClick(ageSegment);
        }
    });
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
            analysisData = data;
            showResults(data);
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
    })
    .catch(error => {
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
    analysisData = data;
    
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
        const sortOrderSelect = document.getElementById('sortOrder');
        const sortOrder = sortOrderSelect ? sortOrderSelect.value : 'desc';
        
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
