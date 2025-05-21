from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
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
from typing import Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация FastAPI приложения
app = FastAPI(
    title="Coordinate Transformation API",
    description="API для преобразования систем координат из Excel-файлов"
)

# Максимальный размер файла (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024

def cleanup_file(path: str):
    """Удаление временного файла с обработкой ошибок"""
    try:
        if path and os.path.exists(path):
            os.unlink(path)
    except Exception as e:
        logger.warning(f"Ошибка при удалении файла {path}: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Coordinate Transformation API работает",
        "endpoints": {
            "/process-excel/": "Загрузка и обработка Excel-файла с координатами"
        }
    }

@app.post("/process-excel/")
async def process_excel(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Обработка Excel-файла с координатами"""
    logger.info(f"Начало обработки файла: {file.filename}")
    
    # Проверка расширения файла
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400, 
            detail="Требуется файл Excel (.xlsx или .xls)"
        )

    # Используем временную директорию
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.xlsx")
        output_md_path = os.path.join(temp_dir, "output.md")
        
        try:
            # Чтение и проверка размера файла
            contents = await file.read()
            if len(contents) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"Файл слишком большой (максимум {MAX_FILE_SIZE/1024/1024:.1f}MB)"
                )
            if not contents:
                raise HTTPException(status_code=400, detail="Файл пуст")

            # Сохранение временного файла
            with open(input_path, "wb") as f:
                f.write(contents)
            background_tasks.add_task(cleanup_file, input_path)

            # Чтение данных с оптимизацией
            try:
                df = pd.read_excel(
                    input_path,
                    engine='openpyxl',
                    usecols=['Name', 'X', 'Y', 'Z'],
                    dtype={'Name': str, 'X': float, 'Y': float, 'Z': float}
                )
                logger.info(f"Прочитано {len(df)} строк")
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ошибка чтения Excel: {str(e)}"
                )

            # Проверка данных
            required_columns = ['Name', 'X', 'Y', 'Z']
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Отсутствуют колонки: {', '.join(missing)}"
                )

            if df[['X', 'Y', 'Z']].isnull().values.any():
                raise HTTPException(
                    status_code=400,
                    detail="Координаты X/Y/Z не могут быть пустыми"
                )

            # Преобразование координат
            try:
                df_transformed = GSK_2011(
                    sk1="СК-42",
                    sk2="ГСК-2011",
                    parameters_path="parameters.json",
                    df=df
                ).rename(columns={
                    "X": "X_new",
                    "Y": "Y_new",
                    "Z": "Z_new"
                })
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка преобразования: {str(e)}"
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
                    raise RuntimeError("Отчет не создан")
                if os.path.getsize(output_md_path) == 0:
                    raise RuntimeError("Отчет пуст")
                    
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка генерации отчета: {str(e)}"
                )

            # Возвращаем результат с фоновой очисткой
            background_tasks.add_task(cleanup_file, output_md_path)
            return FileResponse(
                output_md_path,
                media_type="text/markdown",
                filename="coordinate_report.md"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Внутренняя ошибка сервера"
            )

def keep_alive():
    """Поддержание активности сервера"""
    while True:
        time.sleep(300)
        try:
            requests.get(
                "https://univer-coordinate-backend.onrender.com",
                timeout=10
            )
            logger.info("Keep-alive request sent")
        except Exception as e:
            logger.warning(f"Keep-alive error: {str(e)}")

if __name__ == "__main__":
    # Запуск фонового потока
    threading.Thread(
        target=keep_alive,
        daemon=True,
        name="KeepAliveThread"
    ).start()
    
    # Запуск сервера
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        timeout_keep_alive=30
    )