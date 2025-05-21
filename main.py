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
    logger.info(f"Начало обработки файла: {file.filename}")
    
    # Проверка расширения файла
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400, 
            detail="Требуется файл Excel (.xlsx или .xls)"
        )

    # Используем временную директорию для всех файлов
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.xlsx")
        output_md_path = os.path.join(temp_dir, "output.md")
        
        try:
            # Сохраняем входной файл
            with open(input_path, "wb") as f:
                contents = await file.read()
                if not contents:
                    raise HTTPException(status_code=400, detail="Файл пуст")
                f.write(contents)

            # Чтение данных из Excel с проверкой
            try:
                df = pd.read_excel(input_path, engine='openpyxl')
                logger.info(f"Успешно прочитано {len(df)} строк")
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ошибка чтения Excel файла: {str(e)}"
                )

            # Проверка колонок
            required_columns = ['Name', 'X', 'Y', 'Z']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Отсутствуют обязательные колонки: {', '.join(missing_columns)}"
                )

            # Проверка типов данных
            for col in ['X', 'Y', 'Z']:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Колонка {col} должна содержать числовые значения"
                    )

            # Преобразование координат
            try:
                df_transformed = GSK_2011(
                    sk1="СК-42",
                    sk2="ГСК-2011",
                    parameters_path="parameters.json",
                    df=df,
                    save_path=None
                ).rename(columns={
                    "X": "X_new",
                    "Y": "Y_new",
                    "Z": "Z_new"
                })
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка преобразования координат: {str(e)}"
                )

            # Генерация отчета
            try:
                generate_report_md(
                    df_before=df,
                    sk1="СК-42",
                    sk2="ГСК-2011",
                    parameters_path="parameters.json",
                    md_path=output_md_path
                )
                
                if not os.path.exists(output_md_path):
                    raise RuntimeError("Файл отчета не был создан")
                
                # Проверяем что отчет не пустой
                if os.path.getsize(output_md_path) == 0:
                    raise RuntimeError("Отчет пуст")

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка генерации отчета: {str(e)}"
                )

            # Возвращаем отчет
            return FileResponse(
                output_md_path,
                media_type="text/markdown",
                filename="coordinate_report.md"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка сервера"
            )
# Функция для поддержания активности на render.com

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

# подробное логирование

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)