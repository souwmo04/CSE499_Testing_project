let chart1, chart2, chart3; // Global variables to store Chart instances 

// Function to initialize or update charts
function initializeCharts(data) {
    const ctx1 = document.getElementById('chart-1').getContext('2d');
    const ctx2 = document.getElementById('chart-2').getContext('2d');
    const ctx3 = document.getElementById('chart-3').getContext('2d');

    // Destroy previous charts if they exist
    if (chart1) chart1.destroy();
    if (chart2) chart2.destroy();
    if (chart3) chart3.destroy();

    // Gold chart
    chart1 = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Gold Price',
                data: data.gold,
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.2)',
                tension: 0.3
            }]
        },
        options: { responsive: true }
    });

    // Silver chart
    chart2 = new Chart(ctx2, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Silver Price',
                data: data.silver,
                borderColor: '#6b7280',
                backgroundColor: 'rgba(107,114,128,0.2)',
                tension: 0.3
            }]
        },
        options: { responsive: true }
    });

    // Oil chart
    chart3 = new Chart(ctx3, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Oil Price',
                data: data.oil,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37,99,235,0.2)',
                tension: 0.3
            }]
        },
        options: { responsive: true }
    });

    // Update stats cards
    const totalRecords = document.getElementById('total-records');
    const lastUpdated = document.getElementById('last-updated');
    if (totalRecords) totalRecords.textContent = data.dates.length;
    if (lastUpdated) lastUpdated.textContent = new Date().toLocaleTimeString();
}

// Function to fetch latest chart data from Django API
function fetchChartData() {
    fetch('/dashboard/api/chart-data/')
        .then(response => response.json())
        .then(data => initializeCharts(data))
        .catch(error => console.error('Error fetching chart data:', error));
}

// Safe CSRF token getter
function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!token) {
        console.error("CSRF token not found in DOM");
        return '';
    }
    return token.value;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    fetchChartData();           // Initial load
    setInterval(fetchChartData, 10000); // Refresh every 10 seconds

    // Attach snapshot button listener safely
    const snapshotBtn = document.getElementById('saveSnapshotBtn');
    if (!snapshotBtn) {
        console.warn("Save Snapshot button not found");
        return;
    }

    snapshotBtn.addEventListener('click', () => {
        // Get all chart canvases
        const c1 = document.getElementById('chart-1');
        const c2 = document.getElementById('chart-2');
        const c3 = document.getElementById('chart-3');

        if (!c1 || !c2 || !c3) {
            alert("Charts are not ready yet");
            return;
        }

        // Create a new temporary canvas to combine all charts
        const combinedCanvas = document.createElement('canvas');
        const width = Math.max(c1.width, c2.width, c3.width);
        const height = c1.height + c2.height + c3.height;
        combinedCanvas.width = width;
        combinedCanvas.height = height;
        const ctx = combinedCanvas.getContext('2d');

        // Draw each chart onto the combined canvas
        ctx.drawImage(c1, 0, 0);
        ctx.drawImage(c2, 0, c1.height);
        ctx.drawImage(c3, 0, c1.height + c2.height);

        // Convert combined canvas to image
        const imageData = combinedCanvas.toDataURL('image/png');

        // Send to backend
        fetch('/dashboard/save-snapshot/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ image: imageData })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                alert("Snapshot saved successfully!");
            } else {
                alert("Failed to save snapshot: " + (data.error || ""));
            }
        })
        .catch(err => {
            console.error(err);
            alert("Failed to save snapshot");
        });
    });
});
