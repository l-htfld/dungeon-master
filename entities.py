import math
import pygame, sys
from pygame.locals import *
import numpy as np
import random

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
        self.speed = 24

    def attack(self, target):
        damage = self.power - target.protect
        if damage > 0:
            target.take_damage(damage)
        else:
            print(f"{target.__class__.__name__} заблокировал атаку!")
            if self.hp == 0:
                print('Стоп')
                
                
                
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
    def __init__(self, hp, power, x, y, speed, protect, fov_radius):
        super().__init__(hp, power, x, y, speed)
        self.protect = protect
        self.fov_radius = fov_radius
        self.is_moving = False
        self.neural_net = SimpleNeuralNet()
        self.direction = np.array([random.choice([-1, 1]), random.choice([-1, 1])])  # Начальное направление
        self.step_counter = 0
        self.change_direction_interval = 20  # Сколько шагов идти в одном направлении
        self.move_delay = 20  # Задержка между движениями (количество кадров)
        self.move_timer = 0  # Таймер для отслеживания времени движения

    def update(self, hero, landscape):
        dx, dy = hero.x - self.x, hero.y - self.y
        distance_to_hero = math.hypot(dx, dy)

        inputs = np.array([self.x, self.y, hero.x, hero.y])

        if distance_to_hero <= self.fov_radius:
            # Если герой в поле зрения, враг начинает двигаться к нему
            self.is_moving = True
            dx, dy = dx / distance_to_hero, dy / distance_to_hero
            new_x = self.x + dx * self.speed
            new_y = self.y + dy * self.speed
        else:
            self.is_moving = False
            
            # Используем нейронку для получения движения
            move_decision = self.neural_net.forward(inputs)

            # Плавное случайное движение
            if self.step_counter < self.change_direction_interval:
                # Проверяем, пришло ли время движения
                if self.move_timer <= 0:
                    new_x = self.x + self.direction[0] * self.speed * 0.5  # Уменьшаем скорость
                    new_y = self.y + self.direction[1] * self.speed * 0.5  # Уменьшаем скорость
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

        new_rect = pygame.Rect(new_x, new_y, 32, 32)
        if not any(new_rect.colliderect(segment) for cluster in landscape.mountains for segment in cluster):
            self.x, self.y = new_x, new_y
        else:
            # Если есть препятствие, меняем направление
            self.direction = np.array([random.choice([-1, 1]), random.choice([-1, 1])])
    
    def draw(self, screen):
        pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), 20)

class EnemyArcher(Entity):
    def __init__(self, hp, power, x, y, speed, protect, fov_radius) -> None:
        super().__init__(hp, power, x, y, speed)
        self.protect = protect
        self.fov_radius = fov_radius  # Поле зрения лучника
        self.shoot_delay = 1000 
        self.last_shot = pygame.time.get_ticks() 
        self.bullet = None  # Изначально пуля отсутствует

    def update(self, hero, landscape):  # Добавляем landscape как аргумент
        # Вычисляем расстояние до героя
        dx, dy = hero.x - self.x, hero.y - self.y
        distance_to_hero = math.hypot(dx, dy)

        # Если герой в пределах поля зрения, пытаемся стрелять
        if distance_to_hero <= self.fov_radius:
            now = pygame.time.get_ticks()
            if now - self.last_shot > self.shoot_delay:
                self.shoot()
                self.last_shot = now

    def shoot(self):
        print('archer shot')
        self.bullet = Bullet(self.x, self.y, math.radians(90))  # Создаём новую пулю

    def draw(self, screen):
        # Отрисовка лучника
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




