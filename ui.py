"""Telas e elementos de interface: icone da janela, fundos, menus, ranking,
overlays de transicao/pausa/fim de jogo."""
import math
import random
import pygame

import leaderboard
from fonts import font, big_font, status_font, title_font, menu_font, menu_hint_font
from constants import WIDTH, HEIGHT, WHITE, BLACK, POWERUP_COLORS, MENU_OPTIONS, PAUSE_OPTIONS

__all__ = [
    "build_icon_surface", "format_time", "draw_cannons",
    "draw_retro_background", "draw_starry_background",
    "draw_menu", "draw_credits", "draw_ranking",
    "draw_powerup_timer", "draw_name_entry", "draw_end_message",
    "draw_level_complete", "draw_pause_menu",
]


def build_icon_surface(size=64):
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


def format_time(ms):
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def draw_cannons(surf, paddle):
    """Desenha os dois canhoes nas pontas da raquete enquanto o power-up C esta ativo."""
    turret_w, turret_h = 10, 16
    left = pygame.Rect(int(paddle.x) - 2, paddle.y - turret_h + 4, turret_w, turret_h)
    right = pygame.Rect(int(paddle.x + paddle.width) - turret_w + 2, paddle.y - turret_h + 4, turret_w, turret_h)
    for r in (left, right):
        pygame.draw.rect(surf, POWERUP_COLORS["C"], r, border_radius=3)
        pygame.draw.rect(surf, BLACK, r, width=2, border_radius=3)


def draw_pulsing_title(surf, now_ms, center):
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


def _build_menu_background():
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

    def jagged_mountain(base_y, amplitude, color, seed, step=40):
        rng2 = random.Random(seed)
        pts = [(0, horizon_y)]
        x = 0
        while x <= WIDTH:
            pts.append((x, base_y - rng2.randint(0, amplitude)))
            x += step
        pts.append((WIDTH, horizon_y))
        pygame.draw.polygon(bg, color, pts)

    jagged_mountain(horizon_y - 40, 70, (26, 20, 58), 1)
    jagged_mountain(horizon_y - 8, 50, (16, 13, 42), 2)
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


def draw_retro_background(surf, now_ms):
    global _menu_bg_cache
    if _menu_bg_cache is None:
        _menu_bg_cache = _build_menu_background()
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


def _build_game_starfield():
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


def draw_starry_background(surf, now_ms):
    global _game_bg_cache
    if _game_bg_cache is None:
        _game_bg_cache = _build_game_starfield()
    bg, twinkle_stars = _game_bg_cache
    surf.blit(bg, (0, 0))
    t = now_ms / 1000.0
    for x, y, size, phase in twinkle_stars:
        tw = (math.sin(t * 2.2 + phase) + 1) / 2
        glow = pygame.Surface((size + 2, size + 2), pygame.SRCALPHA)
        glow.fill((255, 255, 255, int(90 + 160 * tw)))
        surf.blit(glow, (x, y))


def draw_menu(surf, now_ms, selected):
    draw_retro_background(surf, now_ms)
    draw_pulsing_title(surf, now_ms, (WIDTH // 2, 120))

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


def draw_credits(surf, now_ms):
    draw_retro_background(surf, now_ms)
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
        "V troca pontos por uma vida extra (se ja perdeu alguma)",
        "",
        "W = raquete larga   M = multi-bola   S = bola lenta   C = canhoes",
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


def draw_ranking(surf, now_ms):
    draw_retro_background(surf, now_ms)
    title = big_font.render("TOP PLACARES", True, (0, 220, 255))
    surf.blit(title, (WIDTH // 2 - title.get_width() // 2, 70))

    status = leaderboard.get_leaderboard_status()
    row_x = WIDTH // 2 - 260
    y = 150
    if status in ("idle", "loading"):
        msg = menu_font.render("Carregando...", True, WHITE)
        surf.blit(msg, (WIDTH // 2 - msg.get_width() // 2, y))
    elif status == "error":
        msg = menu_font.render("Nao foi possivel carregar (sem internet?)", True, (255, 120, 120))
        surf.blit(msg, (WIDTH // 2 - msg.get_width() // 2, y))
    else:
        entries = leaderboard.get_leaderboard_entries()
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

    if leaderboard.get_player_name():
        rename_hint = menu_font.render("N para mudar seu nome no ranking", True, (170, 170, 185))
        surf.blit(rename_hint, (WIDTH // 2 - rename_hint.get_width() // 2, HEIGHT - 54))

    rename_status_msgs = {
        "sending": ("Atualizando nome...", (200, 200, 120)),
        "ok": ("Nome atualizado!", (120, 230, 90)),
        "error": ("Falha ao atualizar (sem internet?)", (255, 120, 120)),
    }
    sub_status = leaderboard.get_rank_submit_status()
    if sub_status in rename_status_msgs:
        text_line, color_line = rename_status_msgs[sub_status]
        rendered = menu_font.render(text_line, True, color_line)
        surf.blit(rendered, (WIDTH // 2 - rendered.get_width() // 2, HEIGHT - 28))


def draw_powerup_timer(surf, label, until_ticks, now, color, y):
    """Desenha a contagem regressiva de um power-up ativo e retorna o próximo y livre."""
    secs_left = (until_ticks - now + 999) // 1000
    txt = status_font.render(f"{label}: {secs_left}s", True, color)
    surf.blit(txt, (20, y))
    return y - 26


def draw_name_entry(surf, name, title="ENTROU NO TOP 100!", title_color=(255, 215, 0),
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


def draw_end_message(surf, text, color, rank_phase=None):
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


def draw_level_complete(surf, level, bonus_gain=0):
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


def draw_pause_menu(surf, now_ms, selected, volume):
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
