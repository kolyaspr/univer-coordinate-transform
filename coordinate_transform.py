import pandas as pd
import json
from sympy import symbols, Matrix, N, latex
from typing import Optional
from io import BytesIO

def GSK_2011(sk1, sk2, parameters_path, df=None, excel_path=None, save_path=None):
    """
    Преобразует координаты между системами координат по алгоритму ГСК-2011.
    """
    try:
        # Загрузка параметров
        with open(parameters_path, 'r', encoding='utf-8') as f:
            parameters = json.load(f)

        if sk1 not in parameters:
            raise ValueError(f"Система {sk1} не найдена в {parameters_path}")

        # Специальный случай каскадного преобразования
        if sk1 == "СК-95" and sk2 == "СК-42":
            df_temp = GSK_2011("СК-95", "ПЗ-90.11", parameters_path, df=df)
            return GSK_2011("ПЗ-90.11", "СК-42", parameters_path, df=df_temp)

        ΔX, ΔY, ΔZ, ωx, ωy, ωz, m = symbols('ΔX ΔY ΔZ ωx ωy ωz m')
        X, Y, Z = symbols('X Y Z')

        formula = (1 + m) * Matrix([
            [1, ωz, -ωy],
            [-ωz, 1, ωx],
            [ωy, -ωx, 1]
        ]) @ Matrix([[X], [Y], [Z]]) + Matrix([[ΔX], [ΔY], [ΔZ]])

        param = parameters[sk1]
        elements_const = {
            ΔX: param["ΔX"],
            ΔY: param["ΔY"],
            ΔZ: param["ΔZ"],
            ωx: param["ωx"],
            ωy: param["ωy"],
            ωz: param["ωz"],
            m: param["m"] * 1e-6
        }

        # Загрузка данных
        if df is None:
            if excel_path:
                df = pd.read_excel(excel_path, engine='openpyxl')
            else:
                raise ValueError("Нужно передать либо df, либо путь к Excel-файлу")

        # Преобразование координат
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

        df_result = pd.DataFrame(transformed, columns=["Name", "X", "Y", "Z"])

        if save_path:
            df_result.to_excel(save_path, index=False, engine='openpyxl')

        return df_result

    except Exception as e:
        raise ValueError(f"Ошибка преобразования: {str(e)}")