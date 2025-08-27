// results.js - JavaScript for the results page

document.addEventListener('DOMContentLoaded', function() {
    // Show upload page when upload button is clicked
    document.getElementById('showUploadBtn').addEventListener('click', function() {
        window.location.href = '/upload';
    });

    // Check if there's any stored analysis data to display
    const storedData = localStorage.getItem('otrsAnalysisData');
    if (storedData) {
        try {
            const analysisData = JSON.parse(storedData);
            displayResults(analysisData);
        } catch (e) {
            console.error('Error parsing stored analysis data:', e);
            localStorage.removeItem('otrsAnalysisData');
        }
    }

    // Handle browser back button
    window.addEventListener('popstate', function(event) {
        if (event.state && event.state.page === 'results') {
            // Refresh the page if coming back to results
            window.location.reload();
        }
    });
});

function displayResults(analysisData) {
    // Hide placeholder and show results section
    document.querySelector('.results-placeholder').style.display = 'none';
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.style.display = 'block';

    // Populate summary cards
    document.getElementById('totalRecords').textContent = analysisData.total_records.toLocaleString();
    document.getElementById('openTickets').textContent = analysisData.stats.current_open_count.toLocaleString();
    document.getElementById('emptyFirstResponse').textContent = analysisData.stats.empty_firstresponse_count.toLocaleString();

    // Populate daily statistics table
    populateDailyTable(analysisData.stats);

    // Populate age segments
    if (analysisData.stats.age_segments) {
        document.getElementById('age24h').textContent = analysisData.stats.age_segments.age_24h.toLocaleString();
        document.getElementById('age24_48h').textContent = analysisData.stats.age_segments.age_24_48h.toLocaleString();
        document.getElementById('age48_72h').textContent = analysisData.stats.age_segments.age_48_72h.toLocaleString();
        document.getElementById('age72h').textContent = analysisData.stats.age_segments.age_72h.toLocaleString();
    }

    // Setup age segment click handlers
    setupAgeSegmentHandlers(analysisData.session_id);

    // Setup export buttons
    setupExportButtons(analysisData);

    // Add re-upload functionality
    setupReuploadButton();
}

function populateDailyTable(stats) {
    const dailyTable = document.getElementById('dailyTable');
    const tbody = dailyTable.querySelector('tbody');
    tbody.innerHTML = '';

    if (stats.daily_new && stats.daily_closed) {
        // Get all unique dates
        const allDates = Object.keys(stats.daily_new).concat(Object.keys(stats.daily_closed))
            .filter((date, index, array) => array.indexOf(date) === index);
        
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
        
        // Now sort dates in descending order for display
        const sortedDatesDesc = [...allDates].sort((a, b) => new Date(b) - new Date(a));
        
        // Display the table with correct cumulative values
        sortedDatesDesc.forEach(date => {
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
    }
}

function setupAgeSegmentHandlers(sessionId) {
    const ageCells = document.querySelectorAll('.age-clickable');
    ageCells.forEach(cell => {
        cell.addEventListener('click', function() {
            const ageSegment = this.getAttribute('data-age-segment');
            getAgeDetails(ageSegment, sessionId);
        });
    });
}

function getAgeDetails(ageSegment, sessionId) {
    fetch('/age-details', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            age_segment: ageSegment,
            session_id: sessionId
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
            <td>${detail.ticket_number}</td>
            <td>${detail.age}</td>
            <td>${detail.created}</td>
            <td>${detail.priority}</td>
        `;
        tbody.appendChild(row);
    });
    
    container.style.display = 'block';
}

function setupExportButtons(analysisData) {
    document.getElementById('exportExcel').addEventListener('click', function() {
        exportToExcel(analysisData);
    });

    document.getElementById('exportTxt').addEventListener('click', function() {
        exportToTxt(analysisData);
    });
}

function exportToExcel(analysisData) {
    fetch('/export/excel', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(analysisData)
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
        a.download = `otrs_analysis_${new Date().toISOString().slice(0, 10)}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error exporting to Excel: ' + error.message);
    });
}

function exportToTxt(analysisData) {
    fetch('/export/txt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(analysisData)
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
        a.download = `otrs_analysis_${new Date().toISOString().slice(0, 10)}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error exporting to text: ' + error.message);
    });
}

function setupReuploadButton() {
    document.getElementById('reuploadBtn').addEventListener('click', function() {
        window.location.href = '/upload';
    });
}

// Function to handle analysis completion (called from upload page)
function handleAnalysisComplete(analysisData) {
    // Store data in localStorage for persistence
    localStorage.setItem('otrsAnalysisData', JSON.stringify(analysisData));
    
    // Update browser history
    window.history.pushState({ page: 'results' }, '', '/');
    
    // Display results
    displayResults(analysisData);
}
