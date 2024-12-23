import math
import pygame, sys
from pygame.locals import *
import numpy as np
import random

class Entity:
    def __init__(self, hp, power, x, y, speed, active) -> None:
        self.hp = hp
        self.power = power
        self.speed = speed
        self.x = x
        self.y = y
        self.active = active

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.die()

    def die(self):
        print(f"{self.__class__.__name__} погиб")


class Hero(Entity):
    def __init__(self, hp, power, x, y, speed, protect, active) -> None:
        super().__init__(hp, power, x, y, speed, active)
        self.protect = protect
        self.bullet = None
        self.speed = speed
        self.rect = pygame.Rect(self.x, self.y, 32, 32)

    def shoot(self, direction):
        if self.power >= 5:
            self.bullet = PlayerBullet(self.x, self.y, direction)
            self.power -= 1

    def updatePower (self):
        if self.power < 15:
            self.power += 5
        else: 
            self.power = 20
                
    def update_rect(self):
        self.rect.x = self.x
        self.rect.y = self.y
        
    def perform_melee_attack(self, enemies, landscape):
        """Атака врагов в радиусе ближнего боя."""
        for enemy in enemies:
            distance = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if distance <= 50:  # Радиус ближнего боя
                print(f"Удар по врагу {enemy.__class__.__name__}!")
                enemy.take_damage(self.power)  # Наносим урон врагу
                enemy.knockback(self)  # Отталкиваем врага
                if enemy.hp <= 0:
                    print(f"{enemy.__class__.__name__} уничтожен!")
                    enemies.remove(enemy)  # Убираем врага из списка
                
                
                
class SimpleNeuralNet:
    def __init__(self, input_size=4, hidden_size=6, output_size=2):
        self.weights = {
            'w1': np.random.randn(input_size, hidden_size),
            'b1': np.random.randn(hidden_size),
            'w2': np.random.randn(hidden_size, output_size),
            'b2': np.random.randn(output_size)
        }

    def forward(self, inputs):
        z1 = np.dot(inputs, self.weights['w1']) + self.weights['b1']
        a1 = np.tanh(z1)
        z2 = np.dot(a1, self.weights['w2']) + self.weights['b2']
        return np.tanh(z2)

                

