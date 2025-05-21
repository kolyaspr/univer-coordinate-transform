# Преобразование координатных данных

## Описание
Веб-приложение для преобразования координат. Пользователь загружает Excel-файл с координатами (столбцы: Name, X, Y, Z), приложение выполняет преобразование и возвращает Markdown-отчет с формулой, примером вычисления, таблицей координат до и после, а также статистикой. Использует FastAPI для бэкенда и Streamlit для фронтенда.

## Структура проекта
- `main.py` — FastAPI-бэкенд для обработки Excel и генерации отчета.
- `app.py` — Streamlit-фронтенд для загрузки файла.
- `coordinate_transform.py` — функции преобразования координат и генерации отчета.
- `generate_test.py` — генерация тестового файла в формате xlsx.
- `help.js` — подсказки для команд в терминале.
- `parameters.json` — параметры преобразования.
- `requirements.txt` — зависимости.
- `.gitignore` — исключение ненужных файлов (venv/, __pycache__).

## Установка и запуск

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/kolyaspr/univer-coordinate-transform.git
   cd univer-coordinate-transform
   ```
   Замените `https://github.com/kolyaspr/univer-coordinate-transform` на URL вашего репозитория.

2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Запустите FastAPI-бэкенд (в одном терминале):
   ```bash
   uvicorn main:app --reload
   ```

5. Запустите Streamlit-фронтенд (в другом терминале):
   ```bash
   streamlit run app.py
   ```

6. Откройте в браузере: http://localhost:8501
   - Загрузите Excel-файл (пример формата):
     ```excel
     Name    X        Y        Z
     Point1  1000.123 1500.234 500.345
     Point2  2000.456 2500.567 1000.678
     ```
   - Нажмите "Преобразовать координаты".
   - Скачайте Markdown-отчет.