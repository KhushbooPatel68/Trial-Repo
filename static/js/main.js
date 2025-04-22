/**
 * Main JavaScript functionality for SmartCafé App
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize nutrition charts if on dashboard
    initializeNutritionCharts();

    // Setup portion selectors
    initializePortionSelectors();

    // Setup mobile navigation active states
    setActiveNavLink();
});

/**
 * Initialize nutrition charts on the dashboard
 */
function initializeNutritionCharts() {
    // Weekly calories chart
    const caloriesChartElem = document.getElementById('weekly-calories-chart');
    if (caloriesChartElem) {
        try {
            const weeklyData = JSON.parse(caloriesChartElem.dataset.chartData);
            
            new Chart(caloriesChartElem, {
                type: 'line',
                data: {
                    labels: weeklyData.dates,
                    datasets: [{
                        label: 'Calories',
                        data: weeklyData.calories,
                        borderColor: '#3f51b5',
                        backgroundColor: 'rgba(63, 81, 181, 0.1)',
                        borderWidth: 2,
                        tension: 0.2,
                        fill: true
                    },
                    {
                        label: 'Target',
                        data: Array(weeklyData.dates.length).fill(weeklyData.target_calories),
                        borderColor: '#ff4081',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        pointStyle: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Calories'
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error("Error initializing calories chart:", error);
        }
    }

    // Macronutrients chart
    const macrosChartElem = document.getElementById('macros-chart');
    if (macrosChartElem) {
        try {
            const weeklyData = JSON.parse(macrosChartElem.dataset.chartData);
            
            new Chart(macrosChartElem, {
                type: 'bar',
                data: {
                    labels: weeklyData.dates,
                    datasets: [
                        {
                            label: 'Protein (g)',
                            data: weeklyData.protein,
                            backgroundColor: 'rgba(76, 175, 80, 0.7)'
                        },
                        {
                            label: 'Carbs (g)',
                            data: weeklyData.carbs,
                            backgroundColor: 'rgba(33, 150, 243, 0.7)'
                        },
                        {
                            label: 'Fat (g)',
                            data: weeklyData.fat,
                            backgroundColor: 'rgba(255, 152, 0, 0.7)'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Grams'
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error("Error initializing macros chart:", error);
        }
    }
}

/**
 * Initialize portion selectors in the food menu
 */
function initializePortionSelectors() {
    const portionOptions = document.querySelectorAll('.portion-option');
    
    portionOptions.forEach(option => {
        option.addEventListener('click', function() {
            const foodId = this.closest('.food-item').dataset.foodId;
            const portionSize = this.dataset.size;
            const portionInput = document.querySelector(`input[name="portion_size_${foodId}"]`);
            
            // Update selection visually
            this.closest('.portion-selector').querySelectorAll('.portion-option').forEach(opt => {
                opt.classList.remove('active');
            });
            this.classList.add('active');
            
            // Update hidden input value
            if (portionInput) {
                portionInput.value = portionSize;
            }
        });
    });
}

/**
 * Set active state for mobile navigation based on current page
 */
function setActiveNavLink() {
    const currentPath = window.location.pathname;
    
    // Get all mobile nav links
    const mobileNavLinks = document.querySelectorAll('.mobile-nav-link');
    
    mobileNavLinks.forEach(link => {
        // Remove active class from all links
        link.classList.remove('active');
        
        // Add active class if the link's href matches the current path
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

/**
 * Fetch nutrition data for charts
 */
function loadNutritionData() {
    fetch('/nutrition-data')
        .then(response => response.json())
        .then(data => {
            // Update charts with new data
            updateNutritionCharts(data);
        })
        .catch(error => {
            console.error("Error fetching nutrition data:", error);
        });
}

/**
 * Update existing charts with new data
 */
function updateNutritionCharts(data) {
    // Implementation to update charts with new data
    // This would be used for dynamic updates if needed
}