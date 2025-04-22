/**
 * Food search and API integration functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize food search on pages that have the search input
    initFoodSearch();
    
    // Initialize CSV food import if needed
    initCsvFoodImport();
});

/**
 * Initialize food search functionality
 */
function initFoodSearch() {
    const searchInput = document.getElementById('food-search-input');
    const searchResults = document.getElementById('search-results');
    
    if (!searchInput || !searchResults) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        
        // Clear any existing timeout
        clearTimeout(searchTimeout);
        
        if (query.length < 2) {
            searchResults.innerHTML = '';
            searchResults.style.display = 'none';
            return;
        }
        
        // Debounce the search to avoid too many requests
        searchTimeout = setTimeout(function() {
            // Make AJAX request to search endpoint
            fetch(`/food-search?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    displaySearchResults(data, searchResults);
                })
                .catch(error => {
                    console.error('Error searching food:', error);
                    searchResults.innerHTML = '<div class="search-result-item">Error searching for food items</div>';
                    searchResults.style.display = 'block';
                });
        }, 300);
    });
    
    // Hide search results when clicking elsewhere
    document.addEventListener('click', function(event) {
        if (!searchInput.contains(event.target) && !searchResults.contains(event.target)) {
            searchResults.style.display = 'none';
        }
    });
}

/**
 * Display search results in the dropdown
 */
function displaySearchResults(results, resultsContainer) {
    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="search-result-item">No matching foods found</div>';
        resultsContainer.style.display = 'block';
        return;
    }
    
    let html = '';
    
    results.forEach(item => {
        const source = item.source === 'db' ? 'Database' : 'CSV';
        const nutritionInfo = `${item.calories} kcal | P: ${item.protein}g | C: ${item.carbs}g | F: ${item.fat}g`;
        
        html += `
            <div class="search-result-item" data-food-id="${item.id || ''}" data-source="${item.source}">
                <div class="search-result-name">${item.name}</div>
                <div class="search-result-info">${nutritionInfo}</div>
                <div class="search-result-source">${source}</div>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = html;
    resultsContainer.style.display = 'block';
    
    // Add click event to each result
    document.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', function() {
            const foodId = this.dataset.foodId;
            const source = this.dataset.source;
            
            if (source === 'db' && foodId) {
                // For database foods, just check the checkbox
                const checkbox = document.querySelector(`input[name="food_id"][value="${foodId}"]`);
                if (checkbox) {
                    checkbox.checked = true;
                    const changeEvent = new Event('change');
                    checkbox.dispatchEvent(changeEvent);
                }
            } else if (source === 'csv') {
                // For CSV foods, add them to the database first
                // and then trigger a page reload to display the new food
                addCsvFoodToDatabase(this.querySelector('.search-result-name').textContent);
            }
            
            // Hide the results
            resultsContainer.style.display = 'none';
        });
    });
}

/**
 * Add a food from CSV to the database
 */
function addCsvFoodToDatabase(foodName) {
    // This functionality would require a backend route
    // For now, just show a message
    alert(`Food "${foodName}" would be added to the database. This feature is coming soon.`);
}

/**
 * Initialize CSV food import functionality
 */
function initCsvFoodImport() {
    const importBtn = document.getElementById('import-csv-btn');
    const fileInput = document.getElementById('csv-file-input');
    
    if (!importBtn || !fileInput) return;
    
    importBtn.addEventListener('click', function() {
        fileInput.click();
    });
    
    fileInput.addEventListener('change', function(event) {
        if (event.target.files && event.target.files[0]) {
            const file = event.target.files[0];
            
            // Check file type
            if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
                alert('Please select a CSV file');
                return;
            }
            
            // Create a FormData object to send the file
            const formData = new FormData();
            formData.append('csv_file', file);
            
            // Import the CSV file
            fetch('/import-csv', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(`Successfully imported ${data.count} food items from CSV`);
                    // Reload the page to show the new foods
                    window.location.reload();
                } else {
                    alert(`Error importing CSV: ${data.error}`);
                }
            })
            .catch(error => {
                console.error('Error importing CSV:', error);
                alert('An error occurred while importing the CSV file');
            });
        }
    });
}