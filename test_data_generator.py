import pandas as pd
import numpy as np

def generate_test_data(output_path="tests/test_data/sample1.xlsx"):
    """Генерация корректных тестовых данных"""
    np.random.seed(42)
    data = {
        'Name': ['Point_A', 'Point_B', 'Point_C'],
        'X': np.random.uniform(1000, 5000, 3).round(3),
        'Y': np.random.uniform(2000, 6000, 3).round(3),
        'Z': np.random.uniform(3000, 7000, 3).round(3)
    }
    pd.DataFrame(data).to_excel(output_path, index=False)

def generate_invalid_data(output_path="tests/test_data/invalid.xlsx"):
    """Генерация данных с ошибками (неправильные колонки)"""
    data = {
        'Name': ['Point_A'],
        'WrongCol1': [1000],  # Некорректные колонки
        'WrongCol2': [2000]
    }
    pd.DataFrame(data).to_excel(output_path, index=False)

if __name__ == "__main__":
    generate_test_data()
    generate_invalid_data()