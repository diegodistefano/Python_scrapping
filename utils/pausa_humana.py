from utils.logger_config import logger
import time
import logging
import random
import pyautogui

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

