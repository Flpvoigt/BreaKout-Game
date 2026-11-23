"""Catalogo de itens compraveis na loja (bolas, raquetes, pocao) e o desenho
de cada skin. Usado tanto pelos objetos de jogo (entities.py) quanto pelo
preview ao vivo na tela da loja (ui.py)."""
import math
import pygame

from constants import BLACK, BALL_COLOR, PADDLE_COLOR

BALL_SKINS = {
    "padrao":    {"nome": "Padrao",   "preco": 0,   "desc": "Bola classica, branca e lisa."},
    "volei":     {"nome": "Volei",    "preco": 80,  "desc": "Gomos azuis, rastro claro."},
    "espinhos":  {"nome": "Espinhos", "preco": 90,  "desc": "Puas afiadas, rastro em brasa."},
    "bomba":     {"nome": "Bomba",    "preco": 100, "desc": "Pavio aceso, rastro de fagulhas."},
}
BALL_SKIN_ORDER = ["padrao", "volei", "espinhos", "bomba"]

PADDLE_SKINS = {
    "padrao":    {"nome": "Padrao",   "preco": 0,   "desc": "Raquete ciano classica."},
    "listrada":  {"nome": "Corrida",  "preco": 70,  "desc": "Listras vermelhas sobre branco."},
    "eletrica":  {"nome": "Eletrica", "preco": 80,  "desc": "Raio aceso com faiscas."},
    "dourada":   {"nome": "Dourada",  "preco": 110, "desc": "Brilho dourado reluzente."},
}
PADDLE_SKIN_ORDER = ["padrao", "listrada", "eletrica", "dourada"]

POTION_PRECO = 250
POTION_NOME = "Pocao da Segunda Chance"
POTION_DESC = "Perdeu a ultima vida? Pergunta se quer continuar com 1 vida. Uso unico por pocao."

_TRAIL_COLORS = {
    "padrao": BALL_COLOR,
    "volei": (230, 230, 230),
    "espinhos": (255, 90, 30),
    "bomba": (255, 190, 60),
}


# ---- bolas ----

def _desenhar_bola_padrao(surf, x, y, radius):
    pygame.draw.circle(surf, BALL_COLOR, (int(x), int(y)), radius)


def _desenhar_bola_volei(surf, x, y, radius):
    pygame.draw.circle(surf, (245, 245, 240), (int(x), int(y)), radius)
    wedge_color = (40, 110, 200)
    for base_angle in (0, 120, 240):
        pts = [(x, y)]
        for a in range(base_angle, base_angle + 50, 10):
            rad = math.radians(a)
            pts.append((x + radius * math.cos(rad), y + radius * math.sin(rad)))
        pygame.draw.polygon(surf, wedge_color, pts)
    pygame.draw.circle(surf, BLACK, (int(x), int(y)), radius, width=1)


def _desenhar_bola_espinhos(surf, x, y, radius):
    base_color = (170, 25, 25)
    pygame.draw.circle(surf, base_color, (int(x), int(y)), radius)
    spike_len = radius * 0.8
    for i in range(8):
        ang = math.radians(i * 45)
        bx1 = x + radius * math.cos(ang - 0.25)
        by1 = y + radius * math.sin(ang - 0.25)
        bx2 = x + radius * math.cos(ang + 0.25)
        by2 = y + radius * math.sin(ang + 0.25)
        tx = x + (radius + spike_len) * math.cos(ang)
        ty = y + (radius + spike_len) * math.sin(ang)
        pygame.draw.polygon(surf, base_color, [(bx1, by1), (tx, ty), (bx2, by2)])
    pygame.draw.circle(surf, BLACK, (int(x), int(y)), radius, width=1)


def _desenhar_bola_bomba(surf, x, y, radius, now_ms):
    pygame.draw.circle(surf, (25, 25, 30), (int(x), int(y)), radius)
    pygame.draw.circle(surf, (70, 70, 80),
                        (int(x - radius * 0.35), int(y - radius * 0.35)), max(2, int(radius * 0.3)))
    fuse_x = x + radius * 0.5
    fuse_y = y - radius * 0.9
    pygame.draw.line(surf, (110, 80, 50), (x + radius * 0.2, y - radius * 0.85), (fuse_x, fuse_y), 2)
    flick = (math.sin(now_ms / 110.0) + 1) / 2
    flame_r = 2 + int(2 * flick)
    flame_color = (255, int(160 + 60 * flick), 40)
    pygame.draw.circle(surf, flame_color, (int(fuse_x), int(fuse_y)), flame_r)


def desenhar_bola(surf, x, y, radius, skin_id, now_ms, trail=None):
    """Desenha o rastro (cor conforme a skin) e depois o corpo da bola."""
    trail_color = _TRAIL_COLORS.get(skin_id, BALL_COLOR)
    if trail:
        n = len(trail)
        for i, (tx, ty) in enumerate(trail):
            alpha = int(255 * (i / n) * 0.5)
            r = int(radius * (i / n))
            if r > 0:
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*trail_color, alpha), (r, r), r)
                surf.blit(s, (tx - r, ty - r))

    if skin_id == "volei":
        _desenhar_bola_volei(surf, x, y, radius)
    elif skin_id == "espinhos":
        _desenhar_bola_espinhos(surf, x, y, radius)
    elif skin_id == "bomba":
        _desenhar_bola_bomba(surf, x, y, radius, now_ms)
    else:
        _desenhar_bola_padrao(surf, x, y, radius)


