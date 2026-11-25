"""Telas e elementos de interface: icone da janela, fundos, menus, ranking,
overlays de transicao/pausa/fim de jogo."""
import math
import random
import pygame

import leaderboard
import player_profile as profile
import skins
from fonts import font, big_font, status_font, title_font, menu_font, menu_hint_font
from constants import (WIDTH, HEIGHT, WHITE, BLACK, POWERUP_COLORS, MENU_OPTIONS, PAUSE_OPTIONS,
                       RAIO_SECRETO_QUEDA_MS, RAIO_SECRETO_DURACAO_MS)

__all__ = [
    "criar_superficie_icone", "formatar_tempo", "desenhar_canhoes",
    "desenhar_fundo_retro", "desenhar_fundo_estrelado",
    "desenhar_menu", "desenhar_creditos", "desenhar_ranking",
    "desenhar_cronometro_powerup", "desenhar_entrada_nome", "desenhar_mensagem_fim",
    "desenhar_nivel_completo", "desenhar_menu_pausa", "desenhar_loja", "desenhar_oferta_pocao",
    "desenhar_notificacao", "desenhar_raio_secreto", "desenhar_inventario",
    "desenhar_icone_inventario", "obter_retangulo_icone_inventario",
    "obter_retangulos_abas_inventario", "obter_itens_possuidos",
    "obter_retangulos_menu", "obter_retangulos_menu_pausa",
]


