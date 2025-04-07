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
DIRECTORIO_GUARDADO = "/app/novels-in-spanish"
os.makedirs(DIRECTORIO_GUARDADO, exist_ok=True)

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

            service = Service(executable_path='/usr/local/bin/geckodriver')
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

def procesar_capitulo(driver, url, file, contador_archivo, contador_global):
    """Procesa un capítulo individual"""
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

        # Extraer contenido
        titulo = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        cuerpo = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "chapter-content")))

        # Guardar texto tal como aparece
        file.write(f"🌟 Capítulo {contador_archivo}\n{titulo.text}\n\n{cuerpo.text}\n\n")
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

        while True:
            try:
                # Manejo de archivos (cada 10 capítulos)
                if contador_archivo == 1:
                    if file:
                        file.close()
                    nombre_archivo = f"{DIRECTORIO_GUARDADO}/{novela_nombre}-{contador_global}-ES.txt"
                    file = open(nombre_archivo, "w", encoding="utf-8")
                    file.write(TEXTO_APOYO)

                # Procesar capítulo actual
                if not procesar_capitulo(driver, url_base, file, contador_archivo, contador_global):
                    break

                # Navegar al siguiente capítulo
                try:
                    siguiente_btn = driver.find_element(By.XPATH, "//a[contains(@class, 'btn-next')]")
                    if "disabled" in siguiente_btn.get_attribute("class"):
                        logger.info("🏋️ No hay más capítulos disponibles")
                        break

                    url_base = siguiente_btn.get_attribute("href")
                    contador_global += 1
                    contador_archivo = contador_archivo + 1 if contador_archivo < 10 else 1
                    pausa_humana()

                except NoSuchElementException:
                    logger.info("🏋️ No se encontró botón de siguiente capítulo")
                    break

            except Exception as e:
                logger.error(f"💣 Error en el bucle principal: {str(e)}")
                break

        logger.info("✅ Proceso completado" if contador_archivo == 1 else "⏸️ Proceso interrumpido")

    except Exception as e:
        logger.error(f"💥 Error global: {str(e)}")
        if file:
            file.close()
            os.rename(nombre_archivo, f"{DIRECTORIO_GUARDADO}/{novela_nombre}-INTERRUMPIDO-{contador_global-1}-ES.txt")
    finally:
        if 'driver' in locals():
            driver.quit()
            logger.info("🛌 Navegador cerrado correctamente")

if __name__ == "__main__":
    main()
