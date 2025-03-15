/**
 * VOTai TRILOGY BRAIN - Dashboard Charts
 * Chart visualizations for the dashboard panels
 */

class DashboardCharts {
  constructor() {
    this.charts = {};
    this.gradients = {};
    this.chartData = {
      memoryUsage: {
        current: 67,
        history: [62, 58, 65, 60, 59, 61, 64, 67]
      },
      tokenProcessing: {
        current: 1.2,
        history: [0.8, 1.1, 0.9, 1.0, 1.2, 1.0, 1.1, 1.2]
      },
      cacheHit: {
        current: 89,
        history: [78, 82, 85, 81, 84, 87, 88, 89]
      },
      zkVerification: {
        current: 42,
        history: [35, 38, 40, 37, 39, 40, 41, 42]
      },
      tokenEconomy: {
        labels: ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'],
        rewards: [423, 512, 398, 634, 582, 498, 670],
        spending: [310, 385, 290, 430, 495, 310, 520]
      }
    };

    this.init();
  }

  init() {
    // Create gradients and initialize charts when DOM is loaded
    document.addEventListener('DOMContentLoaded', () => {
      this.initMemoryUsageChart();
      this.initTokenProcessingChart();
      this.initCacheHitChart();
      this.initZkVerificationChart();
      this.initTokenEconomyChart();
      
      // Set up window resize event handler
      window.addEventListener('resize', this.handleResize.bind(this));
    });
  }

  handleResize() {
    // Throttle resize event
    if (this.resizeTimeout) clearTimeout(this.resizeTimeout);
    this.resizeTimeout = setTimeout(() => {
      // Rebuild charts on resize to ensure proper rendering
      Object.values(this.charts).forEach(chart => chart.resize());
    }, 250);
  }

  createGradient(ctx, colors) {
    const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
    colors.forEach((color, index) => {
      gradient.addColorStop(index / (colors.length - 1), color);
    });
    return gradient;
  }

  // Memory Usage Chart
  initMemoryUsageChart() {
    const ctx = document.getElementById('memoryUsageChart').getContext('2d');
    
    // Create gradient
    this.gradients.memoryUsage = this.createGradient(ctx, [
      'rgba(255, 42, 109, 0.8)',  // Hot pink
      'rgba(255, 42, 109, 0.1)'   // Transparent pink
    ]);
    
    this.charts.memoryUsage = new Chart(ctx, {
      type: 'line',
      data: {
        labels: new Array(this.chartData.memoryUsage.history.length).fill(''),
        datasets: [{
          label: 'Memory Usage (%)',
          data: this.chartData.memoryUsage.history,
          borderColor: 'rgba(255, 42, 109, 1)',
          borderWidth: 2,
          backgroundColor: this.gradients.memoryUsage,
          pointBackgroundColor: 'rgba(255, 42, 109, 1)',
          pointRadius: 0,
          pointHoverRadius: 3,
          tension: 0.3,
          fill: true
        }]
      },
      options: this.getSmallChartOptions()
    });
  }

  // Token Processing Chart
  initTokenProcessingChart() {
    const ctx = document.getElementById('tokenProcessingChart').getContext('2d');
    
    // Create gradient
    this.gradients.tokenProcessing = this.createGradient(ctx, [
      'rgba(16, 165, 245, 0.8)',  // Cyan
      'rgba(16, 165, 245, 0.1)'   // Transparent cyan
    ]);
    
    this.charts.tokenProcessing = new Chart(ctx, {
      type: 'line',
      data: {
        labels: new Array(this.chartData.tokenProcessing.history.length).fill(''),
        datasets: [{
          label: 'Tokens (K/s)',
          data: this.chartData.tokenProcessing.history,
          borderColor: 'rgba(16, 165, 245, 1)',
          borderWidth: 2,
          backgroundColor: this.gradients.tokenProcessing,
          pointBackgroundColor: 'rgba(16, 165, 245, 1)',
          pointRadius: 0,
          pointHoverRadius: 3,
          tension: 0.3,
          fill: true
        }]
      },
      options: this.getSmallChartOptions()
    });
  }

