"""Loop principal do jogo: estados (menu/jogando/pausado), eventos de
teclado, fisica por frame e o desenho de cada tela."""
import random
import sys

import pygame

pygame.init()

import ui
import audio
import leaderboard
from entities import Paddle, Ball, spawn_extra_ball, Projectile, Particle, PowerUp, make_bricks, make_bonus_coins
from fonts import font, score_font, status_font
from constants import *

pygame.display.set_icon(ui.build_icon_surface())

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Breakout")
clock = pygame.time.Clock()

audio.init_audio()


def main():
    state = "menu"  # "menu" ou "playing"
    menu_selected = 0
    menu_view = "main"  # "main" ou "credits"

    paused = False
    pause_selected = 0
    pause_accum_ms = 0  # total de ms "descontados" do relogio por causa das pausas
    frozen_now = 0  # valor de 'now' congelado no instante em que pausou

    paddle = Paddle()
    balls = [Ball()]
    level = 1
    bricks = make_bricks(level)
    particles = []
    powerups = []
    projectiles = []
    score = 0
    lives = 3
    shake = 0
    game_over = False
    entering_name = False
    player_name = ""
    name_entry_context = None  # "gameover_qualify" ou "rename"
    rank_check_phase = "idle"
    transitioning = False
    level_transition_until = 0

    paddle_wide_until = 0
    slow_until = 0
    paddle_cannons_until = 0
    cannon_last_fire = {"left": 0, "right": 0}

    bonus_active = False
    bonus_until = 0
    bonus_coins = []
    bonus_score_gain = 0
    last_bonus_gain = 0

    game_start_ticks = pygame.time.get_ticks()
    elapsed_ms = 0

    def reset_game():
        nonlocal paddle, balls, bricks, particles, powerups, projectiles, score, lives, shake
        nonlocal game_over, entering_name, player_name, name_entry_context, rank_check_phase
        nonlocal paddle_wide_until, slow_until, game_start_ticks, elapsed_ms
        nonlocal paddle_cannons_until, cannon_last_fire
        nonlocal level, transitioning, level_transition_until
        nonlocal paused, pause_selected, pause_accum_ms, frozen_now
        nonlocal bonus_active, bonus_until, bonus_coins, bonus_score_gain, last_bonus_gain
        paddle = Paddle()
        balls = [Ball()]
        level = 1
        bricks = make_bricks(level)
        particles = []
        powerups = []
        projectiles = []
        score = 0
        lives = 3
        shake = 0
        game_over = False
        entering_name = False
        player_name = ""
        name_entry_context = None
        rank_check_phase = "idle"
        transitioning = False
        level_transition_until = 0
        paddle_wide_until = 0
        slow_until = 0
        paddle_cannons_until = 0
        cannon_last_fire = {"left": 0, "right": 0}
        bonus_active = False
        bonus_until = 0
        bonus_coins = []
        bonus_score_gain = 0
        last_bonus_gain = 0
        game_start_ticks = pygame.time.get_ticks()
        elapsed_ms = 0
        paused = False
        pause_selected = 0
        pause_accum_ms = 0
        frozen_now = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if entering_name:
                    if event.key == pygame.K_RETURN:
                        entering_name = False
                        name_final = player_name.strip()[:leaderboard.MAX_NAME_LEN] or "JOGADOR"
                        if name_entry_context == "rename":
                            leaderboard.set_player_name(name_final)
                            if leaderboard.get_best_submitted_score() > 0:
                                leaderboard.submit_rank_async(leaderboard.get_player_id(), name_final,
                                                               leaderboard.get_best_submitted_score())
                        else:
                            leaderboard.set_player_name(name_final)
                            rank_check_phase = "submitting"
                            leaderboard.submit_rank_async(leaderboard.get_player_id(), name_final, score)
                        name_entry_context = None
                    elif event.key == pygame.K_ESCAPE:
                        entering_name = False
                        if name_entry_context == "gameover_qualify":
                            rank_check_phase = "skipped"
                        name_entry_context = None
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    elif event.unicode and event.unicode.isprintable() and len(player_name) < leaderboard.MAX_NAME_LEN:
                        player_name += event.unicode
                elif state == "menu":
                    if menu_view == "ranking":
                        if event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
                            menu_view = "main"
                        elif event.key == pygame.K_n and leaderboard.get_player_name():
                            entering_name = True
                            player_name = leaderboard.get_player_name() or ""
                            name_entry_context = "rename"
                    elif menu_view == "credits":
                        if event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
                            menu_view = "main"
                    else:
                        if event.key in (pygame.K_UP, pygame.K_w):
                            menu_selected = (menu_selected - 1) % len(MENU_OPTIONS)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            menu_selected = (menu_selected + 1) % len(MENU_OPTIONS)
                        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                            choice = MENU_OPTIONS[menu_selected]
                            if choice == "INICIAR JOGO":
                                reset_game()
                                state = "playing"
                            elif choice == "RANKING":
                                menu_view = "ranking"
                                leaderboard.fetch_leaderboard_async()
                            elif choice == "CREDITOS":
                                menu_view = "credits"
                            elif choice == "SAIR":
                                pygame.quit()
                                sys.exit()
                elif event.key == pygame.K_r and game_over:
                    reset_game()
                    state = "menu"
                    menu_view = "main"
                    menu_selected = 0
                elif event.key in (pygame.K_p, pygame.K_ESCAPE) and not game_over and not transitioning:
                    t = pygame.time.get_ticks()
                    if not paused:
                        paused = True
                        pause_selected = 0
                        frozen_now = t - pause_accum_ms
                    else:
                        paused = False
                        pause_accum_ms = t - frozen_now
                elif paused:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        pause_selected = (pause_selected - 1) % len(PAUSE_OPTIONS)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        pause_selected = (pause_selected + 1) % len(PAUSE_OPTIONS)
                    elif event.key in (pygame.K_LEFT, pygame.K_a) and PAUSE_OPTIONS[pause_selected] == "VOLUME":
                        audio.sound_volume = max(0.0, round(audio.sound_volume - 0.1, 2))
                    elif event.key in (pygame.K_RIGHT, pygame.K_d) and PAUSE_OPTIONS[pause_selected] == "VOLUME":
                        audio.sound_volume = min(1.0, round(audio.sound_volume + 0.1, 2))
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        choice = PAUSE_OPTIONS[pause_selected]
                        if choice == "CONTINUAR":
                            t = pygame.time.get_ticks()
                            paused = False
                            pause_accum_ms = t - frozen_now
                        elif choice == "REINICIAR":
                            reset_game()
                        elif choice == "MENU INICIAL":
                            reset_game()
                            state = "menu"
                            menu_view = "main"
                            menu_selected = 0
                elif not game_over and not transitioning:
                    direction = None
                    launch_pressed = False
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        direction = -1
                        launch_pressed = True
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        direction = 1
                        launch_pressed = True
                    elif event.key == pygame.K_SPACE:
                        launch_pressed = True
                    elif event.key == pygame.K_v and not bonus_active:
                        if lives < 3 and score >= EXTRA_LIFE_COST:
                            score -= EXTRA_LIFE_COST
                            lives += 1
                            audio.play_sound("buy_life")
                    if launch_pressed:
                        for b in balls:
                            if b.stuck:
                                b.launch(direction)

        keys = pygame.key.get_pressed()
        # enquanto pausado, 'now' fica congelado no valor de quando pausou -
        # assim nenhum cronometro (power-up, nivel, partida) avanca escondido
        now = frozen_now if paused else (pygame.time.get_ticks() - pause_accum_ms)

        # acompanha a verificacao/envio do ranking apos o game over, sem travar o jogo
        if game_over and rank_check_phase == "checking" and leaderboard.get_rank_check_status() in ("done", "error"):
            if leaderboard.get_rank_check_status() == "error":
                rank_check_phase = "error"
            elif leaderboard.get_rank_check_qualifies():
                if not leaderboard.get_player_name():
                    rank_check_phase = "naming"
                    entering_name = True
                    player_name = ""
                    name_entry_context = "gameover_qualify"
                else:
                    rank_check_phase = "submitting"
                    leaderboard.submit_rank_async(leaderboard.get_player_id(), leaderboard.get_player_name(), score)
            else:
                rank_check_phase = "not_top100" if leaderboard.get_rank_check_reason() == "not_top100" else "not_personal_best"

        if rank_check_phase == "submitting" and leaderboard.get_rank_submit_status() in ("ok", "error"):
            if leaderboard.get_rank_submit_status() == "ok":
                leaderboard.set_best_submitted_score(score)
                rank_check_phase = "submitted_ok"
            else:
                rank_check_phase = "submitted_error"

        # expira a transicao de "nivel completo" (ou de rodada bonus) e avanca pro proximo nivel
        if state == "playing" and transitioning and now >= level_transition_until:
            transitioning = False
            level += 1
            bricks = make_bricks(level)
            balls = [Ball()]
            powerups = []
            projectiles = []
            particles = []
            paddle_wide_until = 0
            slow_until = 0
            paddle_cannons_until = 0
            last_bonus_gain = 0

        if state == "playing" and not game_over and not transitioning and not paused:
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
                    audio.play_sound("hit_paddle")

            # canhoes (power-up C): disparam projeteis das duas pontas da raquete
            if now < paddle_cannons_until:
                for side in ("left", "right"):
                    if now - cannon_last_fire[side] >= CANNON_FIRE_INTERVAL_MS:
                        cannon_last_fire[side] = now
                        px = paddle.x + 7 if side == "left" else paddle.x + paddle.width - 7
                        projectiles.append(Projectile(px, paddle.y))
                        audio.play_sound("cannon_fire")

            for proj in projectiles:
                proj.update()
            projectiles[:] = [p for p in projectiles if p.y + p.h > 0]

            if not bonus_active:
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
                                audio.play_sound("brick_destroy")
                                for _ in range(18):
                                    particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.base_color))
                                if random.random() < POWERUP_DROP_CHANCE:
                                    kind = random.choice(list(POWERUP_COLORS.keys()))
                                    powerups.append(PowerUp(brick.rect.centerx, brick.rect.centery, kind))
                            else:
                                shake = 4
                                audio.play_sound("brick_hit")
                            break

                # canhoes atingindo tijolos - mesmo dano/quebra de uma batida de bola
                for proj in projectiles[:]:
                    for brick in bricks:
                        if brick.alive and proj.rect().colliderect(brick.rect):
                            destroyed = brick.hit()
                            if destroyed:
                                score += 10
                                shake = 6
                                audio.play_sound("brick_destroy")
                                for _ in range(14):
                                    particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.base_color))
                                if random.random() < POWERUP_DROP_CHANCE:
                                    kind = random.choice(list(POWERUP_COLORS.keys()))
                                    powerups.append(PowerUp(brick.rect.centerx, brick.rect.centery, kind))
                            else:
                                audio.play_sound("brick_hit")
                            projectiles.remove(proj)
                            break

                # queda das bolas no vazio - só perde vida quando TODAS caem
                survivors = [b for b in balls if not (b.y - b.radius > HEIGHT)]
                if not survivors:
                    lives -= 1
                    shake = 15
                    if lives <= 0:
                        game_over = True
                        rank_check_phase = "checking"
                        leaderboard.check_rank_async(score, leaderboard.get_player_id())
                        balls = []
                        audio.play_sound("game_over")
                    else:
                        balls = [Ball()]
                        audio.play_sound("lose_life")
                else:
                    balls = survivors

                # power-ups caindo / coleta pela raquete
                still_falling = []
                for pu in powerups:
                    pu.update()
                    if pu.rect().colliderect(paddle.rect()):
                        audio.play_sound("powerup")
                        if pu.kind == "W":
                            paddle_wide_until = now + WIDE_DURATION_MS
                        elif pu.kind == "S":
                            slow_until = now + SLOW_DURATION_MS
                        elif pu.kind == "C":
                            paddle_cannons_until = now + CANNON_DURATION_MS
                            cannon_last_fire["left"] = now - CANNON_FIRE_INTERVAL_MS
                            cannon_last_fire["right"] = now - CANNON_FIRE_INTERVAL_MS
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
                    audio.play_sound("victory")
                    if level % BONUS_LEVEL_INTERVAL == 0:
                        bonus_active = True
                        bonus_until = now + BONUS_LEVEL_DURATION_MS
                        bonus_coins = make_bonus_coins()
                        bonus_score_gain = 0
                        balls = [Ball()]
                        paddle_wide_until = 0
                        slow_until = 0
                        paddle_cannons_until = 0
                        powerups = []
                        projectiles = []
                    else:
                        transitioning = True
                        level_transition_until = now + LEVEL_TRANSITION_MS
            else:
                # rodada bonus: só moedas, sem tijolos nem perda de vida em jogo
                for b in balls:
                    if b.stuck:
                        continue
                    for coin in bonus_coins:
                        if coin.alive and b.rect().colliderect(coin.rect()):
                            coin.alive = False
                            score += BONUS_COIN_VALUE
                            bonus_score_gain += BONUS_COIN_VALUE
                            shake = 3
                            audio.play_sound("coin")
                            for _ in range(10):
                                particles.append(Particle(coin.x, coin.y, (255, 215, 0)))
                bonus_coins = [c for c in bonus_coins if c.alive]

                survivors = [b for b in balls if not (b.y - b.radius > HEIGHT)]
                balls = survivors if survivors else [Ball()]

                if not bonus_coins or now >= bonus_until:
                    bonus_active = False
                    last_bonus_gain = bonus_score_gain
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

        if state == "menu":
            if menu_view == "credits":
                ui.draw_credits(draw_surf, now)
            elif menu_view == "ranking":
                ui.draw_ranking(draw_surf, now)
            else:
                ui.draw_menu(draw_surf, now, menu_selected)
        else:
            ui.draw_starry_background(draw_surf, now)
            if bonus_active:
                for coin in bonus_coins:
                    coin.draw(draw_surf)
            else:
                for brick in bricks:
                    brick.draw(draw_surf)
            paddle.draw(draw_surf)
            if now < paddle_cannons_until:
                ui.draw_cannons(draw_surf, paddle)
            for b in balls:
                b.draw(draw_surf)
            for pu in powerups:
                pu.draw(draw_surf)
            for proj in projectiles:
                proj.draw(draw_surf)
            for p in particles:
                p.draw(draw_surf)

            # placar em destaque (fonte maior, cor dourada) - é a info principal do HUD
            score_text = score_font.render(f"PONTOS: {score}", True, SCORE_COLOR)
            level_label = "RODADA BONUS" if bonus_active else f"NIVEL: {level}"
            level_color = (255, 215, 0) if bonus_active else WHITE
            level_text = font.render(level_label, True, level_color)
            lives_text = font.render(f"VIDAS: {lives}", True, WHITE)
            time_text = font.render(ui.format_time(elapsed_ms), True, WHITE)
            draw_surf.blit(score_text, (20, 14))
            draw_surf.blit(level_text, (20, 58))
            draw_surf.blit(lives_text, (WIDTH - 150, 20))
            draw_surf.blit(time_text, (WIDTH // 2 - time_text.get_width() // 2, 20))

            # contagem regressiva dos power-ups ativos / rodada bonus (tempo real, nao frames)
            # só faz sentido mostrar durante o jogo, não na tela de game over
            if not game_over:
                status_y = HEIGHT - 72
                if now < paddle_wide_until:
                    status_y = ui.draw_powerup_timer(draw_surf, "RAQUETE LARGA", paddle_wide_until, now,
                                                      POWERUP_COLORS["W"], status_y)
                if now < slow_until:
                    status_y = ui.draw_powerup_timer(draw_surf, "BOLA LENTA", slow_until, now,
                                        POWERUP_COLORS["S"], status_y)
                if now < paddle_cannons_until:
                    status_y = ui.draw_powerup_timer(draw_surf, "CANHOES", paddle_cannons_until, now,
                                        POWERUP_COLORS["C"], status_y)
                if bonus_active:
                    ui.draw_powerup_timer(draw_surf, "TEMPO BONUS", bonus_until, now,
                                        (255, 215, 0), status_y)

                if lives < 3 and not bonus_active:
                    cost_color = (120, 230, 90) if score >= EXTRA_LIFE_COST else (140, 140, 150)
                    buy_hint = status_font.render(
                        f"V: trocar {EXTRA_LIFE_COST} pts por 1 vida extra", True, cost_color)
                    draw_surf.blit(buy_hint, (WIDTH - buy_hint.get_width() - 20, HEIGHT - 30))

            if transitioning:
                ui.draw_level_complete(draw_surf, level, last_bonus_gain)

            if game_over and not entering_name:
                ui.draw_end_message(draw_surf, "GAME OVER", (255, 80, 80), rank_check_phase)

            if paused:
                ui.draw_pause_menu(draw_surf, now, pause_selected, audio.sound_volume)

        if entering_name:
            if name_entry_context == "rename":
                ui.draw_name_entry(draw_surf, player_name, "ALTERAR NOME", (0, 220, 255), "Digite o novo nome:")
            else:
                ui.draw_name_entry(draw_surf, player_name)

        screen.blit(draw_surf, (offset_x, offset_y))
        pygame.display.flip()
        clock.tick(FPS)
