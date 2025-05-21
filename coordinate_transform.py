import pandas as pd
from sympy import symbols, Matrix, N, latex
import json  # Добавлен импорт json

def GSK_2011(sk1, sk2, parameters_path, df=None, excel_path=None):
    """
    Преобразует координаты между системами координат (работает только в памяти)
    """
    # Загрузка параметров
    with open(parameters_path, 'r', encoding='utf-8') as f:
        parameters = json.load(f)

    if sk1 not in parameters:
        raise ValueError(f"Система {sk1} не найдена в параметрах")

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

    return pd.DataFrame(transformed, columns=["Name", "X", "Y", "Z"])

def generate_markdown_report(df_before, df_after, sk1, sk2, parameters):
    """Генерация Markdown-отчета в памяти (без сохранения в файл)"""
    ΔX, ΔY, ΔZ, ωx, ωy, ωz, m = symbols('ΔX ΔY ΔZ ωx ωy ωz m')
    X, Y, Z = symbols('X Y Z')
    
    general_formula = (1 + m) * Matrix([
        [1, ωz, -ωy],
        [-ωz, 1, ωx],
        [ωy, -ωx, 1]
    ]) @ Matrix([[X], [Y], [Z]]) + Matrix([[ΔX], [ΔY], [ΔZ]])

    p = parameters.get(sk1)
    if p is None:
        raise ValueError(f"Система {sk1} не найдена в параметрах")
    
    subs_common = {
        ΔX: p["ΔX"], ΔY: p["ΔY"], ΔZ: p["ΔZ"],
        ωx: p["ωx"], ωy: p["ωy"], ωz: p["ωz"],
        m: p["m"] * 1e-6
    }

    # Собираем отчет в строку
    report = []
    report.append("# Отчёт по преобразованию координат\n\n")
    report.append(f"**Исходная система**: {sk1}  \n")
    report.append(f"**Конечная система**: {sk2}  \n\n")

    report.append("## 1. Общая формула\n\n")
    report.append(f"$$\n{latex(general_formula)}\n$$\n\n")

    report.append("## 2. Формула с подстановкой параметров\n\n")
    formula_p = general_formula.subs(subs_common)
    report.append(f"$$\n{latex(formula_p)}\n$$\n\n")

    first = df_before.iloc[0]
    report.append("## 3. Пример для первой точки\n\n")
    report.append(f"- Исходные: $X={first['X']},\\;Y={first['Y']},\\;Z={first['Z']}$  \n")
    subs1 = {**subs_common, X: first["X"], Y: first["Y"], Z: first["Z"]}
    f3 = general_formula.subs(subs1)
    f3n = f3.applyfunc(N)
    report.append(f"- Подстановка в формулу:  \n  $$\n{latex(f3)}\n$$\n")
    report.append(f"- Численный результат: $X'={f3n[0]},\\;Y'={f3n[1]},\\;Z'={f3n[2]}$\n\n")

    report.append("## 4. Таблица до и после и статистика\n\n")
    report.append("| Name | X | Y | Z | X' | Y' | Z' |\n")
    report.append("|---|---|---|---|---|---|---|\n")
    
    for (_, b), (_, a) in zip(df_before.iterrows(), df_after.iterrows()):
        report.append(f"|{b['Name']}|{b['X']:.6f}|{b['Y']:.6f}|{b['Z']:.6f}|"
                     f"{a['X']:.6f}|{a['Y']:.6f}|{a['Z']:.6f}|\n")

    report.append("\n**Статистика (X', Y', Z'):**\n\n")
    stats = df_after[["X", "Y", "Z"]].agg(["mean", "std"])
    
    for idx in stats.index:
        s = stats.loc[idx]
        report.append(f"- {idx}: X'={s['X']:.3f}, Y'={s['Y']:.3f}, Z'={s['Z']:.3f}\n")

    return "".join(report)