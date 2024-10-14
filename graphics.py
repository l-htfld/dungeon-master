import pygame

def draw_entity(screen, entity, x, y):
    color = (0, 128, 0)  # цвет героя
    pygame.draw.rect(screen, color, pygame.Rect(x, y, 50, 50))  # рисуем героя как квадрат 50x50

