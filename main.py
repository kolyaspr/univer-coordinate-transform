# FastAPI бэк

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import pandas as pd
import os
import tempfile
import uvicorn
from coordinate_transform import GSK_2011, generate_report_md

# Инициализация FastAPI приложения
app = FastAPI(
    title="Coordinate Transformation API",
    description="API для преобразования систем координат"
)

# Корневой эндпоинт для проверки работы API
@app.get("/")
async def root():
    return {
        "message": "Coordinate Transformation API работает",
        "endpoints": {
            "/process-csv/": "Загрузка и обработка CSV-файла с координатами"
        }
    }

# Основной эндпоинт для обработки файлов
@app.post("/process-csv/")
async def process_csv(file: UploadFile = File(...)):
    """
    Обрабатывает загруженный CSV-файл с координатами:
    1. Проверяет формат файла
    2. Сохраняет во временный файл
    3. Читает данные в DataFrame
    4. Выполняет преобразование координат
    5. Генерирует отчет в формате Markdown
    6. Возвращает отчет для скачивания
    """
    
    # Проверка расширения файла
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400, 
            detail="Требуется CSV-файл"
        )

    # Создание временных файлов
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_input:
        input_path = tmp_input.name
        tmp_input.write(await file.read())

    output_md_path = tempfile.NamedTemporaryFile(delete=False, suffix=".md").name

    try:
        # Чтение данных из CSV
        df = pd.read_csv(input_path)
        
        # Проверка необходимых колонок
        required_columns = ['Name', 'X', 'Y', 'Z']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(
                status_code=400,
                detail="CSV должен содержать колонки: Name, X, Y, Z"
            )

        # Преобразование координат между системами
        df_transformed = GSK_2011(
            sk1="СК-42",          # Исходная система координат
            sk2="ГСК-2011",       # Целевая система координат
            parameters_path="parameters.json",  # Файл параметров
            df=df,                # Входные данные
            save_path=None         # Не сохранять промежуточный результат
        )

        # Подготовка данных для отчета
        df_transformed = df_transformed.rename(columns={
            "X": "X_new",
            "Y": "Y_new",
            "Z": "Z_new"
        })

        # Генерация Markdown-отчета
        generate_report_md(
            df_before=df,          # Исходные данные
            sk1="СК-42",           # Исходная система
            sk2="ГСК-2011",        # Целевая система
            parameters_path="parameters.json",
            md_path=output_md_path, # Куда сохранить отчет
            csv_before=None,        # Не сохранять CSV
            csv_after=None         # Не сохранять CSV
        )

        # Возврат сгенерированного отчета
        return FileResponse(
            output_md_path,
            media_type="text/markdown",
            filename="report.md"
        )

    # Обработка любых ошибок
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обработки: {str(e)}"
        )
# ошибка

import threading
import time
import requests

def keep_alive():
    while True:
        time.sleep(300)  # Каждые 5 минут
        try:
            requests.get("https://univer-coordinate-backend.onrender.com")
        except:
            pass

if __name__ == "__main__":
    t = threading.Thread(target=keep_alive)
    t.daemon = True
    t.start()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))