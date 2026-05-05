// Charts.js - Chart configurations and utilities for Teacher Evaluation System

class ChartManager {
    constructor() {
        this.charts = {};
        this.defaultColors = {
            primary: '#0d6efd',
            success: '#198754',
            info: '#0dcaf0',
            warning: '#ffc107',
            danger: '#dc3545',
            secondary: '#6c757d',
            light: '#f8f9fa',
            dark: '#212529'
        };
    }

    /**
     * Create a radar chart for category scores
     */
    createCategoryChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const defaultOptions = {
            type: 'radar',
            data: {
                labels: ['Teaching Clarity', 'Engagement', 'Fairness', 
                         'Curriculum', 'Assessment', 'Mentoring',
                         'Attendance', 'Commitment', 'Quality'],
                datasets: [{
                    label: 'Average Score',
                    data: data || [0, 0, 0, 0, 0, 0, 0, 0, 0],
                    backgroundColor: 'rgba(13, 110, 253, 0.2)',
                    borderColor: this.defaultColors.primary,
                    pointBackgroundColor: this.defaultColors.primary,
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: this.defaultColors.primary,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 5,
                        ticks: {
                            stepSize: 1,
                            callback: function(value) {
                                return value + '/5';
                            }
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Score: ${context.raw.toFixed(2)} / 5.00`;
                            }
                        }
                    }
                }
            }
        };

        // Merge user options with defaults
        const config = this.mergeOptions(defaultOptions, options);
        
        // Destroy existing chart if it exists
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(canvas, config);
        return this.charts[canvasId];
    }

    /**
     * Create a line chart for trends over time
     */
    createTrendChart(canvasId, labels, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const defaultOptions = {
            type: 'line',
            data: {
                labels: labels || [],
                datasets: [{
                    label: 'Monthly Average',
                    data: data || [],
                    borderColor: this.defaultColors.primary,
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: this.defaultColors.primary,
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: this.defaultColors.primary,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Score: ${context.parsed.y.toFixed(2)} / 5.00`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 5,
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        },
                        title: {
                            display: true,
                            text: 'Average Score'
                        },
                        ticks: {
                            callback: function(value) {
                                return value + '/5';
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Month'
                        }
                    }
                }
            }
        };

        const config = this.mergeOptions(defaultOptions, options);
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(canvas, config);
        return this.charts[canvasId];
    }

