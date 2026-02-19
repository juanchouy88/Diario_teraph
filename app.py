import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import time

# --- CONFIGURACIÓN DE SEGURIDAD (Secrets) ---
# En Streamlit Cloud, estos datos se cargan desde la pestaña "Secrets"
try:
    # Google Sheets Credentials
    # Extraemos los secretos que configurarás en la nube
    google_creds = st.secrets["gcp_service_account"]
    gemini_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("Error: No se encontraron los Secretos de configuración.")
    st.stop()

# --- FUNCIONES DE SERVICIO ---
def get_google_sheet():
    """Conecta a la hoja de Google Sheets."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
    client = gspread.authorize(creds)
    # Abre el archivo que ya creamos por su nombre exacto
    spreadsheet = client.open("Crear Diario Terapéutico con Glide")
    return spreadsheet.get_worksheet(0)

def get_ai_analysis(texto_paciente):
    """Procesa el texto con la IA de Gemini."""
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    Actúa como un asistente analítico especializado en psicoanálisis. 
    Procesa el registro del paciente e identifica mecanismos de defensa o repeticiones.
    Termina con: 'TEMAS:' seguido de palabras clave.
    
    REGISTRO DEL PACIENTE:
    {texto_paciente}
    """
    response = model.generate_content(prompt)
    return response.text

# --- INTERFAZ DE USUARIO (Streamlit) ---
st.set_page_config(page_title="Diario Terapéutico", page_icon="🧘")

st.title("🧘 Mi Diario Terapéutico")
st.write("Escribe tus pensamientos de hoy. Tu terapeuta recibirá el análisis automáticamente.")

# Campo de entrada para el paciente (Reemplaza la Columna C)
nombre_paciente = st.text_input("Nombre o Identificador")
registro_texto = st.text_area("¿Qué tienes en mente?", height=200)

if st.button("Enviar Registro"):
    if not registro_texto or not nombre_paciente:
        st.warning("Por favor, completa tu nombre y el registro antes de enviar.")
    else:
        with st.spinner("Procesando tu registro con IA..."):
            try:
                # 1. Obtener el análisis de la IA
                analisis_completo = get_ai_analysis(registro_texto)
                
                # Separar análisis de temas
                if "TEMAS:" in analisis_completo:
                    partes = analisis_completo.split("TEMAS:")
                    resumen = partes[0].strip()
                    temas = partes[1].strip()
                else:
                    resumen = analisis_completo
                    temas = "No identificados"

                # 2. Guardar en Google Sheets (Columnas A a F)
                sheet = get_google_sheet()
                fecha_actual = time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Insertar fila: Fecha, Paciente, Registro, Estado (vacío), Temas, Resumen
                nueva_fila = [fecha_actual, nombre_paciente, registro_texto, "", temas, resumen]
                sheet.append_row(nueva_fila)
                
                st.success("¡Registro guardado con éxito!")
                st.subheader("Análisis de hoy:")
                st.info(resumen)
                st.caption(f"Temas detectados: {temas}")
                
            except Exception as e:
                st.error(f"Hubo un error al procesar: {e}")

st.divider()
st.caption("Desarrollado para apoyo terapéutico.")