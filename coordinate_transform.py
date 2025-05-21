# Логика преобразования координат

import pandas as pd
import json
from sympy import symbols, Matrix, N, latex
from typing import Optional

def GSK_2011(sk1, sk2, parameters_path, df=None, csv_path=None, save_path=None):
    """
    Преобразует координаты между системами координат по алгоритму ГСК-2011.
    
    Параметры:
    sk1 (str): Исходная система координат
    sk2 (str): Целевая система координат
    parameters_path (str): Путь к JSON-файлу с параметрами преобразования
    df (DataFrame): Входные данные (опционально)
    csv_path (str): Путь к CSV-файлу (если df не указан)
    save_path (str): Куда сохранить результат (опционально)
    
    Возвращает:
    DataFrame с преобразованными координатами
    """
    
    # Специальный случай каскадного преобразования
    if sk1 == "СК-95" and sk2 == "СК-42":
        df_temp = GSK_2011("СК-95", "ПЗ-90.11", parameters_path, df=df)
        df_result = GSK_2011("ПЗ-90.11", "СК-42", parameters_path, df=df_temp, save_path=save_path)
        return df_result

    # Определение символьных переменных для формул
    ΔX, ΔY, ΔZ, ωx, ωy, ωz, m = symbols('ΔX ΔY ΔZ ωx ωy ωz m')
    X, Y, Z = symbols('X, Y, Z')

    # Основная формула преобразования
    formula = (1 + m) * Matrix([
        [1, ωz, -ωy],
        [-ωz, 1, ωx],
        [ωy, -ωx, 1]
    ]) @ Matrix([[X], [Y], [Z]]) + Matrix([[ΔX], [ΔY], [ΔZ]])

    # Загрузка параметров преобразования
    with open(parameters_path, 'r', encoding='utf-8') as f:
        parameters = json.load(f)

    if sk1 not in parameters:
        raise ValueError(f"Система {sk1} не найдена в {parameters_path}")

    param = parameters[sk1]
    
    # Подстановка параметров в формулу
    elements_const = {
        ΔX: param["ΔX"],
        ΔY: param["ΔY"],
        ΔZ: param["ΔZ"],
        ωx: param["ωx"],
        ωy: param["ωy"],
        ωz: param["ωz"],
        m: param["m"] * 1e-6  # Перевод в правильные единицы
    }

    # Загрузка данных (если не переданы напрямую)
    if df is None:
        if csv_path:
            df = pd.read_csv(csv_path)
        else:
            raise ValueError("Нужно передать либо df, либо путь к CSV")

    # Преобразование каждой точки
    transformed = []
    for _, row in df.iterrows():
        elements = {
            **elements_const,
            X: row["X"],
            Y: row["Y"],
            Z: row["Z"],
        }

        # Вычисление новых координат
        results_vector = formula.subs(elements).applyfunc(N)
        
        # Сохранение результата
        transformed.append([
            row["Name"],
            float(results_vector[0]),
            float(results_vector[1]),
            float(results_vector[2]),
        ])

    # Создание DataFrame с результатами
    df_result = pd.DataFrame(transformed, columns=["Name", "X", "Y", "Z"])

    # Сохранение в файл
    if save_path:
        df_result.to_csv(save_path, index=False)

    return df_result