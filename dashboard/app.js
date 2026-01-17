// PacketBuddy Enhanced Dashboard JavaScript

const API_BASE = 'http://127.0.0.1:7373/api';

let monthlyChart = null;
let pieChart = null;
let currentMonth = new Date();
let peakSpeed = 0;
let refreshIntervals = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    loadDeviceInfo();
    startDataRefresh();
    setupEventListeners();
    updateClock();
    setInterval(updateClock, 1000);
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadAllData();
        showNotification('Data refreshed', 'success');
    });
    document.getElementById('export-btn').addEventListener('click', () => {
        window.location.href = '/api/export?format=csv';
    });
    document.getElementById('llm-export-btn').addEventListener('click', () => {
        window.location.href = '/api/export/llm';
    });

    document.getElementById('prev-month').addEventListener('click', () => {
        currentMonth.setMonth(currentMonth.getMonth() - 1);
        loadMonthlyData();
    });

    document.getElementById('next-month').addEventListener('click', () => {
        currentMonth.setMonth(currentMonth.getMonth() + 1);
        loadMonthlyData();
    });
}

// Clear all refresh intervals
function clearAllIntervals() {
    refreshIntervals.forEach(id => clearInterval(id));
    refreshIntervals = [];
}

// Start data refresh
function startDataRefresh() {
    clearAllIntervals();

    // Load initial data
    loadAllData();

    // Set up intervals
    refreshIntervals.push(setInterval(loadLiveStats, 2000)); // Live stats every 2s
    refreshIntervals.push(setInterval(loadTodayStats, 30000)); // Today every 30s
    refreshIntervals.push(setInterval(loadLifetimeStats, 60000)); // Lifetime every 60s
}

// Load all data
function loadAllData() {
    loadLiveStats();
    loadTodayStats();
    loadLifetimeStats();
    loadMonthlyData();
}

// Update clock
function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
    const elem = document.getElementById('current-time');
    if (elem) elem.textContent = timeStr;
}

// Load device info
async function loadDeviceInfo() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        document.getElementById('device-name').textContent = data.hostname;

        // Update version info
        if (data.version) {
            const versionElem = document.getElementById('app-version');
            if (versionElem) versionElem.textContent = 'v' + data.version;

            // Show release date
            const releaseDateElem = document.getElementById('release-date');
            if (releaseDateElem && data.timestamp) {
                const releaseDate = new Date(data.timestamp);
                const formattedDate = releaseDate.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                });
                releaseDateElem.textContent = ` • Released ${formattedDate}`;
            }
        }

        // Update active device count if provided
        if (data.device_count) {
            const countElem = document.getElementById('device-count');
            if (countElem) countElem.textContent = data.device_count;
        }

        updateLastUpdate();
    } catch (error) {
        console.error('Failed to load device info:', error);
        document.getElementById('device-name').textContent = 'Offline';
    }
}

// Load live stats
async function loadLiveStats() {
    try {
        const response = await fetch(`${API_BASE}/live`);
        const data = await response.json();

        const uploadSpeed = data.bytes_sent;
        const downloadSpeed = data.bytes_received;

        // Update values
        document.getElementById('live-upload').textContent = data.human_readable.sent + '/s';
        document.getElementById('live-download').textContent = data.human_readable.received + '/s';

        // Update progress bars
        const maxSpeed = Math.max(uploadSpeed, downloadSpeed, 1000000); // Min 1MB for scale
        const uploadPercent = (uploadSpeed / maxSpeed) * 100;
        const downloadPercent = (downloadSpeed / maxSpeed) * 100;

        document.getElementById('upload-bar').style.width = uploadPercent + '%';
        document.getElementById('download-bar').style.width = downloadPercent + '%';

        // Track peak speed
        const totalSpeed = uploadSpeed + downloadSpeed;
        if (totalSpeed > peakSpeed) {
            peakSpeed = totalSpeed;
            document.getElementById('peak-speed').textContent = formatBytes(peakSpeed) + '/s';
        }

        updateLastUpdate();
    } catch (error) {
        console.error('Failed to load live stats:', error);
    }
}

// Load today's stats
async function loadTodayStats() {
    try {
        const response = await fetch(`${API_BASE}/today`);
        const data = await response.json();

        // Use global data if available for total stitching
        const displayData = data.global || data;

        document.getElementById('today-upload').textContent = displayData.human_readable.sent;
        document.getElementById('today-download').textContent = displayData.human_readable.received;
        document.getElementById('today-total').textContent = displayData.human_readable.total;

        // Update badge to show if we're seeing global or local
        const todayHeader = document.querySelector('.stats-grid .card:nth-child(2) .badge, .stats-grid .card:nth-child(2) .time-badge');
        if (todayHeader) todayHeader.textContent = data.global ? 'Total Network' : 'This Device';

        // Update peak speed from server today stats if available
        if (displayData.peak_speed && displayData.peak_speed > peakSpeed) {
            peakSpeed = displayData.peak_speed;
            document.getElementById('peak-speed').textContent = displayData.human_readable.peak_speed;
        }

        // Display cost data
        if (displayData.cost && displayData.cost.total) {
            document.getElementById('today-cost').textContent = displayData.cost.total.cost_formatted;
        }

        // Update pie chart
        updatePieChart(data.bytes_sent, data.bytes_received);

        // Update percentages
        const total = data.bytes_sent + data.bytes_received;
        if (total > 0) {
            const uploadPercent = ((data.bytes_sent / total) * 100).toFixed(1);
            const downloadPercent = ((data.bytes_received / total) * 100).toFixed(1);
            document.getElementById('upload-percent').textContent = uploadPercent + '%';
            document.getElementById('download-percent').textContent = downloadPercent + '%';
        }

        updateLastUpdate();
    } catch (error) {
        console.error('Failed to load today stats:', error);
    }
}

