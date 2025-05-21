#генерация тестового файла

import pandas as pd

# Создаем тестовые данные
data = {
    "Name": ["Point1", "Point2", "Point3", "Point4", "Point5"],
    "X": [1000.123, 2000.456, 3000.789, 4000.012, 5000.345],
    "Y": [1500.234, 2500.567, 3500.890, 4500.123, 5500.456],
    "Z": [500.345, 1000.678, 1500.901, 2000.234, 2500.567]
}

# Создаем DataFrame
df = pd.DataFrame(data)

# Сохраняем в Excel
df.to_excel("test_coordinates.xlsx", index=False, engine='openpyxl')