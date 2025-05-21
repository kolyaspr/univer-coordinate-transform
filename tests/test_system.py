import pytest
from coordinate_transform import GSK_2011, generate_report_md
import pandas as pd
import os

@pytest.fixture
def sample_data():
    return pd.read_excel("tests/test_data/sample1.xlsx")

def test_coordinate_transform(sample_data):
    """Проверка преобразования координат"""
    result = GSK_2011(
        sk1="СК-42",
        sk2="ГСК-2011",
        parameters_path="parameters.json",
        df=sample_data
    )
    # Проверка структуры результата
    assert {'Name', 'X', 'Y', 'Z'}.issubset(result.columns)
    # Проверка изменения координат
    assert not result.equals(sample_data)

def test_report_generation(tmp_path, sample_data):
    """Проверка генерации отчета"""
    report_path = os.path.join(tmp_path, "report.md")
    generate_report_md(
        df_before=sample_data,
        sk1="СК-42",
        sk2="ГСК-2011",
        parameters_path="parameters.json",
        md_path=report_path
    )
    
    # Проверка существования файла
    assert os.path.exists(report_path)
    
    # Проверка содержания отчета
    with open(report_path, 'r') as f:
        content = f.read()
        assert "Отчёт по преобразованию координат" in content
        assert "Таблица до и после" in content

def test_invalid_data():
    """Проверка обработки невалидных данных"""
    with pytest.raises(ValueError, match="CSV должен содержать колонки: Name, X, Y, Z"):
        invalid_data = pd.read_excel("tests/test_data/invalid.xlsx")
        # Добавим проверку структуры данных перед вызовом GSK_2011
        if not {'Name', 'X', 'Y', 'Z'}.issubset(invalid_data.columns):
            raise ValueError("CSV должен содержать колонки: Name, X, Y, Z")
        GSK_2011(
            sk1="СК-42",
            sk2="ГСК-2011",
            parameters_path="parameters.json",
            df=invalid_data
        )