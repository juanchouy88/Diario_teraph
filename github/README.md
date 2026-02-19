# Therapeutic Journal AI Processor

This project automates the analysis of therapeutic journal entries using Google Gemini AI and Google Sheets.

## Prerequisites

1.  **Python 3.x**: Ensure Python is installed.
2.  **Google Cloud Project**: You need a Google Cloud project with the **Google Sheets API** and **Google Drive API** enabled.
3.  **Google Gemini API Key**: You need an API key from Google AI Studio.

## Setup Instructions

### 1. Install Dependencies
Open a terminal in this directory and run:
```bash
pip install -r requirements.txt
```

### 2. Configure Credentials

#### Google Sheets
1.  Create a **Service Account** in your Google Cloud Console.
2.  Download the JSON key file and rename it to `credentials.json`.
3.  Place `credentials.json` in this project folder.
4.  **Important**: Share your Google Sheet ("Crear Diario Terapéutico con Glide") with the `client_email` address found inside `credentials.json` (give it "Editor" access).

#### Gemini API
1.  Create a `.env` file in this folder (or rename `.env.example` if provided).
2.  Add your API key:
    ```
    GEMINI_API_KEY=your_actual_api_key_here
    ```

### 3. Run the Script
```bash
python journal_processor.py
```
The script will run immediately and then check for new entries every 10 minutes.

## Glide App Configuration
1.  Ensure your Google Sheet columns match the expectations:
    -   **Col C**: Registro del Día (Input)
    -   **Col E**: Temas Detectados (Output from AI)
    -   **Col F**: Resumen Emocional (Output from AI)
2.  Connect your Glide App to this Google Sheet.
3.  The Python script acts as the "Backend" that processes the text entered in Glide.
