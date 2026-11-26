"""Catalogo de itens compraveis na loja (bolas, raquetes, pocao) e o desenho
de cada skin. Usado tanto pelos objetos de jogo (entities.py) quanto pelo
preview ao vivo na tela da loja (ui.py)."""
import colorsys
import math
import pygame

from constants import BLACK, BALL_COLOR, PADDLE_COLOR

BALL_SKINS = {
    "padrao":    {"nome": "Padrao",   "preco": 0,   "desc": "Bola classica, branca e lisa."},
    "volei":     {"nome": "Volei",    "preco": 140, "desc": "Gomos azuis, rastro claro."},
    "espinhos":  {"nome": "Espinhos", "preco": 160, "desc": "Puas afiadas, rastro em brasa."},
    "bomba":     {"nome": "Bomba",    "preco": 180, "desc": "Pavio aceso, rastro de fagulhas."},
    "cometa":    {"nome": "Cometa",   "preco": 450, "desc": "Cores que nunca param de mudar."},
    "fenix":     {"nome": "Fenix",    "preco": 520, "desc": "Labaredas eternas, renasce a cada rebatida."},
}
BALL_SKIN_ORDER = ["padrao", "volei", "espinhos", "bomba", "cometa", "fenix"]

PADDLE_SKINS = {
    "padrao":     {"nome": "Padrao",     "preco": 0,   "desc": "Raquete ciano classica."},
    "listrada":   {"nome": "Corrida",    "preco": 120, "desc": "Listras vermelhas sobre branco."},
    "eletrica":   {"nome": "Eletrica",   "preco": 150, "desc": "Raio aceso com faiscas."},
    "dourada":    {"nome": "Dourada",    "preco": 220, "desc": "Brilho dourado reluzente."},
    "prisma":     {"nome": "Prisma",     "preco": 500, "desc": "Gradiente arco-iris animado."},
    "nebulosa":   {"nome": "Nebulosa",   "preco": 560, "desc": "Nuvem cosmica com estrelas cintilantes."},
    "tempestade": {"nome": "Tempestade", "preco": 0,   "desc": "So cai do ceu com um codigo secreto."},
}
# "tempestade" fica de fora de proposito: nao aparece na loja, nao se compra.
# So existe uma forma de consegui-la - o codigo secreto (CODIGO_SECRETO, em
# game.py) faz um raio cair do ceu e atingir a raquete, transformando-a nela.
PADDLE_SKIN_ORDER = ["padrao", "listrada", "eletrica", "dourada", "prisma", "nebulosa"]

# Raridades usadas pra desenhar a tag no card da loja/mochila (ui.py).
RARIDADE_LENDARIA = {"cometa", "fenix", "prisma", "nebulosa"}
RARIDADE_SECRETA = {"tempestade"}

POTION_PRECO = 400
POTION_NOME = "Pocao da Segunda Chance"
POTION_DESC = "Perdeu a ultima vida? Pergunta se quer continuar com 1 vida. Uso unico por pocao."

_TRAIL_COLORS = {
    "padrao": BALL_COLOR,
    "volei": (230, 230, 230),
    "espinhos": (255, 90, 30),
    "bomba": (255, 190, 60),
}


def _cor_arco_iris(hue, sat=0.9, val=1.0):
    r, g, b = colorsys.hsv_to_rgb(hue % 1.0, sat, val)
    return int(r * 255), int(g * 255), int(b * 255)


def _cor_fogo(t):
    """Interpola uma cor de 'temperatura' entre vermelho profundo (t=0) e
    dourado quase branco (t=1) - usada na fenix."""
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        a, b, tt = (120, 10, 10), (255, 120, 20), t / 0.5
    else:
        a, b, tt = (255, 120, 20), (255, 230, 150), (t - 0.5) / 0.5
    return tuple(int(a[i] + (b[i] - a[i]) * tt) for i in range(3))


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


