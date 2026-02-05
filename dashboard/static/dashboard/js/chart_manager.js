/**
 * Chart Manager - Dashboard Visualization
 * ========================================
 * 
 * Handles all Chart.js visualizations for the financial dashboard:
 * - Gold, Silver, Oil price trend charts
 * - Bar chart for latest price comparison
 * - Pie chart for price distribution
 * - KPI cards with latest values and changes
 * - Dashboard snapshot capture and save
 */

let chart1, chart2, chart3, barChart, pieChart; // Global chart instances

// =============================================================================
// CHART INITIALIZATION
// =============================================================================

/**
 * Initialize or update all charts with new data.
 * @param {Object} data - Chart data with dates, gold, silver, oil arrays
 */
function initializeCharts(data) {
    const ctx1 = document.getElementById('chart-1')?.getContext('2d');
    const ctx2 = document.getElementById('chart-2')?.getContext('2d');
    const ctx3 = document.getElementById('chart-3')?.getContext('2d');

    if (!ctx1 || !ctx2 || !ctx3) {
        console.error('Chart canvas elements not found');
        return;
    }

    // Destroy previous charts if they exist
    if (chart1) chart1.destroy();
    if (chart2) chart2.destroy();
    if (chart3) chart3.destroy();

    // Common chart options for line charts
    const lineChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: {
                display: true,
                grid: { display: false },
                ticks: { maxTicksLimit: 6, font: { size: 10 } }
            },
            y: {
                display: true,
                grid: { color: 'rgba(0,0,0,0.05)' },
                ticks: { font: { size: 10 } }
            }
        },
        elements: {
            point: { radius: 0, hoverRadius: 4 },
            line: { tension: 0.4 }
        }
    };

    // Gold Price Chart
    chart1 = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Gold Price',
                data: data.gold,
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.15)',
                fill: true,
                borderWidth: 2
            }]
        },
        options: lineChartOptions
    });

    // Silver Price Chart
    chart2 = new Chart(ctx2, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Silver Price',
                data: data.silver,
                borderColor: '#6b7280',
                backgroundColor: 'rgba(107, 114, 128, 0.15)',
                fill: true,
                borderWidth: 2
            }]
        },
        options: lineChartOptions
    });

    // Oil Price Chart
    chart3 = new Chart(ctx3, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Oil Price',
                data: data.oil,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.15)',
                fill: true,
                borderWidth: 2
            }]
        },
        options: lineChartOptions
    });

    // Update stats cards
    updateStatsCards(data);

    // Update KPIs and comparison charts
    if (data.dates.length > 0) {
        updateKPIs(data);
        updateComparisonCharts(data);
    }
}

// =============================================================================
// STATS CARDS UPDATE
// =============================================================================

function updateStatsCards(data) {
    const totalRecords = document.getElementById('total-records');
    const lastUpdated = document.getElementById('last-updated');
    
    if (totalRecords) totalRecords.textContent = data.dates.length;
    if (lastUpdated) lastUpdated.textContent = new Date().toLocaleTimeString();
}

// =============================================================================
// KPI CARDS UPDATE
// =============================================================================

function updateKPIs(data) {
    const lastIndex = data.dates.length - 1;
    const prevIndex = lastIndex - 1 >= 0 ? lastIndex - 1 : 0;

    // Update current prices
    const kpiGold = document.getElementById('kpi-gold');
    const kpiSilver = document.getElementById('kpi-silver');
    const kpiOil = document.getElementById('kpi-oil');
    
    if (kpiGold) kpiGold.textContent = `$${data.gold[lastIndex].toFixed(2)}`;
    if (kpiSilver) kpiSilver.textContent = `$${data.silver[lastIndex].toFixed(2)}`;
    if (kpiOil) kpiOil.textContent = `$${data.oil[lastIndex].toFixed(2)}`;

    // Update dates
    const lastDate = data.dates[lastIndex];
    ['kpi-date', 'kpi-date-2', 'kpi-date-3'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = lastDate;
    });

    // Update trend current values
    const trendGold = document.getElementById('trend-current-gold');
    const trendSilver = document.getElementById('trend-current-silver');
    const trendOil = document.getElementById('trend-current-oil');
    
    if (trendGold) trendGold.textContent = `$${data.gold[lastIndex].toFixed(2)}`;
    if (trendSilver) trendSilver.textContent = `$${data.silver[lastIndex].toFixed(2)}`;
    if (trendOil) trendOil.textContent = `$${data.oil[lastIndex].toFixed(2)}`;

    // Calculate and display changes
    const goldChange = data.gold[lastIndex] - data.gold[prevIndex];
    const silverChange = data.silver[lastIndex] - data.silver[prevIndex];
    const oilChange = data.oil[lastIndex] - data.oil[prevIndex];

    updateChangeDisplay('change-gold', goldChange);
    updateChangeDisplay('change-silver', silverChange);
    updateChangeDisplay('change-oil', oilChange);
}

