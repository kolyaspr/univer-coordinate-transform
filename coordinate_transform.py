import pandas as pd
import json
from sympy import symbols, Matrix, N, latex
from typing import Optional

def GSK_2011(sk1, sk2, parameters_path, df=None, csv_path=None, save_path=None):
    """
    Преобразует координаты между системами координат по алгоритму ГСК-2011.
    
    Параметры:
        sk1 (str): Исходная система координат (например, "СК-42")
        sk2 (str): Целевая система координат (например, "ГСК-2011")
        parameters_path (str): Путь к JSON-файлу с параметрами преобразования
        df (pd.DataFrame, optional): DataFrame с входными координатами
        csv_path (str, optional): Путь к CSV-файлу, если df не передан
        save_path (str, optional): Путь для сохранения результатов в CSV
    
    Возвращает:
        pd.DataFrame: DataFrame с преобразованными координатами
    
    Исключения:
        ValueError: Если система координат не найдена или отсутствуют входные данные
    """
    
    # Специальный случай каскадного преобразования СК-95 → ПЗ-90.11 → СК-42
    if sk1 == "СК-95" and sk2 == "СК-42":
        df_temp = GSK_2011("СК-95", "ПЗ-90.11", parameters_path, df=df)
        df_result = GSK_2011("ПЗ-90.11", "СК-42", parameters_path, df=df_temp, save_path=save_path)
        return df_result

    # Определение символьных переменных для формулы преобразования
    ΔX, ΔY, ΔZ, ωx, ωy, ωz, m = symbols('ΔX ΔY ΔZ ωx ωy ωz m')
    X, Y, Z = symbols('X, Y, Z')

    # Основная формула преобразования (линейное преобразование 7-параметрическим методом)
    formula = (1 + m) * Matrix([
        [1, ωz, -ωy],
        [-ωz, 1, ωx],
        [ωy, -ωx, 1]
    ]) @ Matrix([[X], [Y], [Z]]) + Matrix([[ΔX], [ΔY], [ΔZ]])

    # Загрузка параметров преобразования из JSON-файла
    with open(parameters_path, 'r', encoding='utf-8') as f:
        parameters = json.load(f)

    if sk1 not in parameters:
        raise ValueError(f"Система {sk1} не найдена в {parameters_path}")

    param = parameters[sk1]
    
    # Подстановка параметров для выбранной системы координат
    elements_const = {
        ΔX: param["ΔX"],  # Смещение по оси X (м)
        ΔY: param["ΔY"],  # Смещение по оси Y (м)
        ΔZ: param["ΔZ"],  # Смещение по оси Z (м)
        ωx: param["ωx"],  # Угол поворота вокруг X (рад)
        ωy: param["ωy"],  # Угол поворота вокруг Y (рад)
        ωz: param["ωz"],  # Угол поворота вокруг Z (рад)
        m: param["m"] * 1e-6  # Масштабный коэффициент (ppm → единицы)
    }

    # Загрузка данных (либо из DataFrame, либо из CSV)
    if df is None:
        if csv_path:
            df = pd.read_csv(csv_path)
        else:
            raise ValueError("Нужно передать либо df, либо путь к CSV")

    # Преобразование каждой точки
    transformed = []
    for _, row in df.iterrows():
        # Подстановка конкретных координат точки в формулу
        elements = {
            **elements_const,
            X: row["X"],
            Y: row["Y"],
            Z: row["Z"],
        }

        # Вычисление новых координат с численным приближением
        results_vector = formula.subs(elements).applyfunc(N)
        
        # Сохранение результата
        transformed.append([
            row["Name"],  # Сохраняем исходное название точки
            float(results_vector[0]),  # Новая координата X
            float(results_vector[1]),  # Новая координата Y
            float(results_vector[2])   # Новая координата Z
        ])

    # Создание DataFrame с результатами
    df_result = pd.DataFrame(transformed, columns=["Name", "X", "Y", "Z"])

    # Сохранение в файл (если указан путь)
    if save_path:
        df_result.to_csv(save_path, index=False)

    return df_result

