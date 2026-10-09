import pymupdf  
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import asyncio
import edge_tts  

# Función asíncrona interna para generar el audio sin usar la terminal
async def generar_audio_async(texto, voz, ruta_salida):
    comunicador = edge_tts.Communicate(texto, voz)
    await comunicador.save(ruta_salida)

def pdf_a_mp3_por_partes(ruta_pdf, directorio_salida, prefijo_salida, paginas_por_parte, porc_arriba, porc_abajo, voz, log_func=print):
    log_func(f"Abriendo el archivo: {ruta_pdf}...")
    
    try:
        documento = pymupdf.open(ruta_pdf)
        total_paginas = len(documento)
        log_func(f"El documento tiene un total de {total_paginas} páginas.")
    except Exception as e:
        log_func(f"Error al abrir el PDF: {e}")
        return

    texto_acumulado = ""
    parte = 1
    inicio_rango = 1

    for i, pagina in enumerate(documento):
        rect = pagina.rect  
        alto = rect.height
        
        recorte_sup = alto * (porc_arriba / 100)
        recorte_inf = alto * (porc_abajo / 100)
        
        area_lectura = pymupdf.Rect(rect.x0, rect.y0 + recorte_sup, rect.x1, rect.y1 - recorte_inf)
        texto = pagina.get_text(clip=area_lectura).replace('\n', ' ')
        
        texto_acumulado += texto + " "

        if (i + 1) % paginas_por_parte == 0 or (i + 1) == total_paginas:
            texto_limpio = texto_acumulado.strip()
            
            if texto_limpio:
                fin_rango = i + 1
                nombre_archivo = f"{prefijo_salida}_parte_{parte}.mp3"
                ruta_completa = os.path.join(directorio_salida, nombre_archivo)
                
                log_func(f"Generando {nombre_archivo} (Páginas {inicio_rango} a {fin_rango})...")
                
                try:
                    # Ejecutamos la función asíncrona directamente en Python
                    asyncio.run(generar_audio_async(texto_limpio, voz, ruta_completa))
                    log_func(f"  -> ¡Guardado con éxito con voz neuronal!")
                        
                except Exception as e:
                    log_func(f"  -> Error general: {e}")
            else:
                log_func(f"Las páginas de la {inicio_rango} a la {i + 1} estaban vacías. Se omiten.")

            texto_acumulado = ""
            parte += 1
            inicio_rango = i + 2

    documento.close()
    log_func("¡Proceso completado al 100%!")

# --- FUNCIONES DE LA INTERFAZ ---

def seleccionar_archivo():
    archivo = filedialog.askopenfilename(
        title="Selecciona el PDF",
        filetypes=[("Archivos PDF", "*.pdf")]
    )
    if archivo:
        entrada_pdf.delete(0, tk.END)
        entrada_pdf.insert(0, archivo)
        
        nombre_base = os.path.splitext(os.path.basename(archivo))[0]
        entrada_prefijo.delete(0, tk.END)
        entrada_prefijo.insert(0, nombre_base)
        
        directorio_pdf = os.path.dirname(archivo)
        entrada_directorio.delete(0, tk.END)
        entrada_directorio.insert(0, directorio_pdf)

def seleccionar_directorio():
    directorio = filedialog.askdirectory(title="Selecciona dónde guardar los audios")
    if directorio:
        entrada_directorio.delete(0, tk.END)
        entrada_directorio.insert(0, directorio)

def actualizar_log(mensaje):
    caja_log.config(state=tk.NORMAL)
    caja_log.insert(tk.END, mensaje + "\n")
    caja_log.see(tk.END)
    caja_log.config(state=tk.DISABLED)

def ejecutar_en_hilo():
    btn_iniciar.config(state=tk.DISABLED)
    
    ruta_pdf = entrada_pdf.get()
    directorio_salida = entrada_directorio.get()
    prefijo = entrada_prefijo.get()
    
    try:
        paginas = int(entrada_paginas.get())
        porc_arriba = float(entrada_arriba.get())
        porc_abajo = float(entrada_abajo.get())
    except ValueError:
        messagebox.showerror("Error", "Revisa que las páginas y los porcentajes sean números válidos.")
        btn_iniciar.config(state=tk.NORMAL)
        return

    if not os.path.exists(ruta_pdf) or not os.path.exists(directorio_salida):
        messagebox.showerror("Error", "Ruta de PDF o carpeta de salida no válidas.")
        btn_iniciar.config(state=tk.NORMAL)
        return
        
    # --- NUEVO: DICCIONARIO DE VOCES ACTUALIZADO ---
    diccionario_voces = {
        "Español - Femenina (Elvira)": "es-ES-ElviraNeural",
        "Español - Masculina (Álvaro)": "es-ES-AlvaroNeural",
        "Inglés - Femenina (Aria)": "en-US-AriaNeural",
        "Inglés - Masculina (Guy)": "en-US-GuyNeural",
        "Francés - Femenina (Denise)": "fr-FR-DeniseNeural",
        "Francés - Masculina (Henri)": "fr-FR-HenriNeural",
        "Italiano - Femenina (Elsa)": "it-IT-ElsaNeural",
        "Italiano - Masculina (Diego)": "it-IT-DiegoNeural"
    }
    voz_elegida = diccionario_voces[variable_voz.get()]

    caja_log.config(state=tk.NORMAL)
    caja_log.delete(1.0, tk.END)
    caja_log.config(state=tk.DISABLED)
    
    pdf_a_mp3_por_partes(ruta_pdf, directorio_salida, prefijo, paginas, porc_arriba, porc_abajo, voz_elegida, log_func=actualizar_log)
    
    btn_iniciar.config(state=tk.NORMAL)

