# Streamlit фронт

import streamlit as st
import requests
import io

# URL бэкенд-сервера

# BACKEND_URL = "https://.com"
# BACKEND_URL = "http://127.0.0.1:8000" - локальный

# интерфейс Streamlit
st.title("Преобразование координатных данных")
st.write("""
Загрузите CSV-файл с колонками `Name`, `X`, `Y`, `Z`, и получите Markdown-отчет
с преобразованными координатами.
""")

# Загрузка файла
uploaded_file = st.file_uploader("Выберите CSV-файл", type=["csv"])

if uploaded_file is not None:
    if st.button("Преобразовать координаты"):
        with st.spinner("Обработка файла..."):
            try:
                # Отправка файла на бэк
                files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
                response = requests.post(f"{BACKEND_URL}/process-csv/", files=files)

                if response.status_code == 200:

                    # Кнопка для скачивания Markdown-файла
                    st.download_button(
                        label="Скачать Markdown-отчет",
                        data=response.content,
                        file_name="report.md",
                        mime="text/markdown"
                    )
                    st.success("Отчет успешно сгенерирован!")
                else:

                    # Обработка ошибок от сервера
                    try:
                        error_detail = response.json().get('detail', 'Неизвестная ошибка')
                    except ValueError:
                        error_detail = response.text or 'Неизвестная ошибка'
                    st.error(f"Ошибка: {error_detail}")

            # Обработка ошибок соединения
            except requests.exceptions.RequestException as e:
                st.error(f"Ошибка подключения: {str(e)}")