class EnemyMelee(Entity):
    def __init__(self, hp, power, x, y, speed, protect, fov_radius, active):
        super().__init__(hp, power, x, y, speed, active)
        self.protect = protect
        self.fov_radius = fov_radius
        self.is_moving = False
        self.neural_net = SimpleNeuralNet()
        self.direction = np.array([random.choice([-1, 1]), random.choice([-1, 1])])  # Начальное направление
        self.step_counter = 0
        self.change_direction_interval = 20  # Сколько шагов идти в одном направлении
        self.move_delay = 20  # Задержка между движениями (количество кадров)
        self.move_timer = 0  # Таймер для отслеживания времени движения
        self.hits_taken = 0  # Счётчик ударов
        self.is_alive = True  # Статус врага
        
    def take_damage(self, amount):
        """Обработка получения урона от героя."""
        self.hp -= amount
        print(f"{self.__class__.__name__} получил {amount} урона! Осталось HP: {self.hp}")
        if self.hp <= 0:
            self.is_alive = False

    def knockback(self, hero):
        """Отталкивание врага от героя."""
        dx, dy = self.x - hero.x, self.y - hero.y
        distance = math.hypot(dx, dy)
        if distance > 0:
            dx, dy = dx / distance, dy / distance  # Нормализуем направление
            self.x += dx * 10  # Отталкиваем на небольшое расстояние
            self.y += dy * 10


    def update(self, hero, landscape, hero_attacking=False):
        dx, dy = hero.x - self.x, hero.y - self.y
        distance_to_hero = math.hypot(dx, dy)

        if (pygame.Rect(hero.x, hero.y, 32, 32).colliderect(self.x, self.y, 32, 32)): #урон при коллижне
            hero.hp -= self.damage

        if hero.bullet and (pygame.Rect(self.x, self.y, 32, 32).colliderect(hero.bullet.x, hero.bullet.y, 8, 8)): #урон при коллижне
            self.hp -= 20
            hero.bullet = None

        if self.hp <= 0:
            self.active = 0

        # Проверяем прямую видимость
        def has_line_of_sight():
            steps = max(abs(dx), abs(dy))  # Определяем количество шагов для проверки
            step_x = dx / steps  # Инкремент по x
            step_y = dy / steps  # Инкремент по y
            current_x, current_y = self.x, self.y

            for _ in range(int(steps)):
                current_x += step_x
                current_y += step_y
                check_rect = pygame.Rect(current_x, current_y, 32, 32)
                if any(check_rect.colliderect(segment) for cluster in landscape.mountains for segment in cluster):
                    return False  # Луч пересекает блок горы
            return True

        if hero_attacking and distance_to_hero <= 50:  # Атака возможна только на ближнем расстоянии
            # Уменьшаем здоровье врага
            self.hp -= hero.power
            print(f"Враг получил урон, осталось HP: {self.hp}")

            # Отталкиваем врага
            knockback_x = dx / distance_to_hero * 10  # Сила отталкивания
            knockback_y = dy / distance_to_hero * 10
            new_x = self.x - knockback_x
            new_y = self.y - knockback_y

            # Проверка на столкновение с препятствиями
            knockback_rect = pygame.Rect(new_x, new_y, 32, 32)
            if not any(knockback_rect.colliderect(segment) for cluster in landscape.mountains for segment in cluster):
                self.x, self.y = new_x, new_y

            # Если здоровье врага <= 0, он умирает
            if self.hp <= 0:
                print("Враг уничтожен!")
                self.is_alive = False  # Указываем, что враг мертв
                return  # Выходим из метода

        elif distance_to_hero <= self.fov_radius and has_line_of_sight():
            # Если герой в поле зрения и есть прямая видимость
            self.is_moving = True
            dx, dy = dx / distance_to_hero, dy / distance_to_hero
            new_x = self.x + dx * self.speed
            new_y = self.y + dy * self.speed
        else:
            self.is_moving = False

            # Используем нейронку для получения случайного движения
            inputs = np.array([self.x, self.y, hero.x, hero.y])
            move_decision = self.neural_net.forward(inputs)

            if self.step_counter < self.change_direction_interval:
                # Проверяем, пришло ли время движения
                if self.move_timer <= 0:
                    new_x = self.x + self.direction[0] * self.speed * 0.5  # Уменьшаем скорость
                    new_y = self.y + self.direction[1] * self.speed * 0.5
                    self.move_timer = self.move_delay  # Сбрасываем таймер
                else:
                    new_x, new_y = self.x, self.y  # Остаёмся на месте
                    self.move_timer -= 1  # Уменьшаем таймер
                self.step_counter += 1
            else:
                # Меняем направление
                self.direction = np.array([random.choice([-1, 1]), random.choice([-1, 1])])
                new_x = self.x + self.direction[0] * self.speed * 0.5
                new_y = self.y + self.direction[1] * self.speed * 0.5
                self.move_timer = self.move_delay  # Сбрасываем таймер
                self.step_counter = 0

        # Проверка на столкновения с горами
        new_rect = pygame.Rect(new_x, new_y, 32, 32)
        if not any(new_rect.colliderect(segment) for cluster in landscape.mountains for segment in cluster):
            self.x, self.y = new_x, new_y
        else:
            # Если есть препятствие, меняем направление
            self.direction = np.array([random.choice([-1, 1]), random.choice([-1, 1])])
        
    def draw(self, screen):
        pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), 20)

