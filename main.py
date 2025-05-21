# FastAPI-бэкенд для обработки Excel


from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse
import pandas as pd
from io import BytesIO
import json
import uvicorn
import threading
import time
import requests
from sympy import symbols, Matrix, N, latex
import os

app = FastAPI(
    title="Coordinate Transformation API",
    description="API для преобразования систем координат из Excel-файлов"
)

# Загружаем параметры при старте
with open("parameters.json", "r", encoding="utf-8") as f:
    PARAMETERS = json.load(f)

def transform_coordinates(df, sk1, sk2):
    """Преобразование координат полностью в памяти"""
    if sk1 not in PARAMETERS:
        raise ValueError(f"Система {sk1} не найдена в параметрах")

    ΔX, ΔY, ΔZ, ωx, ωy, ωz, m = symbols('ΔX ΔY ΔZ ωx ωy ωz m')
    X, Y, Z = symbols('X Y Z')

    formula = (1 + m) * Matrix([
        [1, ωz, -ωy],
        [-ωz, 1, ωx],
        [ωy, -ωx, 1]
    ]) @ Matrix([[X], [Y], [Z]]) + Matrix([[ΔX], [ΔY], [ΔZ]])

    param = PARAMETERS[sk1]
    elements_const = {
        ΔX: param["ΔX"],
        ΔY: param["ΔY"],
        ΔZ: param["ΔZ"],
        ωx: param["ωx"],
        ωy: param["ωy"],
        ωz: param["ωz"],
        m: param["m"] * 1e-6
    }

    transformed = []
    for _, row in df.iterrows():
        elements = {**elements_const, X: row["X"], Y: row["Y"], Z: row["Z"]}
        results_vector = formula.subs(elements).applyfunc(N)
        transformed.append([
            row["Name"],
            float(results_vector[0]),
            float(results_vector[1]),
            float(results_vector[2])
        ])

    return pd.DataFrame(transformed, columns=["Name", "X", "Y", "Z"])

@app.post("/process-excel/")
async def process_excel(file: UploadFile = File(...)):
    try:
        # Проверка типа файла
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(400, detail="Требуется файл Excel (.xlsx или .xls)")

        # Чтение содержимого файла в память
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents), engine='openpyxl')

        # Проверка колонок
        required_columns = ['Name', 'X', 'Y', 'Z']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(400, detail="Файл должен содержать колонки: Name, X, Y, Z")

        # Преобразование координат
        df_transformed = transform_coordinates(df, "СК-42", "ГСК-2011")

        # Генерация отчета в памяти
        report = generate_markdown(df, df_transformed, "СК-42", "ГСК-2011")

        return PlainTextResponse(
            content=report,
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=report.md"}
        )

    except Exception as e:
        raise HTTPException(500, detail=f"Ошибка обработки: {str(e)}")

def generate_markdown(df_before, df_after, sk1, sk2):
    """Генерация Markdown полностью в памяти"""
    report = []
    report.append("# Отчёт по преобразованию координат\n\n")
    report.append(f"**Исходная система**: {sk1}  \n")
    report.append(f"**Конечная система**: {sk2}  \n\n")

    return "".join(report)

# эндпоинт для корневого URL (/)
@app.get("/")
async def health_check():
    return {"status": "ok", "systems": list(PARAMETERS.keys())}

def keep_alive():
    while True:
        time.sleep(300) # чтоб не засыпал
        try:
            requests.get("https://univer-coordinate-backend.onrender.com")
        except:
            pass

if __name__ == "__main__":
    t = threading.Thread(target=keep_alive)
    t.daemon = True
    t.start()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))