def iniciar_conversion():
    hilo = threading.Thread(target=ejecutar_en_hilo)
    hilo.start()

# --- DISEÑO DE LA INTERFAZ (Tkinter) ---

ventana = tk.Tk()
ventana.title("Conversor de PDF a Audiolibro (Voces Neuronales Multilingüe)")
ventana.geometry("650x600") 
ventana.config(padx=20, pady=20)

tk.Label(ventana, text="Archivo PDF:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
entrada_pdf = tk.Entry(ventana, width=45)
entrada_pdf.grid(row=0, column=1, padx=10)
tk.Button(ventana, text="Explorar...", command=seleccionar_archivo).grid(row=0, column=2)

tk.Label(ventana, text="Carpeta destino:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
entrada_directorio = tk.Entry(ventana, width=45)
entrada_directorio.grid(row=1, column=1, padx=10)
tk.Button(ventana, text="Explorar...", command=seleccionar_directorio).grid(row=1, column=2)

tk.Label(ventana, text="Nombre (prefijo):", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
entrada_prefijo = tk.Entry(ventana, width=45)
entrada_prefijo.grid(row=2, column=1, padx=10, sticky="w")

tk.Label(ventana, text="Páginas por archivo:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=5)
entrada_paginas = tk.Entry(ventana, width=10)
entrada_paginas.insert(0, "50")
entrada_paginas.grid(row=3, column=1, padx=10, sticky="w")

tk.Label(ventana, text="Recortar ENCABEZADO (%):", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=5)
entrada_arriba = tk.Entry(ventana, width=10)
entrada_arriba.insert(0, "8")
entrada_arriba.grid(row=4, column=1, padx=10, sticky="w")
tk.Label(ventana, text="(Ignora el título del libro)", fg="gray").grid(row=4, column=1, padx=100, sticky="w")

tk.Label(ventana, text="Recortar PIE DE PÁGINA (%):", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky="w", pady=5)
entrada_abajo = tk.Entry(ventana, width=10)
entrada_abajo.insert(0, "10")
entrada_abajo.grid(row=5, column=1, padx=10, sticky="w")
tk.Label(ventana, text="(Ignora el número de página)", fg="gray").grid(row=5, column=1, padx=100, sticky="w")

# --- NUEVO: OPCIONES DE VOZ ACTUALIZADAS ---
tk.Label(ventana, text="Idioma y Voz:", font=("Arial", 10, "bold")).grid(row=6, column=0, sticky="w", pady=5)
variable_voz = tk.StringVar(ventana)
variable_voz.set("Español - Masculina (Álvaro)") 
opciones_voz = [
    "Español - Femenina (Elvira)", 
    "Español - Masculina (Álvaro)", 
    "Inglés - Femenina (Aria)", 
    "Inglés - Masculina (Guy)",
    "Francés - Femenina (Denise)",
    "Francés - Masculina (Henri)",
    "Italiano - Femenina (Elsa)",
    "Italiano - Masculina (Diego)"
]
menu_voz = tk.OptionMenu(ventana, variable_voz, *opciones_voz)
menu_voz.grid(row=6, column=1, sticky="w", padx=10)
# -------------------------------------------

btn_iniciar = tk.Button(ventana, text="INICIAR CONVERSIÓN", bg="green", fg="white", font=("Arial", 10, "bold"), command=iniciar_conversion)
btn_iniciar.grid(row=7, column=0, columnspan=3, pady=15)

tk.Label(ventana, text="Progreso:", font=("Arial", 10, "bold")).grid(row=8, column=0, sticky="w")
caja_log = tk.Text(ventana, height=10, width=75, state=tk.DISABLED, bg="#f0f0f0")
caja_log.grid(row=9, column=0, columnspan=3, pady=5)

ventana.mainloop()