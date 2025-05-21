import pandas as pd
import numpy as np

def generate_test_data(output_path="tests/test_data/sample1.xlsx"):
    """Генерация корректных тестовых данных"""
    np.random.seed(42)
    data = {
    "Name": ["Point1", "Point2"],
    "X": [1000.0, 2000.0],
    "Y": [3000.0, 4000.0],
    "Z": [5000.0, 6000.0]
    }
    pd.DataFrame(data).to_excel(output_path, index=False)

def generate_invalid_data(output_path="tests/test_data/invalid.xlsx"):
    """Генерация данных с ошибками (неправильные колонки)"""
    data = {
        'Name': ['Point_1'],
        'WrongCol1': [1000],  
        'WrongCol2': [2000]
    }
    pd.DataFrame(data).to_excel(output_path, index=False)

if __name__ == "__main__":
    generate_test_data()
    generate_invalid_data()