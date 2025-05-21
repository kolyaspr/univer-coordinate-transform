# coordinate_transform.py
import pandas as pd
import json
from sympy import symbols, Matrix, N, latex
from typing import Optional
from io import StringIO

def GSK_2011(sk1, sk2, parameters_path, df=None, excel_path=None):
    """Преобразование координат без сохранения в файл"""
    with open(parameters_path, 'r', encoding='utf-8') as f:
        parameters = json.load(f)
    
    if sk1 not in parameters:
        raise ValueError(f"Система {sk1} не найдена в {parameters_path}")

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

    if df is None:
        if excel_path:
            df = pd.read_excel(excel_path, engine='openpyxl')
        else:
            raise ValueError("Нужно передать либо df, либо путь к Excel-файлу")

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

def generate_full_report(df_before, sk1, sk2, parameters_path):
    """Генерация полного отчета в строку"""
    ΔX, ΔY, ΔZ, ωx, ωy, ωz, m = symbols('ΔX ΔY ΔZ ωx ωy ωz m')
    X, Y, Z = symbols('X Y Z')
    
    general_formula = (1 + m) * Matrix([
        [1, ωz, -ωy],
        [-ωz, 1, ωx],
        [ωy, -ωx, 1]
    ]) @ Matrix([[X], [Y], [Z]]) + Matrix([[ΔX], [ΔY], [ΔZ]])

    with open(parameters_path, 'r', encoding='utf-8') as f:
        params = json.load(f)
    
    p = params.get(sk1)
    if p is None:
        raise ValueError(f"Система {sk1} не найдена в {parameters_path}")
    
    subs_common = {
        ΔX: p["ΔX"], ΔY: p["ΔY"], ΔZ: p["ΔZ"],
        ωx: p["ωx"], ωy: p["ωy"], ωz: p["ωz"],
        m: p["m"] * 1e-6
    }

    # Преобразование координат
    rows = []
    for _, r in df_before.iterrows():
        subs = {**subs_common, X: r["X"], Y: r["Y"], Z: r["Z"]}
        rv = general_formula.subs(subs).applyfunc(N)
        rows.append({
            "Name": r["Name"],
            "X_new": float(rv[0]),
            "Y_new": float(rv[1]),
            "Z_new": float(rv[2])
        })
    df_after = pd.DataFrame(rows)

    # Генерация отчета в StringIO
    report = StringIO()
    report.write("# Отчёт по преобразованию координат\n\n")
    report.write(f"**Исходная система**: {sk1}  \n")
    report.write(f"**Конечная система**: {sk2}  \n\n")

    report.write("## 1. Общая формула\n\n")
    report.write(f"$$\n{latex(general_formula)}\n$$\n\n")

    report.write("## 2. Формула с подстановкой параметров\n\n")
    formula_p = general_formula.subs(subs_common)
    report.write(f"$$\n{latex(formula_p)}\n$$\n\n")

    first = df_before.iloc[0]
    report.write("## 3. Пример для первой точки\n\n")
    report.write(f"- Исходные: $X={first['X']},\\;Y={first['Y']},\\;Z={first['Z']}$  \n")
    subs1 = {**subs_common, X: first["X"], Y: first["Y"], Z: first["Z"]}
    f3 = general_formula.subs(subs1)
    f3n = f3.applyfunc(N)
    report.write(f"- Подстановка в формулу:  \n  $$\n{latex(f3)}\n$$\n")
    report.write(f"- Численный результат: $X'={f3n[0]},\\;Y'={f3n[1]},\\;Z'={f3n[2]}$\n\n")

    report.write("## 4. Таблица до и после и статистика\n\n")
    report.write("| Name | X | Y | Z | X' | Y' | Z' |\n")
    report.write("|---|---|---|---|---|---|---|\n")
    for b, a in zip(df_before.itertuples(), df_after.itertuples()):
        report.write(f"|{b.Name}|{b.X:.6f}|{b.Y:.6f}|{b.Z:.6f}|"
                     f"{a.X_new:.6f}|{a.Y_new:.6f}|{a.Z_new:.6f}|\n")

    report.write("\n**Статистика (X', Y', Z'):**\n\n")
    stats = df_after[["X_new","Y_new","Z_new"]].agg(["mean","std"])
    for idx in stats.index:
        s = stats.loc[idx]
        report.write(f"- {idx}: X'={s['X_new']:.3f}, Y'={s['Y_new']:.3f}, Z'={s['Z_new']:.3f}\n")

    return report.getvalue()