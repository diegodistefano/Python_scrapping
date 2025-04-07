import os
import time
import logging
import pyautogui
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Chrome  # Cambiado de Firefox a Chrome
from selenium.webdriver.chrome.service import Service  # Cambiado de firefox a chrome
from selenium.webdriver.chrome.options import Options  # Cambiado de firefox a chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random
from fake_useragent import UserAgent
from langdetect import detect

# Configuración de logging (igual que antes)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración global
MAX_REINTENTOS = 3
ESPERA_ENTRE_CAPITULOS = random.uniform(2, 5)
TEXTO_APOYO = "Somos Klan Otaku Novelas Ligeras. Apoyanos en Patreon para más contenido.\n\n"
DIRECTORIO_GUARDADO = "D:/PRUEBAS/scrapping/descargas"
os.makedirs(DIRECTORIO_GUARDADO, exist_ok=True)

IDIOMA_ORIGINAL = "en"  # Inglés (idioma original del sitio)
IDIOMA_DESEADO = "es"    # Español (idioma al que se traduce)

def get_random_user_agent():
    ua = UserAgent()
    return ua.random

def configurar_driver():
    """Configura el driver de Chrome """
    for intento in range(MAX_REINTENTOS):
        try:
            logger.info(f"🥚 Configurando Chrome (Intento {intento+1}/{MAX_REINTENTOS})...")

            options = Options()  # Ahora es ChromeOptions
            # options.add_argument("--headless=new")  # Modo headless en Chrome
            options.add_argument(f"user-agent={get_random_user_agent()}")  # User-Agent aleatorio
            options.add_argument("--disable-blink-features=AutomationControlled")  # Evita detección de bot
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # Configuración de idioma (Chrome usa --lang)
            options.add_argument('--lang=es')  # Forzar idioma del navegador
            options.add_argument('--force-language-detection=es')  # Detección de idioma
            prefs = {
                "translate_whitelists": {"en":"es"},  # Traducir inglés -> español
                "translate":{"enabled":"true"}
            }
            options.add_experimental_option("prefs", prefs)
            # ... (resto del código)

            # Ruta a chromedriver.exe (¡descárgalo y colócalo en tu sistema!)
            service = Service(executable_path=r"D:/recursos-navegador/chromedriver-win64/chromedriver.exe")  # Cambiado a chromedriver

            driver = Chrome(service=service, options=options)  # Ahora es Chrome, no Firefox

            driver.get("about:blank")
            logger.info("✅ Chrome configurado exitosamente")
            return driver

        except Exception as e:
            logger.error(f"⚠️ Error en intento {intento+1}: {str(e)}")
            if intento == MAX_REINTENTOS - 1:
                logger.critical("💥 No se pudo configurar Chrome")
                raise
            time.sleep(2)


def pausa_humana(seg=1.5):
    time.sleep(seg)

def obtener_nombre_novela(url):
    """Extrae el nombre de la novela desde la URL"""
    partes = url.split("/")
    return partes[5].replace("-", " ").title().replace(" ", "")


def verificar_idioma(texto):
    try:
        return detect(texto) == 'es'  # True si es español
    except:
        return False

def forzar_traduccion(driver):
    """Intenta activar la traducción si el sitio lo permite"""
    try:
        # Ejemplo: Busca y hace clic en el botón de traducción si existe
        boton_traduccion = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Translate') or contains(text(), 'Traducir')]"))
        )
        boton_traduccion.click()
        logger.info("🔁 Activando traducción mediante botón")
        return True
    except:
        return False

def esperar_traduccion_completa(driver, locator, timeout=30):
    """Espera que el contenido traducido esté completamente cargado en el DOM"""
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located(locator)
    )
    # Verifica que el contenido traducido esté presente en el DOM
    elemento = driver.find_element(*locator)
    while "Text in english" in elemento.text:  # Compara el texto original con el contenido traducido
        time.sleep(1)  # Espera un poco más
        elemento = driver.find_element(*locator)  # Actualiza el elemento
    return elemento

