# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse
import pandas as pd
from io import BytesIO
from coordinate_transform import GSK_2011, generate_full_report
import uvicorn

app = FastAPI()

@app.post("/process-excel/")
async def process_excel(file: UploadFile = File(...)):
    try:
        # Проверка типа файла
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(400, detail="Требуется файл Excel (.xlsx или .xls)")

        # Чтение файла
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

        # Генерация полного отчета
        report = generate_full_report(
            df_before=df,
            sk1="СК-42",
            sk2="ГСК-2011",
            parameters_path="parameters.json"
        )

        return PlainTextResponse(
            content=report,
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=report.md"}
        )

    except Exception as e:
        raise HTTPException(500, detail=f"Ошибка обработки: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)