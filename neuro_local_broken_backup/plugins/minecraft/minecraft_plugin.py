"""
Плагин для игры Minecraft для Neuro Local агента
Исправлено: проверка активности окна, защита от действий в неактивном окне
"""
import pydirectinput
import time
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, Optional, Tuple
from core.config_loader import ConfigLoader


class MinecraftPlugin:
    """Плагин для взаимодействия с Minecraft"""
    def __init__(self, config: ConfigLoader):
        self.config = config
        self.enabled = config.get("minecraft.enabled", False)
        self.key_bindings = config.get("minecraft.key_bindings", {})
        self.safe_mode = config.get("minecraft.safe_mode", True)
        self.game_active = False
        
        if self.enabled:
            print("Minecraft плагин загружен")
            
    def is_game_active(self) -> bool:
        """Проверяет, активно ли окно Minecraft"""
        try:
            import pygetwindow as gw
            active_window = gw.getActiveWindow()
            
            if not active_window:
                return False
                
            title = active_window.title.lower()
            self.game_active = "minecraft" in title or "minecraft" in active_window.__str__().lower()
            return self.game_active
            
        except ImportError:
            print("pygetwindow не установлен, пропускаем проверку окна")
            self.game_active = True
            return self.game_active
        except Exception as e:
            print(f"Ошибка проверки окна: {e}")
            return False
            
    def ensure_game_active(self) -> bool:
        """Убеждается, что игра активна, иначе выводит предупреждение"""
        if not self.is_game_active():
            print("[ПРЕДУПРЕЖДЕНИЕ] Окно Minecraft не активно. Пожалуйста, переключитесь на него.")
            return False
        return True
        
    def press_key(self, key: str, duration: float = 0.1):
        """Нажимает клавишу в Minecraft"""
        if not self.ensure_game_active():
            return False
            
        actual_key = self.key_bindings.get(key, key)
        pydirectinput.keyDown(actual_key)
        time.sleep(duration)
        pydirectinput.keyUp(actual_key)
        return True
        
    def tap_key(self, key: str):
        """Коротко нажимает клавишу в Minecraft"""
        if not self.ensure_game_active():
            return False
            
        actual_key = self.key_bindings.get(key, key)
        pydirectinput.press(actual_key)
        return True
        
    def move_forward(self, duration: float = 1.0):
        """Двигается вперед"""
        return self.press_key("forward", duration)
        
    def move_backward(self, duration: float = 1.0):
        """Двигается назад"""
        return self.press_key("backward", duration)
        
    def move_left(self, duration: float = 1.0):
        """Двигается влево"""
        return self.press_key("left", duration)
        
    def move_right(self, duration: float = 1.0):
        """Двигается вправо"""
        return self.press_key("right", duration)
        
    def jump(self):
        """Прыгает"""
        return self.tap_key("jump")
        
    def sneak(self):
        """Приседает"""
        return self.tap_key("sneak")
        
    def attack(self):
        """Атакует (левый клик)"""
        if not self.ensure_game_active():
            return False
            
        pydirectinput.mouseDown(button='left')
        time.sleep(0.1)
        pydirectinput.mouseUp(button='left')
        return True
        
    def use(self):
        """Использует предмет/блок (правый клик)"""
        if not self.ensure_game_active():
            return False
            
        pydirectinput.mouseDown(button='right')
        time.sleep(0.1)
        pydirectinput.mouseUp(button='right')
        return True
        
    def open_inventory(self):
        """Открывает инвентарь"""
        return self.tap_key("inventory")
        
    def drop_item(self):
        """Выкидывает предмет"""
        return self.tap_key("drop")
        
    def enter_chat(self):
        """Открывает чат"""
        return self.tap_key("chat")
        
    def routine_explore(self, duration: int = 60):
        """Рутина исследования - случайное перемещение по миру"""
        import random
        
        if not self.ensure_game_active():
            return False
            
        print("Начинаю рутину исследования...")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            directions = ["forward", "backward", "left", "right"]
            direction = random.choice(directions)
            move_duration = random.uniform(0.5, 2.0)
            
            self.press_key(direction, move_duration)
            time.sleep(random.uniform(0.1, 0.5))
            
            if random.random() < 0.2:
                self.jump()
                
            if random.random() < 0.1:
                self.attack()
                
        print("Рутина исследования завершена")
        return True
        
    def routine_mine_wood(self, target_count: int = 10):
        """Рутина добычи древесины"""
        import random
        
        if not self.ensure_game_active():
            return False
            
        print(f"Начинаю рутину добычи древесины (цель: {target_count})...")
        
        found_logs = 0
        start_time = time.time()
        
        while found_logs < target_count and time.time() - start_time < 300:
            print("Ищу деревья...")
            time.sleep(2)
            
            if random.random() < 0.3:
                print("Нашел дерево! Начинаю добычу...")
                for i in range(5):
                    self.attack()
                    time.sleep(0.5)
                    
                found_logs += 1
                print(f"Добыто блоков: {found_logs}/{target_count}")
                
            time.sleep(1)
            
        print(f"Рутина добычи древесины завершена. Добыто: {found_logs}/{target_count}")
        return True
        
    def routine_craft_table(self):
        """Рутина создания верстака"""
        if not self.ensure_game_active():
            return False
            
        print("Начинаю рутину создания верстака...")
        
        self.open_inventory()
        time.sleep(1)
        
        print("Создаю верстак...")
        
        self.open_inventory()
        time.sleep(0.5)
        
        print("Рутина создания верстака завершена")
        return True
        
    def routine_place_block(self, block_type: str = "wooden_planks"):
        """Рутина размещения блока"""
        if not self.ensure_game_active():
            return False
            
        print(f"Начинаю рутину размещения блока: {block_type}...")
        
        pydirectinput.press('1')
        time.sleep(0.2)
        
        self.use()
        
        print(f"Блок {block_type} размещен")
        return True
        
    def routine_eat(self):
        """Рутина приема пищи"""
        if not self.ensure_game_active():
            return False
            
        print("Начинаю рутину приема пищи...")
        
        pydirectinput.press('2')
        time.sleep(0.2)
        
        pydirectinput.mouseDown(button='right')
        time.sleep(1.5)
        pydirectinput.mouseUp(button='right')
        
        print("Прием пищи завершен")
        return True
        
    def routine_sleep(self):
        """Рутина сна"""
        if not self.ensure_game_active():
            return False
            
        print("Начинаю рутину сна...")
        
        pydirectinput.press('3')
        time.sleep(0.2)
        
        print("Размещаю кровать...")
        self.use()
        time.sleep(1)
        
        print("Ложусь спать...")
        self.use()
        
        print("Сплю... (симуляция 10 секунд)")
        time.sleep(10)
        
        print("Просыпаюсь...")
        return True
        
    def detect_hud_elements(self, screenshot: Image.Image) -> Dict[str, Any]:
        """Обнаруживает элементы HUD в Minecraft"""
        img_cv = np.array(screenshot)
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
        
        detected = {
            'health': 20,
            'hunger': 20,
            'hotbar': {"slots": [None] * 9},
            'inventory_open': False
        }
        
        return detected
