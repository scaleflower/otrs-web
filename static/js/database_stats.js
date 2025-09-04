// database_stats.js - JavaScript for the database statistics page

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the page
    initializePage();
    
    // Setup refresh button
    document.getElementById('refreshBtn').addEventListener('click', function() {
        loadDatabaseStats();
    });
    
    // Setup export buttons
    setupExportButtons();
    
    // Setup age segment click handlers
    setupAgeSegmentHandlers();
    
    // Setup sort order change handler
    const sortOrderSelect = document.getElementById('sortOrder');
    if (sortOrderSelect) {
        console.log('Found sortOrder select element');
        sortOrderSelect.addEventListener('change', function() {
            console.log('Sort order changed to:', this.value);
            populateDailyTable(window.currentStats);
        });
    } else {
        console.error('sortOrder select element not found!');
    }
});

function initializePage() {
    // Show loading state
    showLoading();
    
    // Load database statistics
    loadDatabaseStats();
}

function showLoading() {
    document.getElementById('loadingSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('emptyDatabaseSection').style.display = 'none';
    document.getElementById('databaseInfoSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';
}

function showError(message) {
    document.getElementById('loadingSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('emptyDatabaseSection').style.display = 'none';
    document.getElementById('databaseInfoSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
}

function hideError() {
    document.getElementById('errorSection').style.display = 'none';
    initializePage();
}

function loadDatabaseStats() {
    showLoading();
    
    fetch('/database-stats', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            if (data.total_records === 0) {
                showEmptyDatabase();
            } else {
                displayResults(data);
            }
        } else {
            showError(data.error || 'Failed to load database statistics');
        }
    })
    .catch(error => {
        console.error('Error loading database stats:', error);
        showError('Error loading database statistics: ' + error.message);
    });
}

function showEmptyDatabase() {
    document.getElementById('loadingSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('emptyDatabaseSection').style.display = 'block';
    document.getElementById('databaseInfoSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';
}

function displayResults(data) {
    // Store current stats for later use
    window.currentStats = data;
    
    // Hide loading and show results
    document.getElementById('loadingSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';
    document.getElementById('emptyDatabaseSection').style.display = 'none';
    document.getElementById('databaseInfoSection').style.display = 'block';
    document.getElementById('errorSection').style.display = 'none';
    
    // Update database info
    document.getElementById('totalRecordsInfo').textContent = data.total_records.toLocaleString();
    document.getElementById('dataSourcesInfo').textContent = data.data_sources_count.toLocaleString();
    document.getElementById('lastUpdatedInfo').textContent = data.last_updated || 'Never';
    
    // Populate summary cards
    document.getElementById('totalRecords').textContent = data.total_records.toLocaleString();
    document.getElementById('openTickets').textContent = data.stats.current_open_count.toLocaleString();
    document.getElementById('emptyFirstResponse').textContent = data.stats.empty_firstresponse_count.toLocaleString();
    
    // Populate daily statistics table
    populateDailyTable(data.stats);
    
    // Populate age segments
    if (data.stats.age_segments) {
        document.getElementById('age24h').textContent = data.stats.age_segments.age_24h.toLocaleString();
        document.getElementById('age24_48h').textContent = data.stats.age_segments.age_24_48h.toLocaleString();
        document.getElementById('age48_72h').textContent = data.stats.age_segments.age_48_72h.toLocaleString();
        document.getElementById('age72h').textContent = data.stats.age_segments.age_72h.toLocaleString();
    }
    
    // Populate priority distribution
    populatePriorityTable(data.stats.priority_distribution);
    
    // Populate state distribution
    populateStateTable(data.stats.state_distribution);
    
    // Populate empty first response details
    populateEmptyFirstResponseTable(data.empty_firstresponse_details || []);
}

function populateDailyTable(stats) {
    console.log('populateDailyTable called with sort order:', document.getElementById('sortOrder').value);
    
    const dailyTable = document.getElementById('dailyTable');
    const tbody = dailyTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    if (stats.daily_new && stats.daily_closed) {
        // Get all unique dates
        const allDates = Object.keys(stats.daily_new).concat(Object.keys(stats.daily_closed))
            .filter((date, index, array) => array.indexOf(date) === index);
        
        // Get sort order
        const sortOrder = document.getElementById('sortOrder').value;
        console.log('Available dates:', allDates);
        
        // First, always calculate cumulative values from earliest to latest (chronological order)
        const allDatesAsc = [...allDates].sort((a, b) => new Date(a) - new Date(b));
        const cumulativeByDate = {};
        let cumulativeOpen = 0;
        
        // Calculate cumulative open tickets chronologically
        allDatesAsc.forEach(date => {
            const newCount = stats.daily_new[date] || 0;
            const closedCount = stats.daily_closed[date] || 0;
            cumulativeOpen = cumulativeOpen + newCount - closedCount;
            cumulativeByDate[date] = cumulativeOpen;
        });
        
        // Now sort dates for display based on user preference
        const displayDates = [...allDates].sort((a, b) => {
            const dateA = new Date(a);
            const dateB = new Date(b);
            return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
        });
        
        console.log('Display dates order:', displayDates);
        
        // Display the table with correct cumulative values
        displayDates.forEach(date => {
            const newCount = stats.daily_new[date] || 0;
            const closedCount = stats.daily_closed[date] || 0;
            const cumulativeOpen = cumulativeByDate[date] || 0;
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${date}</td>
                <td>${newCount.toLocaleString()}</td>
                <td>${closedCount.toLocaleString()}</td>
                <td>${cumulativeOpen.toLocaleString()}</td>
            `;
            tbody.appendChild(row);
        });
    } else {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center;">无每日统计数据</td></tr>';
    }
}

function populatePriorityTable(priorityDistribution) {
    const priorityTable = document.getElementById('priorityTable');
    const tbody = priorityTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    if (priorityDistribution) {
        Object.entries(priorityDistribution).forEach(([priority, count]) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${priority || 'Unknown'}</td>
                <td>${count.toLocaleString()}</td>
            `;
            tbody.appendChild(row);
        });
    }
}

function populateStateTable(stateDistribution) {
    const stateTable = document.getElementById('stateTable');
    const tbody = stateTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    if (stateDistribution) {
        Object.entries(stateDistribution).forEach(([state, count]) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${state || 'Unknown'}</td>
                <td>${count.toLocaleString()}</td>
            `;
            tbody.appendChild(row);
        });
    }
}

function populateEmptyFirstResponseTable(details) {
    const table = document.getElementById('emptyFirstResponseTable');
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';
    
    details.forEach(detail => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${detail.ticket_number || 'N/A'}</td>
            <td>${detail.age || 'N/A'}</td>
            <td>${detail.created || 'N/A'}</td>
            <td>${detail.priority || 'N/A'}</td>
            <td>${detail.state || 'N/A'}</td>
        `;
        tbody.appendChild(row);
    });
}

function setupAgeSegmentHandlers() {
    const ageCells = document.querySelectorAll('.age-clickable');
    ageCells.forEach(cell => {
        cell.addEventListener('click', function() {
            const ageSegment = this.getAttribute('data-age-segment');
            getAgeDetails(ageSegment);
        });
    });
}

function getAgeDetails(ageSegment) {
    fetch('/age-details', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            age_segment: ageSegment
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAgeDetails(data.details);
        } else {
            alert('Error loading age details: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error loading age details');
    });
}

function showAgeDetails(details) {
    const container = document.getElementById('ageDetailsContainer');
    const table = document.getElementById('ageDetailsTable');
    const tbody = table.querySelector('tbody');
    
    tbody.innerHTML = '';
    
    details.forEach(detail => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${detail.ticket_number || 'N/A'}</td>
            <td>${detail.age || 'N/A'}</td>
            <td>${detail.created || 'N/A'}</td>
            <td>${detail.priority || 'N/A'}</td>
        `;
        tbody.appendChild(row);
    });
    
    container.style.display = 'block';
}

function setupExportButtons() {
    document.getElementById('exportExcel').addEventListener('click', function() {
        exportToExcel();
    });

    document.getElementById('exportTxt').addEventListener('click', function() {
        exportToTxt();
    });
}

function exportToExcel() {
    if (!window.currentStats) {
        alert('No data available to export');
        return;
    }
    
    fetch('/export/excel', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            stats: window.currentStats.stats,
            total_records: window.currentStats.total_records
        })
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Export failed');
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `otrs_database_analysis_${new Date().toISOString().slice(0, 10)}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error exporting to Excel: ' + error.message);
    });
}

function exportToTxt() {
    if (!window.currentStats) {
        alert('No data available to export');
        return;
    }
    
    fetch('/export/txt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            stats: window.currentStats.stats,
            total_records: window.currentStats.total_records
        })
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Export failed');
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `otrs_database_analysis_${new Date().toISOString().slice(0, 10)}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error exporting to text: ' + error.message);
    });
}