class EnemyArcher(Entity):
    def __init__(self, hp, power, x, y, speed, protect, fov_radius, active) -> None:
        super().__init__(hp, power, x, y, speed, active)
        self.protect = protect
        self.fov_radius = fov_radius  # Поле зрения лучника
        self.shoot_delay = 1000  # Задержка между выстрелами (в миллисекундах)
        self.last_shot = pygame.time.get_ticks()
        self.bullet = None  # Изначально пуля отсутствует
        self.is_alive = True  # Враг жив

    def update(self, hero, landscape, hero_attacking=False):  # Добавляем hero_attacking как аргумент
        # Вычисляем расстояние до героя
        dx, dy = hero.x - self.x, hero.y - self.y
        distance_to_hero = math.hypot(dx, dy)

        # Если герой атакует, и враг в радиусе удара, враг может быть поражен
        if hero_attacking and distance_to_hero <= 50:  # 50 пикселей, как пример для ближнего боя
            self.take_damage()  # Если враг в радиусе удара, враг получает урон
            print("Враг атакован!")
            return  # Враг получает урон и не двигается дальше в этот момент

        # Если герой в пределах поля зрения, пытаемся стрелять
        if distance_to_hero <= self.fov_radius:
            now = pygame.time.get_ticks()
            if now - self.last_shot > self.shoot_delay:
                self.shoot(hero)  # Передаем hero сюда
                self.last_shot = now

        if (pygame.Rect(hero.x, hero.y, 32, 32).colliderect(self.x, self.y, 32, 32)): #урон при коллижне
            hero.hp -= self.damage

        if hero.bullet and (pygame.Rect(self.x, self.y, 32, 32).colliderect(hero.bullet.x, hero.bullet.y, 8, 8)): #урон при коллижне
            self.hp -= 20
            hero.bullet = None

        if self.hp <= 0:
            self.active = 0

    def shoot(self, hero):  # Передаем hero сюда
        print('archer shot')
        dx, dy = hero.x - self.x, hero.y - self.y  # Вычисляем направление на героя
        angle = math.atan2(dy, dx)  # Получаем угол между врагом и героем
        self.bullet = Bullet(self.x, self.y, angle)  # Передаем угол в пулю
        
    def take_damage(self):
        self.hp -= 25  # Урон от удара героя
        if self.hp <= 0:
            self.is_alive = False
            print("Archer defeated!")

    def knockback(self, hero):
        # Отталкивание лучника от героя
        dx, dy = self.x - hero.x, self.y - hero.y
        distance = math.hypot(dx, dy)
        if distance == 0:
            return  # Избегаем деления на 0

        # Нормализуем вектор отталкивания
        dx /= distance
        dy /= distance

        # Смещение лучника
        self.x += dx * 10
        self.y += dy * 10

    def draw(self, screen):
        # Отрисовка лучника
        if self.is_alive:
            pygame.draw.circle(screen, (255, 165, 0), (int(self.x), int(self.y)), 20)
        # Отрисовка пули, если она существует
        if self.bullet:
            self.bullet.draw(screen)  # Предполагается, что метод draw() есть у класса Bullet

class Bullet:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.speed = 5	
        self.direction = direction
        self.creation_time = pygame.time.get_ticks()  # Время создания пули

    def update(self, dungeon, hero):
        # Проверяем, прошло ли 3 секунды с момента создания пули
        if pygame.time.get_ticks() - self.creation_time > 3000:
            return False  # Пуля "умирает" через 3 секунды
        
        dx, dy = hero.x - self.x, hero.y - self.y
        dist = math.hypot(dx, dy)
        dx, dy = dx / dist, dy / dist 
        self.x += dx * self.speed
        self.y += dy * self.speed

        return True  # Пуля продолжает существовать

class PlayerBullet:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.speed = 8
        self.direction = direction
        self.creation_time = pygame.time.get_ticks() 

    def update (self):
        if pygame.time.get_ticks() - self.creation_time > 800:
            return False

        if self.direction == 1: #лево
            self.x -= self.speed
        if self.direction == 2: #низ
            self.y += self.speed
        if self.direction == 3: #право
            self.x += self.speed
        if self.direction == 4: #верх
            self.y -= self.speed
        if self.direction == 12: #левониз
            self.x -= self.speed
            self.y += self.speed
        if self.direction == 32: #правониз
            self.x += self.speed
            self.y += self.speed
        if self.direction == 14: #левоверх
            self.x -= self.speed
            self.y -= self.speed
        if self.direction == 34: #правоверх
            self.x += self.speed
            self.y -= self.speed

        return True

