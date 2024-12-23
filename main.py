import pygame, sys
from pygame.locals import *
import random
from entities import Hero, EnemyMelee, EnemyArcher, Cursor, Inventory, CraftingTable
from graphics import Landscape, DarkBiome, Flashlight, DarkGrayMountains
from menu import StartMenu
import math


class Gameplay:
    def __init__(self, map_width, map_height):
        self.FPS = 24
        self.FramePerSec = pygame.time.Clock()

        # Настройки экрана
        self.SCREEN_WIDTH = 1280
        self.SCREEN_HEIGHT = 720
        self.map_width = map_width  # Ширина карты
        self.map_height = map_height  # Высота карты
        self.displaysurf = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))

        # Цвета
        self.WHITE = (255, 255, 255)
        self.YELLOW = (255, 255, 0)
        self.GREEN = (0, 128, 0)
        self.RED = (128, 0, 0)
        self.ORANGE = (255, 128, 0)
        self.BLACK = (0, 0, 0)
        self.L_GREEN = (0, 255, 0)
        self.L_BLUE = (0, 0, 255)
        self.CYAN = (0, 255, 255)
        self.SHADOW = (64, 64, 64)

        #звуки
        self.scroll_sound = pygame.mixer.Sound("sound/menusnd01.wav")
        self.select_sound = pygame.mixer.Sound("sound/menusnd02.wav")
        self.die_sound = pygame.mixer.Sound("sound/boom-shipdie.wav")
        self.shoot_sound = pygame.mixer.Sound("sound/spathi-bullet.wav")
        self.impact_sound = pygame.mixer.Sound("sound/boom-tiny.wav")
        self.player_die_sound = pygame.mixer.Sound("sound/druuge-furnace.wav")
        self.footsteps_sound = pygame.mixer.Sound("sound/minecraft-footsteps.mp3")

        # Расчёт тайлов
        self.tilesX = int(self.SCREEN_WIDTH / 16)
        self.tilesY = int(self.SCREEN_HEIGHT / 16)
        self.brick = pygame.image.load("gfx/brick.png").convert()

        # Позиция камеры
        self.camera_x = 0
        self.camera_y = 0

        # Темный биом
        self.dark_biome = DarkBiome(7000, 7000, map_width, map_height)

        # Фонарь
        self.flashlight = Flashlight(hero)
        
        self.cursor = Cursor()
        
        # Список выпавших предметов
        self.dropped_items = []

        # Список врагов
        self.enemies = []
        
        # Для хранения блоков, которые нужно разрушить
        self.blocks_to_break = []
        
        self.inventory = Inventory(x=50, y=650, cell_size=50, capacity=7)
        self.hero_has_pistol = 1        

    # Рисуем инвентарь
    def draw_inventory(self):
        self.inventory.render(self.displaysurf)

    def quitGame(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and event.mod & pygame.KMOD_CTRL:
                    pygame.quit()
                    sys.exit()

    def spawn_enemy(self, enemy_type, landscape):
        while True:
            # Случайные координаты на карте
            x = random.randint(0, self.map_width)
            y = random.randint(0, self.map_height)

            # Проверка на пересечение с горными массивами
            if not any(
                pygame.Rect(x, y, 32, 32).colliderect(segment)
                for cluster in landscape.mountains for segment in cluster
            ):
                # Проверяем, чтобы враг не спавнился в зоне видимости камеры
                if not (self.camera_x <= x <= self.camera_x + self.SCREEN_WIDTH and
                        self.camera_y <= y <= self.camera_y + self.SCREEN_HEIGHT):
                    if enemy_type == "archer":
                        self.enemies.append(EnemyArcher(hp=100, power=20, x=x, y=y, speed=4, protect=5, fov_radius=200, active=1))
                    elif enemy_type == "melee":
                        self.enemies.append(EnemyMelee(hp=100, power=20, x=x, y=y, speed=4, protect=5, fov_radius=200, active=1))
                    break

    def handleHeroCollisionForEnemies(self, enemies, hero):
        """Обрабатывает столкновение врагов с героем."""
        hero_rect = pygame.Rect(hero.x, hero.y, 32, 32)
        for enemy in enemies:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, 32, 32)
            if hero_rect.colliderect(enemy_rect):
                if enemy_rect.right > hero_rect.left and enemy_rect.left < hero_rect.right:
                    if enemy_rect.bottom > hero_rect.top:
                        enemy.y = hero_rect.top - enemy_rect.height
                    elif enemy_rect.top < hero_rect.bottom:
                        enemy.y = hero_rect.bottom
                elif enemy_rect.bottom > hero_rect.top and enemy_rect.top < hero_rect.bottom:
                    if enemy_rect.right > hero_rect.left:
                        enemy.x = hero_rect.left - enemy_rect.width
                    elif enemy_rect.left < hero_rect.right:
                        enemy.x = hero_rect.right
                        
    def handle_attack(self, hero):
        """Обрабатывает атаку героя по врагам."""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_x = mouse_x + self.camera_x
        world_y = mouse_y + self.camera_y

        for enemy in self.enemies:
            if enemy.is_alive:
                # Проверяем расстояние до врага
                distance = math.hypot(enemy.x - hero.x, enemy.y - hero.y)
                if distance <= 50:  # Ближний бой, враг в радиусе 50 пикселей
                    # Проверяем, попадает ли клик в хитбокс врага
                    if pygame.Rect(enemy.x - 16, enemy.y - 16, 32, 32).collidepoint(world_x, world_y):
                        print("Удар по врагу!")
                        enemy.take_damage()
                        enemy.knockback(hero)
                        if not enemy.is_alive:
                            print("Враг уничтожен!")
                            self.enemies.remove(enemy)
                        return
        print("Нет врага для атаки!")
                    
    def moveCharacter(self, hero, *landscapes):
        keys = pygame.key.get_pressed()
        hero_rect = pygame.Rect(hero.x, hero.y, 32, 32)

        all_segments = []
        for landscape in landscapes:
            if hasattr(landscape, 'mountains'):
                for cluster in landscape.mountains:
                    all_segments.extend(cluster)
            elif hasattr(dark_gray_mountains, 'features'):
                for feature in dark_gray_mountains.features:
                    all_segments.extend(feature)

        enemy_rects = [pygame.Rect(enemy.x, enemy.y, 32, 32) for enemy in self.enemies]
        obstacles = all_segments + enemy_rects 

        def move_enemy(enemy, dx, dy):
            enemy_rect = pygame.Rect(enemy.x, enemy.y, 32, 32)
            new_enemy_rect = enemy_rect.move(dx, dy)
            if not any(new_enemy_rect.colliderect(obstacle) for obstacle in all_segments) and not new_enemy_rect.colliderect(hero_rect):
                enemy.x += dx
                enemy.y += dy
                return True
            return False

        # Movement logic
        if keys[pygame.K_w]:
            new_rect = hero_rect.move(0, -hero.speed)
            collision_segments = [obstacle for obstacle in obstacles if new_rect.colliderect(obstacle)]
            if not collision_segments:
                hero.y -= hero.speed
            else:
                nearest_segment = min(collision_segments, key=lambda s: abs(hero_rect.top - s.bottom))
                if nearest_segment in enemy_rects:
                    enemy_index = enemy_rects.index(nearest_segment)
                    if move_enemy(self.enemies[enemy_index], 0, -hero.speed):
                        hero.y -= hero.speed
                else:
                    hero.y = nearest_segment.bottom

        if keys[pygame.K_s]:
            new_rect = hero_rect.move(0, hero.speed)
            collision_segments = [obstacle for obstacle in obstacles if new_rect.colliderect(obstacle)]
            if not collision_segments:
                hero.y += hero.speed
            else:
                nearest_segment = min(collision_segments, key=lambda s: abs(hero_rect.bottom - s.top))
                if nearest_segment in enemy_rects:
                    enemy_index = enemy_rects.index(nearest_segment)
                    if move_enemy(self.enemies[enemy_index], 0, hero.speed):
                        hero.y += hero.speed
                else:
                    hero.y = nearest_segment.top - hero_rect.height

        if keys[pygame.K_a]:
            new_rect = hero_rect.move(-hero.speed, 0)
            collision_segments = [obstacle for obstacle in obstacles if new_rect.colliderect(obstacle)]
            if not collision_segments:
                hero.x -= hero.speed
            else:
                nearest_segment = min(collision_segments, key=lambda s: abs(hero_rect.left - s.right))
                if nearest_segment in enemy_rects:
                    enemy_index = enemy_rects.index(nearest_segment)
                    if move_enemy(self.enemies[enemy_index], -hero.speed, 0):
                        hero.x -= hero.speed
                else:
                    hero.x = nearest_segment.right

        if keys[pygame.K_d]:
            new_rect = hero_rect.move(hero.speed, 0)
            collision_segments = [obstacle for obstacle in obstacles if new_rect.colliderect(obstacle)]
            if not collision_segments:
                hero.x += hero.speed
            else:
                nearest_segment = min(collision_segments, key=lambda s: abs(hero_rect.right - s.left))
                if nearest_segment in enemy_rects:
                    enemy_index = enemy_rects.index(nearest_segment)
                    if move_enemy(self.enemies[enemy_index], hero.speed, 0):
                        hero.x += hero.speed
                else:
                    hero.x = nearest_segment.left - hero_rect.width

        # Update camera position
        self.camera_x = max(0, hero.x - self.SCREEN_WIDTH // 2)
        self.camera_y = max(0, hero.y - self.SCREEN_HEIGHT // 2)

        if keys[pygame.K_i]:
            print (dungeon.inventory.items)

        
    def renderCursor(self):
        self.cursor.draw(self.displaysurf, self.camera_x, self.camera_y)

    def tileBackground(self, texture):
        for x in range(self.tilesX):
            for y in range(self.tilesY):
                self.displaysurf.blit(texture, (x * 16, y * 16))
                
    def renderBullet(self, color, bullet):
        """Отрисовка пули на экране."""
        pygame.draw.rect(
            self.displaysurf,
            color,
            pygame.Rect(
                bullet.x - self.camera_x,
                bullet.y - self.camera_y,
                8,  # Ширина пули
                8,  # Высота пули
            ),
        )

    def playerShoot (self, hero):

        if self.hero_has_pistol == 1:

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.shoot_sound.play ()
                    hero.shoot (1)
                if event.key == pygame.K_UP:
                    self.shoot_sound.play ()
                    hero.shoot (4)
                if event.key == pygame.K_RIGHT:
                    self.shoot_sound.play ()
                    hero.shoot (3)
                if event.key == pygame.K_DOWN:
                    self.shoot_sound.play ()
                    hero.shoot (2)

    def renderHero(self, color, hero):
        pygame.draw.rect(self.displaysurf, color, pygame.Rect(hero.x - self.camera_x, hero.y - self.camera_y, 32, 32))

    def renderEnemy(self, color, enemy):
        if enemy.active:
            pygame.draw.rect(self.displaysurf, color, pygame.Rect(enemy.x - self.camera_x, enemy.y - self.camera_y, 32, 32))
        if enemy.hp < 100:
            pygame.draw.rect(self.displaysurf, self.L_GREEN, pygame.Rect(enemy.x - self.camera_x, enemy.y - self.camera_y - 8, int(0.32 * enemy.hp), 5))

    def renderDarkBiome(self):
        self.dark_biome.draw(self.displaysurf, self.camera_x, self.camera_y, self.flashlight)

    def renderFlashlight(self):
        self.flashlight.draw(self.displaysurf, self.camera_x, self.camera_y)
        
    
    def handle_mouse_click(self, cursor, landscape, inventory):
        """Обработка клика мыши для разрушения гор."""
        world_x = cursor.world_x
        world_y = cursor.world_y

        # Получаем выбранный предмет
        selected_item = inventory.get_selected_item()
        print(f"Выбранный предмет: {selected_item}")  # Отладка: проверяем текущий выбранный предмет

        # Устанавливаем, можно ли ломать серые горы
        can_break_gray_mountain = selected_item == "pickaxe"

        # Перебираем все кластеры в ландшафте
        for cluster in landscape.mountains:
            for block in cluster:
                if block.collidepoint(world_x, world_y):  # Проверяем, попадает ли клик в блок
                    if hasattr(block, "type") and block.type == "gray_mountain":
                        if not can_break_gray_mountain:
                            print("Нужна кирка для разрушения серой горы!")
                            return  # Нельзя ломать серую гору без кирки
                        else:
                            print("Серая гора разрушена киркой!")

                    # Если это не серая гора, разрушаем блок
                    else:
                        print("Блок разрушен.")

                    # Удаляем блок из кластера
                    cluster.remove(block)
                    return

        # Если курсор не попал в блок
        print("Блок не найден под курсором.")
        
        
if __name__ == '__main__':
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption("Dungeon Sandbox")

    # Создание главного героя
    hero = Hero(hp=100, power=20, x=640, y=360, speed=8, protect=5, active=1)  # Начальная позиция героя в центре

    # Задаем размеры карты
    map_width = 10000  # Ширина карты
    map_height = 10000  # Высота карты

    # Создание темного биома
    dark_biome = DarkBiome(7000, 7000, map_width, map_height)  # Указываем координаты и размер темного биома

    # Создание ландшафта
    landscape = Landscape(map_width, map_height)  # Полный размер карты
    landscape.generate_mountains(random.randint(100, 170), dark_biome)  # Генерация от 100 до 170 гор
    
    dark_gray_mountains = DarkGrayMountains(width=10000, height=10000)
    dark_gray_mountains.generate_features(num_clusters=50, dark_biome=dark_biome)
    
    inventory = Inventory(x=50, y=650, cell_size=50, capacity=9)

    # Создание фонарика
    flashlight = Flashlight(hero)

    # Создание игрового процесса
    dungeon = Gameplay(map_width, map_height)
    
    # Добавляем верстак
    crafting_table = CraftingTable(x=400, y=200, cell_size=50)
    crafting_open = False

    # Спавним случайное количество врагов
    for _ in range(random.randint(100, 105)):  # Генерация от 5 до 25 врагов
        enemy_type = random.choice(["melee", "archer"])
        dungeon.spawn_enemy(enemy_type, landscape)

    # Устанавливаем иконку игры
    pygame.display.set_icon(pygame.transform.scale(pygame.image.load('gfx/brick.png'), (32, 32)))

    clock = pygame.time.Clock()

    running = True
    is_hero_attacking = False
    crafting_open = False  # Флаг для отображения верстака
    dragging_item = None  # Перетаскиваемый предмет

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # Обработка выбора ячейки
                if pygame.K_1 <= event.key <= pygame.K_9:
                    inventory.handle_key_press(event.key)  # Выбор ячейки

                # Открытие/закрытие верстака
                elif event.key == pygame.K_i:
                    crafting_open = not crafting_open  # Переключаем состояние верстака
                    print(f"Верстак открыт: {crafting_open}")

                # Крафт, если верстак открыт
                elif crafting_open and event.key == pygame.K_c:
                    crafted_item = crafting_table.craft()
                    if crafted_item:
                        inventory.add_item(crafted_item)  # Добавляем созданный предмет в инвентарь
                        print(f"Создан предмет: {crafted_item}, текущее состояние инвентаря: {inventory.items}")

            # Перетаскивание предметов
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Левая кнопка
                mouse_x, mouse_y = pygame.mouse.get_pos()

                if crafting_open:
                    if not dragging_item:
                        # Проверяем инвентарь
                        success, dragging_item = dungeon.inventory.handle_click(mouse_x, mouse_y)
                        # Если не из инвентаря, проверяем верстак
                        if not success:
                            _, dragging_item = crafting_table.handle_click(mouse_x, mouse_y)
                else:
                    # Выполняем действия в игровом мире
                    world_x = dungeon.cursor.world_x
                    world_y = dungeon.cursor.world_y

                    # Ближний бой
                    if hero.perform_melee_attack(dungeon.enemies, landscape):
                        print("Враг атакован!")
                    else:
                        # Проверка на разрушение блоков
                        selected_item = inventory.get_selected_item()
                        print(f"Выбранный предмет: {selected_item}")  # Отладка

                        if selected_item == "pickaxe":
                            # Ломание серых или коричневых гор киркой
                            if dark_gray_mountains.break_block(world_x, world_y):
                                print("Серая гора разрушена киркой!")
                            elif landscape.break_block(world_x, world_y, dungeon):
                                print("Коричневый блок разрушен киркой.")
                            else:
                                print("Блок не найден под курсором.")
                        else:
                            # Ломание только коричневых гор
                            if landscape.break_block(world_x, world_y, dungeon):
                                print("Блок разрушен!")
                            else:
                                print("Блок не найден под курсором.")

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:  # Отпускание
                mouse_x, mouse_y = pygame.mouse.get_pos()

                if crafting_open and dragging_item:
                    # Сначала пытаемся положить на верстак
                    success, dragging_item = crafting_table.handle_click(mouse_x, mouse_y, dragging_item)
                    if not success:
                        # Если не удалось, пробуем вернуть в инвентарь
                        _, dragging_item = dungeon.inventory.handle_click(mouse_x, mouse_y, dragging_item)


        

        # Обновление позиции героя
        dungeon.moveCharacter(hero, landscape, dark_gray_mountains)

        hero.update_rect()

        # Проверка, находится ли герой в темном биоме
        if dark_biome.is_hero_in_biome(hero):
            flashlight.is_on = True  # Включаем фонарик, если герой в темном биоме
        else:
            flashlight.is_on = False  # Иначе выключаем фонарик

        # Отрисовка интерфейса
        dungeon.tileBackground(dungeon.brick)

        # Отрисовка ландшафта с учетом камеры
        landscape.draw(dungeon.displaysurf, dungeon.camera_x, dungeon.camera_y, flashlight, dark_biome)
        dark_gray_mountains.draw(dungeon.displaysurf, dungeon.camera_x, dungeon.camera_y, flashlight, dark_biome)

        # Отрисовка темного биома с учетом смещения камеры
        dark_biome.draw(dungeon.displaysurf, dungeon.camera_x, dungeon.camera_y, flashlight)

        # Обновление и отрисовка курсора
        dungeon.cursor.update(dungeon.camera_x, dungeon.camera_y)  # Обновляем мировые координаты курсора
        dungeon.cursor.draw(dungeon.displaysurf)  # Отрисовываем курсор

        # Обновление врагов
        for enemy in dungeon.enemies:
            enemy.update(hero, landscape, hero_attacking=is_hero_attacking)  # Передаем героя врагу

            # Проверка столкновений врагов с героем
            dungeon.handleHeroCollisionForEnemies(dungeon.enemies, hero)

            # Обновление и отрисовка пуль, с проверкой таймера на уничтожение
            if isinstance(enemy, EnemyArcher) and enemy.bullet and enemy.bullet.update(dungeon, hero):
                dungeon.renderBullet(dungeon.WHITE, enemy.bullet)
            else:
                enemy.bullet = None  # Удаляем пулю, если она "умерла"

        # Отрисовка выпавших предметов
        for item in dungeon.dropped_items:
            item.draw(dungeon.displaysurf, dungeon.camera_x, dungeon.camera_y)

        # Проверяем сбор предметов
        for item in dungeon.dropped_items[:]:
            if hero.rect.colliderect(item.rect):
                print(f"Собран предмет: {item.item_type}")
                dungeon.inventory.add_item(item.item_type)
                dungeon.dropped_items.remove(item)

        # Отрисовка интерфейса
        if crafting_open:
            # Отрисовка верстака
            crafting_table.render(dungeon.displaysurf, dungeon.inventory.get_item_icon)
            # Отрисовка инвентаря (чтобы был виден весь интерфейс)
            dungeon.inventory.render(dungeon.displaysurf)
        else:
            # Отрисовка только инвентаря, если верстак закрыт
            dungeon.inventory.render(dungeon.displaysurf)

        # Отрисовка всех объектов на экране
        dungeon.renderHero(dungeon.GREEN, hero)
        if hero.bullet and hero.bullet.update():
            dungeon.renderBullet(dungeon.WHITE, hero.bullet)

        for enemy in dungeon.enemies:
            if isinstance(enemy, EnemyMelee):
                dungeon.renderEnemy(dungeon.RED, enemy)
            elif isinstance(enemy, EnemyArcher):
                dungeon.renderEnemy(dungeon.ORANGE, enemy)

        # Отрисовка фонарика
        flashlight.draw(dungeon.displaysurf, dungeon.camera_x, dungeon.camera_y)

        # Отрисовка
        inventory.render(dungeon.displaysurf)
        #inventory.items[0] = "pickaxe"
        
        # Обновление экрана
        pygame.display.flip()

        # Ограничение FPS
        clock.tick(dungeon.FPS)

    pygame.quit()

