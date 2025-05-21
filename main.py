# FastAPI бэк

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import pandas as pd
import os
import tempfile
import uvicorn
from coordinate_transform import GSK_2011, generate_report_md
import threading
import time
import requests
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация FastAPI приложения
app = FastAPI(
    title="Coordinate Transformation API",
    description="API для преобразования систем координат из Excel-файлов"
)

# Корневой эндпоинт для проверки работы API
@app.get("/")
async def root():
    return {
        "message": "Coordinate Transformation API работает",
        "endpoints": {
            "/process-excel/": "Загрузка и обработка Excel-файла с координатами"
        }
    }

# Основной эндпоинт для обработки Excel-файлов
@app.post("/process-excel/")
async def process_excel(file: UploadFile = File(...)):
    """
    Обрабатывает загруженный Excel-файл с координатами:
    1. Проверяет формат файла (XLSX или XLS)
    2. Сохраняет во временный файл
    3. Читает данные в DataFrame
    4. Выполняет преобразование координат
    5. Генерирует отчет в формате Markdown
    6. Возвращает отчет для скачивания
    """
    
    # Проверка расширения файла
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400, 
            detail="Требуется файл Excel (.xlsx или .xls)"
        )

    # Создаем временную директорию для всех файлов
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Сохраняем входной файл
            input_path = os.path.join(temp_dir, "input.xlsx")
            with open(input_path, "wb") as f:
                f.write(await file.read())

            # Чтение данных из Excel
            df = pd.read_excel(input_path, engine='openpyxl')
            
            # Проверка необходимых колонок
            required_columns = ['Name', 'X', 'Y', 'Z']
            if not all(col in df.columns for col in required_columns):
                raise HTTPException(
                    status_code=400,
                    detail="Excel файл должен содержать колонки: Name, X, Y, Z"
                )

            # Генерация отчета
            report_path = os.path.join(temp_dir, "report.md")
            generate_report_md(
                df_before=df,
                sk1="СК-42",
                sk2="ГСК-2011",
                parameters_path="parameters.json",
                md_path=report_path
            )

            # Проверяем что отчет создан
            if not os.path.exists(report_path):
                raise HTTPException(
                    status_code=500,
                    detail="Не удалось сгенерировать отчет"
                )

            # Возвращаем отчет
            return FileResponse(
                report_path,
                media_type="text/markdown",
                filename="coordinate_report.md"
            )

        except pd.errors.EmptyDataError:
            raise HTTPException(
                status_code=400,
                detail="Excel файл пуст или не содержит данных"
            )
        except Exception as e:
            logger.error(f"Ошибка обработки файла: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка обработки Excel файла: {str(e)}"
            )

# Функция для поддержания активности на render.com
def keep_alive():
    while True:
        time.sleep(300)  # Каждые 5 минут
        try:
            requests.get("https://univer-coordinate-backend.onrender.com")
            logger.info("Keep-alive request sent")
        except Exception as e:
            logger.warning(f"Keep-alive error: {str(e)}")

if __name__ == "__main__":
    t = threading.Thread(target=keep_alive)
    t.daemon = True
    t.start()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))