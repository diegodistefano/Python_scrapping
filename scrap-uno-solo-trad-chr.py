import os
import time
import logging
import pyautogui
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Configuración del logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Configuraciones
DIRECTORIO_CAPTURAS = "capturas"
URL_CAPITULO = "https://www.royalroad.com/fiction/74124/road-to-mastery-a-litrpg-adventure/chapter/1393710/true-north"
TIEMPO_ESPERA = 10

if not os.path.exists(DIRECTORIO_CAPTURAS):
    os.makedirs(DIRECTORIO_CAPTURAS)

def iniciar_driver():
    chrome_driver_path = "D:/recursos-navegador/chromedriver-win64/chromedriver.exe"

    options = Options()
    options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
    return driver

def pausa_humana(seg=1.5):
    time.sleep(seg)

def hacer_scroll_visible(driver):
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

def traducir_con_click_derecho():
    # Asegúrate de que el navegador está enfocado
    pyautogui.click(760, 700)  # Haz clic para asegurarte de que el navegador está en foco
    time.sleep(4)  # Espera un poco más para asegurarse de que el navegador está activo

    # Mover mouse al centro del texto
    logger.info(f"Moviendo mouse al centro del texto: (760, 3129)")
    pyautogui.moveTo(760, 700)

    logger.info("Traduciendo con clic derecho + tecla T...")
    pausa_humana(1)  # Espera por si hay animaciones
    pyautogui.rightClick()
    time.sleep(0.5)
    pyautogui.press('t')  # Asume que 'T' activa la traducción
    pausa_humana(2)  # Espera a que se traduzca

def procesar_capitulo(driver, url, contador_global):
    logger.info(f"Procesando capítulo {contador_global}: {url}")
    driver.get(url)

    try:
        WebDriverWait(driver, TIEMPO_ESPERA).until(
            EC.presence_of_element_located((By.CLASS_NAME, "chapter-content"))
        )
        pausa_humana()
    except Exception as e:
        logger.warning("No se encontró el contenido del capítulo: " + str(e))
        return None

    try:
        close_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[8]/div/div/div[3]/div[1]/button[2]"))
        )
        close_button.click()
        pausa_humana()
        logger.info("Banner cerrado.")
    except Exception as e:
        logger.warning("No se pudo cerrar el banner: " + str(e))

    try:
        pantalla = driver.find_element(By.CLASS_NAME, "chapter-content")

        # Mover el mouse al centro del contenido para hacer clic derecho ahí
        location = pantalla.location
        size = pantalla.size
        centro_x = location['x'] + size['width'] // 2
        centro_y = location['y'] + size['height'] // 2
        logger.info(f"Mover mouse al centro del texto: ({centro_x}, {centro_y})")

        # Desplazar scroll para que esté en pantalla
        driver.execute_script("arguments[0].scrollIntoView(true);", pantalla)
        pausa_humana()

        # Mover mouse y simular clic derecho + T
        pyautogui.moveTo(centro_x, centro_y + 150)  # ajustamos por barra de título/navegador
        traducir_con_click_derecho()

        hacer_scroll_visible(driver)

        cuerpo = driver.find_element(By.CLASS_NAME, "chapter-content")

        # Mover el mouse y copiar como humano
        location = cuerpo.location
        size = cuerpo.size
        centro_x = location['x'] + size['width'] // 2
        centro_y = location['y'] + size['height'] // 2
        pyautogui.moveTo(centro_x, centro_y)
        pyautogui.rightClick()
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        texto = pyperclip.paste()
        
        return texto
    except Exception as e:
        logger.error(f"Error al obtener el texto del capítulo: {e}")
        return None

def guardar_texto(texto, archivo):
    with open(archivo, "a", encoding="utf-8") as f:
        f.write(texto + "\n\n")
    logger.info(f"Capítulo guardado en {archivo}")

def main():
    driver = iniciar_driver()
    try:
        texto = procesar_capitulo(driver, URL_CAPITULO, 1)
        if texto:
            guardar_texto(texto, "novela_traducida.txt")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
