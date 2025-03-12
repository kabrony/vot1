/**
 * VOT1 Memory Chart Visualization
 * 
 * Uses Chart.js to visualize memory usage statistics
 */

let memoryChart = null;

// Initialize the memory chart
function initMemoryChart() {
    const ctx = document.getElementById('memory-chart');
    
    if (!ctx) {
        console.error('Memory chart canvas element not found');
        return;
    }
    
    // Initial empty data
    const data = {
        labels: ['Conversation', 'Semantic'],
        datasets: [{
            label: 'Memory Items',
            data: [0, 0],
            backgroundColor: [
                'rgba(54, 162, 235, 0.6)',
                'rgba(255, 99, 132, 0.6)'
            ],
            borderColor: [
                'rgba(54, 162, 235, 1)',
                'rgba(255, 99, 132, 1)'
            ],
            borderWidth: 1
        }]
    };
    
    // Chart configuration
    const config = {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.8)'
                    }
                },
                title: {
                    display: true,
                    text: 'Memory Distribution',
                    color: 'rgba(255, 255, 255, 0.9)',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} items (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };
    
    // Create the chart
    memoryChart = new Chart(ctx, config);
}

// Update the memory chart with new data
function updateMemoryChart(stats) {
    if (!memoryChart) {
        initMemoryChart();
        if (!memoryChart) return; // Exit if initialization failed
    }
    
    // Update chart data
    memoryChart.data.datasets[0].data = [
        stats.conversation_items || 0,
        stats.semantic_items || 0
    ];
    
    // Update total count in title
    const total = stats.conversation_items + stats.semantic_items;
    memoryChart.options.plugins.title.text = `Memory Distribution (${total} total items)`;
    
    // Refresh the chart
    memoryChart.update();
}

// Initialize the chart when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initMemoryChart();
    
    // Make update function globally available
    window.updateMemoryChart = updateMemoryChart;
}); 