function updateChangeDisplay(elementId, change) {
    const el = document.getElementById(elementId);
    if (!el) return;
    
    const icon = change > 0 ? '↑' : (change < 0 ? '↓' : '→');
    const value = Math.abs(change).toFixed(2);
    el.textContent = `${icon} $${value}`;
    
    // Add color class based on change direction
    el.className = el.className.replace(/\b(positive|negative)\b/g, '');
    if (change > 0) el.classList.add('positive');
    else if (change < 0) el.classList.add('negative');
}

// =============================================================================
// COMPARISON CHARTS (BAR & PIE)
// =============================================================================

function updateComparisonCharts(data) {
    const lastIndex = data.dates.length - 1;
    const latestValues = [
        data.gold[lastIndex],
        data.silver[lastIndex],
        data.oil[lastIndex]
    ];

    // Bar Chart
    const barCtx = document.getElementById('bar-chart')?.getContext('2d');
    if (barCtx) {
        if (barChart) barChart.destroy();
        
        barChart = new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: ['Gold', 'Silver', 'Oil'],
                datasets: [{
                    label: 'Latest Price',
                    data: latestValues,
                    backgroundColor: ['#f59e0b', '#9ca3af', '#2563eb'],
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: false, grid: { color: 'rgba(0,0,0,0.05)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // Pie Chart
    const pieCtx = document.getElementById('pie-chart')?.getContext('2d');
    if (pieCtx) {
        if (pieChart) pieChart.destroy();
        
        pieChart = new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: ['Gold', 'Silver', 'Oil'],
                datasets: [{
                    data: latestValues,
                    backgroundColor: ['#f59e0b', '#9ca3af', '#2563eb'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: { position: 'bottom', labels: { padding: 20 } }
                }
            }
        });
    }
}

// =============================================================================
// DATA FETCHING
// =============================================================================

function fetchChartData() {
    fetch('/dashboard/api/chart-data/')
        .then(res => {
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            return res.json();
        })
        .then(data => {
            if (data.error) {
                console.error('API error:', data.error);
                return;
            }
            initializeCharts(data);
        })
        .catch(err => console.error('Error fetching chart data:', err));
}

// =============================================================================
// CSRF TOKEN
// =============================================================================

function getCSRFToken() {
    // Try form input first
    const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (tokenInput) return tokenInput.value;
    
    // Fallback to cookie
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

// =============================================================================
// SNAPSHOT CAPTURE & SAVE
// =============================================================================

/**
 * Capture dashboard as image and save to server.
 * Also downloads a local copy for the user.
 */
async function captureAndSaveSnapshot() {
    const dashboardElement = document.getElementById('dashboard-container');
    const snapshotBtn = document.getElementById('saveSnapshotBtn');
    const aiContainer = document.querySelector('.ai-container');
    const aiMediaFrame = document.getElementById('ai-media-frame');
    const aiMediaEmpty = document.getElementById('ai-media-empty');
    const aiMediaMeta = document.getElementById('ai-media-meta');
    
    if (!dashboardElement) {
        console.error('Dashboard container not found');
        return;
    }

    // Update button state
    const originalBtnContent = snapshotBtn?.innerHTML;
    if (snapshotBtn) {
        snapshotBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Capturing...</span>';
        snapshotBtn.disabled = true;
    }

    try {
        // Enable snapshot mode for cleaner image
        document.body.classList.add('snapshot-mode');
        
        // Wait for styles to apply
        await new Promise(resolve => setTimeout(resolve, 100));

        // Capture with html2canvas
        const canvas = await html2canvas(dashboardElement, {
            scale: 2,
            useCORS: true,
            backgroundColor: '#ffffff',
            logging: false,
            removeContainer: false
        });

        // Convert to data URL
        const imageData = canvas.toDataURL('image/png', 0.95);

        // Save to server
        const response = await fetch('/dashboard/save-snapshot/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ image: imageData })
        });

        if (!response.ok) {
            // Try to get a helpful error message from the response
            let text = await response.text().catch(() => '');
            text = text ? `: ${text}` : '';
            showNotification(`Failed to save snapshot (HTTP ${response.status})${text}`, 'error');
            console.error('Snapshot save failed:', response.status, text);
            return;
        }

        const data = await response.json();

        if (data.status === 'success') {
            // Show success message
            showNotification('Snapshot saved successfully! AI analysis will be generated.', 'success');

            if (aiContainer && data.snapshot_id) {
                aiContainer.dataset.snapshotId = data.snapshot_id;
            }

            if (aiMediaFrame && data.image_url) {
                let imageEl = document.getElementById('ai-media-image');

                if (!imageEl) {
                    imageEl = document.createElement('img');
                    imageEl.className = 'ai-media-image';
                    imageEl.id = 'ai-media-image';
                    imageEl.alt = '';
                    aiMediaFrame.innerHTML = '';
                    aiMediaFrame.appendChild(imageEl);
                }

                const cacheBustedUrl = `${data.image_url}${data.image_url.includes('?') ? '&' : '?'}v=${Date.now()}`;
                imageEl.src = cacheBustedUrl;
            }

            if (aiMediaEmpty) {
                aiMediaEmpty.remove();
            }

            if (aiMediaMeta && data.created_at) {
                const capturedTime = new Date(data.created_at);
                if (!Number.isNaN(capturedTime.getTime())) {
                    aiMediaMeta.textContent = `Last captured: ${capturedTime.toLocaleString()}`;
                }
            }

            window.dispatchEvent(new CustomEvent('snapshot:saved', {
                detail: {
                    snapshotId: data.snapshot_id,
                    imageUrl: data.image_url,
                    createdAt: data.created_at
                }
            }));
            
            // Also download locally
            const link = document.createElement('a');
            link.download = `dashboard-snapshot-${Date.now()}.png`;
            link.href = imageData;
            link.click();
        } else {
            showNotification('Failed to save snapshot: ' + (data.error || 'Unknown error'), 'error');
        }

    } catch (error) {
        console.error('Snapshot error:', error);
        showNotification('Error capturing snapshot: ' + error.message, 'error');
    } finally {
        // Restore normal mode
        document.body.classList.remove('snapshot-mode');
        
        // Restore button
        if (snapshotBtn) {
            snapshotBtn.innerHTML = originalBtnContent;
            snapshotBtn.disabled = false;
        }
    }
}

/**
 * Show a toast notification.
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `snapshot-notification ${type}`;
    notification.innerHTML = `
        <span class="notification-icon">${type === 'success' ? '✅' : '❌'}</span>
        <span class="notification-text">${message}</span>
    `;
    
    // Add styles if not present
    if (!document.getElementById('notification-styles')) {
        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.textContent = `
            .snapshot-notification {
                position: fixed;
                bottom: 20px;
                right: 20px;
                padding: 16px 24px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                gap: 12px;
                font-size: 14px;
                font-weight: 500;
                z-index: 10000;
                animation: slideIn 0.3s ease, fadeOut 0.3s ease 3.7s forwards;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
            }
            
            .snapshot-notification.success {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
            }
            
            .snapshot-notification.error {
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                color: white;
            }
            
            .notification-icon { font-size: 18px; }
            
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; visibility: hidden; }
            }
        `;
        document.head.appendChild(styles);
    }
    
    document.body.appendChild(notification);
    
    // Remove after 4 seconds
    setTimeout(() => notification.remove(), 4000);
}

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts with data from template or fetch
    if (typeof chartData !== 'undefined' && chartData) {
        initializeCharts(chartData);
    } else {
        fetchChartData();
    }
    
    // Auto-refresh every 10 seconds
    setInterval(fetchChartData, 10000);

    // Snapshot button handler
    const snapshotBtn = document.getElementById('saveSnapshotBtn');
    if (snapshotBtn) {
        snapshotBtn.addEventListener('click', captureAndSaveSnapshot);
    }
});

// Expose functions for console debugging
window.chartManager = {
    refresh: fetchChartData,
    snapshot: captureAndSaveSnapshot
};
