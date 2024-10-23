import pygame, sys
from pygame.locals import *
import random, time
import numpy
from entities import Hero, EnemyMelee, EnemyArcher

class Gameplay:

    def __init__ (self):
        self.FPS = 60
        self.FramePerSec = pygame.time.Clock()

        # Настройки экрана
        self.SCREEN_WIDTH = 1280
        self.SCREEN_HEIGHT = 720
        self.displaysurf = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        
        # Цвета
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 128, 0)
        self.RED = (128, 0, 0)
        self.ORANGE = (255, 128, 0)

        #расчёт тайлов
        self.tilesX = int(self.SCREEN_WIDTH / 16)
        self.tilesY = int(self.SCREEN_HEIGHT / 16)
        self.brick = pygame.image.load("gfx/brick.png").convert()

    def quitGame (self):

        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            print(f"Key {pygame.key.name(event.key)} pressed")

            if event.key == pygame.K_q:
                if event.mod & pygame.KMOD_CTRL:      
                    pygame.quit()
                    sys.exit()

        elif event.type == pygame.KEYUP:
            print(f"Key {pygame.key.name(event.key)} released")

    def moveCharacter (self):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                hero.y -= hero.speed

            if event.key == pygame.K_DOWN:
                hero.y += hero.speed

            if event.key == pygame.K_LEFT:
                hero.x -= hero.speed

            if event.key == pygame.K_RIGHT:
                hero.x += hero.speed

    def tileBackground(self, texture) -> None:
    
        for x in range(self.tilesX):
            for y in range(self.tilesY):
                self.displaysurf.blit(texture, (x * 16, y * 16))

    
    def renderHero(self, color):
        pygame.draw.rect(self.displaysurf, color, pygame.Rect(hero.x, hero.y, 32, 32))

    def renderEnemy(self, color, name):
        pygame.draw.rect(self.displaysurf, color, pygame.Rect(name.x, name.y, 32, 32))

    def renderBullet(self, color, name):
        pygame.draw.rect(self.displaysurf, color, pygame.Rect(name.x, name.y, 8, 8))


if __name__ == '__main__':

    pygame.init()
    pygame.font.init()
    pygame.display.set_caption("Dungeon Sandbox")

    # Создание главного героя
    hero = Hero(hp=100, power=20, x=0, y=0, speed=32, protect=5)

    # Создание врага
    enemy_melee_1 = EnemyMelee(hp=100, power=20, x=256, y=256, speed=4, protect=5)
    enemy_melee_2 = EnemyMelee(hp=100, power=20, x=512, y=512, speed=8, protect=5)
    archer_1 = EnemyArcher (hp=100, power=20, x=400, y=400, speed=8, protect=5)
    archer_2 = EnemyArcher (hp=100, power=20, x=800, y=400, speed=8, protect=5)

    dungeon = Gameplay ()
    pygame.display.set_icon(pygame.transform.scale (pygame.image.load('gfx/brick.png'), (32,32)))

    while True:

            for event in pygame.event.get():
                    dungeon.tileBackground (dungeon.brick)
                    #dungeon.displaysurf.fill(dungeon.WHITE)
                    dungeon.moveCharacter ()
                    enemy_melee_1.move_towards_player (hero)
                    enemy_melee_2.move_towards_player (hero)
                    archer_1.update ()
                    archer_1.bullet.update (dungeon, hero)
                    archer_2.update ()
                    archer_2.bullet.update (dungeon, hero)
                    dungeon.quitGame ()
                    dungeon.renderHero (dungeon.GREEN)
                    dungeon.renderEnemy (dungeon.RED, enemy_melee_1)
                    dungeon.renderEnemy (dungeon.RED, enemy_melee_2)
                    dungeon.renderEnemy (dungeon.ORANGE, archer_1)
                    dungeon.renderEnemy (dungeon.ORANGE, archer_2)
                    dungeon.renderBullet (dungeon.WHITE, archer_1.bullet)
                    dungeon.renderBullet (dungeon.WHITE, archer_2.bullet)
                    pygame.display.flip()
                    dungeon.FramePerSec.tick(dungeon.FPS)
