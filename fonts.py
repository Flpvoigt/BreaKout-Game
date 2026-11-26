"""Fontes compartilhadas entre entities.py e ui.py. So pode ser importado
depois de pygame.init() (feito em game.py antes de importar este modulo)."""
import pygame

font = pygame.font.SysFont("consolas", 28)
big_font = pygame.font.SysFont("consolas", 48, bold=True)
powerup_font = pygame.font.SysFont("consolas", 20, bold=True)
score_font = pygame.font.SysFont("consolas", 34, bold=True)
status_font = pygame.font.SysFont("consolas", 20, bold=True)
title_font = pygame.font.SysFont("consolas", 76, bold=True)
menu_font = pygame.font.SysFont("consolas", 24)
menu_hint_font = pygame.font.SysFont("consolas", 26, bold=True)
tag_font = pygame.font.SysFont("consolas", 12, bold=True)
