/**
 * Update nutrition charts with the provided data
 * @param {Object} data - Nutrition data for charting
 */
function updateNutritionCharts(data) {
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded');
        return;
    }
    
    // Destroy existing charts if they exist
    if (window.caloriesChart) window.caloriesChart.destroy();
    if (window.macrosChart) window.macrosChart.destroy();
    
    // Create calories chart
    const caloriesCtx = document.getElementById('calories-chart');
    if (caloriesCtx) {
        window.caloriesChart = createCaloriesChart(caloriesCtx, data);
    }
    
    // Create macros chart
    const macrosCtx = document.getElementById('macros-chart');
    if (macrosCtx) {
        window.macrosChart = createMacrosChart(macrosCtx, data);
    }
    
    // Update summary values
    updateNutritionSummary(data);
}

/**
 * Create a chart for calorie intake
 */
function createCaloriesChart(ctx, data) {
    // Get today's calorie intake
    const today = new Date().toISOString().split('T')[0];
    const todayIndex = data.dates.indexOf(today);
    const todayCalories = todayIndex >= 0 ? data.calories[todayIndex] : 0;
    
    // Target line
    const targetCalories = data.target_calories || 2000;
    
    // Determine color based on current intake
    const calorieColor = todayCalories > targetCalories ? '#e74c3c' : '#1abc9c';
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.dates.map(date => formatDate(date)),
            datasets: [
                {
                    label: 'Calories',
                    data: data.calories,
                    backgroundColor: calorieColor,
                    borderColor: calorieColor,
                    borderWidth: 1
                },
                {
                    label: 'Target',
                    data: Array(data.dates.length).fill(targetCalories),
                    type: 'line',
                    borderColor: '#3498db',
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Calories (kcal)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        title: function(tooltipItems) {
                            return formatDate(data.dates[tooltipItems[0].dataIndex]);
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create a chart for macronutrient intake
 */
function createMacrosChart(ctx, data) {
    // Target values
    const targetProtein = data.target_protein || 125;
    const targetCarbs = data.target_carbs || 250;
    const targetFat = data.target_fat || 55;
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates.map(date => formatDate(date)),
            datasets: [
                {
                    label: 'Protein (g)',
                    data: data.protein,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    fill: true,
                    tension: 0.1
                },
                {
                    label: 'Carbs (g)',
                    data: data.carbs,
                    borderColor: '#f39c12',
                    backgroundColor: 'rgba(243, 156, 18, 0.1)',
                    fill: true,
                    tension: 0.1
                },
                {
                    label: 'Fat (g)',
                    data: data.fat,
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    fill: true,
                    tension: 0.1
                },
                {
                    label: 'Target Protein',
                    data: Array(data.dates.length).fill(targetProtein),
                    borderColor: '#3498db',
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                },
                {
                    label: 'Target Carbs',
                    data: Array(data.dates.length).fill(targetCarbs),
                    borderColor: '#f39c12',
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                },
                {
                    label: 'Target Fat',
                    data: Array(data.dates.length).fill(targetFat),
                    borderColor: '#e74c3c',
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Amount (g)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                }
            }
        }
    });
}

/**
 * Update nutrition summary on the dashboard
 */
function updateNutritionSummary(data) {
    // Get today's data
    const today = new Date().toISOString().split('T')[0];
    const todayIndex = data.dates.indexOf(today);
    
    if (todayIndex >= 0) {
        // Today's values
        const calories = data.calories[todayIndex];
        const protein = data.protein[todayIndex];
        const carbs = data.carbs[todayIndex];
        const fat = data.fat[todayIndex];
        
        // Target values
        const targetCalories = data.target_calories || 2000;
        const targetProtein = data.target_protein || 125;
        const targetCarbs = data.target_carbs || 250;
        const targetFat = data.target_fat || 55;
        
        // Update summary values
        updateSummaryElement('calories-value', calories);
        updateSummaryElement('protein-value', protein);
        updateSummaryElement('carbs-value', carbs);
        updateSummaryElement('fat-value', fat);
        
        // Update progress bars
        updateProgressBar('calories-progress', calories, targetCalories);
        updateProgressBar('protein-progress', protein, targetProtein);
        updateProgressBar('carbs-progress', carbs, targetCarbs);
        updateProgressBar('fat-progress', fat, targetFat);
        
        // Update remaining values
        updateRemainingElement('calories-remaining', targetCalories - calories);
        updateRemainingElement('protein-remaining', targetProtein - protein);
        updateRemainingElement('carbs-remaining', targetCarbs - carbs);
        updateRemainingElement('fat-remaining', targetFat - fat);
    }
}

/**
 * Update a summary element with the given value
 */
function updateSummaryElement(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = Math.round(value);
    }
}

/**
 * Update a progress bar with the given value and target
 */
function updateProgressBar(elementId, value, target) {
    const element = document.getElementById(elementId);
    if (element) {
        const percentage = Math.min(100, Math.round((value / target) * 100));
        element.style.width = `${percentage}%`;
        
        // Change color if exceeded
        if (percentage > 100) {
            element.classList.add('bg-danger');
        } else {
            element.classList.remove('bg-danger');
        }
    }
}

/**
 * Update a remaining element with the given value
 */
function updateRemainingElement(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = Math.round(value);
        
        // Change color if negative
        if (value < 0) {
            element.classList.add('text-danger');
        } else {
            element.classList.remove('text-danger');
        }
    }
}

/**
 * Format a date string to a more readable format
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
