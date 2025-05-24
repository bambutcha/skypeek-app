document.getElementById('weather-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const city = document.getElementById('city-input').value.trim();
    const resultDiv = document.getElementById('weather-result');
    
    if (!city) {
        resultDiv.innerHTML = '<p style="color: red;">Пожалуйста, введите название города</p>';
        resultDiv.classList.add('show');
        return;
    }
    
    resultDiv.innerHTML = '<p>Загрузка прогноза погоды...</p>';
    resultDiv.classList.add('show');
    
    // Пока что заглушка - API будет в следующем этапе
    setTimeout(() => {
        resultDiv.innerHTML = `
            <h3>Поиск погоды для: ${city}</h3>
            <p><em>🚧 Weather API будет подключено в следующем этапе</em></p>
            <p>Текущий статус: Готово к интеграции с Open-Meteo API</p>
        `;
    }, 1000);
});
