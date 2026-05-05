// Dashboard functionality for Teacher Evaluation System

class DashboardManager {
    constructor() {
        this.charts = {};
    }

    initTeacherDashboard(teacherId) {
        this.loadTeacherStats(teacherId);
        this.loadTeacherTrends(teacherId);
    }

    loadTeacherStats(teacherId) {
        fetch(`/api/teacher/${teacherId}/stats`)
            .then(response => response.json())
            .then(data => {
                this.updateTeacherStats(data);
                this.createCategoryChart(data);
            })
            .catch(error => {
                console.error('Error loading teacher stats:', error);
                this.showError('Failed to load teacher statistics');
            });
    }

    loadTeacherTrends(teacherId) {
        fetch(`/api/teacher/${teacherId}/trends`)
            .then(response => response.json())
            .then(data => {
                if (data && data.months && data.months.length > 0) {
                    this.createTrendChart(data);
                }
            })
            .catch(error => console.error('Error loading teacher trends:', error));
    }

    updateTeacherStats(data) {
        // Update statistics display
        const elements = {
            totalEvaluations: document.getElementById('totalEvaluations'),
            studentScore: document.getElementById('studentScore'),
            programHeadScore: document.getElementById('programHeadScore'),
            deanScore: document.getElementById('deanScore'),
            overallScore: document.getElementById('overallScore')
        };

        if (elements.totalEvaluations) {
            elements.totalEvaluations.textContent = data.total_evaluations || 0;
        }
        if (elements.studentScore) {
            elements.studentScore.textContent = data.scores_by_role?.student?.avg?.toFixed(2) || 'N/A';
        }
        if (elements.programHeadScore) {
            elements.programHeadScore.textContent = data.scores_by_role?.program_head?.avg?.toFixed(2) || 'N/A';
        }
        if (elements.deanScore) {
            elements.deanScore.textContent = data.scores_by_role?.dean?.avg?.toFixed(2) || 'N/A';
        }
        if (elements.overallScore) {
            const scores = [
                data.scores_by_role?.student?.avg || 0,
                data.scores_by_role?.program_head?.avg || 0,
                data.scores_by_role?.dean?.avg || 0
            ];
            const validScores = scores.filter(s => s > 0);
            const avg = validScores.length > 0 
                ? validScores.reduce((a, b) => a + b, 0) / validScores.length 
                : 0;
            elements.overallScore.textContent = avg.toFixed(2);
        }
    }

    createCategoryChart(data) {
        const ctx = document.getElementById('categoryChart')?.getContext('2d');
        if (!ctx) return;

        const categories = [
            'Teaching Clarity', 'Engagement', 'Fairness',
            'Curriculum', 'Assessment', 'Mentoring',
            'Attendance', 'Commitment', 'Teaching Quality'
        ];

        const scores = [
            data.category_averages?.teaching_clarity || 0,
            data.category_averages?.engagement || 0,
            data.category_averages?.fairness || 0,
            data.category_averages?.curriculum || 0,
            data.category_averages?.assessment || 0,
            data.category_averages?.mentoring || 0,
            data.category_averages?.attendance || 0,
            data.category_averages?.commitment || 0,
            data.category_averages?.teaching_quality || 0
        ];

        this.charts.categoryChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: categories,
                datasets: [{
                    label: 'Average Scores by Category',
                    data: scores,
                    backgroundColor: 'rgba(13, 110, 253, 0.2)',
                    borderColor: '#0d6efd',
                    pointBackgroundColor: '#0d6efd',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#0d6efd'
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
                            stepSize: 1
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

    createTrendChart(data) {
        const ctx = document.getElementById('trendChart')?.getContext('2d');
        if (!ctx) return;

        this.charts.trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.months || [],
                datasets: [{
                    label: 'Monthly Average Score',
                    data: data.scores || [],
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#0d6efd',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#0d6efd'
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
                            display: true,
                            color: 'rgba(0,0,0,0.05)'
                        },
                        title: {
                            display: true,
                            text: 'Average Score'
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
        });
    }

    showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="bi bi-exclamation-triangle-fill"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    }
}

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    const dashboard = new DashboardManager();
    
    // Check if we're on a teacher dashboard page
    const teacherDashboard = document.getElementById('teacher-dashboard');
    if (teacherDashboard) {
        const teacherId = teacherDashboard.dataset.teacherId;
        dashboard.initTeacherDashboard(teacherId);
    }
});

// Export functionality
function exportReport(teacherId, format) {
    if (!teacherId) return;
    
    window.location.href = `/export/teacher/${teacherId}/${format}`;
}

// Print dashboard
function printDashboard() {
    window.print();
}

// Form validation
function validateEvaluationForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;

    const requiredFields = form.querySelectorAll('[required]');
    for (let field of requiredFields) {
        if (!field.value) {
            alert('Please fill in all required fields.');
            field.focus();
            return false;
        }
    }

    // Check radio groups
    const radioGroups = {};
    form.querySelectorAll('input[type="radio"]').forEach(radio => {
        if (!radioGroups[radio.name]) {
            radioGroups[radio.name] = false;
        }
        if (radio.checked) {
            radioGroups[radio.name] = true;
        }
    });

    for (let group in radioGroups) {
        if (!radioGroups[group]) {
            alert('Please rate all categories before submitting.');
            return false;
        }
    }

    return confirm('Are you sure you want to submit this evaluation?');
}

// Data export helpers
function exportToCSV(data, filename) {
    const csvContent = data.map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Loading spinner
function showLoading() {
    const overlay = document.createElement('div');
    overlay.className = 'spinner-overlay';
    overlay.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.querySelector('.spinner-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Refresh data periodically
function startAutoRefresh(interval = 30000) {
    setInterval(() => {
        if (document.getElementById('auto-refresh')?.checked) {
            location.reload();
        }
    }, interval);
}