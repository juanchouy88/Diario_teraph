import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURACIÓN DE SEGURIDAD (Secrets) ---
try:
    GCP_CREDS = dict(st.secrets["gcp_service_account"])
    
    # ESTA ES LA LÍNEA MÁGICA QUE ARREGLA EL ERROR BASE64:
    GCP_CREDS["private_key"] = GCP_CREDS["private_key"].replace('\\n', '\n')
    
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("Error: Los Secretos de configuración no están definidos en Streamlit Cloud.")
    st.stop()

# --- FUNCIONES DE SERVICIO ---
def conectar_google_sheet():
    """Establece conexión con tu planilla de Google Sheets."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(GCP_CREDS, scope)
    client = gspread.authorize(creds)
    return client.open("Crear Diario Terapéutico con Glide").get_worksheet(0)

def analizar_con_ia(texto_paciente):
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Usamos el modelo activo y correcto para 2026
    model = genai.GenerativeModel('gemini-2.5-flash') 
    
    prompt = f"""
    Actúa como un asistente analítico especializado en psicoanálisis. 
    Analiza el siguiente registro e identifica mecanismos de defensa o repeticiones significativas.
    
    REGISTRO:
    {texto_paciente}
    """
    response = model.generate_content(prompt)
    return response.text

# --- INTERFAZ DE USUARIO (Streamlit) ---
st.set_page_config(page_title="Diario Terapéutico", page_icon="🧘")

st.title("🧘 Mi Diario Terapéutico")
st.info("Espacio seguro para registrar tus pensamientos. El análisis se enviará automáticamente a tu terapeuta.")

nombre_paciente = st.text_input("Identificador / Nombre")
registro_dia = st.text_area("¿Cómo te sentís hoy?", height=250)

if st.button("Enviar Registro"):
    if not nombre_paciente or not registro_dia:
        st.warning("Por favor, completá ambos campos antes de enviar.")
    else:
        with st.spinner("Procesando con Inteligencia Artificial..."):
            try:
                # 1. Obtener el análisis de Gemini
                analisis_ia = analizar_con_ia(registro_dia)
                
                # 2. Conectar y guardar en Google Sheets
                sheet = conectar_google_sheet()
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                nueva_fila = [fecha_actual, nombre_paciente, registro_dia, "", "", analisis_ia]
                sheet.append_row(nueva_fila)
                
                st.success("¡Registro guardado con éxito!")
                
                with st.expander("Ver análisis de hoy"):
                    st.write(analisis_ia)
                    
            except Exception as e:
                st.error(f"Error al procesar el registro: {e}")

st.divider()
st.caption("Desarrollado para apoyo terapéutico profesional.")