import streamlit as st
import gspread
# ... (usa las mismas credenciales que ya tenés)

st.title("Diario Terapéutico")
registro = st.text_area("¿Cómo te sentís hoy?")

if st.button("Enviar Registro"):
    # 1. Guarda en Google Sheets (Columna C)
    # 2. Llama a Gemini (como ya hace tu script)
    # 3. Muestra el resultado de las columnas E y F en pantalla
    st.success("¡Procesado! Análisis de la IA: ...")