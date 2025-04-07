from selenium import webdriver
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
import os
import logging
from fake_useragent import UserAgent

# Configuración de logging
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
    """Configura el driver de Firefox con manejo robusto de errores"""
    for intento in range(MAX_REINTENTOS):
        try:
            logger.info(f"🥚 Configurando Firefox (Intento {intento+1}/{MAX_REINTENTOS})...")

            options = Options()
            options.headless = True
            options.set_preference("general.useragent.override", get_random_user_agent())
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # Configuración adicional para manejar idiomas
            options.set_preference("intl.accept_languages", IDIOMA_DESEADO)

            service = Service(executable_path=r'D:/PRUEBAS/scrapping/geckodriver.exe')

            driver = Firefox(service=service, options=options)

            driver.get("about:blank")
            logger.info("✅ Firefox configurado exitosamente")
            return driver

        except Exception as e:
            logger.error(f"⚠️ Error en intento {intento+1}: {str(e)}")
            if intento == MAX_REINTENTOS - 1:
                logger.critical("💥 No se pudo configurar Firefox")
                raise
            time.sleep(2)

def pausa_humana():
    """Simula pausas humanas aleatorias"""
    base_wait = ESPERA_ENTRE_CAPITULOS * (0.8 + random.random() * 0.4)
    time.sleep(base_wait)
    if random.random() < 0.2:
        long_pause = random.uniform(5, 15)
        logger.info(f"⏳ Pausa larga simulada: {long_pause:.1f} segundos")
        time.sleep(long_pause)

def obtener_nombre_novela(url):
    """Extrae el nombre de la novela desde la URL"""
    partes = url.split("/")
    return partes[5].replace("-", " ").title().replace(" ", "")

def verificar_idioma(driver, elemento):
    """Verifica específicamente traducción inglés->español con más precisión"""
    texto = elemento.text.lower()
    
    # Palabras clave que indican español vs inglés
    indicadores_es = [" el ", " la ", " los ", " las ", " de ", " que ", " y ", " en "]
    indicadores_en = [" the ", " and ", " of ", " to ", " a ", " in ", " is ", " it "]
    
    conteo_es = sum(texto.count(palabra) for palabra in indicadores_es)
    conteo_en = sum(texto.count(palabra) for palabra in indicadores_en)
    
    # Si encontramos más indicadores de español que de inglés
    return conteo_es > conteo_en

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
    """Procesa un capítulo individual con manejo de traducción"""
    try:
        driver.get(url)
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
        if not cuerpo:
            cuerpo = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "chapter-content")))
            logger.warning("⚠️ No se pudo verificar la traducción del contenido")

        # Verificar si el contenido está en el idioma deseado
        if not verificar_idioma(driver, cuerpo):
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
    main()
