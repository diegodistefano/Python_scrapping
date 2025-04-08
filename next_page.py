from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import os

# Carpeta donde se guardarán los archivos
directorio_guardado = "D:\\novels-in-english"
os.makedirs(directorio_guardado, exist_ok=True)  # Crea la carpeta si no existe

def configurar_driver(headless=True):
    """ Configura y devuelve una instancia de Chrome WebDriver """
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    
    # Configuraciones del navegador
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Modo sin interfaz gráfica opcional
    if headless:
        options.add_argument("--headless=new")
    
    return Chrome(service=service, options=options)

def obtener_nombre_novela(url):
    """Extrae el nombre de la novela desde la URL y lo formatea"""
    partes = url.split("/")
    return partes[5].replace(" ", "-").lower()

def main():
    try:
        url = "https://www.royalroad.com/fiction/33844/the-runesmith/chapter/520102/chapter-1-so-it-begins-with-a-truck"
        novela_slug = obtener_nombre_novela(url)
        driver = configurar_driver()
        driver.get(url)
        
        wait = WebDriverWait(driver, 3)  # Máximo 3 seg
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))  # Espera a h1

        time.sleep(random.uniform(1, 3))  # Espera entre 1 y 3 segundos
        
        # Intentar cerrar el banner
        try:
            close_button = driver.find_element(By.XPATH, "/html/body/div[8]/div/div/div[3]/div[1]/button[2]")
            close_button.click()
            print("Banner cerrado con éxito.")
        except Exception as e:
            print("No se pudo cerrar el banner:", e)

        contador = 1
        while True:
            if (contador - 1) % 10 == 0:
                contador_inicial = contador
                contador_final = contador_inicial + 9
                nombre_archivo = f"{directorio_guardado}\\{novela_slug}-{contador_inicial}-{contador_final}.txt"
                file = open(nombre_archivo, "w", encoding="utf-8")
            
            # Espera breve
            time.sleep(random.uniform(0.2, 0.5))
            
            title = driver.find_element(By.TAG_NAME, "h1").text
            body = driver.find_element(By.CLASS_NAME, "chapter-content").text
            
            # Escribir en el archivo
            file.write(title + "\n")
            file.write(body + "\n\n")
            
            print(f"Capítulo {contador} guardado en {nombre_archivo}")
            
            # Intentar avanzar a la siguiente página
            try:
                next_button = driver.find_element(By.XPATH, "/html/body/div[3]/div/div/div/div[1]/div[2]/div[2]/div[1]/div[2]/a")
                if "disabled" in next_button.get_attribute("class"):
                    print("No hay más capítulos disponibles.")
                    break
                next_button.click()
                contador += 1
            except Exception:
                print("No se encontró el botón de siguiente capítulo.")
                break
            
            # Cerrar el archivo cada 10 capítulos
            if contador % 10 == 1:
                file.close()
        
        print("Descarga completada.")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
