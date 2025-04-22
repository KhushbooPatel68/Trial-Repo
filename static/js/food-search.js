/**
 * Food search and selection functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize food selection on the menu page
    initFoodSelection();
    
    // Initialize voice support if available
    initVoiceSearch();
});

/**
 * Initialize food selection functionality
 */
function initFoodSelection() {
    const foodCheckboxes = document.querySelectorAll('.food-select-checkbox');
    
    foodCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const foodId = this.dataset.foodId;
            const foodItem = document.querySelector(`.menu-item[data-food-id="${foodId}"]`);
            
            if (this.checked) {
                foodItem.classList.add('selected');
            } else {
                foodItem.classList.remove('selected');
            }
            
            updateSelectedCount();
        });
    });
    
    // Update selected count initially
    updateSelectedCount();
}

/**
 * Update the selected items count in the UI
 */
function updateSelectedCount() {
    const selectedCountElement = document.getElementById('selected-count');
    if (!selectedCountElement) return;
    
    const selectedCount = document.querySelectorAll('.food-select-checkbox:checked').length;
    selectedCountElement.textContent = selectedCount;
    
    // Show/hide the add meal button
    const addMealBtn = document.getElementById('add-meal-btn');
    if (addMealBtn) {
        addMealBtn.style.display = selectedCount > 0 ? 'block' : 'none';
    }
}

/**
 * Initialize voice search capability if supported
 */
function initVoiceSearch() {
    const voiceSearchBtn = document.getElementById('voice-search-btn');
    const searchInput = document.getElementById('food-search');
    
    if (!voiceSearchBtn || !searchInput) return;
    
    // Check if browser supports speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        voiceSearchBtn.style.display = 'block';
        
        voiceSearchBtn.addEventListener('click', function() {
            // Create recognition object
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            
            // Set properties
            recognition.lang = document.documentElement.lang || 'en-US';
            recognition.continuous = false;
            recognition.interimResults = false;
            
            // Start listening
            recognition.start();
            
            // Show listening indicator
            voiceSearchBtn.classList.add('listening');
            
            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                searchInput.value = transcript;
                
                // Trigger input event to filter foods
                const inputEvent = new Event('input', { bubbles: true });
                searchInput.dispatchEvent(inputEvent);
                
                voiceSearchBtn.classList.remove('listening');
            };
            
            recognition.onerror = function() {
                voiceSearchBtn.classList.remove('listening');
            };
            
            recognition.onend = function() {
                voiceSearchBtn.classList.remove('listening');
            };
        });
    } else {
        // Hide button if speech recognition is not supported
        voiceSearchBtn.style.display = 'none';
    }
}

/**
 * Load food image via file upload or camera
 */
function initImageUpload() {
    const imageUploadBtn = document.getElementById('image-upload-btn');
    const imageInput = document.getElementById('image-input');
    const imagePreview = document.getElementById('image-preview');
    
    if (!imageUploadBtn || !imageInput || !imagePreview) return;
    
    imageUploadBtn.addEventListener('click', function() {
        imageInput.click();
    });
    
    imageInput.addEventListener('change', function(event) {
        if (event.target.files && event.target.files[0]) {
            const file = event.target.files[0];
            const reader = new FileReader();
            
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
                
                // Here you would typically send the image to your backend
                // for AI-based food recognition (future enhancement)
                console.log('Image uploaded, ready for AI processing');
            };
            
            reader.readAsDataURL(file);
        }
    });
}
