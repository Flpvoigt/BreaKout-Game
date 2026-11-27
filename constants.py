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
    "G": (255, 105, 180),  # ima - gruda a bola na raquete pra mirar - rosa
    "F": (210, 210, 230),  # fantasma - bola atravessa tijolos sem quicar - branco-azulado
    "L": (80, 220, 120),   # vida extra - verde
    "P": (120, 120, 130),  # penalidade - raquete encolhe (powerup ruim) - cinza
}
# Peso de sorteio de cada power-up (nao e chance de cair, so o peso relativo
# entre os tipos quando um cai) - os mais fortes (vida extra, fantasma) saem
# bem mais raro que os efeitos simples, senao o jogador nunca morre.
POWERUP_WEIGHTS = {
    "W": 5, "S": 5,
    "M": 3, "C": 3, "G": 3, "P": 3,
    "F": 1, "L": 1,
}
WIDE_DURATION_MS = 8000
SLOW_DURATION_MS = 8000
SLOW_FACTOR = 0.55
MAX_BALLS = 9
CANNON_DURATION_MS = 8000
CANNON_FIRE_INTERVAL_MS = 450
CANNON_PROJECTILE_SPEED = 8
MAGNET_DURATION_MS = 8000
GHOST_DURATION_MS = 6000
SHRINK_DURATION_MS = 6000
SHRINK_FACTOR = 0.6

# ---- Progressao de niveis (modo infinito: sem vitoria fixa, so aumenta a dificuldade) ----
LEVEL_PATTERNS = 10  # variacoes de disposicao dos tijolos que se alternam por nivel
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

# ---- Combo (tijolos destruidos seguidos sem a bola voltar na raquete) ----
COMBO_TIMEOUT_MS = 2500          # tempo parado sem quebrar tijolo que zera o combo
COMBO_MULTIPLICADOR_PASSO = 3    # a cada N acertos seguidos, o multiplicador sobe 1
COMBO_MULTIPLICADOR_MAX = 5
# (multiplicador novo atingido) -> (mensagem de hype, cor)
COMBO_MENSAGENS = {
    2: ("COMBO!", (255, 230, 60)),
    3: ("OTIMO!", (255, 170, 60)),
    4: ("INCRIVEL!", (255, 110, 60)),
    5: ("IMPARAVEL!", (255, 70, 130)),
}

MENU_OPTIONS = ["INICIAR JOGO", "RANKING", "CREDITOS", "SAIR"]
PAUSE_OPTIONS = ["CONTINUAR", "VOLUME", "REINICIAR", "MENU INICIAL"]