class Cursor:
    def __init__(self):
        self.image = pygame.image.load("gfx/cursor.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.world_x = 0
        self.world_y = 0

    def update(self, camera_x, camera_y):
        """Обновление положения курсора"""
        # Получаем экранные координаты мыши
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Позиция курсора в игровом мире
        self.world_x = mouse_x + camera_x
        self.world_y = mouse_y + camera_y

        # Устанавливаем экранные координаты курсора для отрисовки
        self.rect.center = (mouse_x, mouse_y)

        # Отладка
        #print(f"Cursor screen: ({mouse_x}, {mouse_y}), world: ({self.world_x}, {self.world_y})")

    def draw(self, surface):
        """Отрисовка курсора"""
        surface.blit(self.image, self.rect)


class Inventory:
    def __init__(self, x, y, cell_size, capacity):
        self.x = x
        self.y = y
        self.cell_size = cell_size
        self.capacity = capacity
        self.items = [None] * capacity  # Пустые ячейки
        self.selected_index = None  # Выбранная ячейка
        self.mouse_offset = (0, 0)  # Смещение для отображения перетаскиваемого предмета
        self.selected_item = None  # Перетаскиваемый предмет

    def handle_key_press(self, key):
        """Обрабатывает нажатие клавиши для выбора ячейки."""
        if pygame.K_1 <= key <= pygame.K_9:  # Клавиши от 1 до 9
            index = key - pygame.K_1  # Преобразуем клавишу в индекс (0-8)
            if index < self.capacity:
                self.selected_index = index  # Устанавливаем выбранный индекс
                self.selected_item = self.items[index] if self.items[index] else None  # Обновляем выбранный предмет

                if self.selected_item:
                    print(f"Выбрана ячейка {index}, предмет: {self.selected_item}")
                else:
                    print(f"Выбрана ячейка {index}, но она пуста.")
            else:
                print(f"Индекс {index} выходит за пределы вместимости инвентаря!")
        else:
            print(f"Нажата неподдерживаемая клавиша: {key}")


    def render(self, screen):
        """Отрисовывает инвентарь на экране."""
        for index in range(self.capacity):
            x = self.x + 60 * index
            y = self.y
            color = (200, 200, 200)  # Обычная рамка

            if index == self.selected_index:
                color = (255, 255, 0)  # Подсветка выделенной ячейки

            pygame.draw.rect(screen, color, (x, y, self.cell_size, self.cell_size), 2)

            if self.items[index]:
                icon = self.get_item_icon(self.items[index])
                if icon:
                    screen.blit(icon, (x + 5, y + 5))

        # Если есть перетаскиваемый предмет, отрисовываем его на курсоре
        if self.selected_item:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            icon = self.get_item_icon(self.selected_item)
            if icon:
                screen.blit(icon, (mouse_x + self.mouse_offset[0], mouse_y + self.mouse_offset[1]))

    def handle_click(self, mouse_x, mouse_y, dragging_item=None):
        """Обрабатывает взаимодействие с ячейками инвентаря."""
        for index in range(self.capacity):
            x = self.x + index * (self.cell_size + 10)
            y = self.y
            cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)

            if cell_rect.collidepoint(mouse_x, mouse_y):
                if dragging_item:
                    # Перемещаем предмет в выбранную ячейку
                    if self.items[index] is None:
                        self.items[index] = dragging_item
                        dragging_item = None
                    else:
                        self.items[index], dragging_item = dragging_item, self.items[index]
                    return True, dragging_item
                else:
                    # Забираем предмет из ячейки
                    if self.items[index]:
                        dragging_item = self.items[index]
                        self.items[index] = None
                        return True, dragging_item
        return False, dragging_item
    
    def add_item(self, item_type):
        """Добавляет предмет в первую пустую ячейку инвентаря."""
        for index in range(self.capacity):
            if self.items[index] is None:  # Если ячейка пустая
                self.items[index] = item_type
                print(f"Предмет {item_type} добавлен в инвентарь, ячейка {index}.")
                return True
        print("Инвентарь полон!")
        return False

    def remove_selected_item(self):
        """Удаляет выбранный предмет из инвентаря."""
        if self.selected_index is not None:
            self.items[self.selected_index] = None
            print(f"Предмет из ячейки {self.selected_index} удален.")

    def get_selected_item(self):
        """Возвращает предмет из выбранной ячейки."""
        if self.selected_index is not None and self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None

    def get_item_icon(self, item_type):
        """Заглушка для получения иконки предмета."""
        if item_type == "brown_mountain_block":
            return pygame.image.load("gfx/mount.png").convert_alpha()
        elif item_type == "pickaxe":
            return pygame.image.load("gfx/pickaxe.png").convert_alpha()
        return None
    
    
class DroppedItem:
    def __init__(self, x, y, item_type):
        self.x = x
        self.y = y
        self.item_type = item_type
        self.rect = pygame.Rect(x, y, 16, 16)  # Маленький размер для иконки

    def draw(self, screen, camera_x, camera_y):
        """Отрисовка иконки предмета."""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        pygame.draw.rect(screen, (200, 100, 50), (screen_x, screen_y, 16, 16))  # Оранжевый цвет иконки