def generate_report_md(
    df_before: pd.DataFrame,
    sk1: str,
    sk2: str,
    parameters_path: str,
    md_path: str,
    csv_before: Optional[str] = None,
    csv_after: Optional[str] = None
) -> pd.DataFrame:
    """
    Генерирует Markdown-отчет о преобразовании координат
    
    Параметры:
        df_before: DataFrame с исходными координатами
        sk1: исходная система координат
        sk2: целевая система координат
        parameters_path: путь к JSON-файлу параметров
        md_path: путь для сохранения отчета
        csv_before: путь для сохранения исходных данных (опционально)
        csv_after: путь для сохранения преобразованных данных (опционально)
    
    Возвращает:
        pd.DataFrame: DataFrame с преобразованными координатами
    
    Исключения:
        ValueError: Если система координат не найдена
    """
    
    # Определение символьных переменных
    ΔX, ΔY, ΔZ, ωx, ωy, ωz, m = symbols('ΔX ΔY ΔZ ωx ωy ωz m')
    X, Y, Z = symbols('X, Y, Z')
    
    # Формула преобразования (аналогичная GSK_2011)
    general_formula = (1 + m) * Matrix([[1, ωz, -ωy], [-ωz, 1, ωx], [ωy, -ωx, 1]]) @ Matrix([[X], [Y], [Z]]) + Matrix([[ΔX], [ΔY], [ΔZ]])

    # Загрузка параметров преобразования
    with open(parameters_path, 'r', encoding='utf-8') as f:
        params = json.load(f)
    
    # Проверка наличия системы координат
    p = params.get(sk1)
    if p is None:
        raise ValueError(f"Система {sk1} не найдена в {parameters_path}")
    
    # Подстановка параметров
    subs_common = {
        ΔX: p["ΔX"], ΔY: p["ΔY"], ΔZ: p["ΔZ"],
        ωx: p["ωx"], ωy: p["ωy"], ωz: p["ωz"],
        m: p["m"] * 1e-6  # Перевод ppm в единицы
    }

    # Сохранение исходных данных (если нужно)
    if csv_before:
        df_before.to_csv(csv_before, index=False)

    # Преобразование всех точек
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

    # Сохранение преобразованных данных (если нужно)
    if csv_after:
        df_after.to_csv(csv_after, index=False)

    # Генерация Markdown-отчета
    with open(md_path, 'w', encoding='utf-8') as md:
        # Заголовок отчета
        md.write(f"# Отчёт по преобразованию координат\n\n")
        md.write(f"**Исходная система**: {sk1}  \n")
        md.write(f"**Конечная система**: {sk2}  \n\n")

        # Раздел с общей формулой преобразования
        md.write("## 1. Общая формула\n\n")
        md.write(f"$$\n{latex(general_formula)}\n$$\n\n")

        # Раздел с подставленными параметрами
        md.write("## 2. Формула с подстановкой параметров\n\n")
        formula_p = general_formula.subs(subs_common)
        md.write(f"$$\n{latex(formula_p)}\n$$\n\n")

        # Пример преобразования для первой точки
        md.write("## 3. Пример для первой точки\n\n")
        first = df_before.iloc[0]
        md.write(f"- Исходные: $X={first['X']},\\;Y={first['Y']},\\;Z={first['Z']}$  \n")
        subs1 = {**subs_common, X: first["X"], Y: first["Y"], Z: first["Z"]}
        f3 = general_formula.subs(subs1)
        f3n = f3.applyfunc(N)
        md.write(f"- Подстановка в формулу:  \n  $$\n{latex(f3)}\n$$\n")
        md.write(f"- Численный результат: $X'={f3n[0]},\\;Y'={f3n[1]},\\;Z'={f3n[2]}$\n\n")

        # Таблица сравнения исходных и преобразованных координат
        md.write("## 4. Таблица до и после и статистика\n\n")
        md.write("| Name | X | Y | Z | X' | Y' | Z' |\n")
        md.write("|---|---|---|---|---|---|---|\n")
        for b,a in zip(df_before.itertuples(), df_after.itertuples()):
            md.write(f"|{b.Name}|{b.X:.6f}|{b.Y:.6f}|{b.Z:.6f}"
                     f"|{a.X_new:.6f}|{a.Y_new:.6f}|{a.Z_new:.6f}|\n")

        # Статистика по преобразованным координатам
        md.write("\n**Статистика (X', Y', Z'):**\n\n")
        stats = df_after[["X_new","Y_new","Z_new"]].agg(["mean","std"])
        for idx in stats.index:
            s = stats.loc[idx]
            md.write(f"- {idx}: X'={s['X_new']:.3f}, Y'={s['Y_new']:.3f}, Z'={s['Z_new']:.3f}\n")

    return df_after