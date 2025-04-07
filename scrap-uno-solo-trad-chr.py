import os
import time
import logging
import random
import pyautogui
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fake_useragent import UserAgent
from langdetect import detect

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración global
MAX_REINTENTOS = 3
DIRECTORIO_GUARDADO = "D:/PRUEBAS/scrapping/descargas"
TEXTO_APOYO = "Somos Klan Otaku Novelas Ligeras. Apoyanos en Patreon para más contenido.\n\n"
os.makedirs(DIRECTORIO_GUARDADO, exist_ok=True)

def get_random_user_agent():
    return UserAgent().random

def configurar_driver():
    for intento in range(MAX_REINTENTOS):
        try:
            logger.info(f"Configurando Chrome (Intento {intento+1}/{MAX_REINTENTOS})...")

            options = Options()
            options.add_argument(f"user-agent={get_random_user_agent()}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--lang=es")

            prefs = {
                "translate_whitelists": {"en": "es"},
                "translate": {"enabled": "true"}
            }
            options.add_experimental_option("prefs", prefs)

            service = Service(executable_path=r"D:/recursos-navegador/chromedriver-win64/chromedriver.exe")
            driver = Chrome(service=service, options=options)
            driver.get("about:blank")
            logger.info("Chrome configurado exitosamente")
            return driver

        except Exception as e:
            logger.error(f"Error en intento {intento+1}: {e}")
            if intento == MAX_REINTENTOS - 1:
                raise
            time.sleep(2)

def pausa_humana(min_seg=0.3, max_seg=0.7, scroll=False, mover_mouse=False):
    """Simula una pausa humana con comportamiento aleatorio opcional"""

    tiempo = random.uniform(min_seg, max_seg)
    logger.info(f"⏳ Pausa humana de {tiempo:.2f} segundos")
    time.sleep(tiempo)

    if scroll:
        # Scroll aleatorio hacia abajo y luego arriba
        for _ in range(random.randint(1, 3)):
            pyautogui.scroll(-random.randint(50, 150))
            time.sleep(0.1)
        for _ in range(random.randint(1, 2)):
            pyautogui.scroll(random.randint(30, 100))
            time.sleep(0.1)

    if mover_mouse:
        # Mueve el mouse suavemente a una posición aleatoria
        ancho, alto = pyautogui.size()
        x = random.randint(0, ancho)
        y = random.randint(0, alto)
        pyautogui.moveTo(x, y, duration=random.uniform(0.5, 1.2))
        logger.info(f"🖱️ Movimiento del mouse simulado a ({x}, {y})")

def obtener_nombre_novela(url):
    return url.split("/")[5].replace("-", "").title()

def verificar_idioma(texto):
    try:
        return detect(texto) == 'es'
    except:
        return False

def esperar_traduccion(driver, locator, timeout=30):
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
        elemento = driver.find_element(*locator)
        while "Text in english" in elemento.text:
            time.sleep(1)
            elemento = driver.find_element(*locator)
        return elemento
    except TimeoutException:
        return None

def hacer_scroll_completo(driver):
    altura_total = driver.execute_script("return document.body.scrollHeight")
    paso = random.randint(250, 350)
    for pos in range(0, altura_total, paso):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.2)
    for pos in range(altura_total, 0, -paso):
        driver.execute_script(f"window.scrollTo(0, {pos});")
        time.sleep(0.2)
    driver.execute_script("window.scrollTo(0, 0);")

def procesar_capitulo(driver, url, file, contador_archivo, contador_global):
    try:
        driver.get(url)
        time.sleep(8)
        pausa_humana()

        try:
            driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]").click()
            pausa_humana()
        except NoSuchElementException:
            pass

        titulo = esperar_traduccion(driver, (By.TAG_NAME, "h1"))
        cuerpo = esperar_traduccion(driver, (By.CLASS_NAME, "chapter-content"))
        hacer_scroll_completo(driver)
        time.sleep(random.uniform(0.2, 0.5))

        if not cuerpo:
            cuerpo = driver.find_element(By.CLASS_NAME, "chapter-content")

        if not verificar_idioma(cuerpo.text):
            logger.warning("Contenido posiblemente no traducido.")

        file.write(f"\n{titulo.text}\n\n{cuerpo.text}\n\n")
        logger.info(f"Capítulo {contador_global} guardado (local: {contador_archivo})")

        if contador_archivo in [5, 10]:
            file.write(TEXTO_APOYO)

        return True
    except Exception as e:
        logger.error(f"Error procesando capítulo: {e}")
        return False

def main():
    driver = None
    file = None
    try:
        driver = configurar_driver()
        url = "https://www.royalroad.com/fiction/21220/mother-of-learning/chapter/301778/1-good-morning-brother"
        nombre_novela = obtener_nombre_novela(url)

        contador_global = 1
        contador_archivo = 1
        nombre_archivo = f"{DIRECTORIO_GUARDADO}/{nombre_novela}-{contador_global}.txt"
        file = open(nombre_archivo, "w", encoding="utf-8")
        file.write(TEXTO_APOYO)

        if not procesar_capitulo(driver, url, file, contador_archivo, contador_global):
            return

        logger.info("Proceso completado")

    except Exception as e:
        logger.error(f"Error global: {e}")
        if file:
            file.close()
            os.rename(nombre_archivo, f"{DIRECTORIO_GUARDADO}/{nombre_novela}-INTERRUMPIDO-{contador_global-1}.txt")
    finally:
        if driver:
            driver.quit()
            logger.info("Navegador cerrado correctamente")

if __name__ == "__main__":
    main()
