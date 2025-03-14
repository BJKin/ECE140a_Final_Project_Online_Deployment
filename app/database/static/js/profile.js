// DOM elements
const addDeviceBtn = document.getElementById('addDeviceBtn');
const removeDeviceBtn = document.getElementById('removeDeviceBtn');
const addDeviceId = document.getElementById('addDeviceId');
const addDeviceMac = document.getElementById('addDeviceMac');
const removeDeviceId = document.getElementById('removeDeviceId');
const deviceList = document.getElementById('deviceList');
const userName = document.getElementById('userName');
const userRole = document.getElementById('userRole');
const logoutForm = document.getElementById('logoutForm');

document.addEventListener('DOMContentLoaded', () => {

    // API endpoints
    const API_ENDPOINTS = {
        DEVICES: '/api/devices',
        PROFILE: '/api/profile',
        LOGOUT: '/logout'
    };

    // Show message
    const showMessage = (message, isError = false) => {
        alert(message);
    };

    // Render device list
    const renderDeviceList = (devices) => {
        if (!devices || devices.length === 0) {
            deviceList.innerHTML = '<p>No devices connected yet</p>';
            return;
        }
        
        let deviceListHtml = '';
        devices.forEach(device => {
            deviceListHtml += `
                <div class="device-item">
                    <div class="device-item-info">
                        <div class="device-id">Device ID: ${device.device_id}</div>
                        <div class="device-mac">MAC Address: ${device.mac_address}</div>
                    </div>
                </div>
            `;
        });
        
        deviceList.innerHTML = deviceListHtml;
    };

    // Get user data
    const getUserData = async () => {
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
    
    // Load users devices
    const loadDevices = async () => {
        try {
            const response = await fetch(API_ENDPOINTS.DEVICES, {method: 'GET', headers: {'Accept': 'application/json'}, credentials: 'same-origin'});
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const devices = await response.json();
            renderDeviceList(devices);
        } catch (error) {
            deviceList.innerHTML = '<p>Error loading devices. Please try again later.</p>';
        }
    };
    
    //Add a new device
    const addDevice = async () => {
        const deviceId = addDeviceId.value.trim();
        const macAddress = addDeviceMac.value.trim();
        
        if (!deviceId || !macAddress) {
            showMessage('Please enter both Device ID and MAC Address', true);
            return;
        }

        const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$|^([0-9A-Fa-f]{12})$/;
        if (!macAddress || !macRegex.test(macAddress)) {
            showMessage('Please try again, MAC Address was not properly formatted', true);
            return;
        }
        
        try {
            const response = await fetch(API_ENDPOINTS.DEVICES, {method: 'POST', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'}, credentials: 'same-origin', body: JSON.stringify({device_id: deviceId, mac_address: macAddress})});
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const result = await response.json();
            if (result.success) {
                addDeviceId.value = '';
                addDeviceMac.value = '';
                
                loadDevices();
                showMessage('Device added successfully!');
            } else {
                showMessage(`Failed to add device: ${result.message || 'Unknown error'}`, true);
            }
        } catch (error) {
            showMessage(`Error adding device: ${error.message}`, true);
        }
    };
    
    // Remove a device
    const removeDevice = async () => {
        const deviceId = removeDeviceId.value.trim();
        
        if (!deviceId) {
            showMessage('Please enter a Device ID to remove', true);
            return;
        }
        
        try {
            const devicesResponse = await fetch(API_ENDPOINTS.DEVICES, {method: 'GET', headers: {'Accept': 'application/json'}, credentials: 'same-origin'});
            
            if (!devicesResponse.ok) {
                throw new Error(`HTTP error! Status: ${devicesResponse.status}`);
            }
            
            const devices = await devicesResponse.json();
            const device = devices.find(d => d.device_id === deviceId);
            if (!device) {
                showMessage('Device not found. Please check the ID and try again.', true);
                return;
            }
            
            if (confirm(`Are you sure you want to remove device "${deviceId}"?`)) {
                const deleteUrl = `${API_ENDPOINTS.DEVICES}/${deviceId}?mac_address=${encodeURIComponent(device.mac_address)}`;
                
                const deleteResponse = await fetch(deleteUrl, {method: 'DELETE', headers: {'Accept': 'application/json'}, credentials: 'same-origin'});
                if (!deleteResponse.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                
                const result = await deleteResponse.json();
                if (result.success) {
                    removeDeviceId.value = '';

                    loadDevices();
                    showMessage('Device removed successfully!');
                } else {
                    showMessage(`Failed to remove device: ${result.message || 'Unknown error'}`, true);
                }
            }
        } catch (error) {
            showMessage(`Error removing device: ${error.message}`, true);
        }
    };
    
    // Handle logout
    const handleLogout = async (event) => {
        event.preventDefault();
        
        try {
            await fetch(API_ENDPOINTS.LOGOUT, {method: 'POST', credentials: 'same-origin'});
        } catch (error) {
            console.error('Error during logout:', error);
        } finally {
            window.location.href = '/login';
        }
    };
    
    if (addDeviceBtn) addDeviceBtn.addEventListener('click', addDevice);
    if (removeDeviceBtn) removeDeviceBtn.addEventListener('click', removeDevice);
    if (logoutForm) logoutForm.addEventListener('submit', handleLogout);
    
    getUserData();
    loadDevices();
});