// Load lifetime stats
async function loadLifetimeStats() {
    try {
        const response = await fetch(`${API_BASE}/summary`);
        const data = await response.json();

        // Use global data if available for total stitching
        const displayData = data.global || data;

        document.getElementById('lifetime-upload').textContent = displayData.human_readable.sent;
        document.getElementById('lifetime-download').textContent = displayData.human_readable.received;
        document.getElementById('lifetime-total').textContent = displayData.human_readable.total;

        // Update badge
        const lifetimeBadge = document.querySelector('.stats-grid .card:nth-child(3) .badge');
        if (lifetimeBadge) {
            lifetimeBadge.textContent = data.global ? 'Total Network' : 'This Device';
        }

        // Display lifetime cost data
        if (displayData.cost && displayData.cost.total) {
            const costElem = document.getElementById('lifetime-cost');
            if (costElem) costElem.textContent = displayData.cost.total.cost_formatted;
        }

        // Calculate average daily usage (estimate)
        const totalBytes = data.total_bytes;
        const avgDaily = totalBytes / 30; // Rough estimate
        document.getElementById('avg-daily').textContent = formatBytes(avgDaily);

        updateLastUpdate();
    } catch (error) {
        console.error('Failed to load lifetime stats:', error);
    }
}

// Load monthly data
async function loadMonthlyData() {
    const monthStr = formatMonth(currentMonth);
    document.getElementById('current-month').textContent = formatMonthDisplay(currentMonth);

    try {
        const response = await fetch(`${API_BASE}/month?month=${monthStr}`);
        const data = await response.json();

        updateMonthlyChart(data.days);

        // Update data points counter
        document.getElementById('data-points').textContent = data.days.length;
    } catch (error) {
        console.error('Failed to load monthly data:', error);
    }
}

// Format month as YYYY-MM
function formatMonth(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    return `${year}-${month}`;
}

// Format month for display
function formatMonthDisplay(date) {
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long'
    });
}

// Initialize charts
function initCharts() {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
                labels: {
                    color: '#e2e8f0',
                    font: {
                        family: 'Inter, sans-serif',
                        size: 12
                    }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(26, 31, 53, 0.95)',
                titleColor: '#e2e8f0',
                bodyColor: '#94a3b8',
                borderColor: 'rgba(99, 102, 241, 0.3)',
                borderWidth: 1,
                padding: 12,
                cornerRadius: 8,
                displayColors: true
            }
        }
    };

    // Monthly chart
    const monthlyCtx = document.getElementById('monthly-chart').getContext('2d');
    monthlyChart = new Chart(monthlyCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Upload',
                    data: [],
                    backgroundColor: 'rgba(139, 92, 246, 0.8)',
                    borderColor: 'rgba(139, 92, 246, 1)',
                    borderWidth: 2,
                    borderRadius: 6
                },
                {
                    label: 'Download',
                    data: [],
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 2,
                    borderRadius: 6
                }
            ]
        },
        options: {
            ...commonOptions,
            scales: {
                x: {
                    grid: {
                        color: 'rgba(99, 102, 241, 0.05)',
                        borderColor: 'rgba(99, 102, 241, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8',
                        font: {
                            family: 'Inter, sans-serif'
                        }
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(99, 102, 241, 0.05)',
                        borderColor: 'rgba(99, 102, 241, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8',
                        font: {
                            family: 'Inter, sans-serif'
                        },
                        callback: function (value) {
                            return formatBytes(value);
                        }
                    }
                }
            }
        }
    });

    // Pie chart
    const pieCtx = document.getElementById('pie-chart').getContext('2d');
    pieChart = new Chart(pieCtx, {
        type: 'doughnut',
        data: {
            labels: ['Upload', 'Download'],
            datasets: [{
                data: [0, 0],
                backgroundColor: [
                    'rgba(139, 92, 246, 0.8)',
                    'rgba(59, 130, 246, 0.8)'
                ],
                borderColor: [
                    'rgba(139, 92, 246, 1)',
                    'rgba(59, 130, 246, 1)'
                ],
                borderWidth: 2,
                hoverOffset: 10
            }]
        },
        options: {
            ...commonOptions,
            cutout: '70%',
            plugins: {
                ...commonOptions.plugins,
                legend: {
                    display: false
                }
            }
        }
    });
}

// Update monthly chart
function updateMonthlyChart(days) {
    const labels = days.map(d => {
        const date = new Date(d.date);
        return date.getDate();
    });

    const uploadData = days.map(d => d.bytes_sent);
    const downloadData = days.map(d => d.bytes_received);

    monthlyChart.data.labels = labels;
    monthlyChart.data.datasets[0].data = uploadData;
    monthlyChart.data.datasets[1].data = downloadData;
    monthlyChart.update('active');
}

// Update pie chart
function updatePieChart(sent, received) {
    pieChart.data.datasets[0].data = [sent, received];
    pieChart.update('active');
}

// Format bytes helper
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';

    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const k = 1000;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const size = bytes / Math.pow(k, i);

    return (i === 0 ? Math.round(size) : size.toFixed(2)) + ' ' + units[i];
}

// Update last update time
function updateLastUpdate() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    const elem = document.getElementById('last-update');
    if (elem) elem.textContent = timeStr;
}

// Show notification (simple implementation)
function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // You could add a toast notification system here
}
