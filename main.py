from utils.pausa_humana import pausa_humana
from utils.logger_config import logger
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
from bs4 import BeautifulSoup


MAX_REINTENTOS = 3
DESCARGAS_ESP = "D:/PRUEBAS/scrapping/descargas/novelas_esp"
DESCARGAS_ENG = "D:/PRUEBAS/scrapping/descargas/novelas_eng"
URL = "https://www.royalroad.com/fiction/21220/mother-of-learning/chapter/301778/1-good-morning-brother"
TEXTO_APOYO = "Somos Klan Otaku Novelas Ligeras. Apoyanos en Patreon para más contenido.\n\n"

os.makedirs(DESCARGAS_ESP, exist_ok=True)
os.makedirs(DESCARGAS_ENG, exist_ok=True)

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


def obtener_nombre_novela(URL):
    return URL.split("/")[5].replace("-", "").title()

def obtener_contenido_original(driver):
    try:
        codigo_fuente = driver.page_source
        soup = BeautifulSoup(codigo_fuente, 'html.parser')
        
        titulo_original = soup.find('h1')  
        cuerpo_original = soup.find('div', class_='chapter-content') 

        if titulo_original and cuerpo_original:
            return titulo_original, cuerpo_original
        else:
            logger.error("❌ No se encontró el título o el cuerpo en el código fuente")
            return None, None
    except Exception as e:
        logger.error(f"❌ Error al obtener contenido original: {str(e)}")
        return None, None

def guardar_capitulo_original(titulo, cuerpo, nombre_novela, contador_global):
    try:
        nombre_archivo_original = f"{DESCARGAS_ENG}/{nombre_novela}-{contador_global}-english.txt"
        with open(nombre_archivo_original, "w", encoding="utf-8") as file_original:
            file_original.write(f"Title (Original): {titulo.text}\n\n")
            file_original.write(f"Body (Original):\n{cuerpo.text}\n\n")
        logger.info(f"✅ Capítulo en inglés guardado: {nombre_archivo_original}")
    except Exception as e:
        logger.error(f"❌ Error al guardar el capítulo original: {str(e)}")

def realizar_traduccion(driver):
    try:
        titulo_traducido = esperar_traduccion(driver, (By.TAG_NAME, "h1"))
        cuerpo_traducido = esperar_traduccion(driver, (By.CLASS_NAME, "chapter-content"))
        return titulo_traducido, cuerpo_traducido
    except Exception as e:
        logger.error(f"❌ Error durante la traducción: {str(e)}")
        return None, None

def guardar_capitulo_traducido(file, titulo, cuerpo):
    try:
        file.write(f"\n{titulo.text}\n\n{cuerpo.text}\n\n")
        logger.info("✅ Capítulo traducido guardado.")
    except Exception as e:
        logger.error(f"❌ Error al guardar el capítulo traducido: {str(e)}")


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

def procesar_capitulo(driver, URL, file, contador_archivo, contador_global, ultima_peticion=None):
    if ultima_peticion:
        tiempo_transcurrido = time.time() - ultima_peticion
        if tiempo_transcurrido < 30: 
            espera = 30 - tiempo_transcurrido
            logger.info(f"🕒 Esperando {espera:.2f} segundos para evitar sobrecarga de peticiones...")
            time.sleep(espera)
            
            
    try:
        driver.get(URL)
        time.sleep(8)
        pausa_humana()
        
        try:
            driver.find_element(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Aceptar')]").click()
            pausa_humana()
        except NoSuchElementException:
            pass

        titulo_original, cuerpo_original = obtener_contenido_original(driver)
        if titulo_original is None or cuerpo_original is None:
            return False, ultima_peticion

        guardar_capitulo_original(titulo_original, cuerpo_original, obtener_nombre_novela(URL), contador_global)

        titulo_traducido, cuerpo_traducido = realizar_traduccion(driver)

        hacer_scroll_completo(driver)
        time.sleep(random.uniform(0.2, 0.5))

        if not cuerpo_traducido:
            cuerpo_traducido = driver.find_element(By.CLASS_NAME, "chapter-content")

        if not verificar_idioma(cuerpo_traducido.text):
            logger.warning("Contenido posiblemente no traducido.")

        guardar_capitulo_traducido(file, titulo_traducido, cuerpo_traducido)

        logger.info(f"Capítulo {contador_global} guardado (local: {contador_archivo})")

        if contador_archivo in [5, 10]:
            file.write(TEXTO_APOYO)


        return True, time.time()
    
    except Exception as e:
        logger.error(f"Error procesando capítulo: {e}")
        return False, ultima_peticion

def main():
    ultima_peticion = None
    driver = None
    file = None
    try:
        driver = configurar_driver()
        nombre_novela = obtener_nombre_novela(URL)
        
        contador_global = 1
        contador_archivo = 1
        nombre_archivo = f"{DESCARGAS_ESP}/{nombre_novela}-{contador_global}.txt"
        file = open(nombre_archivo, "w", encoding="utf-8")
        file.write(TEXTO_APOYO)
   
        exito, ultima_peticion = procesar_capitulo(driver, URL, file, contador_archivo, contador_global, ultima_peticion)
        if not exito:
            return

        logger.info("Proceso completado")
        
    except Exception as e:
        logger.error(f"Error global: {e}")
        if file:
            file.close()
            os.rename(nombre_archivo, f"{DESCARGAS_ESP}/{nombre_novela}-INTERRUMPIDO-{contador_global-1}.txt")
    finally:
        if driver:
            driver.quit()
            logger.info("Navegador cerrado correctamente")

if __name__ == "__main__":
    main()
