import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
from datetime import datetime
import json
from streamlit_mic_recorder import mic_recorder

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Diario Terapéutico", page_icon="🧘", layout="centered")

# --- AUTENTICACIÓN / LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Acceso Seguro al Diario Terapéutico")
    st.info("Por favor, ingresa tu contraseña para acceder a la aplicación.")
    password = st.text_input("Contraseña clave", type="password")
    if st.button("Ingresar", type="primary"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta. Intenta nuevamente.")
    st.stop()

# --- CONFIGURACIÓN DE SEGURIDAD (Secrets) ---
try:
    # 1. Credenciales de Google Sheets
    gcp_json_crudo = st.secrets["GCP_JSON"]
    GCP_CREDS = json.loads(gcp_json_crudo)
    
    # Obligatorio: limpieza de la private_key para evitar fallos Base64
    if "private_key" in GCP_CREDS:
        GCP_CREDS["private_key"] = GCP_CREDS["private_key"].replace('\\n', '\n').replace('\r', '')
    
    # 2. Gemini API Key
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception as e:
    st.error(f"Error al cargar las credenciales: {e}")
    st.stop()

# Configurar el cliente de IA de Gemini
genai.configure(api_key=GEMINI_API_KEY)

# --- FUNCIONES DE SERVICIO ---
def conectar_google_sheet():
    """Establece conexión con la planilla de Google Sheets."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(GCP_CREDS, scope)
    client = gspread.authorize(creds)
    return client.open("Crear Diario Terapéutico con Glide").get_worksheet(0)

def transcribir_audio(audio_bytes):
    """Transcribe el audio manteniendo pausas y repeticiones usando Gemini."""
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = """
    Transcribe el siguiente audio palabra por palabra. 
    Es CRUCIAL que mantengas todas las dudas, pausas ('eh', 'mmm'), titubeos y repeticiones de palabras exactamente como se pronuncian. 
    No corrijas la gramática ni omitas estos elementos, ya que son esenciales para un análisis psicoanalítico posterior.
    """
    
    try:
        response = model.generate_content([
            prompt,
            {
                "mime_type": "audio/webm",
                "data": audio_bytes
            }
        ])
        return response.text
    except Exception as e:
        # Fallback en caso de que sea un WAV u otro formato
        try:
             response = model.generate_content([
                prompt,
                {
                    "mime_type": "audio/wav",
                    "data": audio_bytes
                }
            ])
             return response.text
        except Exception as e2:
            st.error(f"Error en la transcripción: {e2}")
            return ""

def analizar_con_ia(texto_paciente):
    """Realiza un procesamiento analítico silencioso del texto."""
    model = genai.GenerativeModel('gemini-2.5-flash') 
    
    prompt = f"""
    Actúa como un asistente analítico especializado en psicoanálisis. 
    Analiza el siguiente registro e identifica mecanismos de defensa o repeticiones significativas.
    
    REGISTRO:
    {texto_paciente}
    """
    response = model.generate_content(prompt)
    return response.text

# --- INTERFAZ PRINCIPAL (UX DESARROLLADOR Y PACIENTE) ---
col1, col2 = st.columns([8, 2])
with col2:
    if st.button("Cerrar Sesión", key="logout"):
        st.session_state.logged_in = False
        st.rerun()

st.title("🧘 Mi Diario Terapéutico")
st.info("Espacio seguro para registrar tus pensamientos. Todo lo que compartas cuenta con estricta privacidad.")

# Variables de Estado de la Sesión para persistir el texto transcrito
if 'transcripcion' not in st.session_state:
    st.session_state.transcripcion = ""
if 'last_audio_id' not in st.session_state:
    st.session_state.last_audio_id = None

nombre_paciente = st.text_input("Identificador / Nombre", placeholder="Escribe tu nombre aquí...")

st.markdown("### 🎙️ Graba tu voz o escribe")
st.write("Usa el micrófono para hablar libremente. Tu ritmo natural será respetado.")

# mic_recorder para audio multimodal
audio = mic_recorder(
    start_prompt="🔴 Iniciar Grabación",
    stop_prompt="⏹️ Detener Grabación",
    just_once=False,
    use_container_width=False,
    key='mic_recorder'
)

# Procesamiento de voz a texto
if audio is not None:
    if st.session_state.last_audio_id != audio['id']:
        with st.spinner("🎙️ Transcribiendo tu audio, manteniendo pausas y dudas..."):
            texto_transcrito = transcribir_audio(audio['bytes'])
            if texto_transcrito:
                if st.session_state.transcripcion:
                    st.session_state.transcripcion += "\n\n" + texto_transcrito.strip()
                else:
                    st.session_state.transcripcion = texto_transcrito.strip()
        st.session_state.last_audio_id = audio['id']
        st.rerun()

# El valor de registro_dia está atado a st.session_state.transcripcion gracias al key
registro_dia = st.text_area(
    "¿Cómo te sentís hoy?", 
    key="transcripcion",
    height=250, 
    max_chars=3000, 
    help="Límite: 3000 caracteres. Siente la libertad de escribir o editar lo transcrito."
)

if st.button("Enviar Registro", type="primary"):
    if not nombre_paciente.strip() or not registro_dia.strip():
        st.warning("⚠️ Por favor, completá tu nombre y escribe un registro antes de enviar.")
    else:
        # UX Empática para procesamiento
        with st.spinner("Procesando tu registro de forma confidencial..."):
            try:
                # 1. Obtener el análisis profundo de Gemini (Silencioso para el paciente)
                analisis_ia = analizar_con_ia(registro_dia)
                
                # 2. Conectar y guardar los datos en Google Sheets
                sheet = conectar_google_sheet()
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Formato mantenido de columnas: [Fecha, Nombre, Registro, vacío, vacío, Análisis]
                # para resguardar la compatibilidad con el formato "Crear Diario Terapéutico con Glide"
                nueva_fila = [fecha_actual, nombre_paciente, registro_dia, "", "", analisis_ia]
                sheet.append_row(nueva_fila)
                
                # 3. REGLA DE ORO: Solo mostrar mensaje de éxito (Sin revelar el análisis al paciente)
                st.success("Tu terapeuta ha recibido tu registro de forma segura")
                st.balloons()
                
            except Exception as e:
                st.error(f"Error al enviar el registro. Revisa tu conexión: {e}")

st.divider()
st.caption("Desarrollado para apoyo terapéutico profesional con IA.")