# ---- raquetes ----

def _desenhar_raquete_padrao(surf, rect):
    pygame.draw.rect(surf, PADDLE_COLOR, rect, border_radius=8)


def _desenhar_raquete_listrada(surf, rect):
    pygame.draw.rect(surf, (235, 235, 235), rect, border_radius=8)
    old_clip = surf.get_clip()
    surf.set_clip(rect)
    stripe_color = (210, 30, 30)
    step = 14
    for sx in range(rect.x - rect.height, rect.x + rect.width, step):
        pygame.draw.line(surf, stripe_color, (sx, rect.y + rect.height), (sx + rect.height, rect.y), 6)
    surf.set_clip(old_clip)
    pygame.draw.rect(surf, BLACK, rect, width=2, border_radius=8)


def _desenhar_raquete_eletrica(surf, rect, now_ms):
    pygame.draw.rect(surf, (35, 32, 45), rect, border_radius=8)
    midy = rect.centery
    pts = [
        (rect.x + 4, rect.y + 3),
        (rect.x + rect.width * 0.35, midy - 4),
        (rect.x + rect.width * 0.5, rect.y + 3),
        (rect.x + rect.width * 0.65, midy + 4),
        (rect.x + rect.width - 4, rect.y + rect.height - 3),
    ]
    pygame.draw.lines(surf, (255, 230, 60), False, pts, 3)
    if (now_ms // 150) % 3 == 0:
        spark_pos = pts[2]
        pygame.draw.circle(surf, (255, 255, 200), (int(spark_pos[0]), int(spark_pos[1])), 3)
    pygame.draw.rect(surf, BLACK, rect, width=2, border_radius=8)


def _desenhar_raquete_dourada(surf, rect, now_ms):
    pygame.draw.rect(surf, (210, 170, 40), rect, border_radius=8)
    band_w = 18
    cycle = 1400
    t = (now_ms % cycle) / cycle
    bx = int(-band_w + t * (rect.width + band_w * 2))
    shine = pygame.Surface((band_w, rect.height), pygame.SRCALPHA)
    shine.fill((255, 255, 220, 120))
    old_clip = surf.get_clip()
    surf.set_clip(rect)
    surf.blit(shine, (rect.x + bx, rect.y))
    surf.set_clip(old_clip)
    pygame.draw.rect(surf, BLACK, rect, width=2, border_radius=8)
    pygame.draw.rect(surf, (255, 230, 140), rect.inflate(-4, -4), width=1, border_radius=6)


def desenhar_raquete(surf, rect, skin_id, now_ms):
    if skin_id == "listrada":
        _desenhar_raquete_listrada(surf, rect)
    elif skin_id == "eletrica":
        _desenhar_raquete_eletrica(surf, rect, now_ms)
    elif skin_id == "dourada":
        _desenhar_raquete_dourada(surf, rect, now_ms)
    else:
        _desenhar_raquete_padrao(surf, rect)


# ---- pocao ----

def desenhar_icone_pocao(surf, cx, cy, now_ms, scale=1.0):
    """Frasco de pocao com liquido borbulhante (muda de tom com o tempo)."""
    neck_w, neck_h = int(9 * scale), int(11 * scale)
    neck_rect = pygame.Rect(0, 0, neck_w, neck_h)
    neck_rect.midbottom = (cx, cy - int(15 * scale))
    pygame.draw.rect(surf, (90, 70, 60), neck_rect, border_radius=2)

    cork_rect = pygame.Rect(0, 0, neck_w + 6, int(6 * scale))
    cork_rect.midbottom = (cx, neck_rect.top + int(3 * scale))
    pygame.draw.rect(surf, (150, 110, 70), cork_rect, border_radius=2)

    body_w, body_h = int(28 * scale), int(30 * scale)
    body_rect = pygame.Rect(0, 0, body_w, body_h)
    body_rect.midtop = (cx, neck_rect.bottom - int(2 * scale))

    inner = body_rect.inflate(-int(6 * scale), -int(6 * scale))
    bub = (math.sin(now_ms / 220.0) + 1) / 2
    liquid_color = (int(210 + 20 * bub), int(50 + 30 * bub), int(150 + 30 * bub))
    pygame.draw.ellipse(surf, liquid_color, inner)

    shine_rect = pygame.Rect(0, 0, max(2, int(body_w * 0.22)), max(2, int(body_h * 0.35)))
    shine_rect.topleft = (inner.x + int(3 * scale), inner.y + int(3 * scale))
    shine = pygame.Surface(shine_rect.size, pygame.SRCALPHA)
    shine.fill((255, 255, 255, 100))
    surf.blit(shine, shine_rect.topleft)

    pygame.draw.ellipse(surf, (20, 20, 30), body_rect, width=max(1, int(2 * scale)))
