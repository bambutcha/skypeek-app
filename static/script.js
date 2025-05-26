let lastCity = null;
let autocompleteTimeout = null;
let selectedIndex = -1;
let autocompleteItems = [];

// Загружаем последний город при загрузке страницы
document.addEventListener('DOMContentLoaded', async function() {
    await loadLastCity();
    await loadSearchHistory();
    setupAutocomplete();
});

// Настройка автодополнения
function setupAutocomplete() {
    const input = document.getElementById('city-input');
    const dropdown = document.getElementById('autocomplete-dropdown');
    
    // Обработчик ввода текста
    input.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            hideAutocomplete();
            return;
        }
        
        // Debounce - ждем 300ms после последнего ввода
        clearTimeout(autocompleteTimeout);
        autocompleteTimeout = setTimeout(() => {
            fetchCitySuggestions(query);
        }, 300);
    });
    
    // Обработчик клавий
    input.addEventListener('keydown', function(e) {
        const dropdown = document.getElementById('autocomplete-dropdown');
        
        if (dropdown.style.display === 'none') return;
        
        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, autocompleteItems.length - 1);
                updateSelection();
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, -1);
                updateSelection();
                break;
                
            case 'Enter':
                e.preventDefault();
                if (selectedIndex >= 0) {
                    selectCity(autocompleteItems[selectedIndex]);
                } else {
                    document.getElementById('weather-form').dispatchEvent(new Event('submit'));
                }
                break;
                
            case 'Escape':
                hideAutocomplete();
                break;
        }
    });
    
    // Скрываем автодополнение при клике вне
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-container')) {
            hideAutocomplete();
        }
    });
    
    // Предотвращаем скрытие при клике на dropdown
    dropdown.addEventListener('click', function(e) {
        e.stopPropagation();
    });
}

// Получение предложений городов
async function fetchCitySuggestions(query) {
    try {
        const response = await fetch(`/api/cities?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        showAutocomplete(data.cities);
    } catch (error) {
        console.error('Ошибка получения предложений городов:', error);
        hideAutocomplete();
    }
}

// Показ автодополнения
function showAutocomplete(cities) {
    const dropdown = document.getElementById('autocomplete-dropdown');
    const input = document.getElementById('city-input');
    
    if (cities.length === 0) {
        hideAutocomplete();
        return;
    }
    
    autocompleteItems = cities;
    selectedIndex = -1;
    
    dropdown.innerHTML = '';
    
    cities.forEach((city, index) => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.innerHTML = `
            <span class="city-name">${city.name}</span>
            <span class="city-source source-${city.source}">
                ${city.source === 'history' ? 'Из истории' : 'Найдено'}
            </span>
        `;
        
        item.addEventListener('click', () => selectCity(city));
        item.addEventListener('mouseenter', () => {
            selectedIndex = index;
            updateSelection();
        });
        
        dropdown.appendChild(item);
    });
    
    input.classList.add('autocomplete-active');
    dropdown.style.display = 'block';
}

// Скрытие автодополнения
function hideAutocomplete() {
    const dropdown = document.getElementById('autocomplete-dropdown');
    const input = document.getElementById('city-input');
    
    dropdown.style.display = 'none';
    input.classList.remove('autocomplete-active');
    selectedIndex = -1;
    autocompleteItems = [];
}

// Обновление выделения в списке
function updateSelection() {
    const items = document.querySelectorAll('.autocomplete-item');
    
    items.forEach((item, index) => {
        if (index === selectedIndex) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }
    });
}

// Выбор города из автодополнения
function selectCity(city) {
    const input = document.getElementById('city-input');
    input.value = city.name;
    hideAutocomplete();
    
    // Автоматический поиск после выбора
    searchWeather(city.name);
}

// Обработчик формы поиска
document.getElementById('weather-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const city = document.getElementById('city-input').value.trim();
    if (!city) {
        showError('Пожалуйста, введите название города');
        return;
    }
    
    hideAutocomplete();
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

// Остальные функции остаются без изменений...
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
