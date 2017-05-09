__all__ = ['USE_PG']

try:
    import pygame
    USE_PG = True
except:
    USE_PG = False
