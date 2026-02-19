import os
import time
import schedule
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# --- Configuración ---
SHEET_NAME = "Crear Diario Terapéutico con Glide"
CREDENTIALS_FILE = "credentials.json"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

# Índices de Columnas (C=3, E=5, F=6)
COL_REGITRO = 3
COL_TEMAS = 5
COL_RESUMEN = 6

SYSTEM_PROMPT = """
Actúa como un asistente analítico especializado en procesamiento de lenguaje natural para psicólogos de orientación psicoanalítica. 
Tu tarea es procesar el registro de un paciente y devolver un análisis descriptivo de mecanismos de defensa o repeticiones. 
Termina siempre con: 'TEMAS:' seguido de las palabras clave.
"""

def setup_services():
    """Inicializa Sheets usando el índice de pestaña para evitar errores de nombre."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        
        # ACCIÓN: Abrimos el archivo y seleccionamos la PRIMERA pestaña (índice 0)
        spreadsheet = client.open(SHEET_NAME)
        sheet = spreadsheet.get_worksheet(0) 
        
        print(f"Conectado a la pestaña: '{sheet.title}'")

        if not GEMINI_API_KEY:
             raise ValueError("GEMINI_API_KEY no encontrada.")
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        return sheet, model
    except Exception as e:
        print(f"Error al configurar servicios: {e}")
        return None, None

def process_journal_entries():
    print(f"\nCiclo iniciado: {time.strftime('%H:%M:%S')}")
    sheet, model = setup_services()
    if not sheet or not model: return

    try:
        all_records = sheet.get_all_values()
        if len(all_records) <= 1:
            print("Hoja vacía o solo encabezados.")
            return

        for i, row in enumerate(all_records[1:]):
            row_num = i + 2
            registro_dia = row[COL_REGITRO - 1] if len(row) >= COL_REGITRO else ""
            resumen_existente = row[COL_RESUMEN - 1] if len(row) >= COL_RESUMEN else ""

            if registro_dia and not resumen_existente:
                print(f"Procesando Fila {row_num}...")
                prompt = f"{SYSTEM_PROMPT}\n\nREGISTRO:\n{registro_dia}"
                response = model.generate_content(prompt)
                
                # Split de seguridad para TEMAS
                txt = response.text
                analysis = txt.split("TEMAS:")[0].strip()
                themes = txt.split("TEMAS:")[1].strip() if "TEMAS:" in txt else "No detectados"

                sheet.update_cell(row_num, COL_RESUMEN, analysis)
                time.sleep(1)
                sheet.update_cell(row_num, COL_TEMAS, themes)
                print(f"Fila {row_num} lista.")
                time.sleep(2)
    except Exception as e:
        print(f"Error en proceso: {e}")

def main():
    print("--- Procesador Activo ---")
    process_journal_entries()
    schedule.every(10).minutes.do(process_journal_entries)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()