def _desenhar_bola_cometa(surf, x, y, radius, now_ms):
    """Skin lendaria: nucleo com cor cíclica arco-iris + 4 faiscas orbitando."""
    hue = now_ms / 1500.0
    pygame.draw.circle(surf, _cor_arco_iris(hue), (int(x), int(y)), radius)
    pygame.draw.circle(surf, (255, 255, 255),
                        (int(x - radius * 0.3), int(y - radius * 0.3)), max(1, int(radius * 0.3)))
    for i in range(4):
        ang = now_ms / 300.0 + i * (math.pi / 2)
        sx = x + (radius + 4) * math.cos(ang)
        sy = y + (radius + 4) * math.sin(ang)
        pygame.draw.circle(surf, _cor_arco_iris(hue + i * 0.25), (int(sx), int(sy)), 2)
    pygame.draw.circle(surf, BLACK, (int(x), int(y)), radius, width=1)


def _desenhar_bola_fenix(surf, x, y, radius, now_ms):
    """Skin lendaria: nucleo incandescente com labaredas lambendo a bola e um
    halo de calor por fora - cores sempre quentes (vermelho -> dourado)."""
    glow_r = int(radius * 1.8)
    glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 120, 30, 60), (glow_r, glow_r), glow_r)
    surf.blit(glow, (x - glow_r, y - glow_r))

    flick = (math.sin(now_ms / 90.0) + 1) / 2
    for i in range(7):
        ang = (i / 7) * (2 * math.pi) + now_ms / 400.0
        wobble = math.sin(now_ms / 150.0 + i * 1.7)
        tip_len = radius * (0.9 + 0.3 * wobble + 0.3 * flick)
        base_a, base_b = ang - 0.22, ang + 0.22
        p1 = (x + radius * 0.6 * math.cos(base_a), y + radius * 0.6 * math.sin(base_a))
        p2 = (x + (radius + tip_len) * math.cos(ang), y + (radius + tip_len) * math.sin(ang))
        p3 = (x + radius * 0.6 * math.cos(base_b), y + radius * 0.6 * math.sin(base_b))
        pygame.draw.polygon(surf, _cor_fogo(0.3 + 0.5 * wobble), [p1, p2, p3])

    pygame.draw.circle(surf, (255, 200, 60), (int(x), int(y)), radius)
    pygame.draw.circle(surf, (255, 255, 220),
                        (int(x - radius * 0.25), int(y - radius * 0.25)), max(1, int(radius * 0.3)))
    pygame.draw.circle(surf, (140, 20, 10), (int(x), int(y)), radius, width=1)


def desenhar_bola(surf, x, y, radius, skin_id, now_ms, trail=None):
    """Desenha o rastro (cor conforme a skin) e depois o corpo da bola."""
    if trail:
        n = len(trail)
        if skin_id == "cometa":
            for i, (tx, ty) in enumerate(trail):
                alpha = int(255 * (i / n) * 0.6)
                r = int(radius * (i / n))
                if r > 0:
                    hue = (now_ms / 1500.0) + i * 0.05
                    s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*_cor_arco_iris(hue), alpha), (r, r), r)
                    surf.blit(s, (tx - r, ty - r))
        elif skin_id == "fenix":
            for i, (tx, ty) in enumerate(trail):
                alpha = int(255 * (i / n) * 0.6)
                r = int(radius * (i / n))
                if r > 0:
                    s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*_cor_fogo(i / n), alpha), (r, r), r)
                    surf.blit(s, (tx - r, ty - r))
        else:
            trail_color = _TRAIL_COLORS.get(skin_id, BALL_COLOR)
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
    elif skin_id == "cometa":
        _desenhar_bola_cometa(surf, x, y, radius, now_ms)
    elif skin_id == "fenix":
        _desenhar_bola_fenix(surf, x, y, radius, now_ms)
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