    /**
     * Create a bar chart for comparisons
     */
    createBarChart(canvasId, labels, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const defaultOptions = {
            type: 'bar',
            data: {
                labels: labels || [],
                datasets: [{
                    label: 'Average Score',
                    data: data || [],
                    backgroundColor: this.defaultColors.primary,
                    borderRadius: 6,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Score: ${context.raw.toFixed(2)} / 5.00`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 5,
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        },
                        title: {
                            display: true,
                            text: 'Average Score'
                        },
                        ticks: {
                            callback: function(value) {
                                return value + '/5';
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        };

        const config = this.mergeOptions(defaultOptions, options);
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(canvas, config);
        return this.charts[canvasId];
    }

    /**
     * Create a pie chart for distribution
     */
    createPieChart(canvasId, labels, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const defaultOptions = {
            type: 'pie',
            data: {
                labels: labels || [],
                datasets: [{
                    data: data || [],
                    backgroundColor: [
                        this.defaultColors.primary,
                        this.defaultColors.success,
                        this.defaultColors.warning,
                        this.defaultColors.info,
                        this.defaultColors.danger
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.raw / total) * 100).toFixed(1);
                                return `${context.label}: ${context.raw} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        };

        const config = this.mergeOptions(defaultOptions, options);
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(canvas, config);
        return this.charts[canvasId];
    }

    /**
     * Create a doughnut chart for progress
     */
    createDoughnutChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const defaultOptions = {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'Remaining'],
                datasets: [{
                    data: data || [0, 100],
                    backgroundColor: [this.defaultColors.success, this.defaultColors.light],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.raw}%`;
                            }
                        }
                    }
                }
            }
        };

        const config = this.mergeOptions(defaultOptions, options);
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(canvas, config);
        return this.charts[canvasId];
    }

    /**
     * Update chart data
     */
    updateChart(chartId, newData, newLabels = null) {
        const chart = this.charts[chartId];
        if (!chart) return false;

        if (newLabels) {
            chart.data.labels = newLabels;
        }
        
        if (Array.isArray(newData)) {
            chart.data.datasets[0].data = newData;
        } else if (typeof newData === 'object') {
            Object.assign(chart.data.datasets[0], newData);
        }
        
        chart.update();
        return true;
    }

    /**
     * Destroy specific chart
     */
    destroyChart(chartId) {
        if (this.charts[chartId]) {
            this.charts[chartId].destroy();
            delete this.charts[chartId];
            return true;
        }
        return false;
    }

    /**
     * Destroy all charts
     */
    destroyAllCharts() {
        Object.keys(this.charts).forEach(chartId => {
            this.charts[chartId].destroy();
        });
        this.charts = {};
    }

    /**
     * Merge default options with user options
     */
    mergeOptions(defaults, userOptions) {
        return JSON.parse(JSON.stringify({ ...defaults, ...userOptions }));
    }

    /**
     * Get color by name or index
     */
    getColor(name, index = 0) {
        if (this.defaultColors[name]) {
            return this.defaultColors[name];
        }
        
        const colors = Object.values(this.defaultColors);
        return colors[index % colors.length];
    }

    /**
     * Generate gradient for chart
     */
    createGradient(ctx, color1, color2) {
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, color1);
        gradient.addColorStop(1, color2);
        return gradient;
    }

    /**
     * Export chart as image
     */
    exportChartAsImage(chartId, filename = 'chart.png') {
        const chart = this.charts[chartId];
        if (!chart) return false;

        const canvas = chart.canvas;
        const image = canvas.toDataURL('image/png');
        
        const link = document.createElement('a');
        link.download = filename;
        link.href = image;
        link.click();
        
        return true;
    }

    /**
     * Resize all charts
     */
    resizeAllCharts() {
        Object.values(this.charts).forEach(chart => {
            chart.resize();
        });
    }
}

// Initialize chart manager
const chartManager = new ChartManager();

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = chartManager;
}

// Helper functions for common chart types
const Charts = {
    /**
     * Initialize teacher dashboard charts
     */
    initTeacherCharts: function(teacherId, categoryData, monthlyData) {
        // Category radar chart
        chartManager.createCategoryChart('categoryChart', categoryData);
        
        // Monthly trend line chart
        if (monthlyData && monthlyData.labels && monthlyData.labels.length > 0) {
            chartManager.createTrendChart('trendChart', monthlyData.labels, monthlyData.scores);
        }
    },

    /**
     * Initialize admin dashboard charts
     */
    initAdminCharts: function(evaluationsByRole, departmentScores) {
        // Evaluations by role pie chart
        if (evaluationsByRole) {
            chartManager.createPieChart('evaluationsByRoleChart', 
                ['Students', 'Program Heads', 'Deans'],
                [evaluationsByRole.student, evaluationsByRole.program_head, evaluationsByRole.dean]
            );
        }
        
        // Department scores bar chart
        if (departmentScores && departmentScores.departments) {
            chartManager.createBarChart('departmentScoresChart',
                departmentScores.departments,
                departmentScores.scores,
                {
                    options: {
                        scales: {
                            y: {
                                max: 5
                            }
                        }
                    }
                }
            );
        }
    },

    /**
     * Initialize program dashboard charts
     */
    initProgramCharts: function(teacherLabels, teacherScores) {
        if (teacherLabels && teacherScores) {
            chartManager.createBarChart('teacherChart', teacherLabels, teacherScores, {
                options: {
                    plugins: {
                        tooltip: {
                            callbacks: {
                                afterLabel: function(context) {
                                    const evaluations = teacherScores.evaluations?.[context.dataIndex];
                                    return evaluations ? `Evaluations: ${evaluations}` : '';
                                }
                            }
                        }
                    }
                }
            });
        }
    },

    /**
     * Create completion doughnut chart
     */
    createCompletionChart: function(canvasId, completed, total) {
        const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
        return chartManager.createDoughnutChart(canvasId, [percentage, 100 - percentage], {
            options: {
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.raw}% Complete`;
                            }
                        }
                    }
                }
            }
        });
    },

    /**
     * Update all charts with new data
     */
    refreshAllCharts: function() {
        chartManager.resizeAllCharts();
    },

    /**
     * Destroy all charts
     */
    cleanup: function() {
        chartManager.destroyAllCharts();
    }
};

// Auto-resize charts on window resize
let resizeTimeout;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function() {
        Charts.refreshAllCharts();
    }, 250);
});

// Export Charts object for global use
window.Charts = Charts;