import math
import pygame, sys
from pygame.locals import *

class Entity:
    def __init__(self, hp, power, x, y, speed) -> None:
        self.hp = hp
        self.power = power
        self.speed = speed
        self.x = x
        self.y = y

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.die()

    def die(self):
        print(f"{self.__class__.__name__} погиб")


class Hero(Entity):
    def __init__(self, hp, power, x, y, speed, protect) -> None:
        super().__init__(hp, power, x, y, speed)
        self.protect = protect
  

    def attack(self, target):
        damage = self.power - target.protect
        if damage > 0:
            target.take_damage(damage)
        else:
            print(f"{target.__class__.__name__} заблокировал атаку!")
            if self.hp == 0:
                print('Стоп')


class EnemyMelee(Entity):
    def __init__(self, hp, power, x, y, speed, protect) -> None:
        super().__init__(hp, power, x, y, speed)
        self.protect = protect

    def move_towards_player(self, hero):

        dx, dy = hero.x - self.x, hero.y - self.y
        dist = math.hypot(dx, dy)
        dx, dy = dx / dist, dy / dist 
        self.x += dx * self.speed
        self.y += dy * self.speed

class EnemyArcher(Entity):
    def __init__(self, hp, power, x, y, speed, protect) -> None:
        super().__init__(hp, power, x, y, speed)
        self.protect = protect
        self.shoot_delay = 1000 
        self.last_shot = pygame.time.get_ticks() 
        self.bullet = Bullet(self.x, self.y, math.radians(90))

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.shoot()
            self.last_shot = now    

    def shoot(self):
        print ('archer shot')
        self.bullet = Bullet(self.x, self.y, math.radians(90))

class Bullet():
    def __init__(self, x, y, direction):
        super().__init__()
        self.x = x
        self.y = y
        self.speed = 8
        self.direction = direction
        print ('bullet initialized')

    def update(self, dungeon, hero):
        print ('bullet is at ', self.x, ' ', self.y)
        dx, dy = hero.x - self.x, hero.y - self.y
        dist = math.hypot(dx, dy)
        dx, dy = dx / dist, dy / dist 
        self.x += dx * self.speed
        self.y += dy * self.speed

        if self.x < 0 or self.x > dungeon.SCREEN_WIDTH or self.y < 0 or self.y > dungeon.SCREEN_HEIGHT:
            self.kill()