def _desenhar_raquete_prisma(surf, rect, now_ms):
    """Skin lendaria: faixas verticais em gradiente arco-iris, deslizando com
    o tempo, mais uma faixa de brilho branco por cima (igual a dourada)."""
    old_clip = surf.get_clip()
    surf.set_clip(rect)
    strips = 24
    strip_w = max(1, rect.width // strips + 1)
    t_offset = (now_ms / 1200.0) % 1.0
    for i in range(strips + 1):
        hue = (i / strips) + t_offset
        strip_rect = pygame.Rect(rect.x + i * strip_w, rect.y, strip_w, rect.height)
        pygame.draw.rect(surf, _cor_arco_iris(hue, sat=0.8), strip_rect)

    band_w = 14
    cycle = 1000
    t = (now_ms % cycle) / cycle
    bx = int(-band_w + t * (rect.width + band_w * 2))
    shine = pygame.Surface((band_w, rect.height), pygame.SRCALPHA)
    shine.fill((255, 255, 255, 90))
    surf.blit(shine, (rect.x + bx, rect.y))
    surf.set_clip(old_clip)
    pygame.draw.rect(surf, BLACK, rect, width=2, border_radius=8)


def _desenhar_raquete_nebulosa(surf, rect, now_ms):
    """Skin lendaria: nuvem cosmica roxa/azul ondulando por dentro da
    raquete, com estrelinhas cintilantes por cima."""
    old_clip = surf.get_clip()
    surf.set_clip(rect)
    base = pygame.Surface(rect.size, pygame.SRCALPHA)
    base.fill((25, 10, 45, 255))
    surf.blit(base, rect.topleft)

    blobs = 5
    for i in range(blobs):
        t = now_ms / 1000.0 + i * 1.3
        bx = rect.x + rect.width * (0.5 + 0.45 * math.sin(t * 0.6 + i))
        by = rect.centery + rect.height * 0.3 * math.sin(t * 0.9 + i * 2)
        r = rect.height * (0.9 + 0.3 * math.sin(t))
        hue = (i / blobs + now_ms / 4000.0) % 1.0
        color = _cor_arco_iris(hue, sat=0.55, val=0.9)
        cloud = pygame.Surface((int(r * 2), int(r * 2)), pygame.SRCALPHA)
        pygame.draw.circle(cloud, (*color, 90), (int(r), int(r)), int(r))
        surf.blit(cloud, (bx - r, by - r))

    for i in range(10):
        sx = rect.x + (i * 37 + 11) % rect.width
        sy = rect.y + (i * 19 + 5) % rect.height
        tw = (math.sin(now_ms / 200.0 + i * 2.1) + 1) / 2
        c = int(180 + 70 * tw)
        pygame.draw.circle(surf, (c, c, 255), (sx, sy), 1)

    surf.set_clip(old_clip)
    pygame.draw.rect(surf, BLACK, rect, width=2, border_radius=8)
    pygame.draw.rect(surf, (200, 160, 255), rect.inflate(-4, -4), width=1, border_radius=6)


def _desenhar_raquete_tempestade(surf, rect, now_ms):
    """Skin ultra-rara (so pelo codigo secreto): tempestade eletrica dentro da
    raquete - ceu tempestuoso de fundo, nuvens densas, uma faixa de energia
    sempre varrendo a raquete e raios horizontais crepitando de ponta a ponta,
    com uma aura pulsante em duas camadas por fora. De proposito a skin mais
    trabalhada do jogo: e a recompensa do segredo."""
    pulse = (math.sin(now_ms / 260.0) + 1) / 2

    for pad, alpha_base in ((16, 70), (8, 110)):
        aura_pad = int(pad + 5 * pulse)
        aura = pygame.Surface((rect.width + aura_pad * 2, rect.height + aura_pad * 2), pygame.SRCALPHA)
        pygame.draw.rect(aura, (130, 190, 255, int(alpha_base * (0.6 + 0.4 * pulse))),
                          aura.get_rect(), border_radius=14)
        surf.blit(aura, (rect.x - aura_pad, rect.y - aura_pad))

    old_clip = surf.get_clip()
    surf.set_clip(rect)

    bands = 10
    for i in range(bands):
        t = i / bands
        c = (int(8 + 14 * t), int(6 + 16 * t), int(22 + 34 * t))
        band_rect = pygame.Rect(rect.x, rect.y + int(i * rect.height / bands), rect.width,
                                 int(rect.height / bands) + 1)
        pygame.draw.rect(surf, c, band_rect)

    for i in range(4):
        t = now_ms / 1300.0 + i * 1.9
        cx = rect.x + rect.width * (0.5 + 0.5 * math.sin(t * 0.45 + i))
        cy = rect.centery + rect.height * 0.4 * math.sin(t * 0.8 + i * 2)
        cr = rect.height * 1.1
        cloud = pygame.Surface((int(cr * 2), int(cr * 2)), pygame.SRCALPHA)
        pygame.draw.circle(cloud, (50, 45, 75, 170), (int(cr), int(cr)), int(cr))
        surf.blit(cloud, (cx - cr, cy - cr))

    # faixa de energia varrendo a raquete - sempre visivel, garante
    # movimento mesmo nos frames em que nenhum raio esta "acendendo"
    band_w = max(6, rect.width // 7)
    cycle = 900
    t = (now_ms % cycle) / cycle
    bx = int(-band_w + t * (rect.width + band_w * 2))
    shine = pygame.Surface((band_w, rect.height), pygame.SRCALPHA)
    shine.fill((180, 220, 255, 90))
    surf.blit(shine, (rect.x + bx, rect.y))

    # raios horizontais crepitando de ponta a ponta (eixo longo da raquete),
    # ziguezagueando na altura disponivel - forma pseudo-aleatoria mas
    # deterministica, que muda a cada ~70ms pra parecer eletricidade viva
    altura_zigzag = max(1, rect.height - 2)
    for b in range(2):
        seed = (int(now_ms // 70) * 7 + b * 1931) & 0x7fffffff
        segments = 10
        points = []
        for s in range(segments + 1):
            seed = (seed * 1103515245 + 12345) & 0x7fffffff
            jitter = seed % altura_zigzag
            px = rect.x + (rect.width * s) // segments
            py = rect.y + 1 + jitter
            points.append((px, py))
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        if (seed % 5) != 0:
            color = (235, 245, 255) if b == 0 else (170, 205, 255)
            local_pts = [(px - rect.x, py - rect.y) for px, py in points]
            glow_s = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.lines(glow_s, (*color, 90), False, local_pts, 5)
            surf.blit(glow_s, rect.topleft)
            pygame.draw.lines(surf, color, False, points, 2)

    surf.set_clip(old_clip)

    border_color = (220, 235, 255) if pulse > 0.5 else (150, 190, 255)
    pygame.draw.rect(surf, border_color, rect, width=3, border_radius=8)
    pygame.draw.rect(surf, (255, 255, 255), rect.inflate(-4, -4), width=1, border_radius=6)

    for i in range(4):
        ang = now_ms / 220.0 + i * (math.pi / 2)
        ex = rect.centerx + (rect.width * 0.5 + 7) * math.cos(ang)
        ey = rect.centery + (rect.height * 1.8) * math.sin(ang) * 0.5
        pygame.draw.circle(surf, (210, 230, 255), (int(ex), int(ey)), 3)
        pygame.draw.circle(surf, (255, 255, 255), (int(ex), int(ey)), 1)


def desenhar_raquete(surf, rect, skin_id, now_ms):
    if skin_id == "listrada":
        _desenhar_raquete_listrada(surf, rect)
    elif skin_id == "eletrica":
        _desenhar_raquete_eletrica(surf, rect, now_ms)
    elif skin_id == "dourada":
        _desenhar_raquete_dourada(surf, rect, now_ms)
    elif skin_id == "prisma":
        _desenhar_raquete_prisma(surf, rect, now_ms)
    elif skin_id == "nebulosa":
        _desenhar_raquete_nebulosa(surf, rect, now_ms)
    elif skin_id == "tempestade":
        _desenhar_raquete_tempestade(surf, rect, now_ms)
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