  // Cache Hit Chart
  initCacheHitChart() {
    const ctx = document.getElementById('cacheHitChart').getContext('2d');
    
    // Create gradient
    this.gradients.cacheHit = this.createGradient(ctx, [
      'rgba(58, 16, 120, 0.8)',  // Purple
      'rgba(58, 16, 120, 0.1)'   // Transparent purple
    ]);
    
    this.charts.cacheHit = new Chart(ctx, {
      type: 'line',
      data: {
        labels: new Array(this.chartData.cacheHit.history.length).fill(''),
        datasets: [{
          label: 'Hit Rate (%)',
          data: this.chartData.cacheHit.history,
          borderColor: 'rgba(58, 16, 120, 1)',
          borderWidth: 2,
          backgroundColor: this.gradients.cacheHit,
          pointBackgroundColor: 'rgba(58, 16, 120, 1)',
          pointRadius: 0,
          pointHoverRadius: 3,
          tension: 0.3,
          fill: true
        }]
      },
      options: this.getSmallChartOptions()
    });
  }

  // ZK Verification Chart
  initZkVerificationChart() {
    const ctx = document.getElementById('zkVerificationChart').getContext('2d');
    
    // Create gradient
    this.gradients.zkVerification = this.createGradient(ctx, [
      'rgba(255, 239, 64, 0.8)',  // Yellow
      'rgba(255, 239, 64, 0.1)'   // Transparent yellow
    ]);
    
    this.charts.zkVerification = new Chart(ctx, {
      type: 'line',
      data: {
        labels: new Array(this.chartData.zkVerification.history.length).fill(''),
        datasets: [{
          label: 'Verifications/min',
          data: this.chartData.zkVerification.history,
          borderColor: 'rgba(255, 239, 64, 1)',
          borderWidth: 2,
          backgroundColor: this.gradients.zkVerification,
          pointBackgroundColor: 'rgba(255, 239, 64, 1)',
          pointRadius: 0,
          pointHoverRadius: 3,
          tension: 0.3,
          fill: true
        }]
      },
      options: this.getSmallChartOptions()
    });
  }

