from fastapi import FastAPI

app = FastAPI(
    title="SkyPeek",
    description="Приложение для получения прогноза погоды",
    version="1.0.0"
)

@app.get("/")
async def read_root():
    """Главная страница"""
    return {"message": "SkyPeek is running", "status": "ok"}

@app.get("/health")
async def health_check():
    """Проверка работоспособности"""
    return {"status": "ok", "service": "skypeek-app"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