def hacer_scroll_completo(driver):
    altura_total = driver.execute_script("return document.body.scrollHeight")
    logger.info(f"Haciendo scroll visible (Altura total: {altura_total}px)")

    paso = 250

    for pos in range(0, altura_total, paso):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.4)

    for pos in range(altura_total, 0, -paso):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.4)

    driver.execute_script("window.scrollTo(0, 0);")
    logger.info("Scroll visible completado")

def obtener_texto_traducido(driver, locator):
    """Obtiene el texto traducido desde el DOM renderizado completamente"""
    try:
        elemento = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(locator)
        )
        # Verifica que el texto traducido esté visible y no el texto original
        texto = elemento.text
        if "Text in english" in texto:  # Asegúrate de que no estás obteniendo el texto original
            logger.warning("⚠️ Se obtuvo el texto original en lugar del traducido.")
            return None
        return texto
    except TimeoutException:
        logger.error("❌ Tiempo de espera agotado para obtener el texto traducido.")
        return None

def procesar_capitulo(driver, url, file, contador_archivo, contador_global):
    try:
        driver.get(url)

        ##############################################################
        time.sleep(8)  # Espera inicial para cargar la página
        ##############################################################
        pausa_humana()

        # Cerrar banners si existen
        try:
            driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]").click()
            logger.info("✅ Banner cerrado")
            pausa_humana()
        except NoSuchElementException:
            pass

        # Esperar a que la traducción se complete
        titulo = esperar_traduccion_completa(driver, (By.TAG_NAME, "h1"))
        if not titulo:
            titulo = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            logger.warning("⚠️ No se pudo verificar la traducción del título")

        cuerpo = esperar_traduccion_completa(driver, (By.CLASS_NAME, "chapter-content"))

        
        # Scroll completo (bajar + subir)
        hacer_scroll_completo(driver)
        
        # Espera adicional para traducción
        time.sleep(5)

        if not cuerpo:
            cuerpo = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "chapter-content")))
            logger.warning("⚠️ No se pudo verificar la traducción del contenido")

        # Verificar si el contenido está en el idioma deseado
        if not verificar_idioma(cuerpo.text):
            logger.warning("⚠️ El contenido no está en el idioma deseado")

        # Guardar texto tal como aparece
        file.write(f"\n{titulo.text}\n\n{cuerpo.text}\n\n")
        logger.info(f"📖 Capítulo {contador_global} guardado (local: {contador_archivo})")

        # Texto de apoyo estratégico
        if contador_archivo in [5, 10]:
            file.write(TEXTO_APOYO)

        return True

    except Exception as e:
        logger.error(f"❌ Error procesando capítulo: {str(e)}")
        return False

def main():
    try:
        driver = configurar_driver()
        url_base = "https://www.royalroad.com/fiction/33844/the-runesmith/chapter/520102/chapter-1-so-it-begins-with-a-truck"
        novela_nombre = obtener_nombre_novela(url_base)

        contador_global = 1
        contador_archivo = 1
        file = None

        # Manejo de archivos (se procesará solo una página)
        if contador_archivo == 1:
            if file:
                file.close()
            nombre_archivo = f"{DIRECTORIO_GUARDADO}/{novela_nombre}-{contador_global}.txt"
            file = open(nombre_archivo, "w", encoding="utf-8")
            file.write(TEXTO_APOYO)

        # Procesar capítulo actual
        if not procesar_capitulo(driver, url_base, file, contador_archivo, contador_global):
            return

        logger.info("✅ Proceso completado")

    except Exception as e:
        logger.error(f"💥 Error global: {str(e)}")
        if file:
            file.close()
            os.rename(nombre_archivo, f"{DIRECTORIO_GUARDADO}/{novela_nombre}-INTERRUMPIDO-{contador_global-1}.txt")
    finally:
        if 'driver' in locals():
            driver.quit()
            logger.info("🛌 Navegador cerrado correctamente")

if __name__ == "__main__":
    main()  # Todo lo demás funciona igual.