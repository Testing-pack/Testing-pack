from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.experiments import router as experiments_router
from api.metrics import router as metrics_router
from api.files import router as files_router
from api.mapping import router as mapping_router
from api.split import router as health_router, experiments_storage

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging
# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)






app = FastAPI(title="A/B Test Configuration API")



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Преобразуем ошибки, заменяя несериализуемые объекты (например, ValueError) на строки
    errors = []
    for error in exc.errors():
        error_copy = dict(error)
        if 'ctx' in error_copy and 'error' in error_copy['ctx']:
            error_copy['ctx']['error'] = str(error_copy['ctx']['error'])
        errors.append(error_copy)

    logger.error(f"Validation error for {request.method} {request.url}")
    logger.error(f"Errors: {errors}")
    body = await request.body()
    logger.error(f"Request body: {body.decode('utf-8', errors='ignore')}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors, "body": exc.body},
    )
# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(experiments_router)
app.include_router(metrics_router)
app.include_router(files_router)
app.include_router(mapping_router)
app.include_router(health_router)

# Экспорт глобального хранилища для обратной совместимости
app.state.experiments_storage = experiments_storage


@app.on_event("startup")
async def startup_event():
    """Создание таблиц и инициализация при запуске приложения"""
    try:
        from core.database_pgsql import async_engine, Base
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Таблицы базы данных созданы/проверены")
    except Exception as e:
        logger.error(f"Ошибка запуска приложения: {e}")


if __name__ == "__main__":
    import uvicorn

    logger.info("   Запуск A/B Test Configuration API...")
    logger.info("   Доступные эндпоинты:")
    logger.info("   GET  / - информация о API")
    logger.info("   GET  /health - проверка состояния")
    logger.info("   GET  /experiments - все эксперименты")
    logger.info("   GET  /experiment/{test_id} - детали эксперимента")
    logger.info("   PUT  /experiment/{test_id} - обновить эксперимент")
    logger.info("   DELETE /experiment/{test_id} - удалить эксперимент")
    logger.info("   PATCH /experiment/{test_id}/status - обновить статус")
    logger.info("   POST /experiment/{test_id}/metric - добавить метрику")
    logger.info("   DELETE /experiment/{test_id}/metric/{index} - удалить метрику")
    logger.info("   GET  /metrics/available - список метрик")
    logger.info("   GET  /available_data_sources - список источников данных")
    logger.info("   POST /files/upload_csv - загрузка CSV файла")
    logger.info("   POST /files/analyze_csv - детальный анализ CSV файла")
    logger.info("   GET  /files/s3_files - файлы в S3")
    logger.info("   POST /experiments/setup_test - создание A/B теста")
    logger.info("   POST /metrics/calculate_sample_size - расчет размера выборки")
    logger.info("   GET  /mapping/experiment/{experiment_id} - схемы маппинга")
    logger.info("   POST /mapping/upload_csv_with_mapping - загрузка с маппингом")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)