def criar_superficie_icone(size=64):
    """Icone da janela/barra de tarefas: mini-cena do jogo (tijolos + bola +
    raquete), no lugar do mascote padrao do Pygame."""
    icon = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(icon, (10, 10, 20, 255), (2, 2, size - 4, size - 4), border_radius=size // 6)

    brick_colors = [(255, 80, 80), (80, 160, 255)]
    cols = 4
    brick_w = (size - 16) // cols
    brick_h = max(4, size // 10)
    gap = 2
    for row, color in enumerate(brick_colors):
        y = 8 + row * (brick_h + gap)
        for col in range(cols):
            x = 8 + col * (brick_w + gap)
            pygame.draw.rect(icon, color, (x, y, brick_w - gap, brick_h), border_radius=2)

    ball_radius = max(3, size // 12)
    pygame.draw.circle(icon, (255, 255, 255), (size * 2 // 3, size * 2 // 3), ball_radius)

    paddle_w = size // 2
    paddle_h = max(5, size // 10)
    paddle_rect = pygame.Rect(size // 2 - paddle_w // 2, size - paddle_h - 6, paddle_w, paddle_h)
    pygame.draw.rect(icon, (0, 220, 255), paddle_rect, border_radius=paddle_h // 2)
    return icon


def formatar_tempo(ms):
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def desenhar_canhoes(surf, paddle):
    """Desenha os dois canhoes nas pontas da raquete enquanto o power-up C esta ativo."""
    turret_w, turret_h = 10, 16
    left = pygame.Rect(int(paddle.x) - 2, paddle.y - turret_h + 4, turret_w, turret_h)
    right = pygame.Rect(int(paddle.x + paddle.width) - turret_w + 2, paddle.y - turret_h + 4, turret_w, turret_h)
    for r in (left, right):
        pygame.draw.rect(surf, POWERUP_COLORS["C"], r, border_radius=3)
        pygame.draw.rect(surf, BLACK, r, width=2, border_radius=3)


def desenhar_titulo_pulsante(surf, now_ms, center):
    """Desenha 'BREAKOUT' com sombra + brilho suave pulsante, sem duplicar/desalinhar
    o texto (evita o artefato de usar dois rotozoom com escalas diferentes)."""
    t = now_ms / 1000.0
    pulse = (math.sin(t * 2.4) + 1) / 2  # 0..1

    base_color = (0, 220, 255)
    accent_color = (255, 90, 200)
    color = tuple(int(base_color[i] * (1 - pulse) + accent_color[i] * pulse) for i in range(3))

    text = "BREAKOUT"
    main_surface = title_font.render(text, True, color)
    rect = main_surface.get_rect(center=center)

    # sombra solida leve, pra dar profundidade sem usar escala/blur (que gera "fantasma"
    # em texto de borda nitida) - só um offset simples atras do texto principal
    shadow_surface = title_font.render(text, True, (20, 10, 30))
    surf.blit(shadow_surface, (rect.x + 5, rect.y + 5))
    surf.blit(main_surface, rect)


_menu_bg_cache = None


def _criar_fundo_menu():
    """Monta (uma unica vez) o cenario retro 8-bit: ceu em gradiente, montanhas
    e skyline de cidade com janelas acesas. Fica em cache porque usa posicoes
    aleatorias fixas - gerar de novo a cada frame faria tudo "piscar" trocando
    de lugar."""
    bg = pygame.Surface((WIDTH, HEIGHT))
    horizon_y = 430

    top_color = (12, 10, 45)
    bottom_color = (4, 4, 16)
    for y in range(horizon_y):
        t = y / horizon_y
        color = tuple(int(top_color[i] * (1 - t) + bottom_color[i] * t) for i in range(3))
        pygame.draw.line(bg, color, (0, y), (WIDTH, y))
    pygame.draw.rect(bg, bottom_color, (0, horizon_y, WIDTH, HEIGHT - horizon_y))

    rng = random.Random(42)
    for _ in range(70):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, horizon_y - 50)
        size = rng.choice([1, 1, 1, 2])
        pygame.draw.rect(bg, (200, 200, 235), (x, y, size, size))

    def montanha_irregular(base_y, amplitude, color, seed, step=40):
        rng2 = random.Random(seed)
        pts = [(0, horizon_y)]
        x = 0
        while x <= WIDTH:
            pts.append((x, base_y - rng2.randint(0, amplitude)))
            x += step
        pts.append((WIDTH, horizon_y))
        pygame.draw.polygon(bg, color, pts)

    montanha_irregular(horizon_y - 40, 70, (26, 20, 58), 1)
    montanha_irregular(horizon_y - 8, 50, (16, 13, 42), 2)
    pygame.draw.rect(bg, (45, 65, 150), (0, horizon_y, WIDTH, 3))

    rng3 = random.Random(7)
    building_color = (32, 16, 55)
    x = 0
    while x < WIDTH:
        bw = rng3.randint(32, 64)
        bh = rng3.randint(60, 160)
        by = HEIGHT - bh
        pygame.draw.rect(bg, building_color, (x, by, bw, HEIGHT - by))
        wx = x + 5
        while wx < x + bw - 5:
            wy = by + 6
            while wy < HEIGHT - 8:
                if rng3.random() < 0.3:
                    wc = rng3.choice([(255, 220, 120), (255, 120, 180), (150, 220, 255)])
                    pygame.draw.rect(bg, wc, (wx, wy, 3, 4))
                wy += 9
            wx += 8
        x += bw + 3
    return bg


def desenhar_fundo_retro(surf, now_ms):
    global _menu_bg_cache
    if _menu_bg_cache is None:
        _menu_bg_cache = _criar_fundo_menu()
    surf.blit(_menu_bg_cache, (0, 0))
    t = now_ms / 1000.0
    for i in range(5):
        tw = (math.sin(t * 2 + i * 1.3) + 1) / 2
        x = 70 + i * 160
        y = 35 + (i % 3) * 22
        dot = pygame.Surface((2, 2), pygame.SRCALPHA)
        dot.fill((255, 255, 255, int(100 + 150 * tw)))
        surf.blit(dot, (x, y))


_game_bg_cache = None


def _criar_ceu_estrelado_jogo():
    """Fundo da tela de JOGO: so ceu noturno em gradiente + estrelas fixas,
    sem montanha/skyline (que atrapalhariam a leitura dos tijolos). Fica em
    cache - a posicao das estrelas e fixa, so o brilho delas pisca depois."""
    bg = pygame.Surface((WIDTH, HEIGHT))
    top_color = (6, 8, 28)
    bottom_color = (0, 0, 6)
    for y in range(HEIGHT):
        t = y / HEIGHT
        color = tuple(int(top_color[i] * (1 - t) + bottom_color[i] * t) for i in range(3))
        pygame.draw.line(bg, color, (0, y), (WIDTH, y))

    rng = random.Random(99)
    stars = []
    for _ in range(140):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, HEIGHT)
        size = rng.choice([1, 1, 1, 2])
        base_bright = rng.randint(120, 220)
        pygame.draw.rect(bg, (base_bright, base_bright, min(255, base_bright + 25)), (x, y, size, size))
        if rng.random() < 0.18:
            stars.append((x, y, size, rng.uniform(0, 6.28)))
    return bg, stars


def desenhar_fundo_estrelado(surf, now_ms):
    global _game_bg_cache
    if _game_bg_cache is None:
        _game_bg_cache = _criar_ceu_estrelado_jogo()
    bg, twinkle_stars = _game_bg_cache
    surf.blit(bg, (0, 0))
    t = now_ms / 1000.0
    for x, y, size, phase in twinkle_stars:
        tw = (math.sin(t * 2.2 + phase) + 1) / 2
        glow = pygame.Surface((size + 2, size + 2), pygame.SRCALPHA)
        glow.fill((255, 255, 255, int(90 + 160 * tw)))
        surf.blit(glow, (x, y))


_LOJA_ICON_W, _LOJA_ICON_H = 26, 28


def obter_retangulo_icone_loja():
    """Retangulo clicavel do mini-icone da loja, canto superior esquerdo do menu."""
    return pygame.Rect(14, 14, _LOJA_ICON_W, _LOJA_ICON_H)


def _renderizar_superficie_icone_loja():
    """Mini barraquinha (toldo listrado + balcao com uma moeda), desenhada numa
    surface propria pra poder ser escalada (zoom no hover) sem precisar de
    nenhuma caixa/contorno ao redor."""
    w, h = _LOJA_ICON_W, _LOJA_ICON_H
    icon = pygame.Surface((w, h), pygame.SRCALPHA)

    awning_colors = [(0, 200, 230), (235, 235, 240)]
    stripe_w = w / 4
    awning_bottom = 9
    for i in range(4):
        c = awning_colors[i % 2]
        x0 = i * stripe_w
        pts = [(x0, 0), (x0 + stripe_w, 0), (x0 + stripe_w + 2, awning_bottom), (x0 - 2, awning_bottom)]
        pygame.draw.polygon(icon, c, pts)
    pygame.draw.line(icon, BLACK, (-2, awning_bottom), (w + 2, awning_bottom), 1)

    counter_rect = pygame.Rect(2, awning_bottom + 1, w - 4, h - awning_bottom - 1)
    pygame.draw.rect(icon, (110, 75, 45), counter_rect, border_radius=2)
    pygame.draw.rect(icon, BLACK, counter_rect, width=1, border_radius=2)

    coin_pos = (counter_rect.centerx, counter_rect.centery + 1)
    pygame.draw.circle(icon, (255, 215, 0), coin_pos, 3)
    pygame.draw.circle(icon, BLACK, coin_pos, 3, width=1)
    return icon


def desenhar_icone_loja(surf, now_ms, hover=False):
    """So um icone pequeno no canto - ao passar o mouse, da um zoom bem leve
    nele mesmo (sem criar nenhuma caixa/contorno ao redor)."""
    rect = obter_retangulo_icone_loja()
    icon = _renderizar_superficie_icone_loja()
    if hover:
        icon = pygame.transform.smoothscale(icon, (int(_LOJA_ICON_W * 1.18), int(_LOJA_ICON_H * 1.18)))
    draw_rect = icon.get_rect(center=rect.center)
    surf.blit(icon, draw_rect.topleft)

    if hover:
        label = status_font.render("Loja", True, WHITE)
        label_bg = pygame.Rect(0, 0, label.get_width() + 8, label.get_height() + 4)
        label_bg.midleft = (rect.right + 8, rect.centery)
        pygame.draw.rect(surf, (20, 18, 30), label_bg, border_radius=5)
        surf.blit(label, (label_bg.x + 4, label_bg.y + 2))


def obter_retangulos_menu():
    """Retangulo clicavel/hover de cada opcao do menu principal, na mesma
    posicao usada pelo desenho (largura calculada pro pior caso, com ou sem
    os '> <' do item selecionado, pra nao mudar de tamanho ao passar o mouse)."""
    option_y, spacing = 300, 46
    text_h = menu_hint_font.get_height()
    rects = {}
    for i, option in enumerate(MENU_OPTIONS):
        w = max(menu_hint_font.size(option)[0], menu_hint_font.size(f"> {option} <")[0])
        rect = pygame.Rect(0, option_y + i * spacing - 4, w + 24, text_h + 8)
        rect.centerx = WIDTH // 2
        rects[i] = rect
    return rects


def desenhar_menu(surf, now_ms, selected, loja_hover=False, inv_hover=False):
    desenhar_fundo_retro(surf, now_ms)
    desenhar_titulo_pulsante(surf, now_ms, (WIDTH // 2, 120))

    option_y = 300
    spacing = 46
    for i, option in enumerate(MENU_OPTIONS):
        is_sel = i == selected
        color = (255, 230, 60) if is_sel else (210, 210, 220)
        label = f"> {option} <" if is_sel else option
        rendered = menu_hint_font.render(label, True, color)
        surf.blit(rendered, (WIDTH // 2 - rendered.get_width() // 2, option_y + i * spacing))

    hint = menu_font.render("Use as SETAS para escolher e ESPACO para confirmar", True, (170, 170, 185))
    surf.blit(hint, (WIDTH // 2 - hint.get_width() // 2, option_y + len(MENU_OPTIONS) * spacing + 24))

    coins_text = menu_font.render(f"Moedas: {profile.obter_moedas()}", True, (255, 215, 0))
    surf.blit(coins_text, (WIDTH // 2 - coins_text.get_width() // 2, 180))

    desenhar_icone_loja(surf, now_ms, loja_hover)
    desenhar_icone_inventario(surf, now_ms, inv_hover)


def desenhar_creditos(surf, now_ms):
    desenhar_fundo_retro(surf, now_ms)
    title = big_font.render("CREDITOS", True, (0, 220, 255))
    surf.blit(title, (WIDTH // 2 - title.get_width() // 2, 70))

    lines = [
        "Criacao: Felipe Voigt Postai",
        "",
        "Jogo desenvolvido em Python + Pygame",
        "Baseado no classico Arkanoid / Breakout",
        "",
        "Controles: SETAS ou A / D para mover a raquete",
        "ESPACO lanca a bola e confirma opcoes do menu",
        "",
        "W = raquete larga   M = multi-bola   S = bola lenta   C = canhoes",
        "Colete moedas na rodada bonus e gaste na LOJA do menu principal",
        "F11 alterna tela cheia",
        "",
        "Trabalho AV2 - Linguagens - Uniasselvi",
    ]
    y = 160
    for line in lines:
        if line:
            rendered = menu_font.render(line, True, WHITE)
            surf.blit(rendered, (WIDTH // 2 - rendered.get_width() // 2, y))
        y += 30

    hint = menu_font.render("Pressione ESPACO ou ESC para voltar", True, (120, 230, 90))
    surf.blit(hint, (WIDTH // 2 - hint.get_width() // 2, y + 16))


RANK_TAGS = {
    0: ("#1 RANKING MUNDIAL", (255, 215, 0)),
    1: ("#2 TOP MUNDIAL", (210, 210, 225)),
    2: ("#3 TOP MUNDIAL", (205, 140, 70)),
    3: ("#4 TOP MUNDIAL", (120, 200, 255)),
    4: ("#5 TOP MUNDIAL", (150, 230, 150)),
}


def desenhar_ranking(surf, now_ms):
    desenhar_fundo_retro(surf, now_ms)
    title = big_font.render("TOP PLACARES", True, (0, 220, 255))
    surf.blit(title, (WIDTH // 2 - title.get_width() // 2, 70))

    status = leaderboard.obter_status_ranking()
    row_x = WIDTH // 2 - 260
    y = 150
    if status in ("idle", "loading"):
        msg = menu_font.render("Carregando...", True, WHITE)
        surf.blit(msg, (WIDTH // 2 - msg.get_width() // 2, y))
    elif status == "error":
        msg = menu_font.render("Nao foi possivel carregar (sem internet?)", True, (255, 120, 120))
        surf.blit(msg, (WIDTH // 2 - msg.get_width() // 2, y))
    else:
        entries = leaderboard.obter_entradas_ranking()
        if not entries:
            msg = menu_font.render("Nenhuma pontuacao registrada ainda.", True, WHITE)
            surf.blit(msg, (WIDTH // 2 - msg.get_width() // 2, y))
        else:
            for i, (name, score) in enumerate(entries):
                color = (255, 230, 60) if i == 0 else (210, 210, 220)
                line = f"{i + 1:>2}. {name:<12} {score:>6} pts"
                rendered = menu_font.render(line, True, color)
                surf.blit(rendered, (row_x, y + i * 32))
                if i in RANK_TAGS:
                    tag_text, tag_color = RANK_TAGS[i]
                    tag_rendered = status_font.render(tag_text, True, tag_color)
                    surf.blit(tag_rendered, (row_x + rendered.get_width() + 16, y + i * 32 + 3))

    hint = menu_font.render("Pressione ESPACO ou ESC para voltar", True, (120, 230, 90))
    surf.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 80))

    if profile.obter_nome_jogador():
        rename_hint = menu_font.render("N para mudar seu nome no ranking", True, (170, 170, 185))
        surf.blit(rename_hint, (WIDTH // 2 - rename_hint.get_width() // 2, HEIGHT - 54))

    rename_status_msgs = {
        "sending": ("Atualizando nome...", (200, 200, 120)),
        "ok": ("Nome atualizado!", (120, 230, 90)),
        "error": ("Falha ao atualizar (sem internet?)", (255, 120, 120)),
    }
    sub_status = leaderboard.obter_status_envio()
    if sub_status in rename_status_msgs:
        text_line, color_line = rename_status_msgs[sub_status]
        rendered = menu_font.render(text_line, True, color_line)
        surf.blit(rendered, (WIDTH // 2 - rendered.get_width() // 2, HEIGHT - 28))


def _quebrar_texto(text, font_obj, max_width):
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if font_obj.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


_loja_bg_cache = None


def _criar_fundo_loja():
    """Cenario proprio da loja: ceu roxo-noturno + fileira de barracas de
    feira com toldos listrados. Diferente de proposito do skyline do menu,
    pra loja parecer um lugar a parte, nao so um menu com uma caixa em cima."""
    bg = pygame.Surface((WIDTH, HEIGHT))
    top_color = (24, 14, 36)
    bottom_color = (8, 4, 14)
    for y in range(HEIGHT):
        t = y / HEIGHT
        color = tuple(int(top_color[i] * (1 - t) + bottom_color[i] * t) for i in range(3))
        pygame.draw.line(bg, color, (0, y), (WIDTH, y))

    rng = random.Random(55)
    for _ in range(90):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, HEIGHT - 130)
        size = rng.choice([1, 1, 2])
        c = rng.choice([(255, 215, 0), (255, 235, 150), (255, 255, 255)])
        pygame.draw.rect(bg, c, (x, y, size, size))

    rng2 = random.Random(21)
    stall_colors = [(150, 50, 50), (50, 90, 150), (60, 140, 70), (150, 110, 40)]
    stall_top = HEIGHT - 110
    x = 0
    while x < WIDTH:
        w = rng2.randint(70, 110)
        color = rng2.choice(stall_colors)
        stripe_w = 10
        sx = x
        stripe_idx = 0
        while sx < x + w:
            c = color if stripe_idx % 2 == 0 else (245, 240, 230)
            pygame.draw.polygon(bg, c, [(sx, stall_top), (sx + stripe_w, stall_top),
                                        (sx + stripe_w + 6, stall_top + 16), (sx - 6 + stripe_w, stall_top + 16)])
            sx += stripe_w
            stripe_idx += 1
        pygame.draw.rect(bg, (40, 30, 35), (x, stall_top + 16, w, HEIGHT - (stall_top + 16)))
        x += w + 6
    return bg


def desenhar_fundo_loja(surf, now_ms):
    global _loja_bg_cache
    if _loja_bg_cache is None:
        _loja_bg_cache = _criar_fundo_loja()
    surf.blit(_loja_bg_cache, (0, 0))


LOJA_CATEGORIAS = [("bolas", "BOLAS"), ("raquetes", "RAQUETES"), ("pocoes", "POCOES")]
INVENTARIO_CATEGORIAS = [("bolas", "BOLAS"), ("raquetes", "RAQUETES"), ("pocoes", "POCAO")]
LOJA_CONTENT_TOP = 150


def _desenhar_icone_moeda(surf, cx, cy, r=7):
    pygame.draw.circle(surf, (255, 215, 0), (cx, cy), r)
    pygame.draw.circle(surf, (170, 130, 0), (cx, cy), r, width=1)


def obter_retangulo_fechar_loja():
    return pygame.Rect(WIDTH - 54, 18, 36, 36)


def _obter_retangulos_abas(categorias):
    """Largura de cada aba calculada a partir do texto real (+ preenchimento),
    pra nunca estourar a caixa independente da fonte do sistema."""
    pad_x, gap, tab_h, ty = 20, 14, 42, 84
    widths = [menu_hint_font.size(label)[0] + pad_x * 2 for _, label in categorias]
    total_w = sum(widths) + gap * (len(widths) - 1)
    tx = WIDTH // 2 - total_w // 2
    rects = {}
    for (cat_id, _), w in zip(categorias, widths):
        rects[cat_id] = pygame.Rect(tx, ty, w, tab_h)
        tx += w + gap
    return rects


def obter_retangulos_abas_loja():
    return _obter_retangulos_abas(LOJA_CATEGORIAS)


def obter_retangulos_abas_inventario():
    return _obter_retangulos_abas(INVENTARIO_CATEGORIAS)


def obter_retangulos_setas_loja():
    cy = LOJA_CONTENT_TOP + 95
    left = pygame.Rect(26, cy - 22, 36, 44)
    right = pygame.Rect(WIDTH - 62, cy - 22, 36, 44)
    return left, right


def _desenhar_botao_seta(surf, rect, direction):
    pygame.draw.rect(surf, (25, 20, 35), rect, border_radius=8)
    pygame.draw.rect(surf, (255, 215, 0), rect, width=2, border_radius=8)
    cx, cy = rect.center
    size = 8
    if direction == "left":
        pts = [(cx + size // 2, cy - size), (cx - size // 2, cy), (cx + size // 2, cy + size)]
    else:
        pts = [(cx - size // 2, cy - size), (cx + size // 2, cy), (cx - size // 2, cy + size)]
    pygame.draw.polygon(surf, (255, 215, 0), pts)


def desenhar_raio_secreto(surf, x, target_y, elapsed_ms):
    """Efeito de impacto do codigo secreto: um raio cai do topo da tela,
    crepitando, e atinge a raquete num flash - acompanha o desbloqueio da
    skin ultra-rara 'tempestade'."""
    progresso_queda = min(1.0, elapsed_ms / RAIO_SECRETO_QUEDA_MS)
    topo_y = -20
    fundo_y = topo_y + (target_y - topo_y) * progresso_queda

    segments = 9
    pts = [(x, topo_y)]
    seed = (int(elapsed_ms // 40) * 2654435761 + 1) & 0x7fffffff
    for s in range(1, segments + 1):
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        jitter = (seed % 41) - 20
        py = topo_y + (fundo_y - topo_y) * s / segments
        pts.append((x + jitter, py))

    glow = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    pygame.draw.lines(glow, (160, 200, 255, 110), False, pts, 10)
    surf.blit(glow, (0, 0))
    pygame.draw.lines(surf, (235, 245, 255), False, pts, 3)

    if elapsed_ms >= RAIO_SECRETO_QUEDA_MS:
        janela = max(1, RAIO_SECRETO_DURACAO_MS - RAIO_SECRETO_QUEDA_MS)
        flash_progresso = max(0.0, min(1.0, (elapsed_ms - RAIO_SECRETO_QUEDA_MS) / janela))
        flash_r = int(70 * (1 - flash_progresso)) + 10
        alpha = int(220 * (1 - flash_progresso))
        if alpha > 0:
            flash = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash, (235, 245, 255, alpha), (flash_r, flash_r), flash_r)
            surf.blit(flash, (x - flash_r, target_y - flash_r))


_MOCHILA_ICON_W, _MOCHILA_ICON_H = 26, 28


def obter_retangulo_icone_inventario():
    """Retangulo clicavel do mini-icone da mochila, canto superior direito do
    menu - espelha o icone da loja no canto esquerdo."""
    return pygame.Rect(WIDTH - 14 - _MOCHILA_ICON_W, 14, _MOCHILA_ICON_W, _MOCHILA_ICON_H)


def _renderizar_superficie_icone_inventario():
    """Mini mochila (aba + corpo + bolso + alcas), no mesmo espirito pixelado
    da barraquinha da loja."""
    w, h = _MOCHILA_ICON_W, _MOCHILA_ICON_H
    icon = pygame.Surface((w, h), pygame.SRCALPHA)

    pygame.draw.line(icon, (90, 60, 35), (w * 0.5 - 5, 4), (w * 0.5 - 5, 0), 2)
    pygame.draw.line(icon, (90, 60, 35), (w * 0.5 + 5, 4), (w * 0.5 + 5, 0), 2)

    flap_rect = pygame.Rect(4, 3, w - 8, 9)
    pygame.draw.rect(icon, (150, 100, 60), flap_rect, border_radius=4)
    pygame.draw.rect(icon, BLACK, flap_rect, width=1, border_radius=4)

    body_rect = pygame.Rect(3, 9, w - 6, h - 10)
    pygame.draw.rect(icon, (170, 115, 70), body_rect, border_radius=6)
    pygame.draw.rect(icon, BLACK, body_rect, width=1, border_radius=6)

    pocket_rect = pygame.Rect(body_rect.x + 5, body_rect.y + body_rect.height - 11, body_rect.width - 10, 9)
    pygame.draw.rect(icon, (140, 92, 55), pocket_rect, border_radius=3)
    pygame.draw.rect(icon, BLACK, pocket_rect, width=1, border_radius=3)
    return icon


def desenhar_icone_inventario(surf, now_ms, hover=False):
    """Icone da mochila no canto superior direito - mesmo zoom leve no hover
    usado no icone da loja, so que com o rotulo aparecendo pra esquerda (pra
    nao vazar pra fora da tela)."""
    rect = obter_retangulo_icone_inventario()
    icon = _renderizar_superficie_icone_inventario()
    if hover:
        icon = pygame.transform.smoothscale(icon, (int(_MOCHILA_ICON_W * 1.18), int(_MOCHILA_ICON_H * 1.18)))
    draw_rect = icon.get_rect(center=rect.center)
    surf.blit(icon, draw_rect.topleft)

    if hover:
        label = status_font.render("Mochila", True, WHITE)
        label_bg = pygame.Rect(0, 0, label.get_width() + 8, label.get_height() + 4)
        label_bg.midright = (rect.left - 8, rect.centery)
        pygame.draw.rect(surf, (20, 18, 30), label_bg, border_radius=5)
        surf.blit(label, (label_bg.x + 4, label_bg.y + 2))


def obter_itens_possuidos(categoria):
    """Skins que o jogador ja possui numa categoria ('bolas'/'raquetes'), na
    ordem da loja + a raquete ultra-rara 'tempestade' no final, se ja foi
    conquistada (ela nunca aparece em PADDLE_SKIN_ORDER)."""
    if categoria == "bolas":
        return [sid for sid in skins.BALL_SKIN_ORDER if profile.possui_skin_bola(sid)]
    itens = [sid for sid in skins.PADDLE_SKIN_ORDER if profile.possui_skin_raquete(sid)]
    if profile.possui_skin_raquete("tempestade"):
        itens.append("tempestade")
    return itens


def _desenhar_card_pocao_inventario(surf, top_y, now_ms):
    card_w, card_h = 340, 260
    rect = pygame.Rect(0, 0, card_w, card_h)
    rect.centerx = WIDTH // 2
    rect.top = top_y

    card_bg = pygame.Surface(rect.size, pygame.SRCALPHA)
    card_bg.fill((45, 30, 55, 230))
    surf.blit(card_bg, rect.topleft)
    pygame.draw.rect(surf, (255, 100, 200), rect, width=3, border_radius=14)

    skins.desenhar_icone_pocao(surf, rect.centerx, rect.y + 68, now_ms, scale=2.0)

    y = rect.y + 122
    for line in _quebrar_texto(skins.POTION_NOME, menu_font, rect.width - 40):
        rendered = menu_font.render(line, True, (255, 230, 60))
        surf.blit(rendered, (rect.centerx - rendered.get_width() // 2, y))
        y += 26

    y += 6
    for line in _quebrar_texto(skins.POTION_DESC, status_font, rect.width - 40):
        rendered = status_font.render(line, True, (210, 210, 220))
        surf.blit(rendered, (rect.centerx - rendered.get_width() // 2, y))
        y += 20

    qtd_text = status_font.render(f"Voce tem: {profile.obter_pocoes()}", True, (255, 215, 0))
    surf.blit(qtd_text, (rect.centerx - qtd_text.get_width() // 2, y + 10))


def desenhar_inventario(surf, now_ms, categoria, idx, mensagem="", mensagem_until=0):
    """Tela propria (fora da loja) com tudo que o jogador ja possui - bolas,
    raquetes (incluindo a ultra-rara 'tempestade', se conquistada) e poções.
    Selecionar um item e apertar ESPACO equipa ele; selecionar 'Padrao' e
    equipar e a forma de 'desequipar' e voltar ao visual padrao."""
    desenhar_fundo_loja(surf, now_ms)

    title = big_font.render("MOCHILA", True, (255, 215, 0))
    banner = pygame.Rect(0, 0, title.get_width() + 70, 48)
    banner.centerx = WIDTH // 2
    banner.top = 14
    pygame.draw.rect(surf, (40, 30, 55), banner, border_radius=10)
    pygame.draw.rect(surf, (255, 215, 0), banner, width=2, border_radius=10)
    surf.blit(title, (banner.centerx - title.get_width() // 2, banner.centery - title.get_height() // 2))

    close_rect = obter_retangulo_fechar_loja()
    pygame.draw.circle(surf, (50, 18, 22), close_rect.center, close_rect.width // 2)
    pygame.draw.circle(surf, (255, 100, 100), close_rect.center, close_rect.width // 2, width=2)
    x_label = menu_hint_font.render("X", True, (255, 160, 160))
    surf.blit(x_label, (close_rect.centerx - x_label.get_width() // 2, close_rect.centery - x_label.get_height() // 2))

    tab_rects = obter_retangulos_abas_inventario()
    for cat_id, label in INVENTARIO_CATEGORIAS:
        rect = tab_rects[cat_id]
        is_sel = cat_id == categoria
        bg = (255, 215, 0) if is_sel else (25, 20, 35)
        pygame.draw.rect(surf, bg, rect, border_radius=10)
        pygame.draw.rect(surf, BLACK if is_sel else (255, 215, 0), rect, width=2, border_radius=10)
        color = BLACK if is_sel else (210, 210, 220)
        rendered = menu_hint_font.render(label, True, color)
        surf.blit(rendered, (rect.centerx - rendered.get_width() // 2, rect.centery - rendered.get_height() // 2))

    content_top = LOJA_CONTENT_TOP
    if categoria == "pocoes":
        _desenhar_card_pocao_inventario(surf, content_top, now_ms)
    else:
        ordem = obter_itens_possuidos(categoria)
        if not ordem:
            msg = menu_font.render("Nada guardado ainda - visite a loja!", True, (170, 170, 185))
            surf.blit(msg, (WIDTH // 2 - msg.get_width() // 2, content_top + 40))
        else:
            catalogo = skins.BALL_SKINS if categoria == "bolas" else skins.PADDLE_SKINS
            owned_fn = (lambda sid: True)
            equipped_fn = (profile.obter_skin_bola_equipada if categoria == "bolas"
                           else profile.obter_skin_raquete_equipada)
            idx = idx % len(ordem)
            _desenhar_cards_loja(surf, content_top, now_ms, categoria, ordem, catalogo, idx, owned_fn, equipped_fn)

            left_arrow, right_arrow = obter_retangulos_setas_loja()
            _desenhar_botao_seta(surf, left_arrow, "left")
            _desenhar_botao_seta(surf, right_arrow, "right")

    if mensagem and now_ms < mensagem_until:
        msg_rendered = menu_font.render(mensagem, True, (255, 230, 60))
        surf.blit(msg_rendered, (WIDTH // 2 - msg_rendered.get_width() // 2, HEIGHT - 86))

    if categoria == "pocoes":
        hint_txt = "ESC/X: volta"
    else:
        hint_txt = "SETAS/MOUSE: navega   ESPACO: equipa   ESC/X: volta"
    hint = menu_font.render(hint_txt, True, (210, 210, 220))
    surf.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 36))


def _desenhar_cards_loja(surf, top_y, now_ms, categoria, ordem, catalogo, idx, owned_fn, equipped_fn):
    n = len(ordem)
    gap = 20
    max_total_w = WIDTH - 60
    card_w = min(155, (max_total_w - gap * (n - 1)) // n)
    card_h = 190
    total_w = card_w * n + gap * (n - 1)
    start_x = WIDTH // 2 - total_w // 2
    equipada = equipped_fn()

    for i, skin_id in enumerate(ordem):
        info = catalogo[skin_id]
        rect = pygame.Rect(start_x + i * (card_w + gap), top_y, card_w, card_h)
        is_sel = i == idx
        is_owned = owned_fn(skin_id)
        is_equipped = skin_id == equipada

        card_bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        card_bg.fill((55, 45, 20, 230) if is_sel else (35, 30, 50, 220))
        surf.blit(card_bg, rect.topleft)
        border_color = (255, 215, 0) if is_sel else ((120, 230, 90) if is_equipped else (100, 95, 120))
        pygame.draw.rect(surf, border_color, rect, width=3 if is_sel else 2, border_radius=12)

        preview_cy = rect.y + 56
        if categoria == "bolas":
            skins.desenhar_bola(surf, rect.centerx, preview_cy, 24, skin_id, now_ms)
        else:
            prect = pygame.Rect(0, 0, 104, 18)
            prect.center = (rect.centerx, preview_cy)
            skins.desenhar_raquete(surf, prect, skin_id, now_ms)

        name_rendered = status_font.render(info["nome"], True, WHITE)
        surf.blit(name_rendered, (rect.centerx - name_rendered.get_width() // 2, rect.y + 100))

        status_y = rect.y + 136
        if is_equipped:
            status_rendered = status_font.render("EQUIPADA", True, (120, 230, 90))
            surf.blit(status_rendered, (rect.centerx - status_rendered.get_width() // 2, rect.y + 130))
        elif is_owned:
            status_rendered = status_font.render("COMPRADA", True, (170, 200, 230))
            surf.blit(status_rendered, (rect.centerx - status_rendered.get_width() // 2, rect.y + 130))
        else:
            price_rendered = status_font.render(str(info["preco"]), True, (255, 215, 0))
            block_w = price_rendered.get_width() + 18
            block_x = rect.centerx - block_w // 2
            _desenhar_icone_moeda(surf, block_x + 7, status_y, r=7)
            surf.blit(price_rendered, (block_x + 18, status_y - price_rendered.get_height() // 2))

        if is_sel:
            arrow = menu_font.render("^", True, (255, 215, 0))
            surf.blit(arrow, (rect.centerx - arrow.get_width() // 2, rect.bottom + 2))


def _desenhar_card_pocao(surf, top_y, now_ms):
    card_w, card_h = 340, 320
    rect = pygame.Rect(0, 0, card_w, card_h)
    rect.centerx = WIDTH // 2
    rect.top = top_y

    card_bg = pygame.Surface(rect.size, pygame.SRCALPHA)
    card_bg.fill((45, 30, 55, 230))
    surf.blit(card_bg, rect.topleft)
    pygame.draw.rect(surf, (255, 100, 200), rect, width=3, border_radius=14)

    skins.desenhar_icone_pocao(surf, rect.centerx, rect.y + 68, now_ms, scale=2.0)

    y = rect.y + 122
    for line in _quebrar_texto(skins.POTION_NOME, menu_font, rect.width - 40):
        rendered = menu_font.render(line, True, (255, 230, 60))
        surf.blit(rendered, (rect.centerx - rendered.get_width() // 2, y))
        y += 26

    y += 10
    for line in _quebrar_texto(skins.POTION_DESC, menu_font, rect.width - 40):
        rendered = menu_font.render(line, True, WHITE)
        surf.blit(rendered, (rect.centerx - rendered.get_width() // 2, y))
        y += 24

    preco_text = status_font.render(f"{skins.POTION_PRECO} moedas - voce tem {profile.obter_pocoes()}",
                                     True, (255, 215, 0))
    surf.blit(preco_text, (rect.centerx - preco_text.get_width() // 2, y + 10))


def desenhar_loja(surf, now_ms, categoria, idx, mensagem="", mensagem_until=0):
    desenhar_fundo_loja(surf, now_ms)

    title = big_font.render("LOJA", True, (255, 215, 0))
    banner = pygame.Rect(0, 0, title.get_width() + 70, 48)
    banner.centerx = WIDTH // 2
    banner.top = 14
    pygame.draw.rect(surf, (40, 30, 55), banner, border_radius=10)
    pygame.draw.rect(surf, (255, 215, 0), banner, width=2, border_radius=10)
    surf.blit(title, (banner.centerx - title.get_width() // 2, banner.centery - title.get_height() // 2))

    coin_text = menu_font.render(str(profile.obter_moedas()), True, (255, 215, 0))
    coin_badge = pygame.Rect(16, 20, coin_text.get_width() + 46, 36)
    pygame.draw.rect(surf, (30, 24, 10), coin_badge, border_radius=18)
    pygame.draw.rect(surf, (255, 215, 0), coin_badge, width=2, border_radius=18)
    _desenhar_icone_moeda(surf, coin_badge.x + 20, coin_badge.centery)
    surf.blit(coin_text, (coin_badge.x + 34, coin_badge.centery - coin_text.get_height() // 2))

    close_rect = obter_retangulo_fechar_loja()
    pygame.draw.circle(surf, (50, 18, 22), close_rect.center, close_rect.width // 2)
    pygame.draw.circle(surf, (255, 100, 100), close_rect.center, close_rect.width // 2, width=2)
    x_label = menu_hint_font.render("X", True, (255, 160, 160))
    surf.blit(x_label, (close_rect.centerx - x_label.get_width() // 2, close_rect.centery - x_label.get_height() // 2))

    tab_rects = obter_retangulos_abas_loja()
    for cat_id, label in LOJA_CATEGORIAS:
        rect = tab_rects[cat_id]
        is_sel = cat_id == categoria
        bg = (255, 215, 0) if is_sel else (25, 20, 35)
        pygame.draw.rect(surf, bg, rect, border_radius=10)
        pygame.draw.rect(surf, BLACK if is_sel else (255, 215, 0), rect, width=2, border_radius=10)
        color = BLACK if is_sel else (210, 210, 220)
        rendered = menu_hint_font.render(label, True, color)
        surf.blit(rendered, (rect.centerx - rendered.get_width() // 2, rect.centery - rendered.get_height() // 2))

    content_top = LOJA_CONTENT_TOP
    if categoria == "pocoes":
        _desenhar_card_pocao(surf, content_top, now_ms)
    else:
        if categoria == "bolas":
            ordem, catalogo = skins.BALL_SKIN_ORDER, skins.BALL_SKINS
            owned_fn, equipped_fn = profile.possui_skin_bola, profile.obter_skin_bola_equipada
        else:
            ordem, catalogo = skins.PADDLE_SKIN_ORDER, skins.PADDLE_SKINS
            owned_fn, equipped_fn = profile.possui_skin_raquete, profile.obter_skin_raquete_equipada
        _desenhar_cards_loja(surf, content_top, now_ms, categoria, ordem, catalogo, idx, owned_fn, equipped_fn)

        left_arrow, right_arrow = obter_retangulos_setas_loja()
        _desenhar_botao_seta(surf, left_arrow, "left")
        _desenhar_botao_seta(surf, right_arrow, "right")

    if mensagem and now_ms < mensagem_until:
        msg_rendered = menu_font.render(mensagem, True, (255, 230, 60))
        surf.blit(msg_rendered, (WIDTH // 2 - msg_rendered.get_width() // 2, HEIGHT - 86))

    hint = menu_font.render("SETAS/MOUSE: navega   ESPACO: compra/equipa   ESC/X: volta", True, (210, 210, 220))
    surf.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 36))


def desenhar_oferta_pocao(surf, potions_left):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    surf.blit(overlay, (0, 0))

    title = big_font.render("ULTIMA VIDA PERDIDA!", True, (255, 80, 80))
    surf.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 110))

    prompt = font.render(f"Usar {skins.POTION_NOME}? (restam {potions_left})", True, WHITE)
    surf.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT // 2 - 40))

    hint = menu_hint_font.render("S: Sim, continuar com 1 vida   -   N: Nao", True, (170, 170, 185))
    surf.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 20))


def desenhar_notificacao(surf, texto):
    """Banner curto no topo da tela, usado p.ex. pro aviso de codigo secreto.
    Funciona por cima de qualquer tela (menu ou jogo). Quebra em varias linhas
    se o texto nao couber na largura da tela."""
    max_w = WIDTH - 60
    palavras = texto.split(" ")
    linhas = []
    linha_atual = ""
    for palavra in palavras:
        candidata = f"{linha_atual} {palavra}".strip()
        if menu_hint_font.size(candidata)[0] <= max_w or not linha_atual:
            linha_atual = candidata
        else:
            linhas.append(linha_atual)
            linha_atual = palavra
    if linha_atual:
        linhas.append(linha_atual)

    rendereds = [menu_hint_font.render(linha, True, (255, 230, 60)) for linha in linhas]
    largura = max(r.get_width() for r in rendereds)
    altura_linha = rendereds[0].get_height()
    box = pygame.Rect(0, 0, largura + 40, altura_linha * len(rendereds) + 20)
    box.centerx = WIDTH // 2
    box.top = 90
    bg = pygame.Surface(box.size, pygame.SRCALPHA)
    bg.fill((20, 15, 35, 220))
    surf.blit(bg, box.topleft)
    pygame.draw.rect(surf, (190, 100, 255), box, width=2, border_radius=10)
    for i, rendered in enumerate(rendereds):
        y = box.top + 10 + i * altura_linha
        surf.blit(rendered, (box.centerx - rendered.get_width() // 2, y))


def desenhar_cronometro_powerup(surf, label, until_ticks, now, color, y):
    """Desenha a contagem regressiva de um power-up ativo e retorna o próximo y livre."""
    secs_left = (until_ticks - now + 999) // 1000
    txt = status_font.render(f"{label}: {secs_left}s", True, color)
    surf.blit(txt, (20, y))
    return y - 26


def desenhar_entrada_nome(surf, name, title="ENTROU NO TOP 100!", title_color=(255, 215, 0),
                           prompt="Digite seu nome para o ranking:"):
    """Tela pra digitar/corrigir o nome usado no ranking - tanto no primeiro
    ingresso no Top 100 quanto ao renomear depois, pela tela de ranking."""
    msg = big_font.render(title, True, title_color)
    surf.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 100))

    prompt_text = font.render(prompt, True, WHITE)
    surf.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, HEIGHT // 2 - 40))

    box = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2, 280, 40)
    pygame.draw.rect(surf, (30, 30, 40), box, border_radius=6)
    pygame.draw.rect(surf, (0, 220, 255), box, width=2, border_radius=6)
    name_text = font.render(name + "_", True, WHITE)
    surf.blit(name_text, (box.x + 10, box.y + 5))

    hint = menu_font.render("ENTER confirma   -   ESC cancela", True, (170, 170, 185))
    surf.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 60))


def desenhar_mensagem_fim(surf, text, color, rank_phase=None, skin_revelada=None, now_ms=0):
    if skin_revelada:
        info = skins.PADDLE_SKINS[skin_revelada]
        desc_lines = _quebrar_texto(info["desc"], menu_hint_font, 400)
        banner = pygame.Rect(0, 0, 460, 128 + 20 * len(desc_lines))
        banner.centerx = WIDTH // 2
        banner.bottom = HEIGHT // 2 - 60
        bg = pygame.Surface(banner.size, pygame.SRCALPHA)
        bg.fill((40, 20, 55, 235))
        surf.blit(bg, banner.topleft)
        pygame.draw.rect(surf, (255, 215, 0), banner, width=3, border_radius=14)

        titulo = font.render("SKIN LENDARIA DESBLOQUEADA!", True, (255, 215, 0))
        surf.blit(titulo, (banner.centerx - titulo.get_width() // 2, banner.y + 10))

        prect = pygame.Rect(0, 0, 140, 22)
        prect.center = (banner.centerx, banner.y + 60)
        skins.desenhar_raquete(surf, prect, skin_revelada, now_ms)

        nome = status_font.render(info["nome"], True, (255, 230, 150))
        surf.blit(nome, (banner.centerx - nome.get_width() // 2, banner.y + 88))

        y = banner.y + 110
        for line in desc_lines:
            desc = menu_hint_font.render(line, True, (210, 210, 220))
            surf.blit(desc, (banner.centerx - desc.get_width() // 2, y))
            y += 20

    msg = big_font.render(text, True, color)
    surf.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 40))

    status_by_phase = {
        "checking": ("Verificando ranking...", (200, 200, 120)),
        "submitting": ("Enviando ao ranking...", (200, 200, 120)),
        "submitted_ok": ("Pontuacao registrada no ranking!", (120, 230, 90)),
        "submitted_error": ("Falha ao enviar ao ranking (sem internet?)", (255, 120, 120)),
        "not_top100": ("Pontuacao nao entrou no Top 100.", (170, 170, 185)),
        "not_personal_best": ("Pontuacao nao superou seu recorde no ranking.", (170, 170, 185)),
        "skipped": ("Envio ao ranking pulado.", (170, 170, 185)),
        "error": ("Nao foi possivel verificar o ranking.", (255, 120, 120)),
    }
    sub_y = HEIGHT // 2 + 20
    if rank_phase in status_by_phase:
        text_line, color_line = status_by_phase[rank_phase]
        st = font.render(text_line, True, color_line)
        surf.blit(st, (WIDTH // 2 - st.get_width() // 2, sub_y))
        sub_y += 34

    sub = font.render("Pressione R pra voltar ao menu", True, WHITE)
    surf.blit(sub, (WIDTH // 2 - sub.get_width() // 2, sub_y))


def desenhar_nivel_completo(surf, level, bonus_gain=0):
    """Overlay rapido de transicao mostrado entre um nivel e o proximo. Se vem
    logo apos uma rodada bonus (bonus_gain > 0), mostra o total de moedas
    pontuadas em vez do aviso de nivel completo."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surf.blit(overlay, (0, 0))
    if bonus_gain > 0:
        msg = big_font.render(f"BONUS CONCLUIDO! +{bonus_gain} PONTOS", True, (255, 215, 0))
    else:
        msg = big_font.render(f"NIVEL {level} COMPLETO!", True, (120, 230, 90))
    sub = font.render("Preparando o proximo nivel...", True, WHITE)
    surf.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 30))
    surf.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 30))


def obter_retangulos_menu_pausa():
    """Mesma ideia de obter_retangulos_menu(), mas pro menu de pausa - o item
    VOLUME mostra uma porcentagem, entao usa uma largura generosa fixa pra
    cobrir qualquer valor de 0 a 100%."""
    option_y, spacing = 230, 48
    text_h = menu_hint_font.get_height()
    rects = {}
    for i, option in enumerate(PAUSE_OPTIONS):
        if option == "VOLUME":
            w = max(menu_hint_font.size("VOLUME: 100%")[0], menu_hint_font.size("< VOLUME: 100% >")[0])
        else:
            w = max(menu_hint_font.size(option)[0], menu_hint_font.size(f"> {option} <")[0])
        rect = pygame.Rect(0, option_y + i * spacing - 4, w + 24, text_h + 8)
        rect.centerx = WIDTH // 2
        rects[i] = rect
    return rects


def desenhar_menu_pausa(surf, now_ms, selected, volume):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    surf.blit(overlay, (0, 0))

    title = big_font.render("PAUSADO", True, (255, 230, 60))
    surf.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))

    option_y = 230
    spacing = 48
    for i, option in enumerate(PAUSE_OPTIONS):
        is_sel = i == selected
        color = (255, 230, 60) if is_sel else (210, 210, 220)
        if option == "VOLUME":
            pct = int(round(volume * 100))
            label = f"< VOLUME: {pct}% >" if is_sel else f"VOLUME: {pct}%"
        else:
            label = f"> {option} <" if is_sel else option
        rendered = menu_hint_font.render(label, True, color)
        surf.blit(rendered, (WIDTH // 2 - rendered.get_width() // 2, option_y + i * spacing))

    hint = menu_font.render("P / ESC continua    SETAS navega    ESPACO confirma", True, (170, 170, 185))
    surf.blit(hint, (WIDTH // 2 - hint.get_width() // 2, option_y + len(PAUSE_OPTIONS) * spacing + 20))
