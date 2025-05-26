let lastCity = null;

// Загружаем последний город при загрузке страницы
document.addEventListener('DOMContentLoaded', async function() {
    await loadLastCity();
    await loadSearchHistory();
});

// Обработчик формы поиска
document.getElementById('weather-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const city = document.getElementById('city-input').value.trim();
    if (!city) {
        showError('Пожалуйста, введите название города');
        return;
    }
    
    await searchWeather(city);
});

// Обработчики для последнего города
document.getElementById('use-last-city-btn').addEventListener('click', async function() {
    if (lastCity) {
        document.getElementById('city-input').value = lastCity;
        await searchWeather(lastCity);
        hideLastCitySuggestion();
    }
});

document.getElementById('dismiss-suggestion-btn').addEventListener('click', function() {
    hideLastCitySuggestion();
});

// Функция поиска погоды
async function searchWeather(city) {
    showLoading();
    
    try {
        const response = await fetch(`/api/weather?city=${encodeURIComponent(city)}`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка при получении данных');
        }
        
        const weatherData = await response.json();
        showWeather(weatherData);
        
        // Обновляем историю после успешного поиска
        await loadSearchHistory();
        
    } catch (error) {
        showError(error.message);
    }
}

// Загрузка последнего города
async function loadLastCity() {
    try {
        const response = await fetch('/api/last-city');
        const data = await response.json();
        
        if (data.last_city) {
            lastCity = data.last_city;
            showLastCitySuggestion(data.last_city, data.searched_at);
        }
    } catch (error) {
        console.error('Ошибка загрузки последнего города:', error);
    }
}

// Загрузка истории поиска
async function loadSearchHistory() {
    try {
        const response = await fetch('/api/history');
        const history = await response.json();
        
        if (history.length > 0) {
            showSearchHistory(history);
        }
    } catch (error) {
        console.error('Ошибка загрузки истории:', error);
    }
}

// Показ предложения последнего города
function showLastCitySuggestion(city, searchedAt) {
    const suggestion = document.getElementById('last-city-suggestion');
    const timeAgo = getTimeAgo(new Date(searchedAt));
    
    suggestion.querySelector('p').textContent = 
        `Посмотреть погоду в городе ${city}? (искали ${timeAgo})`;
    suggestion.style.display = 'flex';
}

function hideLastCitySuggestion() {
    document.getElementById('last-city-suggestion').style.display = 'none';
}

// Показ истории поиска
function showSearchHistory(history) {
    const historySection = document.getElementById('search-history');
    const historyList = document.getElementById('history-list');
    const toggleBtn = document.getElementById('toggle-history');
    
    historyList.innerHTML = '';
    
    history.forEach(search => {
        const item = document.createElement('div');
        item.className = 'history-item';
        item.innerHTML = `
            <div>
                <div class="history-city">${search.city}</div>
                <div class="history-temp">${Math.round(search.temperature)}°C - ${search.description}</div>
            </div>
            <div class="history-time">${getTimeAgo(new Date(search.searched_at))}</div>
        `;
        
        item.addEventListener('click', () => {
            document.getElementById('city-input').value = search.city;
            searchWeather(search.city);
        });
        
        historyList.appendChild(item);
    });
    
    historySection.style.display = 'block';
    
    // Обработчик переключения видимости истории
    toggleBtn.onclick = function() {
        const isHidden = historyList.style.display === 'none';
        historyList.style.display = isHidden ? 'block' : 'none';
        toggleBtn.textContent = isHidden ? 'Скрыть историю' : 'Показать историю';
    };
    
    // По умолчанию скрываем список
    historyList.style.display = 'none';
}

// Остальные функции (showLoading, showWeather, showError, getWeatherEmoji) остаются без изменений...

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
        'ясно': '☀️',
        'облачно': '☁️',
        'переменная облачность': '⛅',
        'небольшая облачность': '🌤️',
        'пасмурно': '☁️',
        'дождь': '🌧️',
        'небольшой дождь': '🌦️',
        'ливень': '⛈️',
        'снег': '❄️',
        'туман': '🌫️',
        'гроза': '⛈️'
    };
    
    const desc = description.toLowerCase();
    for (const [key, emoji] of Object.entries(emojiMap)) {
        if (desc.includes(key)) {
            return emoji;
        }
    }
    
    return '🌤️';
}

function getTimeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'только что';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} мин назад`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} ч назад`;
    
    return `${Math.floor(diffInSeconds / 86400)} дн назад`;
}