class CraftingTable:
    def __init__(self, x, y, cell_size):
        self.x = x  # Позиция верстака по оси X
        self.y = y  # Позиция верстака по оси Y
        self.cell_size = cell_size  # Размер ячеек
        self.items = [None] * 10  # 10 ячеек для крафта, изначально пустые
        self.selected_item = None  # Выбранный предмет, изначально None
        self.selected_index = None  # Индекс выбранной ячейки

    def handle_click(self, mouse_x, mouse_y, dragging_item=None):
        """Обрабатывает взаимодействие с ячейками верстака."""
        for index in range(10):  # У верстака теперь 10 ячеек
            col = index % 3
            row = index // 3
            x = self.x + (self.cell_size + 10) * col
            y = self.y + (self.cell_size + 10) * row
            cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)

            if cell_rect.collidepoint(mouse_x, mouse_y):  # Проверяем попадание мыши
                if dragging_item:  # Если перетаскиваемый предмет есть
                    if self.items[index] is None:  # Если ячейка пустая
                        self.items[index] = dragging_item
                        dragging_item = None
                    else:  # Меняем местами предметы
                        self.items[index], dragging_item = dragging_item, self.items[index]
                    return True, dragging_item
                else:  # Если предмет не перетаскивается, выбираем предмет из ячейки
                    if self.items[index]:
                        dragging_item = self.items[index]
                        self.items[index] = None
                        return True, dragging_item
        return False, dragging_item

    def add_item(self, item):
        """Добавляет предмет в первую пустую ячейку верстака."""
        for index in range(len(self.items)):
            if self.items[index] is None:  # Если ячейка пустая
                self.items[index] = item
                print(f"Добавлен предмет {item} в ячейку верстака {index}.")
                return
        print("Верстак полон!")

    def remove_selected_item(self):
        """Удаляет выбранный предмет из верстака."""
        if self.selected_item in self.items:
            index = self.items.index(self.selected_item)
            self.items[index] = None
            print(f"Предмет {self.selected_item} удален из верстака.")
            self.selected_item = None

    def render(self, screen, get_icon):
        """Отрисовка верстака на экране."""
        for index in range(10):  # У верстака теперь 10 ячеек
            col = index % 3
            row = index // 3
            x = self.x + (self.cell_size + 10) * col
            y = self.y + (self.cell_size + 10) * row
            pygame.draw.rect(screen, (200, 200, 200), (x, y, self.cell_size, self.cell_size), 2)  # Рамка ячейки

            # Если в ячейке есть предмет, отрисовываем его иконку
            if self.items[index]:
                icon = get_icon(self.items[index])
                if icon:
                    screen.blit(icon, (x + 5, y + 5))  # С отступом, чтобы иконка смотрелась лучше

    def get_item_icon(self, item_type):
        """Получает иконку предмета по его типу."""
        if item_type == "brown_mountain_block":
            return pygame.image.load("gfx/brick.png").convert_alpha()
        elif item_type == "pickaxe":
            return pygame.image.load("gfx/pickaxe.png").convert_alpha()
        return None

    def can_craft(self):
        """Проверяет возможность крафта (форма T)."""
        t_pattern = [1, 4, 7, 3, 5]  # Индексы для формы T
        required_items = [self.items[i] for i in t_pattern]  # Предметы в позиции T
        print(f"Проверяем предметы в позиции T: {required_items}")  # Отладочная информация

        is_t_shape = all(item == "brown_mountain_block" for item in required_items)  # Проверяем, что все нужные блоки

        if is_t_shape:
            print("Форма T собрана, можно крафтить!")
            return True
        else:
            print("Форма T не собрана.")
            print(f"Текущие предметы: {self.items}")
            return False

    def craft(self):
        """Создает предмет на основе расположения в верстаке."""
        if self.can_craft():
            # Удаляем использованные предметы
            for i in [1, 4, 7, 3, 5]:
                self.items[i] = None
            print("Крафт завершен! Пиксaxe появляется в 10-й ячейке.")
            self.items[9] = "pickaxe"  # В 10-й ячейке появляется pickaxe
            return "pickaxe"  # Возвращаем созданный предмет
        return None

