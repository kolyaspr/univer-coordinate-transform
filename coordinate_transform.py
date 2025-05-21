import pandas as pd
from sympy import symbols, Matrix, N
import json

def GSK_2011(sk1, sk2, parameters_path, df=None):
    """Упрощенная версия без работы с файлами"""
    with open(parameters_path, 'r', encoding='utf-8') as f:
        parameters = json.load(f)
    
    if sk1 not in parameters:
        raise ValueError(f"Система {sk1} не найдена в параметрах")

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