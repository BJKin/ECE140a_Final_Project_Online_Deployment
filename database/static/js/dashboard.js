// DOM Elements
const userName = document.getElementById('userName');
const userRole = document.getElementById('userRole');
const deviceSelect = document.getElementById('deviceSelect');
const weatherAssistBtn = document.getElementById('weatherAssistBtn');
const aiResponse = document.getElementById('aiResponse');
const aiMessageElement = document.getElementById('aiMessage');
const closeAiResponse = document.getElementById('closeAiResponse');
const locationElement = document.getElementById("location");
const condElement = document.getElementById("conditions");
const tempElement = document.getElementById("temperature");
const forecastElement = document.getElementById("forecast");

const last24HoursBtn = document.getElementById('last24HoursBtn');
const lastWeekBtn = document.getElementById('lastWeekBtn');

// Chart 
let deviceDataChart;
let updateInterval;
const UPDATE_FREQUENCY = 1000;
let currentTimeRange = 'week';

// Weather API
let userLocation = "";
let currentTemperature = "";
let currentConditions = "";
let forecastConditions = "";

// API Endpoints
const API_ENDPOINTS = {
    PROFILE: "/api/profile",
    DEVICES: "/api/devices",
    DEVICE_DATA: "/api/devices",
    WARDROBE: "/api/wardrobe",
    AI: "/api/ai"
};

