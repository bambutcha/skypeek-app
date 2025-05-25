document.getElementById('weather-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const city = document.getElementById('city-input').value.trim();
    const resultDiv = document.getElementById('weather-result');
    
    if (!city) {
        showError('Пожалуйста, введите название города');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`/api/weather?city=${encodeURIComponent(city)}`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка при получении данных');
        }
        
        const weatherData = await response.json();
        showWeather(weatherData);
        
    } catch (error) {
        showError(error.message);
    }
});

function showLoading() {
    const resultDiv = document.getElementById('weather-result');
    resultDiv.innerHTML = `
        <div class="loading">
            <p>🌤️ Загрузка прогноза погоды...</p>
        </div>
    `;
    resultDiv.classList.add('show');
}

function showWeather(data) {
    const resultDiv = document.getElementById('weather-result');
    
    // Определяем emoji для погоды
    const weatherEmoji = getWeatherEmoji(data.description);
    
    resultDiv.innerHTML = `
        <div class="weather-card">
            <h3>${weatherEmoji} ${data.city}</h3>
            <div class="weather-main">
                <div class="temperature">
                    <span class="temp-value">${Math.round(data.temperature)}°C</span>
                    <span class="feels-like">Ощущается как ${Math.round(data.feels_like)}°C</span>
                </div>
                <div class="weather-desc">${data.description}</div>
            </div>
            <div class="weather-details">
                <div class="detail-item">
                    <span class="detail-label">💧 Влажность:</span>
                    <span class="detail-value">${data.humidity}%</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">💨 Ветер:</span>
                    <span class="detail-value">${data.wind_speed} км/ч</span>
                </div>
            </div>
            <div class="timestamp">
                Обновлено: ${new Date(data.timestamp).toLocaleString('ru-RU')}
            </div>
        </div>
    `;
    resultDiv.classList.add('show');
}

function showError(message) {
    const resultDiv = document.getElementById('weather-result');
    resultDiv.innerHTML = `
        <div class="error">
            <p>❌ ${message}</p>
            <p><small>Попробуйте ввести название города на русском или английском языке</small></p>
        </div>
    `;
    resultDiv.classList.add('show');
}

function getWeatherEmoji(description) {
    const emojiMap = {
        'Ясно': '☀️',
        'В основном ясно': '🌤️', 
        'Переменная облачность': '⛅',
        'Пасмурно': '☁️',
        'Туман': '🌫️',
        'Легкий дождь': '🌦️',
        'Умеренный дождь': '🌧️',
        'Сильный дождь': '⛈️',
        'Ливень': '⛈️',
        'Легкий снег': '🌨️',
        'Умеренный снег': '❄️',
        'Сильный снег': '❄️',
        'Гроза': '⛈️'
    };
    
    return emojiMap[description] || '🌤️';
}
