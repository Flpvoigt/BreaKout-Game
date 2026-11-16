import pygame
import random
import sys
import math

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Breakout")
clock = pygame.time.Clock()
FPS = 60

# ---- Audio: todos os efeitos sonoros sao gerados programaticamente (sem arquivos externos) ----
try:
    import numpy as np
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "numpy"], check=False)
    try:
        import numpy as np
    except ImportError:
        np = None

sound_enabled = True
SOUNDS = {}
AUDIO_SAMPLE_RATE = 44100


def _tone_array(freq, duration_ms, volume=0.5, wave="sine", sample_rate=AUDIO_SAMPLE_RATE):
    """Gera um array numpy PCM16 mono curto com um tom simples (senoidal ou quadrada).
    So e chamada a partir de init_audio() apos a checagem `if np is None: return`,
    entao o numpy sempre esta disponivel aqui - o assert so informa isso ao Pylance."""
    assert np is not None
    n_samples = max(1, int(sample_rate * duration_ms / 1000))
    t = np.linspace(0, duration_ms / 1000.0, n_samples, endpoint=False)
    if wave == "square":
        data = np.sign(np.sin(2 * np.pi * freq * t))
    else:
        data = np.sin(2 * np.pi * freq * t)
    # envelope de fade-in/out pra evitar "cliques" nas bordas
    fade = max(1, min(n_samples // 4, int(sample_rate * 0.005)))
    envelope = np.ones(n_samples)
    envelope[:fade] = np.linspace(0, 1, fade)
    envelope[-fade:] = np.linspace(1, 0, fade)
    data = data * envelope * volume
    return (data * 32767).astype(np.int16)


def _sequence_array(notes):
    """Concatena varias notas (freq, duration_ms, volume, wave) num unico array."""
    assert np is not None
    pieces = [_tone_array(*note) for note in notes]
    return np.concatenate(pieces)


def init_audio():
    """Inicializa o mixer e constroi cada efeito sonoro na hora, via numpy.
    Se nao houver numpy ou dispositivo de audio disponivel, desativa o som
    silenciosamente (o jogo continua funcionando sem efeitos sonoros)."""
    global sound_enabled
    if np is None:
        sound_enabled = False
        return
    try:
        pygame.mixer.quit()
        pygame.mixer.init(frequency=AUDIO_SAMPLE_RATE, size=-16, channels=1)
    except Exception:
        sound_enabled = False
        return
    try:
        SOUNDS["hit_paddle"] = pygame.sndarray.make_sound(_tone_array(220, 70, 0.45, "square"))
        SOUNDS["hit_wall"] = pygame.sndarray.make_sound(_tone_array(150, 60, 0.35, "sine"))
        SOUNDS["brick_hit"] = pygame.sndarray.make_sound(_tone_array(320, 70, 0.35, "sine"))
        SOUNDS["brick_destroy"] = pygame.sndarray.make_sound(_sequence_array([
            (660, 50, 0.45, "square"), (990, 90, 0.5, "square"),
        ]))
        SOUNDS["powerup"] = pygame.sndarray.make_sound(_sequence_array([
            (500, 60, 0.4, "sine"), (750, 100, 0.45, "sine"),
        ]))
        SOUNDS["lose_life"] = pygame.sndarray.make_sound(_sequence_array([
            (400, 90, 0.4, "sine"), (240, 140, 0.4, "sine"),
        ]))
        SOUNDS["game_over"] = pygame.sndarray.make_sound(_sequence_array([
            (300, 150, 0.45, "square"), (220, 150, 0.45, "square"), (150, 220, 0.5, "square"),
        ]))
        SOUNDS["victory"] = pygame.sndarray.make_sound(_sequence_array([
            (523, 100, 0.45, "sine"), (659, 100, 0.45, "sine"), (784, 160, 0.5, "sine"),
        ]))
    except Exception:
        sound_enabled = False


_last_played_ms = {}
SOUND_THROTTLE_MS = 40  # evita "cacho" de som quando varios eventos batem no mesmo frame


def play_sound(name):
    if not sound_enabled:
        return
    now = pygame.time.get_ticks()
    if now - _last_played_ms.get(name, -SOUND_THROTTLE_MS) < SOUND_THROTTLE_MS:
        return
    snd = SOUNDS.get(name)
    if snd is not None:
        try:
            snd.play()
            _last_played_ms[name] = now
        except Exception:
            pass


init_audio()

WHITE = (255, 255, 255)
BLACK = (10, 10, 15)
PADDLE_COLOR = (0, 220, 255)
BALL_COLOR = (255, 255, 255)

BRICK_COLORS = [
    (255, 80, 80),
    (255, 160, 60),
    (255, 230, 60),
    (120, 230, 90),
    (80, 160, 255),
]

font = pygame.font.SysFont("consolas", 28)
big_font = pygame.font.SysFont("consolas", 48, bold=True)
powerup_font = pygame.font.SysFont("consolas", 20, bold=True)
score_font = pygame.font.SysFont("consolas", 34, bold=True)
status_font = pygame.font.SysFont("consolas", 20, bold=True)
title_font = pygame.font.SysFont("consolas", 76, bold=True)
menu_font = pygame.font.SysFont("consolas", 24)
menu_hint_font = pygame.font.SysFont("consolas", 26, bold=True)

SCORE_COLOR = (255, 215, 0)

# ---- Power-up tuning ----
POWERUP_DROP_CHANCE = 0.15
POWERUP_FALL_SPEED = 3
POWERUP_COLORS = {
    "W": (255, 160, 60),   # paddle larga - laranja
    "M": (160, 80, 220),   # multi-ball - roxo
    "S": (120, 200, 255),  # bola lenta - azul claro
}
WIDE_DURATION_MS = 8000
SLOW_DURATION_MS = 8000
SLOW_FACTOR = 0.55
MAX_BALLS = 9

# ---- Progressao de niveis ----
MAX_LEVEL = 5
LEVEL_TRANSITION_MS = 2500


class Paddle:
    def __init__(self):
        self.base_width = 110
        self.width = self.base_width
        self.height = 16
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - 40
        self.speed = 9

    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        self.x = max(0, min(WIDTH - self.width, self.x))

    def set_width(self, new_width):
        """Change width while keeping the paddle centered on the same spot."""
        if new_width == self.width:
            return
        center = self.x + self.width / 2
        self.width = new_width
        self.x = int(center - self.width / 2)
        self.x = max(0, min(WIDTH - self.width, self.x))

    def draw(self, surf):
        pygame.draw.rect(surf, PADDLE_COLOR, self.rect(), border_radius=8)


class Ball:
    def __init__(self):
        self.radius = 9
        self.trail = []
        self.reset()

    def reset(self):
        """Ball is born/reborn stuck on top of the paddle, not moving."""
        self.x = WIDTH // 2
        self.y = HEIGHT - 60
        self.vx = 0.0
        self.vy = 0.0
        self.stuck = True
        self.trail = []

    def launch(self, direction=None):
        if not self.stuck:
            return
        self.stuck = False
        if direction is not None and direction != 0:
            self.vx = 5 if direction > 0 else -5
        else:
            self.vx = random.choice([-5, 5])
        self.vy = -5

    def stick_to(self, paddle):
        self.x = paddle.x + paddle.width / 2
        self.y = paddle.y - self.radius - 1
        self.trail = []

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                            self.radius * 2, self.radius * 2)

    def update(self, speed_factor=1.0):
        if self.stuck:
            return
        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)
        self.x += self.vx * speed_factor
        self.y += self.vy * speed_factor

        if self.x - self.radius <= 0 or self.x + self.radius >= WIDTH:
            self.vx *= -1
            play_sound("hit_wall")
        if self.y - self.radius <= 0:
            self.vy *= -1
            play_sound("hit_wall")

    def draw(self, surf):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)) * 0.5)
            r = int(self.radius * (i / len(self.trail)))
            if r > 0:
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*BALL_COLOR, alpha), (r, r), r)
                surf.blit(s, (tx - r, ty - r))
        pygame.draw.circle(surf, BALL_COLOR, (int(self.x), int(self.y)), self.radius)