  // Token Economy Chart
  initTokenEconomyChart() {
    const ctx = document.getElementById('tokenEconomyChart').getContext('2d');
    
    // Create gradients
    this.gradients.tokenRewards = this.createGradient(ctx, [
      'rgba(5, 255, 161, 0.8)',  // Green
      'rgba(5, 255, 161, 0.1)'   // Transparent green
    ]);
    
    this.gradients.tokenSpending = this.createGradient(ctx, [
      'rgba(255, 56, 96, 0.8)',   // Red
      'rgba(255, 56, 96, 0.1)'    // Transparent red
    ]);
    
    this.charts.tokenEconomy = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: this.chartData.tokenEconomy.labels,
        datasets: [
          {
            label: 'Rewards',
            data: this.chartData.tokenEconomy.rewards,
            backgroundColor: this.gradients.tokenRewards,
            borderColor: 'rgba(5, 255, 161, 1)',
            borderWidth: 1
          },
          {
            label: 'Spending',
            data: this.chartData.tokenEconomy.spending,
            backgroundColor: this.gradients.tokenSpending,
            borderColor: 'rgba(255, 56, 96, 1)',
            borderWidth: 1
          }
        ]
      },
      options: this.getTokenChartOptions()
    });
  }

  // Small chart options (for metric cards)
  getSmallChartOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          displayColors: false,
          backgroundColor: 'rgba(15, 10, 38, 0.9)',
          titleFont: {
            family: "'Share Tech Mono', monospace",
            size: 10
          },
          bodyFont: {
            family: "'Share Tech Mono', monospace",
            size: 12
          },
          padding: 8,
          borderWidth: 1,
          borderColor: 'rgba(58, 16, 120, 0.5)',
          callbacks: {
            title: function(context) {
              return '';
            },
            label: function(context) {
              return context.dataset.label + ': ' + context.parsed.y;
            }
          }
        }
      },
      scales: {
        x: {
          display: false
        },
        y: {
          display: false,
          beginAtZero: false
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      },
      animation: {
        duration: 1000,
        easing: 'easeOutQuart'
      }
    };
  }

  // Token economy chart options
  getTokenChartOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
          align: 'end',
          labels: {
            color: 'rgba(224, 224, 255, 0.8)',
            font: {
              family: "'Share Tech Mono', monospace",
              size: 10
            },
            boxWidth: 12,
            padding: 10
          }
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          displayColors: true,
          backgroundColor: 'rgba(15, 10, 38, 0.9)',
          titleFont: {
            family: "'Share Tech Mono', monospace",
            size: 10
          },
          bodyFont: {
            family: "'Share Tech Mono', monospace",
            size: 12
          },
          padding: 8,
          borderWidth: 1,
          borderColor: 'rgba(58, 16, 120, 0.5)',
          callbacks: {
            label: function(context) {
              return context.dataset.label + ': ' + context.parsed.y + ' VOT';
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(160, 160, 208, 0.1)',
            borderColor: 'rgba(160, 160, 208, 0.2)',
            tickColor: 'rgba(160, 160, 208, 0.2)'
          },
          ticks: {
            color: 'rgba(160, 160, 208, 0.7)',
            font: {
              family: "'Share Tech Mono', monospace",
              size: 9
            }
          }
        },
        y: {
          grid: {
            color: 'rgba(160, 160, 208, 0.1)',
            borderColor: 'rgba(160, 160, 208, 0.2)',
            tickColor: 'rgba(160, 160, 208, 0.2)'
          },
          ticks: {
            color: 'rgba(160, 160, 208, 0.7)',
            font: {
              family: "'Share Tech Mono', monospace",
              size: 9
            },
            callback: function(value) {
              if (value >= 1000) {
                return value / 1000 + 'K';
              }
              return value;
            }
          }
        }
      },
      animation: {
        duration: 1000,
        easing: 'easeOutQuart'
      }
    };
  }

  // Methods to update chart data
  updateMemoryUsage(value) {
    this.chartData.memoryUsage.history.push(value);
    this.chartData.memoryUsage.history.shift();
    this.chartData.memoryUsage.current = value;
    
    this.charts.memoryUsage.data.datasets[0].data = this.chartData.memoryUsage.history;
    this.charts.memoryUsage.update();
    
    // Update the displayed value
    document.querySelector('.metric-card:nth-child(1) .metric-value').innerHTML = 
      `${value}<span class="unit">%</span>`;
  }

  updateTokenProcessing(value) {
    this.chartData.tokenProcessing.history.push(value);
    this.chartData.tokenProcessing.history.shift();
    this.chartData.tokenProcessing.current = value;
    
    this.charts.tokenProcessing.data.datasets[0].data = this.chartData.tokenProcessing.history;
    this.charts.tokenProcessing.update();
    
    // Update the displayed value
    document.querySelector('.metric-card:nth-child(2) .metric-value').innerHTML = 
      `${value.toFixed(1)}<span class="unit">K/s</span>`;
  }

  updateCacheHit(value) {
    this.chartData.cacheHit.history.push(value);
    this.chartData.cacheHit.history.shift();
    this.chartData.cacheHit.current = value;
    
    this.charts.cacheHit.data.datasets[0].data = this.chartData.cacheHit.history;
    this.charts.cacheHit.update();
    
    // Update the displayed value
    document.querySelector('.metric-card:nth-child(3) .metric-value').innerHTML = 
      `${value}<span class="unit">%</span>`;
  }

  updateZkVerification(value) {
    this.chartData.zkVerification.history.push(value);
    this.chartData.zkVerification.history.shift();
    this.chartData.zkVerification.current = value;
    
    this.charts.zkVerification.data.datasets[0].data = this.chartData.zkVerification.history;
    this.charts.zkVerification.update();
    
    // Update the displayed value
    document.querySelector('.metric-card:nth-child(4) .metric-value').innerHTML = 
      `${value}<span class="unit">/min</span>`;
  }

  updateTokenEconomy(rewards, spending) {
    this.chartData.tokenEconomy.rewards = rewards;
    this.chartData.tokenEconomy.spending = spending;
    
    this.charts.tokenEconomy.data.datasets[0].data = rewards;
    this.charts.tokenEconomy.data.datasets[1].data = spending;
    this.charts.tokenEconomy.update();
  }

  // Simulate data updates for demo purposes
  startSimulation() {
    setInterval(() => {
      // Random fluctuations for memory usage (60-70%)
      const memoryValue = Math.floor(60 + Math.random() * 10);
      this.updateMemoryUsage(memoryValue);
      
      // Random fluctuations for token processing (0.8-1.5 K/s)
      const tokenValue = 0.8 + Math.random() * 0.7;
      this.updateTokenProcessing(tokenValue);
      
      // Random fluctuations for cache hit rate (75-95%)
      const cacheValue = Math.floor(75 + Math.random() * 20);
      this.updateCacheHit(cacheValue);
      
      // Random fluctuations for ZK verifications (30-50/min)
      const zkValue = Math.floor(30 + Math.random() * 20);
      this.updateZkVerification(zkValue);
    }, 5000); // Update every 5 seconds
  }
}

// Initialize charts
document.addEventListener('DOMContentLoaded', () => {
  window.dashboardCharts = new DashboardCharts();
  
  // Start simulation for demo
  window.dashboardCharts.startSimulation();
}); 