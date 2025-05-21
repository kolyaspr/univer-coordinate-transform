from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pandas as pd
from io import BytesIO
from coordinate_transform import GSK_2011, generate_markdown_report
import json
import uvicorn  # Добавлен импорт uvicorn
import threading
import time
import requests
import os

app = FastAPI(
    title="Coordinate Transformation API",
    description="API для преобразования систем координат из Excel-файлов"
)

# Загружаем параметры один раз при старте
with open("parameters.json", "r", encoding="utf-8") as f:
    PARAMETERS = json.load(f)

@app.post("/process-excel/")
async def process_excel(file: UploadFile = File(...)):
    try:
        # Проверка типа файла
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(400, detail="Требуется файл Excel (.xlsx или .xls)")

        # Чтение файла в память
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents), engine='openpyxl')

        # Проверка колонок
        required_columns = ['Name', 'X', 'Y', 'Z']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(400, detail="Файл должен содержать колонки: Name, X, Y, Z")

        # Преобразование координат
        df_transformed = GSK_2011(
            sk1="СК-42",
            sk2="ГСК-2011",
            parameters_path="parameters.json",
            df=df
        )

        # Генерация отчета в памяти
        report_content = generate_markdown_report(
            df_before=df,
            df_after=df_transformed,
            sk1="СК-42",
            sk2="ГСК-2011",
            parameters=PARAMETERS
        )

        return Response(
            content=report_content,
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=report.md"}
        )

    except Exception as e:
        raise HTTPException(500, detail=f"Ошибка обработки: {str(e)}")

@app.get("/")
async def health_check():
    return {"status": "ok", "systems": list(PARAMETERS.keys())}

def keep_alive():
    while True:
        time.sleep(300)
        try:
            requests.get("https://univer-coordinate-backend.onrender.com")
        except:
            pass

if __name__ == "__main__":
    t = threading.Thread(target=keep_alive)
    t.daemon = True
    t.start()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))