def spawn_extra_ball(source, vx_offset):
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


class Brick:
    def __init__(self, x, y, w, h, color, lives=1):
        self.rect = pygame.Rect(x, y, w, h)
        self.base_color = color
        self.color = color
        self.max_lives = max(1, lives)
        self.lives = self.max_lives
        self.alive = True

    def hit(self):
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

    def draw(self, surf):
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

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.life -= 1

    def draw(self, surf):
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

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h)

    def update(self):
        self.y += self.vy

    def draw(self, surf):
        r = self.rect()
        pygame.draw.rect(surf, self.color, r, border_radius=6)
        pygame.draw.rect(surf, BLACK, r, width=2, border_radius=6)
        label = powerup_font.render(self.kind, True, BLACK)
        surf.blit(label, (r.centerx - label.get_width() // 2, r.centery - label.get_height() // 2))


def make_bricks(level=1):
    """Monta o grid de tijolos. Linhas mais perto do topo quebram com 1 batida;
    linhas mais perto da raquete precisam de mais batidas, ate um maximo de 3.
    Conforme o nivel sobe, o grid cresce (mais linhas), mas o teto de vida por
    tijolo continua fixo em 3."""
    bricks = []
    rows = min(5 + (level - 1) // 2, 8)
    cols = 10
    padding = 6
    offset_top = 60
    offset_side = 20
    brick_w = (WIDTH - offset_side * 2 - padding * (cols - 1)) // cols
    brick_h = 24

    # limites das "faixas" de vida: primeiros ~40% das linhas = 1 vida,
    # ate ~80% = 2 vidas, resto (mais perto da raquete) = 3 vidas.
    # Para o grid padrao de 5 linhas isso da exatamente: linha 0-1=1, 2-3=2, 4=3.
    boundary_1 = round(rows * 0.4)
    boundary_2 = round(rows * 0.8)

    for row in range(rows):
        if row < boundary_1:
            lives = 1
        elif row < boundary_2:
            lives = 2
        else:
            lives = 3  # maximo de 3 toques de vida, fixo, independente do nivel
        for col in range(cols):
            x = offset_side + col * (brick_w + padding)
            y = offset_top + row * (brick_h + padding)
            bricks.append(Brick(x, y, brick_w, brick_h, BRICK_COLORS[row % len(BRICK_COLORS)], lives))
    return bricks


def format_time(ms):
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def draw_pulsing_title(surf, now_ms, center):
    """Draws 'BREAKOUT' with a soft pulsing glow/scale effect, based on real time."""
    t = now_ms / 1000.0
    pulse = (math.sin(t * 2.4) + 1) / 2  # 0..1
    scale = 1.0 + 0.06 * pulse
    glow_alpha = int(70 + 130 * pulse)

    base_color = (0, 220, 255)
    accent_color = (255, 90, 200)
    color = tuple(int(base_color[i] * (1 - pulse) + accent_color[i] * pulse) for i in range(3))

    text = "BREAKOUT"
    main_surface = title_font.render(text, True, color)
    glow_surface = title_font.render(text, True, accent_color)

    scaled_main = pygame.transform.rotozoom(main_surface, 0, scale)
    scaled_glow = pygame.transform.rotozoom(glow_surface, 0, scale * 1.15)
    scaled_glow.set_alpha(glow_alpha)

    glow_rect = scaled_glow.get_rect(center=center)
    main_rect = scaled_main.get_rect(center=center)
    surf.blit(scaled_glow, glow_rect)
    surf.blit(scaled_main, main_rect)


def draw_menu(surf, now_ms):
    surf.fill(BLACK)
    draw_pulsing_title(surf, now_ms, (WIDTH // 2, HEIGHT // 2 - 120))

    lines = [
        "Use as SETAS (<- ->) ou A / D para mover a raquete",
        "Quebre os tijolos e colete as capsulas de power-up:",
    ]
    y = HEIGHT // 2 - 10
    for line in lines:
        rendered = menu_font.render(line, True, WHITE)
        surf.blit(rendered, (WIDTH // 2 - rendered.get_width() // 2, y))
        y += 32

    legend = [
        ("W", POWERUP_COLORS["W"], "raquete larga"),
        ("M", POWERUP_COLORS["M"], "multi-bola"),
        ("S", POWERUP_COLORS["S"], "bola lenta"),
    ]
    legend_y = y + 6
    total_w = len(legend) * 170
    start_x = WIDTH // 2 - total_w // 2
    for i, (letter, color, label) in enumerate(legend):
        bx = start_x + i * 170
        box = pygame.Rect(bx, legend_y, 26, 26)
        pygame.draw.rect(surf, color, box, border_radius=6)
        pygame.draw.rect(surf, BLACK, box, width=2, border_radius=6)
        letter_surf = powerup_font.render(letter, True, BLACK)
        surf.blit(letter_surf, (box.centerx - letter_surf.get_width() // 2,
                                 box.centery - letter_surf.get_height() // 2))
        label_surf = menu_font.render(label, True, WHITE)
        surf.blit(label_surf, (bx + 34, legend_y + 2))

    # hint pisca suavemente, baseado em tempo real
    blink = (math.sin(now_ms / 250.0) + 1) / 2
    hint_alpha = int(140 + 115 * blink)
    hint_surface = menu_hint_font.render("Pressione ESPACO para comecar", True, (120, 230, 90))
    hint_surface.set_alpha(hint_alpha)
    surf.blit(hint_surface, (WIDTH // 2 - hint_surface.get_width() // 2, legend_y + 70))


def draw_powerup_timer(surf, label, until_ticks, now, color, y):
    """Desenha a contagem regressiva de um power-up ativo e retorna o próximo y livre."""
    secs_left = (until_ticks - now + 999) // 1000
    txt = status_font.render(f"{label}: {secs_left}s", True, color)
    surf.blit(txt, (20, y))
    return y - 26


def draw_end_message(surf, text, color):
    msg = big_font.render(text, True, color)
    sub = font.render("Pressione R pra voltar ao menu", True, WHITE)
    surf.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 40))
    surf.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 20))


def draw_level_complete(surf, level):
    """Overlay rapido de transicao mostrado entre um nivel e o proximo."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surf.blit(overlay, (0, 0))
    msg = big_font.render(f"NIVEL {level} COMPLETO!", True, (120, 230, 90))
    sub = font.render("Preparando o proximo nivel...", True, WHITE)
    surf.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 30))
    surf.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 30))


def main():
    state = "menu"  # "menu" ou "playing"

    paddle = Paddle()
    balls = [Ball()]
    level = 1
    bricks = make_bricks(level)
    particles = []
    powerups = []
    score = 0
    lives = 3
    shake = 0
    game_over = False
    won = False
    transitioning = False
    level_transition_until = 0

    paddle_wide_until = 0
    slow_until = 0

    game_start_ticks = pygame.time.get_ticks()
    elapsed_ms = 0

    def reset_game():
        nonlocal paddle, balls, bricks, particles, powerups, score, lives, shake
        nonlocal game_over, won, paddle_wide_until, slow_until, game_start_ticks, elapsed_ms
        nonlocal level, transitioning, level_transition_until
        paddle = Paddle()
        balls = [Ball()]
        level = 1
        bricks = make_bricks(level)
        particles = []
        powerups = []
        score = 0
        lives = 3
        shake = 0
        game_over = False
        won = False
        transitioning = False
        level_transition_until = 0
        paddle_wide_until = 0
        slow_until = 0
        game_start_ticks = pygame.time.get_ticks()
        elapsed_ms = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if state == "menu":
                    if event.key == pygame.K_SPACE:
                        reset_game()
                        state = "playing"
                elif event.key == pygame.K_r and (game_over or won):
                    reset_game()
                    state = "menu"
                elif not game_over and not won and not transitioning:
                    direction = None
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        direction = -1
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        direction = 1
                    if direction is not None:
                        for b in balls:
                            if b.stuck:
                                b.launch(direction)

        keys = pygame.key.get_pressed()
        now = pygame.time.get_ticks()

        # expira a transicao de "nivel completo" e avanca pro proximo nivel
        if state == "playing" and transitioning and now >= level_transition_until:
            transitioning = False
            level += 1
            bricks = make_bricks(level)
            balls = [Ball()]
            powerups = []
            particles = []
            paddle_wide_until = 0
            slow_until = 0

        if state == "playing" and not game_over and not won and not transitioning:
            elapsed_ms = now - game_start_ticks

            paddle.update(keys)

            # efeito raquete larga (duracao real em ms)
            target_width = int(paddle.base_width * 1.6) if now < paddle_wide_until else paddle.base_width
            paddle.set_width(target_width)

            # efeito bola lenta (duracao real em ms)
            speed_factor = SLOW_FACTOR if now < slow_until else 1.0

            for b in balls:
                if b.stuck:
                    b.stick_to(paddle)
                else:
                    b.update(speed_factor)

            # colisao com a raquete
            for b in balls:
                if not b.stuck and b.rect().colliderect(paddle.rect()) and b.vy > 0:
                    b.vy *= -1
                    hit_pos = (b.x - paddle.x) / paddle.width - 0.5
                    b.vx += hit_pos * 6
                    b.vx = max(-9, min(9, b.vx))
                    play_sound("hit_paddle")

            # colisao com tijolos
            for b in balls:
                if b.stuck:
                    continue
                for brick in bricks:
                    if brick.alive and b.rect().colliderect(brick.rect):
                        destroyed = brick.hit()
                        b.vy *= -1
                        if destroyed:
                            score += 10
                            shake = 8
                            play_sound("brick_destroy")
                            for _ in range(18):
                                particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.base_color))
                            if random.random() < POWERUP_DROP_CHANCE:
                                kind = random.choice(list(POWERUP_COLORS.keys()))
                                powerups.append(PowerUp(brick.rect.centerx, brick.rect.centery, kind))
                        else:
                            shake = 4
                            play_sound("brick_hit")
                        break

            # queda das bolas no vazio - só perde vida quando TODAS caem
            survivors = [b for b in balls if not (b.y - b.radius > HEIGHT)]
            if not survivors:
                lives -= 1
                shake = 15
                if lives <= 0:
                    game_over = True
                    balls = []
                    play_sound("game_over")
                else:
                    balls = [Ball()]
                    play_sound("lose_life")
            else:
                balls = survivors

            # power-ups caindo / coleta pela raquete
            still_falling = []
            for pu in powerups:
                pu.update()
                if pu.rect().colliderect(paddle.rect()):
                    play_sound("powerup")
                    if pu.kind == "W":
                        paddle_wide_until = now + WIDE_DURATION_MS
                    elif pu.kind == "S":
                        slow_until = now + SLOW_DURATION_MS
                    elif pu.kind == "M":
                        if all(b.stuck for b in balls):
                            direction = random.choice([-1, 1])
                            for b in balls:
                                if b.stuck:
                                    b.launch(direction)
                        source = next((b for b in balls if not b.stuck), None)
                        if source is not None:
                            to_add = min(2, MAX_BALLS - len(balls))
                            for i in range(to_add):
                                offset = -3 if i == 0 else 3
                                balls.append(spawn_extra_ball(source, offset))
                    continue
                if pu.y - pu.h / 2 > HEIGHT:
                    continue
                still_falling.append(pu)
            powerups = still_falling

            if bricks and all(not b.alive for b in bricks):
                play_sound("victory")
                if level >= MAX_LEVEL:
                    won = True
                else:
                    transitioning = True
                    level_transition_until = now + LEVEL_TRANSITION_MS

        for p in particles:
            p.update()
        particles[:] = [p for p in particles if p.life > 0]

        if shake > 0:
            shake -= 1

        offset_x = random.randint(-shake, shake) if shake > 0 else 0
        offset_y = random.randint(-shake, shake) if shake > 0 else 0

        screen.fill(BLACK)
        draw_surf = pygame.Surface((WIDTH, HEIGHT))
        draw_surf.fill(BLACK)

        if state == "menu":
            draw_menu(draw_surf, now)
        else:
            for brick in bricks:
                brick.draw(draw_surf)
            paddle.draw(draw_surf)
            for b in balls:
                b.draw(draw_surf)
            for pu in powerups:
                pu.draw(draw_surf)
            for p in particles:
                p.draw(draw_surf)

            # placar em destaque (fonte maior, cor dourada) - é a info principal do HUD
            score_text = score_font.render(f"PONTOS: {score}", True, SCORE_COLOR)
            level_text = font.render(f"NIVEL: {level}", True, WHITE)
            lives_text = font.render(f"VIDAS: {lives}", True, WHITE)
            time_text = font.render(format_time(elapsed_ms), True, WHITE)
            draw_surf.blit(score_text, (20, 14))
            draw_surf.blit(level_text, (20, 58))
            draw_surf.blit(lives_text, (WIDTH - 150, 20))
            draw_surf.blit(time_text, (WIDTH // 2 - time_text.get_width() // 2, 20))

            # contagem regressiva dos power-ups ativos (tempo real, nao frames)
            # só faz sentido mostrar durante o jogo, não na tela de game over/vitória
            if not game_over and not won:
                status_y = HEIGHT - 72
                if now < paddle_wide_until:
                    status_y = draw_powerup_timer(draw_surf, "RAQUETE LARGA", paddle_wide_until, now,
                                                   POWERUP_COLORS["W"], status_y)
                if now < slow_until:
                    draw_powerup_timer(draw_surf, "BOLA LENTA", slow_until, now,
                                        POWERUP_COLORS["S"], status_y)

            if transitioning:
                draw_level_complete(draw_surf, level)

            if game_over:
                draw_end_message(draw_surf, "GAME OVER", (255, 80, 80))
            elif won:
                draw_end_message(draw_surf, "VOCE VENCEU!", (120, 230, 90))
                level_info = font.render(f"Nivel final alcancado: {level}", True, WHITE)
                draw_surf.blit(level_info, (WIDTH // 2 - level_info.get_width() // 2, HEIGHT // 2 + 60))

        screen.blit(draw_surf, (offset_x, offset_y))
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