document.addEventListener('DOMContentLoaded', () => {

    // Load user profile data
    const loadUserProfile = async () => {
        try {
            const response = await fetch(API_ENDPOINTS.PROFILE, {method: 'GET', headers: {'Accept': 'application/json'}, credentials: 'same-origin'});
            const userData = await response.json();

            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            userLocation = userData.location;
            
            if (userName && userData) {
                userName.textContent = userData.name || 'User';
                userRole.textContent = "ESP32 Champion";
            }
            
            await loadWeatherData(userLocation);
        } catch (error) {
            console.error('Error fetching user data:', error);
        }
    };

    // Load weather data
    const loadWeatherData = async (location) => {
        try {
            if (locationElement) {
                locationElement.textContent = `Location: ${location}`;
            }
            
            const enc_city = encodeURIComponent(location);
            const geoResponse = await fetch(`https://nominatim.openstreetmap.org/search?q=${enc_city}&format=json`);
            const geoData = await geoResponse.json();
            
            if (!geoData || geoData.length === 0) {
                console.error('Location not found');
                return;
            }
            
            const lat = geoData[0].lat;
            const lon = geoData[0].lon;
            
            const pointsResponse = await fetch(`https://api.weather.gov/points/${lat},${lon}`);
            const pointsData = await pointsResponse.json();
            
            const forecastUrl = pointsData.properties.forecast;
            const forecastResponse = await fetch(forecastUrl);
            const forecastData = await forecastResponse.json();
            
            const currentPeriod = forecastData.properties.periods[0];
            const nextPeriod = forecastData.properties.periods[1];
            
            currentTemperature = `${currentPeriod.temperature} ${currentPeriod.temperatureUnit}`;
            currentConditions = currentPeriod.shortForecast;
            forecastConditions = nextPeriod.shortForecast;
            

            if (tempElement) {
                tempElement.textContent = `Temperature: ${currentTemperature}`;
            }
            if (condElement) {
                condElement.textContent = `Conditions: ${currentConditions}`;
            }
            if (forecastElement) {
                forecastElement.textContent = `Forecast: ${forecastConditions}`;
            }
        } catch (error) {
            console.error('Error loading weather data:', error)
        }
    };

    // Get user's wardrobe
    const getUserWardrobe = async () => {
        try {
            const response = await fetch(API_ENDPOINTS.WARDROBE, {method: 'GET', headers: {'Accept': 'application/json'}, credentials: 'same-origin'});   
            
            const wardrobe = await response.json();
            return wardrobe;
        } catch (error) {
            console.error('Error fetching wardrobe:', error);
            return [];
        }
    };

    // Function to initialize device dropdown
    const initDeviceDropdown = async () => {
        try {
            const response = await fetch(API_ENDPOINTS.DEVICES, {method: 'GET', headers: {'Accept': 'application/json'}, credentials: 'same-origin'});
            
            const devices = await response.json();
            deviceSelect.innerHTML = '<option value="">Select a device</option>';
            
            if (devices && devices.length > 0) {
                devices.forEach(device => {
                    const option = document.createElement('option');
                    option.value = device.id;
                    option.textContent = `${device.device_id}`;
                    deviceSelect.appendChild(option);
                });
                
                deviceSelect.value = devices[0].id;
                startDeviceDataUpdates(devices[0].id);
            } else {
                updateDeviceDataChart([], []);
            }
        } catch (error) {
            console.error('Error loading devices:', error);
        }
    };

    // Event listener for device selection changes
    if (deviceSelect) {
        deviceSelect.addEventListener('change', () => {
            const selectedDeviceId = deviceSelect.value;
            if (selectedDeviceId) {
                startDeviceDataUpdates(selectedDeviceId);
            } else {
                if (updateInterval) {
                    clearInterval(updateInterval);
                }
                updateDeviceDataChart([], []);
            }
        });
    }


    const initTimeFilterButtons = () => {
        if (last24HoursBtn && lastWeekBtn) {
            lastWeekBtn.classList.add('active');
            
            last24HoursBtn.addEventListener('click', () => {
                setActiveTimeFilter('day');
            });
            lastWeekBtn.addEventListener('click', () => {
                setActiveTimeFilter('week');
            });
        }
    };
    
    // Set active time filter
    const setActiveTimeFilter = (timeRange) => {

        currentTimeRange = timeRange;
        last24HoursBtn.classList.toggle('active', timeRange === 'day');
        lastWeekBtn.classList.toggle('active', timeRange === 'week');
        
        const selectedDeviceId = deviceSelect.value;
        if (selectedDeviceId) {
            loadDeviceData(selectedDeviceId);
        }
    };
    
    // Calculate time range based on current selection
    const calculateTimeRange = () => {
        const now = new Date();
        let startDate = new Date(now);
        
        if (currentTimeRange === 'day') {
            startDate.setDate(now.getDate() - 1);
        } else{
            startDate.setDate(now.getDate() - 7);
        }
        
        return {
            startDate: startDate.toISOString().split('.')[0].replace('T', ' '),
            endDate: now.toISOString().split('.')[0].replace('T', ' ')
        };
    };
    
    // Load device sensor data with time filtering
    const loadDeviceData = async (deviceId) => {
        try {
            const { startDate, endDate } = calculateTimeRange();
    
            const url = new URL(`${API_ENDPOINTS.DEVICE_DATA}/${deviceId}/data`, window.location.origin);
            url.searchParams.append('start_date', startDate);
            url.searchParams.append('end_date', endDate);
            
            const response = await fetch(url, {method: 'GET', headers: {'Accept': 'application/json'}, credentials: 'same-origin'});
            
            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            if (!data) {
                updateDeviceDataChart([], [], [], []);
                return;
            }
            
            const timestamps = data.map(item => {
                const date = new Date(item.timestamp);
                
                if (currentTimeRange === 'day') {
                    return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                } else {
                    return `${date.toLocaleDateString([], {month: 'short', day: 'numeric'})} ${date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
                }
            });
            
            const temperatures = data.map(item => item.temperature);
            const pressures = data.map(item => item.pressure);
            const temperatureUnit = data.length > 0 ? data[0].temperature_unit : '°C';
            const pressureUnit = data.length > 0 ? data[0].pressure_unit : 'Pa';
            
            updateDeviceDataChart(timestamps, temperatures, pressures, [temperatureUnit, pressureUnit]);
        } catch (error) {
            console.error('Error loading device data:', error);
        }
    };
    
    // Start auto-updating device data
    const startDeviceDataUpdates = (deviceId) => {

        if (updateInterval) {
            clearInterval(updateInterval);
        }

        loadDeviceData(deviceId);
        
        updateInterval = setInterval(() => {
            loadDeviceData(deviceId);
        }, UPDATE_FREQUENCY);
    };
    
    // Initialize device data chart
    const initDeviceDataChart = () => {
        const canvas = document.getElementById('deviceDataChart');
        if (!canvas) {
            console.error('Chart canvas element not found');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        if (deviceDataChart) {
            deviceDataChart.destroy();
        }
        
        deviceDataChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Temperature (°C)',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        yAxisID: 'y',
                    },
                    {
                        label: 'Pressure (Pa)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        yAxisID: 'y1',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2.5,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                stacked: false,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Temperature (°C)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false,
                        },
                        title: {
                            display: true,
                            text: 'Pressure (Pa)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                }
            }
        });
    };

    // Update device data chart
    const updateDeviceDataChart = (labels, temperatureData, pressureData, units = ['°C', 'Pa']) => {
        if (deviceDataChart) {
            deviceDataChart.data.labels = labels;
            
            deviceDataChart.data.datasets[0].data = temperatureData;
            deviceDataChart.data.datasets[0].label = `Temperature (${units[0]})`;
            deviceDataChart.options.scales.y.title.text = `Temperature (${units[0]})`;
            
            deviceDataChart.data.datasets[1].data = pressureData;
            deviceDataChart.data.datasets[1].label = `Pressure (${units[1]})`;
            deviceDataChart.options.scales.y1.title.text = `Pressure (${units[1]})`;
            
            deviceDataChart.update();
        }
    };

    // Show AI response
    const showAiResponse = async () => {
        try {
            if (aiResponse) {
                aiResponse.style.display = 'block';
            }
            if (aiMessageElement) {
                aiMessageElement.textContent = "Thinking about what you should wear...";
            }
            
            const wardrobe = await getUserWardrobe();
            const clothingList = wardrobe.map(item => {
                if (item.color) {
                    return `${item.color} ${item.name}`;
                }
                return item.name;
            }).join(', ');

            let aiPrompt;
            if (wardrobe.length !== 0){
                aiPrompt = {
                    prompt: `It is currently ${currentTemperature} and ${currentConditions} outside and forecasted to be ${forecastConditions}. 
                    I need to decide what to wear from the following list: ${clothingList}. What should I wear? Do not comment on non chosen items.`
                };
            } else {
                aiPrompt = {
                    prompt: `It is currently ${currentTemperature} and ${currentConditions} outside and forecasted to be ${forecastConditions}. 
                    The user does not have any clothes added to their wardrobe, tell them so and what they should buy to fit the current conditions.`
                };
            }
            
            const response = await fetch(API_ENDPOINTS.AI, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(aiPrompt)});
            
            if (!response.ok) {
                throw new Error(`AI API error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            if (aiMessageElement && data.result && data.result.response) {
                aiMessageElement.textContent = data.result.response;
            } else {
                throw new Error('Invalid AI response format');
            }
            
        } catch (error) {
            console.error('Error fetching AI response:', error);
            if (aiMessageElement) {
                aiMessageElement.textContent = "Sorry, I couldn't provide a recommendation right now.";
            }
        }
    };

    const hideAiResponse = () => {
        if (aiResponse) {
            aiResponse.style.display = 'none';
        }
    };

    if (weatherAssistBtn) {
        weatherAssistBtn.addEventListener('click', showAiResponse);
    }
    if (closeAiResponse) {
        closeAiResponse.addEventListener('click', hideAiResponse);
    }

    loadUserProfile();
    initDeviceDataChart();
    initDeviceDropdown();
    initTimeFilterButtons();
    
    if (aiResponse) {
        aiResponse.style.display = 'none';
    }
});