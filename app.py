# Streamlit фронтенд для загрузки Excel-файлов

import streamlit as st
import requests

# URL бэкенд-сервера
BACKEND_URL = "https://univer-coordinate-backend.onrender.com"

# Настройка интерфейса Streamlit
st.title("Преобразование координатных данных")
st.write("""
Загрузите Excel-файл (.xlsx) с колонками `Name`, `X`, `Y`, `Z`, и получите Markdown-отчет
с преобразованными координатами.
""")

# Загрузка файла
uploaded_file = st.file_uploader(
    "Выберите Excel-файл", 
    type=["xlsx", "xls"],
    help="Файл должен содержать колонки: Name, X, Y, Z"
)

if uploaded_file is not None:
    if st.button("Преобразовать координаты"):
        with st.spinner("Обработка файла..."):
            try:
                # Отправка файла на бэкенд
                files = {
                    "file": (
                        uploaded_file.name, 
                        uploaded_file, 
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                }
                response = requests.post(
                    f"{BACKEND_URL}/process-excel/", 
                    files=files,
                    timeout=30
                )

                if response.status_code == 200:
                    # Показ предпросмотра отчета
                    st.markdown("### Предпросмотр отчета")
                    st.markdown(response.content.decode('utf-8')[:1000] + "...")
                    
                    # Кнопка для скачивания
                    st.download_button(
                        label="Скачать полный Markdown-отчет",
                        data=response.content,
                        file_name="coordinate_report.md",
                        mime="text/markdown"
                    )
                    st.success("Преобразование выполнено успешно!")
                    
                else:
                    try:
                        error_detail = response.json().get('detail', response.text)
                    except ValueError:
                        error_detail = response.text
                    
                    st.error(f"Ошибка сервера: {error_detail}")
                    st.info("Проверьте, что файл содержит правильные колонки: Name, X, Y, Z")

            except requests.exceptions.Timeout:
                st.error("Превышено время ожидания ответа от сервера")
            except requests.exceptions.RequestException as e:
                st.error(f"Ошибка подключения: {str(e)}")
            except Exception as e:
                st.error(f"Неожиданная ошибка: {str(e)}")