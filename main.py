import os
import time
import logging
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Inicializar el bot con tu token de Telegram
bot = telebot.TeleBot("7519736547:AAGLA7-IWiLp-FbMrWQJablCbbItdrkEi-U")

# URL de la página Binance Learn and Earn
url = "https://academy.binance.com/es/learn-and-earn"

# Tu ID de usuario de Telegram
Chat_ID = int(os.getenv('CHAT_ID'))

def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920x1080')

    return webdriver.Chrome(options=chrome_options)

def obtener_publicaciones_actuales():
    """Obtiene los títulos y URLs de los cursos actuales en Binance usando Selenium"""
    driver = setup_selenium()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        cursos_elementos = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'css-yhgbpk')))
        
        cursos_actuales = []
        for curso in cursos_elementos:
            titulo = curso.find_element(By.CLASS_NAME, 'course-name').text
            enlace = curso.find_element(By.TAG_NAME, 'a').get_attribute('href')
            cursos_actuales.append((titulo, enlace))
        
        logging.info(f"Obtenidas {len(cursos_actuales)} publicaciones actuales")
        return cursos_actuales
    except Exception as e:
        logging.error(f"Error al obtener las publicaciones actuales: {e}")
    finally:
        driver.quit()
    return []

def leer_publicaciones_guardadas():
    """Lee las publicaciones guardadas desde el archivo 'cursos_binance.txt'"""
    publicaciones_guardadas = []
    try:
        if os.path.exists('cursos_binance.txt'):
            with open('cursos_binance.txt', 'r', encoding='utf-8') as f:
                contenido = f.read().strip().split('\n\n')
                for bloque in contenido:
                    lineas = bloque.split('\n')
                    titulo = lineas[0].replace("Título: ", "")
                    url = lineas[1].replace("URL: ", "")
                    publicaciones_guardadas.append((titulo, url))
            logging.info(f"Leídas {len(publicaciones_guardadas)} publicaciones guardadas.")
        else:
            logging.info("El archivo 'cursos_binance.txt' aún no existe.")
    except Exception as e:
        logging.error(f"Error al leer las publicaciones guardadas: {e}")
    return publicaciones_guardadas

def guardar_publicaciones_nuevas(cursos):
    """Guarda las nuevas publicaciones en 'cursos_binance.txt'"""
    try:
        with open('cursos_binance.txt', 'w', encoding='utf-8') as f:
            for titulo, url_curso in cursos:
                f.write(f"Título: {titulo}\n")
                f.write(f"URL: {url_curso}\n\n")
        logging.info("Publicaciones guardadas correctamente.")
    except Exception as e:
        logging.error(f"Error al guardar las publicaciones nuevas: {e}")

def verificar_nuevas_publicaciones():
    """Verifica si hay nuevas publicaciones comparando con el archivo guardado"""
    publicaciones_guardadas = leer_publicaciones_guardadas()
    publicaciones_actuales = obtener_publicaciones_actuales()
    
    if not publicaciones_actuales:
        return None
    
    # Comparamos las publicaciones actuales con las guardadas
    nuevas_publicaciones = [pub for pub in publicaciones_actuales if pub not in publicaciones_guardadas]
    
    if nuevas_publicaciones:
        logging.info(f"Se detectaron {len(nuevas_publicaciones)} nuevas publicaciones.")
        guardar_publicaciones_nuevas(publicaciones_actuales)
        return nuevas_publicaciones
    else:
        logging.info("No se detectaron nuevas publicaciones.")
    return None

@bot.message_handler(commands=['start', 'help'])
def enviar_bienvenida(mensaje):
    teclado = InlineKeyboardMarkup()
    teclado.row(InlineKeyboardButton("Verificar nuevas publicaciones", callback_data="verificar_publicaciones"))
    bot.reply_to(mensaje, 
                 "¡Bienvenido! Te ayudaré a verificar nuevas publicaciones en Binance Aprende y Gana.\n"
                 "Usa /init para verificar manualmente las nuevas publicaciones.", 
                 reply_markup=teclado)

@bot.message_handler(commands=['init'])
def comando_init(mensaje):
    nuevas_publicaciones = verificar_nuevas_publicaciones()
    if nuevas_publicaciones:
        for titulo, url in nuevas_publicaciones:
            bot.reply_to(mensaje, f"¡Nueva publicación encontrada!\n\nTítulo: {titulo}\nURL: {url}")
    else:
        bot.reply_to(mensaje, "No hay nuevas publicaciones en este momento.")

@bot.callback_query_handler(func=lambda llamada: True)
def manejador_consulta_callback(llamada):
    if llamada.data == "verificar_publicaciones":
        nuevas_publicaciones = verificar_nuevas_publicaciones()
        if nuevas_publicaciones:
            mensaje = "\n\n".join([f"Título: {titulo}\nURL: {url}" for titulo, url in nuevas_publicaciones])
            bot.answer_callback_query(llamada.id, f"Nuevas publicaciones encontradas:\n{mensaje}", show_alert=True)
        else:
            bot.answer_callback_query(llamada.id, "No hay nuevas publicaciones en este momento.", show_alert=True)

def main():
    logging.info("Bot iniciado. Ejecutando en modo continuo.")
    
    while True:
        try:
            nuevas_publicaciones = verificar_nuevas_publicaciones()
            if nuevas_publicaciones:
                for titulo, url in nuevas_publicaciones:
                    bot.send_message(Chat_ID, f"¡Nueva publicación en Binance Aprende y Gana!\n\nTítulo: {titulo}\nURL: {url}")
            
            # Esperar 30 minutos antes de la próxima verificación
            logging.info("Esperando 30 minutos antes de la próxima verificación")
            time.sleep(1800)
        except Exception as e:
            logging.error(f"Error en el bucle principal: {e}")
            time.sleep(60)  # Esperar 1 minuto en caso de error

if __name__ == '__main__':
    import threading
    threading.Thread(target=bot.polling, daemon=True).start()
    main()
