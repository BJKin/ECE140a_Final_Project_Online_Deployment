document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const addClothingName = document.getElementById('addClothingName');
    const addClothingColor = document.getElementById('addClothingColor');
    const addClothingBtn = document.getElementById('addClothingBtn');
    
    const removeClothingSelect = document.getElementById('removeClothingSelect');
    const removeClothingBtn = document.getElementById('removeClothingBtn');
    
    const updateClothingSelect = document.getElementById('updateClothingSelect');
    const newClothingName = document.getElementById('newClothingName');
    const newClothingColor = document.getElementById('newClothingColor');
    const updateClothingBtn = document.getElementById('updateClothingBtn');
    
    const clothesList = document.getElementById('clothesList');
    const userName = document.getElementById('userName');
    const userRole = document.getElementById('userRole');

    // API Endpoints
    const API_ENDPOINTS = {
        WARDROBE: '/api/wardrobe',
        PROFILE: '/api/profile',
    };

    // Load user profile data
    const loadUserProfile = async () => {
        try {
            const response = await fetch(API_ENDPOINTS.PROFILE, {method: 'GET', headers: {'Accept': 'application/json'}, credentials: 'same-origin'});
            
            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const userData = await response.json();
            
            if (userName && userData) {
                userName.textContent = userData.name || 'User';
                userRole.textContent = "ESP32 Champion";
            }
        } catch (error) {
            console.error('Error fetching user data:', error);
        }
    };

    // Render clothing list
    const renderClothingList = (clothes) => {
        if (!clothes || clothes.length === 0) {
            clothesList.innerHTML = '<p>No clothing items added yet</p>';
            return;
        }
        
        let clothingHTML = '';
        clothes.forEach(item => {
            clothingHTML += `
                <div class="clothing-timeline">
                    <div class="timeline-dot"></div>
                    <div class="clothing-item" data-id="${item.id}">
                        <div class="color-swatch" style="background-color: ${item.color};"></div>
                        <p>${item.name}</p>
                    </div>
                </div>
            `;
        });
        
        clothesList.innerHTML = clothingHTML;
    };

    // Populate clothing dropdowns
    const populateSelectDropdowns = (clothes) => {
        removeClothingSelect.innerHTML = '<option value="">Select item to remove</option>';
        updateClothingSelect.innerHTML = '<option value="">Select item to update</option>';
        
        if (clothes && clothes.length > 0) {
            clothes.forEach(item => {
                const removeOption = document.createElement('option');
                removeOption.value = item.id;
                removeOption.textContent = `${item.name} (${item.color})`;
                removeClothingSelect.appendChild(removeOption);
                
                const updateOption = document.createElement('option');
                updateOption.value = item.id;
                updateOption.textContent = `${item.name} (${item.color})`;
                updateOption.dataset.name = item.name;
                updateOption.dataset.color = item.color;
                updateClothingSelect.appendChild(updateOption);
            });
        }
    };

    // Load clothing
    const loadClothing = async () => {
        try {
            clothesList.innerHTML = '<p>Loading clothing items...</p>';
            
            const response = await fetch(API_ENDPOINTS.WARDROBE, {method: 'GET',headers: {'Accept': 'application/json'}, credentials: 'same-origin'});
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const clothes = await response.json();
            renderClothingList(clothes);
            populateSelectDropdowns(clothes);
        } catch (error) {
            clothesList.innerHTML = '<p>Error loading clothing items. Please try again later.</p>';
        }
    };

    // Add clothing item
    const addClothing = async () => {
        const name = addClothingName.value.trim();
        const color = addClothingColor.value.trim();
        
        if (!name || !color) {
            alert('Please enter both name and color for the clothing item');
            return;
        }
        
        try {
            const response = await fetch(API_ENDPOINTS.WARDROBE, {method: 'POST', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'}, credentials: 'same-origin', body: JSON.stringify({name: name, color: color})});       
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                addClothingName.value = '';
                addClothingColor.value = '';
                
                loadClothing();
                alert('Clothing item added successfully!');
            } else {
                alert(`Failed to add clothing: ${result.message || 'Unknown error'}`);
            }
        } catch (error) {
            alert(`Error adding clothing: ${error.message}`);
        }
    };

    // Remove clothing item
    const removeClothing = async () => {
        const clothingId = removeClothingSelect.value;
        
        if (!clothingId) {
            alert('Please select an item to remove');
            return;
        }
        
        if (confirm('Are you sure you want to remove this clothing item?')) {
            try {
                const response = await fetch(`${API_ENDPOINTS.WARDROBE}/${clothingId}`, {method: 'DELETE', headers: {'Accept': 'application/json'}, credentials: 'same-origin'});
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                
                const result = await response.json();
                
                if (result.success) {
                    removeClothingSelect.value = '';
                    
                    loadClothing();
                    alert('Clothing item removed successfully!');
                } else {
                    alert(`Failed to remove clothing: ${result.message || 'Unknown error'}`);
                }
            } catch (error) {
                alert(`Error removing clothing: ${error.message}`);
            }
        }
    };

    // Update clothing item
    const updateClothing = async () => {
        const clothingId = updateClothingSelect.value;
        const newName = newClothingName.value.trim();
        const newColor = newClothingColor.value.trim();
        
        if (!clothingId) {
            alert('Please select a clothing item to update');
            return;
        }
        
        if (!newName || !newColor) {
            alert('Please enter both new name and new color');
            return;
        }
        
        try {
            const response = await fetch(`${API_ENDPOINTS.WARDROBE}/${clothingId}`, {method: 'PUT', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'}, credentials: 'same-origin', body: JSON.stringify({new_name: newName, new_color: newColor})});
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const result = await response.json();
            if (result.success) {
                updateClothingSelect.value = '';
                newClothingName.value = '';
                newClothingColor.value = '';
                
                loadClothing();
                alert('Clothing item updated successfully!');
            } else {
                alert(`Failed to update clothing: ${result.message || 'Unknown error'}`);
            }
        } catch (error) {
            alert(`Error updating clothing: ${error.message}`);
        }
    };

    addClothingBtn.addEventListener('click', addClothing);
    removeClothingBtn.addEventListener('click', removeClothing);
    updateClothingBtn.addEventListener('click', updateClothing);

    loadUserProfile();
    loadClothing();
});