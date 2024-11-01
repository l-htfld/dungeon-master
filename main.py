import pygame, sys
from pygame.locals import *
import random
from entities import Hero, EnemyMelee, EnemyArcher
from graphics import Landscape

class Gameplay:
    def __init__(self):
        self.FPS = 24
        self.FramePerSec = pygame.time.Clock()

        # Настройки экрана 123
        self.SCREEN_WIDTH = 1280
        self.SCREEN_HEIGHT = 720
        self.displaysurf = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        
        # Цвета
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 128, 0)
        self.RED = (128, 0, 0)
        self.ORANGE = (255, 128, 0)

        # Расчёт тайлов
        self.tilesX = int(self.SCREEN_WIDTH / 16)
        self.tilesY = int(self.SCREEN_HEIGHT / 16)
        self.brick = pygame.image.load("gfx/brick.png").convert()

        # Позиция камеры
        self.camera_x = 0
        self.camera_y = 0

        # Список врагов
        self.enemies = []

    def quitGame(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    if event.mod & pygame.KMOD_CTRL:      
                        pygame.quit()
                        sys.exit()

    def spawn_enemy(self, enemy_type, landscape):
        x = random.randint(0, self.SCREEN_WIDTH)
        y = random.randint(0, self.SCREEN_HEIGHT)
        
        # Проверка на пересечение с каждым сегментом горных массивов
        if not any(pygame.Rect(x, y, 32, 32).colliderect(segment) 
                for cluster in landscape.mountains for segment in cluster):
            if enemy_type == "archer":
                self.enemies.append(EnemyArcher(hp=100, power=20, x=x, y=y, speed=4, protect=5, fov_radius=200))
            elif enemy_type == "melee":
                self.enemies.append(EnemyMelee(hp=100, power=20, x=x, y=y, speed=4, protect=5, fov_radius=200))

    def moveCharacter(self, hero, landscape):
        keys = pygame.key.get_pressed()
        hero_rect = pygame.Rect(hero.x, hero.y, 32, 32)
        old_x, old_y = hero.x, hero.y

        if keys[pygame.K_UP]:
            new_rect = hero_rect.move(0, -hero.speed)
            if not any(new_rect.colliderect(segment) for cluster in landscape.mountains for segment in cluster):
                hero.y -= hero.speed

        if keys[pygame.K_DOWN]:
            new_rect = hero_rect.move(0, hero.speed)
            if not any(new_rect.colliderect(segment) for cluster in landscape.mountains for segment in cluster):
                hero.y += hero.speed

        if keys[pygame.K_LEFT]:
            new_rect = hero_rect.move(-hero.speed, 0)
            if not any(new_rect.colliderect(segment) for cluster in landscape.mountains for segment in cluster):
                hero.x -= hero.speed

        if keys[pygame.K_RIGHT]:
            new_rect = hero_rect.move(hero.speed, 0)
            if not any(new_rect.colliderect(segment) for cluster in landscape.mountains for segment in cluster):
                hero.x += hero.speed

        # Обновляем позицию камеры
        self.camera_x = hero.x - self.SCREEN_WIDTH // 2
        self.camera_y = hero.y - self.SCREEN_HEIGHT // 2
        self.camera_x = max(0, self.camera_x)  # Ограничиваем камеру по x
        self.camera_y = max(0, self.camera_y)  # Ограничиваем камеру по y

    def tileBackground(self, texture) -> None:
        for x in range(self.tilesX):
            for y in range(self.tilesY):
                self.displaysurf.blit(texture, (x * 16, y * 16))

    def renderHero(self, color, hero):
        pygame.draw.rect(self.displaysurf, color, pygame.Rect(hero.x - self.camera_x, hero.y - self.camera_y, 32, 32))

    def renderEnemy(self, color, enemy):
        pygame.draw.rect(self.displaysurf, color, pygame.Rect(enemy.x - self.camera_x, enemy.y - self.camera_y, 32, 32))

    def renderBullet(self, color, bullet):
        pygame.draw.rect(self.displaysurf, color, pygame.Rect(bullet.x - self.camera_x, bullet.y - self.camera_y, 8, 8))

if __name__ == '__main__':
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption("Dungeon Sandbox")

    # Создание главного героя
    hero = Hero(hp=100, power=20, x=640, y=360, speed=8, protect=5)  # Начальная позиция героя в центре

    # Создание ландшафта
    landscape = Landscape(2000, 2000)  # Увеличиваем размеры ландшафта
    landscape.generate_mountains(random.randint(10, 150))  # Генерация от 10 до 150 гор

    dungeon = Gameplay()

    # Спавним случайное количество врагов
    for _ in range(random.randint(5, 25)):  # Генерация от 5 до 15 врагов
        if random.choice(["melee", "archer"]) == "melee":
            dungeon.spawn_enemy("melee", landscape)
        else:
            dungeon.spawn_enemy("archer", landscape)

    pygame.display.set_icon(pygame.transform.scale(pygame.image.load('gfx/brick.png'), (32,32)))

    clock = pygame.time.Clock()

    running = True
    while running:
        # Обработка событий
        dungeon.quitGame()

        # Отрисовка фона
        dungeon.tileBackground(dungeon.brick)
        
        # Обновление позиции героя
        dungeon.moveCharacter(hero, landscape)

        # Обновление врагов
        for enemy in dungeon.enemies:
            enemy.update(hero, landscape)  # Передаём героя

            # Обновление и отрисовка пуль, с проверкой таймера на уничтожение
            if isinstance(enemy, EnemyArcher) and enemy.bullet and enemy.bullet.update(dungeon, hero):
                dungeon.renderBullet(dungeon.WHITE, enemy.bullet)
            else:
                enemy.bullet = None  # Удаляем пулю, если она "умерла"

        # Отрисовка ландшафта с учетом камеры
        landscape.draw(dungeon.displaysurf, dungeon.camera_x, dungeon.camera_y)

        # Отрисовка всех объектов на экране
        dungeon.renderHero(dungeon.GREEN, hero)
        for enemy in dungeon.enemies:
            if isinstance(enemy, EnemyMelee):
                dungeon.renderEnemy(dungeon.RED, enemy)
            elif isinstance(enemy, EnemyArcher):
                dungeon.renderEnemy(dungeon.ORANGE, enemy)

        # Обновление экрана
        pygame.display.flip()

        # Ограничение FPS
        clock.tick(dungeon.FPS)

    pygame.quit()