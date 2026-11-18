# Asistente Virtual para Peluquería con IA

Aplicación de escritorio en Python que funciona como chat de atención al cliente
para una peluquería. El usuario escribe una pregunta (por ejemplo, "¿Cuánto cuesta
teñirse el pelo?") y el asistente responde usando la API de Google Gemini.

## Características
- Interfaz gráfica con Tkinter (entrada de texto, botón Enviar y área de respuestas con scroll).
- Contexto con in-context learning: los servicios, precios y horarios se leen de
  `servicios.txt` y se inyectan en el prompt, sin entrenar ningún modelo.
- El asistente solo responde sobre la peluquería.
- Procesamiento de la respuesta JSON de Gemini para mostrar solo el texto útil.
- API Key protegida con `python-dotenv` (archivo `.env` excluido con `.gitignore`).
- Gestión de errores de conexión sin cerrar la aplicación.

## Instalación
1. Clona el repositorio.
2. Instala las dependencias: `pip install -r requirements.txt`
3. Copia `.env.example` como `.env` y escribe tu clave:
   `API_KEY=tu_clave_api_aqui`
   (se obtiene en https://makersuite.google.com/app/apikey)
4. Ejecuta: `python asistente_gui.py`

## Archivos
- `asistente_gui.py`: código de la aplicación
- `servicios.txt`: información de la peluquería (contexto para la IA)
- `requirements.txt`: dependencias
- `.env.example`: plantilla de configuración (sin clave real)

## Tecnologías
Python, Tkinter, Google Gemini API, python-dotenv
