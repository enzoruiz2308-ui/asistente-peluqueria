"""Asistente virtual para una peluquería (Tkinter + Gemini)."""
import os
import re
import threading
import tkinter as tk
from tkinter import scrolledtext

from dotenv import load_dotenv
import google.generativeai as genai

# ---------------------------------------------------------------
# 1. CONFIGURACIÓN Y SEGURIDAD
# ---------------------------------------------------------------
# load_dotenv() lee el archivo .env y copia sus líneas (API_KEY=...)
# a las variables de entorno del proceso. Así la clave nunca queda
# escrita en el código ni se sube a GitHub (.env está en .gitignore).
load_dotenv()
API_KEY = os.getenv("API_KEY")
# Modelo configurable desde .env; "flash" es rápido, barato y suficiente
# para un chat de preguntas cortas.
MODELO = os.getenv("MODELO", "gemini-2.5-flash")

if not API_KEY:
    raise SystemExit("Falta API_KEY. Crea un archivo .env (mira .env.example).")

genai.configure(api_key=API_KEY)

# ---------------------------------------------------------------
# 2. CONTEXTO (in-context learning, NO entrenamiento)
# ---------------------------------------------------------------
# No entrenamos el modelo: le pasamos servicios.txt en cada consulta
# como instrucciones de sistema. El modelo ya sabe lenguaje; los datos
# concretos (precios, horarios) los toma del texto que le damos.
RUTA_SERVICIOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "servicios.txt")
with open(RUTA_SERVICIOS, encoding="utf-8") as f:
    INFO_PELUQUERIA = f.read()

INSTRUCCIONES = f"""Eres el asistente virtual de una peluquería.
Responde SOLO usando la información de abajo. Sé amable y breve.
Si la pregunta no tiene que ver con la peluquería, o el dato no aparece
en la información, di educadamente que solo puedes ayudar con los
servicios, precios y horarios de la peluquería. No inventes datos.
Escribe en texto plano, sin Markdown (sin asteriscos ni negritas).

INFORMACIÓN DE LA PELUQUERÍA:
{INFO_PELUQUERIA}"""

# system_instruction fija el rol y el contexto para toda la conversación.
modelo = genai.GenerativeModel(MODELO, system_instruction=INSTRUCCIONES)


# ---------------------------------------------------------------
# 3. LLAMADA A LA API Y MANEJO DEL JSON
# ---------------------------------------------------------------
def extraer_texto(respuesta):
    """Recorre el JSON (dict) de Gemini y devuelve solo el texto útil.

    Estructura: {"candidates": [{"content": {"parts": [{"text": "..."}]}}]}
    """
    datos = respuesta.to_dict()  # respuesta de la API como diccionario/JSON
    try:
        partes = datos["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in partes).strip()
    except (KeyError, IndexError, TypeError):
        # Si falta algo (p. ej. respuesta bloqueada) no rompemos la app.
        return "No he podido generar una respuesta. Prueba a reformular la pregunta."


def limpiar_markdown(texto):
    """Por si el modelo usa Markdown: quita ** y convierte '* ' en viñetas."""
    texto = texto.replace("**", "")
    return re.sub(r"^\s*[*-]\s+", "• ", texto, flags=re.MULTILINE)


def preguntar_a_gemini(pregunta):
    respuesta = modelo.generate_content(pregunta)
    return limpiar_markdown(extraer_texto(respuesta))


# ---------------------------------------------------------------
# 4. INTERFAZ GRÁFICA
# ---------------------------------------------------------------
class AsistenteApp:
    def __init__(self, root):
        self.root = root
        root.title("Asistente de Peluquería")
        root.geometry("640x560")

        # ScrolledText = Text con barra de scroll incluida.
        self.salida = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, state="disabled", font=("Arial", 11))
        self.salida.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
        self.salida.tag_config("usuario", foreground="blue", font=("Arial", 11, "bold"))
        self.salida.tag_config("asistente", foreground="green4")
        self.salida.tag_config("error", foreground="red")

        marco = tk.Frame(root)
        marco.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.entrada = tk.Entry(marco, font=("Arial", 11))
        self.entrada.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.entrada.bind("<Return>", lambda e: self.enviar())  # Enter también envía
        self.boton = tk.Button(marco, text="Enviar", command=self.enviar,
                               bg="#0078d7", fg="white", font=("Arial", 10, "bold"))
        self.boton.pack(side=tk.RIGHT, padx=(8, 0))

        self.escribir("Bienvenido al Asistente de Peluquería.\n"
                      "Escribe tu pregunta abajo y presiona 'Enviar'.\n\n")
        self.entrada.focus()

    def escribir(self, texto, etiqueta=None):
        # El Text está "disabled" para que el usuario no lo edite;
        # hay que habilitarlo un instante para insertar texto.
        self.salida.config(state="normal")
        self.salida.insert(tk.END, texto, etiqueta)
        self.salida.config(state="disabled")
        self.salida.see(tk.END)  # baja el scroll al final

    def enviar(self):
        pregunta = self.entrada.get().strip()
        if not pregunta:
            return
        self.entrada.delete(0, tk.END)  # limpia el input tras enviar
        self.escribir(f"Tú: {pregunta}\n", "usuario")
        self.boton.config(state="disabled")
        self.escribir("Asistente: escribiendo...\n", "asistente")

        # La llamada a la API tarda; si se hiciera en el hilo principal la
        # ventana se congelaría. Por eso usamos un hilo aparte.
        threading.Thread(target=self.consultar, args=(pregunta,), daemon=True).start()

    def consultar(self, pregunta):
        try:
            texto = preguntar_a_gemini(pregunta)
            # Tkinter no es thread-safe: volvemos al hilo principal con after().
            self.root.after(0, self.mostrar, texto, False)
        except Exception as e:  # sin internet, clave inválida, cuota, etc.
            msg = f"No se pudo conectar con el asistente ({type(e).__name__}). " \
                  "Revisa tu conexión a internet y tu API Key."
            self.root.after(0, self.mostrar, msg, True)

    def mostrar(self, texto, es_error):
        # Borra la línea "escribiendo..." y pone la respuesta real.
        self.salida.config(state="normal")
        self.salida.delete("end-2l linestart", "end-1c")
        self.salida.config(state="disabled")
        if es_error:
            self.escribir(f"⚠ {texto}\n\n", "error")
        else:
            self.escribir(f"Asistente: {texto}\n\n", "asistente")
        self.boton.config(state="normal")
        self.entrada.focus()


if __name__ == "__main__":
    ventana = tk.Tk()
    AsistenteApp(ventana)
    ventana.mainloop()
