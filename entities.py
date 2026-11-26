"""Classes de jogo (raquete, bola, projetil, tijolo, particula, power-up,
moeda) e as funcoes que montam o grid de tijolos e a grade de moedas bonus."""
import random
import pygame

import audio
import player_profile as profile
import skins
from fonts import powerup_font
from constants import (
    WIDTH, HEIGHT, BLACK, BRICK_COLORS, BALL_MIN_VX,
    POWERUP_FALL_SPEED, POWERUP_COLORS, CANNON_PROJECTILE_SPEED, LEVEL_PATTERNS,
)

__all__ = [
    "Paddle", "Ball", "criar_bola_extra", "Projectile", "Brick", "Particle",
    "PowerUp", "BonusCoin", "criar_moedas_bonus", "criar_tijolos",
]


class Paddle:
    def __init__(self):
        self.base_width = 110
        self.width = self.base_width
        self.height = 16
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - 40
        self.speed = 9
        self.skin = profile.obter_skin_raquete_equipada()

    def retangulo(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def atualizar(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        self.x = max(0, min(WIDTH - self.width, self.x))

    def definir_largura(self, new_width):
        """Change width while keeping the paddle centered on the same spot."""
        if new_width == self.width:
            return
        center = self.x + self.width / 2
        self.width = new_width
        self.x = int(center - self.width / 2)
        self.x = max(0, min(WIDTH - self.width, self.x))

    def desenhar(self, surf, now_ms=0):
        skins.desenhar_raquete(surf, self.retangulo(), self.skin, now_ms)


class Ball:
    def __init__(self):
        self.radius = 9
        self.trail = []
        self.skin = profile.obter_skin_bola_equipada()
        self.reiniciar()

    def reiniciar(self):
        """Ball is born/reborn stuck on top of the paddle, not moving."""
        self.x = WIDTH // 2
        self.y = HEIGHT - 60
        self.vx = 0.0
        self.vy = 0.0
        self.stuck = True
        self.trail = []

    def lancar(self, direction=None):
        if not self.stuck:
            return
        self.stuck = False
        if direction is not None and direction != 0:
            self.vx = 5 if direction > 0 else -5
        else:
            self.vx = random.choice([-5, 5])
        self.vy = -5

    def grudar_em(self, paddle):
        self.x = paddle.x + paddle.width / 2
        self.y = paddle.y - self.radius - 1
        self.trail = []

    def retangulo(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                            self.radius * 2, self.radius * 2)

    def garantir_vx_minimo(self):
        """Evita trajetoria quase vertical (ver BALL_MIN_VX em constants.py)."""
        if abs(self.vx) < BALL_MIN_VX:
            sinal = 1 if self.vx > 0 else (-1 if self.vx < 0 else random.choice([-1, 1]))
            self.vx = sinal * BALL_MIN_VX

    def atualizar(self, speed_factor=1.0):
        if self.stuck:
            return
        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)
        self.x += self.vx * speed_factor
        self.y += self.vy * speed_factor

        if self.x - self.radius <= 0 or self.x + self.radius >= WIDTH:
            self.vx *= -1
            audio.tocar_som("hit_wall")
        if self.y - self.radius <= 0:
            self.vy *= -1
            audio.tocar_som("hit_wall")
        self.garantir_vx_minimo()

    def desenhar(self, surf, now_ms=0):
        skins.desenhar_bola(surf, self.x, self.y, self.radius, self.skin, now_ms, self.trail)


def criar_bola_extra(source, vx_offset):
    nb = Ball()
    nb.x = source.x
    nb.y = source.y
    nb.stuck = False
    nb.radius = source.radius
    base_vx = source.vx if source.vx != 0 else random.choice([-5, 5])
    new_vx = base_vx + vx_offset
    new_vx = max(-9, min(9, new_vx))
    if -1 < new_vx < 1:
        new_vx = 5 if vx_offset >= 0 else -5
    nb.vx = new_vx
    nb.vy = -abs(source.vy) if source.vy != 0 else -5
    nb.trail = []
    return nb


class Projectile:
    """Projetil disparado pelos canhoes da raquete (power-up C). Sobe e dana
    tijolos como se fosse uma batida da bola, podendo quebra-los."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 4
        self.h = 12
        self.vy = -CANNON_PROJECTILE_SPEED

    def retangulo(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h),
                            self.w, self.h)

    def atualizar(self):
        self.y += self.vy

    def desenhar(self, surf):
        pygame.draw.rect(surf, (255, 140, 60), self.retangulo(), border_radius=2)


class Brick:
    def __init__(self, x, y, w, h, color, lives=1):
        self.rect = pygame.Rect(x, y, w, h)
        self.base_color = color
        self.color = color
        self.max_lives = max(1, lives)
        self.lives = self.max_lives
        self.alive = True

    def atingir(self):
        """Aplica uma batida no tijolo. Retorna True se ele quebrou de vez
        nessa batida (lives chegou a 0), False se apanhou mas sobreviveu."""
        if not self.alive:
            return False
        self.lives -= 1
        if self.lives <= 0:
            self.alive = False
            return True
        # ainda vivo: escurece a cor gradualmente pra sinalizar o dano
        factor = 0.5 + 0.5 * (self.lives / self.max_lives)
        self.color = tuple(max(0, int(c * factor)) for c in self.base_color)
        return False

    def desenhar(self, surf):
        if not self.alive:
            return
        pygame.draw.rect(surf, self.color, self.rect, border_radius=4)
        pygame.draw.rect(surf, BLACK, self.rect, width=2, border_radius=4)
        hits_taken = self.max_lives - self.lives
        if hits_taken > 0:
            # pequenas rachaduras: uma linha extra por batida sofrida
            r = self.rect
            crack_color = (25, 25, 25)
            for i in range(hits_taken):
                x1 = min(r.x + 5 + i * 7, r.right - 5)
                y1 = r.y + 3
                x2 = max(r.right - 5 - i * 5, r.x + 5)
                y2 = r.bottom - 3
                pygame.draw.line(surf, crack_color, (x1, y1), (x2, y2), 2)


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        speed = random.uniform(2, 6)
        self.vx = speed * random.uniform(-1, 1)
        self.vy = speed * random.uniform(-1, 1)
        self.color = color
        self.life = random.randint(20, 40)
        self.max_life = self.life
        self.size = random.randint(2, 5)

    def atualizar(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.life -= 1

    def desenhar(self, surf):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
            surf.blit(s, (self.x - self.size, self.y - self.size))


class PowerUp:
    SIZE = 28

    def __init__(self, x, y, kind):
        self.kind = kind
        self.x = x
        self.y = y
        self.vy = POWERUP_FALL_SPEED
        self.w = PowerUp.SIZE
        self.h = PowerUp.SIZE
        self.color = POWERUP_COLORS[kind]

    def retangulo(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h)

    def atualizar(self):
        self.y += self.vy

    def desenhar(self, surf):
        r = self.retangulo()
        pygame.draw.rect(surf, self.color, r, border_radius=6)
        pygame.draw.rect(surf, BLACK, r, width=2, border_radius=6)
        label = powerup_font.render(self.kind, True, BLACK)
        surf.blit(label, (r.centerx - label.get_width() // 2, r.centery - label.get_height() // 2))


class BonusCoin:
    """Moeda estatica da rodada bonus - some ao ser tocada pela bola e da pontos."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 12
        self.alive = True

    def retangulo(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                            self.radius * 2, self.radius * 2)

    def desenhar(self, surf):
        if not self.alive:
            return
        pygame.draw.circle(surf, (255, 215, 0), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, (120, 90, 0), (int(self.x), int(self.y)), self.radius, width=2)


def criar_moedas_bonus():
    """Grade de moedas da rodada bonus - sem tijolos, so pontos extras."""
    coins = []
    rows, cols = 5, 9
    top = 120
    spacing_y = 42
    spacing_x = (WIDTH - 120) / (cols - 1)
    for row in range(rows):
        for col in range(cols):
            x = 60 + col * spacing_x
            y = top + row * spacing_y
            coins.append(BonusCoin(x, y))
    return coins


def _padrao_presente(pattern, row, col, rows, cols):
    """Decide se a celula (row, col) do grid tem tijolo, de acordo com o padrao
    do nivel. Padrao 0 e a grade classica cheia (sempre usada no nivel 1).
    Os demais abrem vãos diferentes a cada rotacao de nivel, pra nao repetir
    sempre a mesma disposicao, sem ficar absurdo."""
    if pattern == 0:
        return True
    if pattern == 1:  # friso vertical: uma coluna vazia a cada 4
        return col % 4 != 3
    if pattern == 2:  # piramide: fileiras mais perto da raquete ficam mais estreitas
        margin = min(row // 2, (cols - 1) // 2)
        return margin <= col < cols - margin
    if pattern == 3:  # buraco em losango no meio do grid
        cx, cy = (cols - 1) / 2, (rows - 1) / 2
        dist = abs(col - cx) + abs(row - cy)
        return dist > 1.5
    if pattern == 4:  # fileiras pares perdem as pontas, impares ficam cheias
        if row % 2 == 0:
            return col != 0 and col != cols - 1
        return True
    return True


def criar_tijolos(level=1):
    """Monta o grid de tijolos. A fileira mais perto da raquete (a primeira que
    a bola encontra ao jogar) quebra com 1 batida; subindo dai pra cima as
    fileiras exigem mais batidas, ate um maximo de 3. Conforme o nivel sobe, o
    grid cresce (mais linhas), mas o teto de vida por tijolo continua fixo em 3.
    A disposicao das celulas tambem roda entre alguns padroes (LEVEL_PATTERNS)
    pra variar o layout entre niveis - o nivel 1 sempre usa a grade classica."""
    bricks = []
    rows = min(5 + (level - 1) // 2, 8)
    cols = 10
    padding = 6
    offset_top = 60
    offset_side = 20
    brick_w = (WIDTH - offset_side * 2 - padding * (cols - 1)) // cols
    brick_h = 24

    # so a fileira mais perto da raquete (ultima linha do grid) quebra com 1
    # toque, a anterior com 2 toques, e todo o resto (mais longe, perto do
    # topo) ja fica no teto de 3 toques, em qualquer nivel.
    boundary_1 = 1
    boundary_2 = 2

    pattern = 0 if level == 1 else (level - 1) % LEVEL_PATTERNS

    for row in range(rows):
        from_paddle = rows - 1 - row  # 0 = fileira mais perto da raquete
        if from_paddle < boundary_1:
            lives = 1
        elif from_paddle < boundary_2:
            lives = 2
        else:
            lives = 3  # maximo de 3 toques de vida, fixo, independente do nivel
        for col in range(cols):
            if not _padrao_presente(pattern, row, col, rows, cols):
                continue
            x = offset_side + col * (brick_w + padding)
            y = offset_top + row * (brick_h + padding)
            bricks.append(Brick(x, y, brick_w, brick_h, BRICK_COLORS[row % len(BRICK_COLORS)], lives))
    return bricks
