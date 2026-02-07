// PacketBuddy Enhanced Dashboard JavaScript

const API_BASE = 'http://127.0.0.1:7373/api';

let monthlyChart = null;
let pieChart = null;
let currentMonth = new Date();
currentMonth.setDate(1); // Fix: Set to 1st of month to avoid rollover bugs when navigating from 31st
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
    document.getElementById('html-export-btn').addEventListener('click', () => {
        window.location.href = '/api/export?format=html';
    });
    document.getElementById('llm-export-btn').addEventListener('click', () => {
        window.location.href = '/api/export/llm';
    });

    document.getElementById('prev-month').addEventListener('click', () => {
        console.log('Previous month clicked');
        currentMonth.setDate(1); // Enforce first day
        currentMonth.setMonth(currentMonth.getMonth() - 1);
        loadMonthlyData();
    });

    document.getElementById('next-month').addEventListener('click', () => {
        console.log('Next month clicked');
        currentMonth.setDate(1); // Enforce first day
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
        // FIX: Always use server's peak_speed as source of truth to prevent reset on page refresh
        if (displayData.peak_speed !== undefined && displayData.peak_speed !== null) {
            // Set peakSpeed to server value (this fixes the reset issue)
            peakSpeed = displayData.peak_speed;

            // Display the peak speed
            if (displayData.human_readable && displayData.human_readable.peak_speed) {
                document.getElementById('peak-speed').textContent = displayData.human_readable.peak_speed;
            } else if (peakSpeed > 0) {
                document.getElementById('peak-speed').textContent = formatBytes(peakSpeed) + '/s';
            }
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
    const primaryTeal = 'hsl(170, 70%, 42%)';
    const accentPink = 'hsl(340, 60%, 60%)';
    const textColor = 'hsl(200, 25%, 90%)';
    const mutedColor = 'hsl(200, 15%, 55%)';
    const gridColor = 'hsla(180, 20%, 18%, 0.3)';

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                backgroundColor: 'hsla(240, 10%, 11%, 0.95)',
                titleColor: textColor,
                bodyColor: textColor,
                borderColor: primaryTeal,
                borderWidth: 1,
                padding: 12,
                cornerRadius: 12,
                displayColors: true,
                titleFont: {
                    family: "'Nunito', sans-serif",
                    size: 14,
                    weight: '800'
                },
                bodyFont: {
                    family: "'Nunito', sans-serif",
                    size: 13,
                    weight: '600'
                }
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
                    backgroundColor: 'hsla(340, 60%, 60%, 0.8)',
                    borderColor: accentPink,
                    borderWidth: 0,
                    borderRadius: 6
                },
                {
                    label: 'Download',
                    data: [],
                    backgroundColor: 'hsla(170, 70%, 42%, 0.8)',
                    borderColor: primaryTeal,
                    borderWidth: 0,
                    borderRadius: 6
                }
            ]
        },
        options: {
            ...commonOptions,
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: mutedColor,
                        font: {
                            family: "'Nunito', sans-serif",
                            weight: '700'
                        }
                    }
                },
                y: {
                    grid: {
                        color: gridColor
                    },
                    ticks: {
                        color: mutedColor,
                        font: {
                            family: "'Nunito', sans-serif",
                            weight: '700'
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
                    accentPink,
                    primaryTeal
                ],
                borderWidth: 0,
                hoverOffset: 15
            }]
        },
        options: {
            ...commonOptions,
            cutout: '75%',
            plugins: {
                ...commonOptions.plugins
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
