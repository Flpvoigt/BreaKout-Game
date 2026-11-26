"""Constantes puras do jogo: tamanhos, cores, tempos e tuning de todas as
mecanicas. Nao depende de pygame.init() nem de nenhum outro modulo do jogo."""

WIDTH, HEIGHT = 800, 600
FPS = 60

WHITE = (255, 255, 255)
BLACK = (10, 10, 15)
PADDLE_COLOR = (0, 220, 255)
BALL_COLOR = (255, 255, 255)
SCORE_COLOR = (255, 215, 0)

BRICK_COLORS = [
    (255, 80, 80),
    (255, 160, 60),
    (255, 230, 60),
    (120, 230, 90),
    (80, 160, 255),
]

# ---- Fisica da bola ----
# Impede a trajetoria quase vertical (sobe reto, bate no teto, desce reto na
# raquete, repete para sempre) - nada no jogo muda vx ao rebater em tijolo ou
# teto, entao sem isso ela pode ficar presa em loop infinito.
BALL_MIN_VX = 1.5

# ---- Power-up tuning ----
POWERUP_DROP_CHANCE = 0.15
POWERUP_FALL_SPEED = 3
POWERUP_COLORS = {
    "W": (255, 160, 60),   # paddle larga - laranja
    "M": (160, 80, 220),   # multi-ball - roxo
    "S": (120, 200, 255),  # bola lenta - azul claro
    "C": (220, 60, 60),    # canhoes na raquete - vermelho
}
WIDE_DURATION_MS = 8000
SLOW_DURATION_MS = 8000
SLOW_FACTOR = 0.55
MAX_BALLS = 9
CANNON_DURATION_MS = 8000
CANNON_FIRE_INTERVAL_MS = 450
CANNON_PROJECTILE_SPEED = 8

# ---- Progressao de niveis (modo infinito: sem vitoria fixa, so aumenta a dificuldade) ----
LEVEL_PATTERNS = 5  # variacoes de disposicao dos tijolos que se alternam por nivel
LEVEL_TRANSITION_MS = 2500

# ---- Nivel bonus (moedas), a cada N niveis concluidos ----
BONUS_LEVEL_INTERVAL = 5
BONUS_LEVEL_DURATION_MS = 15000
BONUS_COIN_VALUE = 25

# ---- Moedas persistentes (loja) ----
COINS_PER_LEVEL_CLEARED = 5  # bonus de moeda so por limpar a fase, alem das da rodada bonus

# ---- Codigo secreto / skin ultra-rara "tempestade" ----
RAIO_SECRETO_QUEDA_MS = 450    # tempo do raio caindo do topo da tela ate a raquete
RAIO_SECRETO_DURACAO_MS = 650  # duracao total do efeito (queda + flash de impacto)

MENU_OPTIONS = ["INICIAR JOGO", "RANKING", "CREDITOS", "SAIR"]
PAUSE_OPTIONS = ["CONTINUAR", "VOLUME", "REINICIAR", "MENU INICIAL"]
