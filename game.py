"""Loop principal do jogo: estados (menu/jogando/pausado), eventos de
teclado, fisica por frame e o desenho de cada tela."""
import random
import sys

import pygame

pygame.init()

import ui
import audio
import leaderboard
import player_profile as profile
import skins
from entities import Paddle, Ball, criar_bola_extra, Projectile, Particle, PowerUp, criar_tijolos, criar_moedas_bonus
from fonts import font, score_font
from constants import *

pygame.display.set_icon(ui.criar_superficie_icone())

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
pygame.display.set_caption("Breakout")
clock = pygame.time.Clock()

audio.iniciar_audio()

# Codigo secreto (estilo Konami) que desbloqueia a raquete ultra-rara
# "tempestade" - funciona em qualquer tela, so observando as setas digitadas.
CODIGO_SECRETO = [
    pygame.K_UP, pygame.K_UP, pygame.K_DOWN, pygame.K_DOWN,
    pygame.K_LEFT, pygame.K_RIGHT, pygame.K_LEFT, pygame.K_RIGHT,
]


def principal():
    state = "menu"  # "menu" ou "playing"
    menu_selected = 0
    menu_view = "main"  # "main", "credits", "ranking" ou "loja"

    loja_categoria = "bolas"
    loja_idx = 0
    loja_msg = ""
    loja_msg_until = 0

    codigo_secreto_buffer = []
    codigo_secreto_msg = ""
    codigo_secreto_msg_until = 0
    raio_secreto_ativo = False
    raio_secreto_inicio = 0
    raio_secreto_x = 0
    raio_secreto_trovao_tocado = False
    revelar_skin_lendaria = False

    inv_categoria = "bolas"
    inv_idx = 0
    inv_msg = ""
    inv_msg_until = 0

    paused = False
    pause_selected = 0
    pause_accum_ms = 0  # total de ms "descontados" do relogio por causa das pausas
    frozen_now = 0  # valor de 'now' congelado no instante em que pausou

    paddle = Paddle()
    balls = [Ball()]
    level = 1
    bricks = criar_tijolos(level)
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
    offering_potion = False
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

    def reiniciar_jogo():
        nonlocal paddle, balls, bricks, particles, powerups, projectiles, score, lives, shake
        nonlocal game_over, entering_name, player_name, name_entry_context, rank_check_phase, offering_potion
        nonlocal paddle_wide_until, slow_until, game_start_ticks, elapsed_ms
        nonlocal paddle_cannons_until, cannon_last_fire
        nonlocal level, transitioning, level_transition_until
        nonlocal paused, pause_selected, pause_accum_ms, frozen_now
        nonlocal bonus_active, bonus_until, bonus_coins, bonus_score_gain, last_bonus_gain
        nonlocal raio_secreto_ativo, raio_secreto_trovao_tocado, revelar_skin_lendaria
        paddle = Paddle()
        balls = [Ball()]
        level = 1
        bricks = criar_tijolos(level)
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
        offering_potion = False
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
        raio_secreto_ativo = False
        raio_secreto_trovao_tocado = False
        revelar_skin_lendaria = False
        game_start_ticks = pygame.time.get_ticks()
        elapsed_ms = 0
        paused = False
        pause_selected = 0
        pause_accum_ms = 0
        frozen_now = 0

    def executar_opcao_menu(choice):
        nonlocal state, menu_view
        if choice == "INICIAR JOGO":
            reiniciar_jogo()
            state = "playing"
        elif choice == "RANKING":
            menu_view = "ranking"
            leaderboard.buscar_ranking_async()
        elif choice == "CREDITOS":
            menu_view = "credits"
        elif choice == "SAIR":
            pygame.quit()
            sys.exit()

    def executar_opcao_pausa(choice):
        nonlocal paused, pause_accum_ms, state, menu_view, menu_selected
        if choice == "CONTINUAR":
            t = pygame.time.get_ticks()
            paused = False
            pause_accum_ms = t - frozen_now
        elif choice == "REINICIAR":
            reiniciar_jogo()
        elif choice == "MENU INICIAL":
            reiniciar_jogo()
            state = "menu"
            menu_view = "main"
            menu_selected = 0

    now = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "menu" and menu_view == "main" and not entering_name:
                    if ui.obter_retangulo_icone_loja().collidepoint(event.pos):
                        menu_view = "loja"
                        loja_categoria = "bolas"
                        loja_idx = 0
                        loja_msg = ""
                    elif ui.obter_retangulo_icone_inventario().collidepoint(event.pos):
                        menu_view = "inventario"
                        inv_categoria = "bolas"
                        inv_idx = 0
                        inv_msg = ""
                    else:
                        for i, rect in ui.obter_retangulos_menu().items():
                            if rect.collidepoint(event.pos):
                                menu_selected = i
                                executar_opcao_menu(MENU_OPTIONS[i])
                elif paused:
                    for i, rect in ui.obter_retangulos_menu_pausa().items():
                        if rect.collidepoint(event.pos):
                            pause_selected = i
                            executar_opcao_pausa(PAUSE_OPTIONS[i])
                elif state == "menu" and menu_view == "loja":
                    if ui.obter_retangulo_fechar_loja().collidepoint(event.pos):
                        menu_view = "main"
                    else:
                        for cat_id, rect in ui.obter_retangulos_abas_loja().items():
                            if rect.collidepoint(event.pos):
                                loja_categoria = cat_id
                                loja_idx = 0
                        if loja_categoria != "pocoes":
                            lista = skins.BALL_SKIN_ORDER if loja_categoria == "bolas" else skins.PADDLE_SKIN_ORDER
                            left_arrow, right_arrow = ui.obter_retangulos_setas_loja()
                            if left_arrow.collidepoint(event.pos):
                                loja_idx = (loja_idx - 1) % len(lista)
                            elif right_arrow.collidepoint(event.pos):
                                loja_idx = (loja_idx + 1) % len(lista)
                elif state == "menu" and menu_view == "inventario":
                    if ui.obter_retangulo_fechar_loja().collidepoint(event.pos):
                        menu_view = "main"
                    else:
                        for cat_id, rect in ui.obter_retangulos_abas_inventario().items():
                            if rect.collidepoint(event.pos):
                                inv_categoria = cat_id
                                inv_idx = 0
                        if inv_categoria != "pocoes":
                            lista = ui.obter_itens_possuidos(inv_categoria)
                            left_arrow, right_arrow = ui.obter_retangulos_setas_loja()
                            if lista:
                                if left_arrow.collidepoint(event.pos):
                                    inv_idx = (inv_idx - 1) % len(lista)
                                elif right_arrow.collidepoint(event.pos):
                                    inv_idx = (inv_idx + 1) % len(lista)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    codigo_secreto_buffer.append(event.key)
                    codigo_secreto_buffer[:] = codigo_secreto_buffer[-len(CODIGO_SECRETO):]
                    if codigo_secreto_buffer == CODIGO_SECRETO:
                        codigo_secreto_buffer.clear()
                        ja_tinha = profile.possui_skin_raquete("tempestade")
                        profile.desbloquear_skin_raquete("tempestade")
                        profile.equipar_skin_raquete("tempestade")
                        paddle_visivel = state == "playing" and not game_over and not transitioning
                        if paddle_visivel:
                            paddle.skin = "tempestade"
                        if ja_tinha:
                            codigo_secreto_msg = "Tempestade reequipada!"
                            codigo_secreto_msg_until = now + 2000
                            audio.tocar_som("powerup")
                        else:
                            codigo_secreto_msg = "Um raio cortou o ceu..."
                            codigo_secreto_msg_until = now + 2200
                            revelar_skin_lendaria = True
                            if paddle_visivel:
                                raio_secreto_ativo = True
                                raio_secreto_inicio = now
                                raio_secreto_trovao_tocado = False
                                raio_secreto_x = paddle.retangulo().centerx
                                audio.tocar_som("raio_caindo")
                            else:
                                audio.tocar_som("trovao")
                if entering_name:
                    if event.key == pygame.K_RETURN:
                        entering_name = False
                        name_final = player_name.strip()[:leaderboard.MAX_NAME_LEN] or "JOGADOR"
                        if name_entry_context == "rename":
                            profile.definir_nome_jogador(name_final)
                            if profile.obter_melhor_pontuacao_enviada() > 0:
                                leaderboard.enviar_colocacao_async(profile.obter_id_jogador(), name_final,
                                                                    profile.obter_melhor_pontuacao_enviada())
                        else:
                            profile.definir_nome_jogador(name_final)
                            rank_check_phase = "submitting"
                            leaderboard.enviar_colocacao_async(profile.obter_id_jogador(), name_final, score)
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
                elif offering_potion:
                    if event.key in (pygame.K_s, pygame.K_SPACE, pygame.K_RETURN):
                        profile.usar_pocao()
                        offering_potion = False
                        lives = 1
                        balls = [Ball()]
                        audio.tocar_som("buy_life")
                    elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                        offering_potion = False
                        game_over = True
                        rank_check_phase = "checking"
                        leaderboard.verificar_colocacao_async(score, profile.obter_id_jogador())
                        audio.tocar_som("game_over")
                elif state == "menu":
                    if menu_view == "ranking":
                        if event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
                            menu_view = "main"
                        elif event.key == pygame.K_n and profile.obter_nome_jogador():
                            entering_name = True
                            player_name = profile.obter_nome_jogador() or ""
                            name_entry_context = "rename"
                    elif menu_view == "credits":
                        if event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
                            menu_view = "main"
                    elif menu_view == "loja":
                        categorias = ["bolas", "raquetes", "pocoes"]
                        if event.key == pygame.K_ESCAPE:
                            menu_view = "main"
                        elif event.key in (pygame.K_UP, pygame.K_w):
                            loja_categoria = categorias[(categorias.index(loja_categoria) - 1) % len(categorias)]
                            loja_idx = 0
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            loja_categoria = categorias[(categorias.index(loja_categoria) + 1) % len(categorias)]
                            loja_idx = 0
                        elif event.key in (pygame.K_LEFT, pygame.K_a) and loja_categoria in ("bolas", "raquetes"):
                            lista = skins.BALL_SKIN_ORDER if loja_categoria == "bolas" else skins.PADDLE_SKIN_ORDER
                            loja_idx = (loja_idx - 1) % len(lista)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d) and loja_categoria in ("bolas", "raquetes"):
                            lista = skins.BALL_SKIN_ORDER if loja_categoria == "bolas" else skins.PADDLE_SKIN_ORDER
                            loja_idx = (loja_idx + 1) % len(lista)
                        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                            t = pygame.time.get_ticks()
                            if loja_categoria == "bolas":
                                skin_id = skins.BALL_SKIN_ORDER[loja_idx]
                                info = skins.BALL_SKINS[skin_id]
                                if profile.possui_skin_bola(skin_id):
                                    profile.equipar_skin_bola(skin_id)
                                    loja_msg = f"{info['nome']} equipada!"
                                elif profile.gastar_moedas(info["preco"]):
                                    profile.desbloquear_skin_bola(skin_id)
                                    profile.equipar_skin_bola(skin_id)
                                    audio.tocar_som("powerup")
                                    loja_msg = f"{info['nome']} comprada e equipada!"
                                else:
                                    loja_msg = "Moedas insuficientes!"
                                loja_msg_until = t + 1500
                            elif loja_categoria == "raquetes":
                                skin_id = skins.PADDLE_SKIN_ORDER[loja_idx]
                                info = skins.PADDLE_SKINS[skin_id]
                                if profile.possui_skin_raquete(skin_id):
                                    profile.equipar_skin_raquete(skin_id)
                                    loja_msg = f"{info['nome']} equipada!"
                                elif profile.gastar_moedas(info["preco"]):
                                    profile.desbloquear_skin_raquete(skin_id)
                                    profile.equipar_skin_raquete(skin_id)
                                    audio.tocar_som("powerup")
                                    loja_msg = f"{info['nome']} comprada e equipada!"
                                else:
                                    loja_msg = "Moedas insuficientes!"
                                loja_msg_until = t + 1500
                            elif loja_categoria == "pocoes":
                                if profile.gastar_moedas(skins.POTION_PRECO):
                                    profile.adicionar_pocao()
                                    audio.tocar_som("powerup")
                                    loja_msg = f"Pocao comprada! Total: {profile.obter_pocoes()}"
                                else:
                                    loja_msg = "Moedas insuficientes!"
                                loja_msg_until = t + 1500
                    elif menu_view == "inventario":
                        categorias = ["bolas", "raquetes", "pocoes"]
                        if event.key == pygame.K_ESCAPE:
                            menu_view = "main"
                        elif event.key in (pygame.K_UP, pygame.K_w):
                            inv_categoria = categorias[(categorias.index(inv_categoria) - 1) % len(categorias)]
                            inv_idx = 0
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            inv_categoria = categorias[(categorias.index(inv_categoria) + 1) % len(categorias)]
                            inv_idx = 0
                        elif event.key in (pygame.K_LEFT, pygame.K_a) and inv_categoria != "pocoes":
                            lista = ui.obter_itens_possuidos(inv_categoria)
                            if lista:
                                inv_idx = (inv_idx - 1) % len(lista)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d) and inv_categoria != "pocoes":
                            lista = ui.obter_itens_possuidos(inv_categoria)
                            if lista:
                                inv_idx = (inv_idx + 1) % len(lista)
                        elif event.key in (pygame.K_SPACE, pygame.K_RETURN) and inv_categoria != "pocoes":
                            lista = ui.obter_itens_possuidos(inv_categoria)
                            if lista:
                                skin_id = lista[inv_idx % len(lista)]
                                if inv_categoria == "bolas":
                                    profile.equipar_skin_bola(skin_id)
                                    info = skins.BALL_SKINS[skin_id]
                                else:
                                    profile.equipar_skin_raquete(skin_id)
                                    info = skins.PADDLE_SKINS[skin_id]
                                audio.tocar_som("powerup")
                                inv_msg = f"{info['nome']} equipada!"
                                inv_msg_until = pygame.time.get_ticks() + 1500
                    else:
                        if event.key in (pygame.K_UP, pygame.K_w):
                            menu_selected = (menu_selected - 1) % len(MENU_OPTIONS)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            menu_selected = (menu_selected + 1) % len(MENU_OPTIONS)
                        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                            executar_opcao_menu(MENU_OPTIONS[menu_selected])
                elif event.key == pygame.K_r and game_over:
                    reiniciar_jogo()
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
                        executar_opcao_pausa(PAUSE_OPTIONS[pause_selected])
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
                    if launch_pressed:
                        for b in balls:
                            if b.stuck:
                                b.lancar(direction)

        keys = pygame.key.get_pressed()
        # enquanto pausado, 'now' fica congelado no valor de quando pausou -
        # assim nenhum cronometro (power-up, nivel, partida) avanca escondido
        now = frozen_now if paused else (pygame.time.get_ticks() - pause_accum_ms)

        if raio_secreto_ativo:
            if not raio_secreto_trovao_tocado and now - raio_secreto_inicio >= RAIO_SECRETO_QUEDA_MS:
                audio.tocar_som("trovao")
                raio_secreto_trovao_tocado = True
            if now - raio_secreto_inicio >= RAIO_SECRETO_DURACAO_MS:
                raio_secreto_ativo = False

        # acompanha a verificacao/envio do ranking apos o game over, sem travar o jogo
        if game_over and rank_check_phase == "checking" and leaderboard.obter_status_verificacao() in ("done", "error"):
            if leaderboard.obter_status_verificacao() == "error":
                rank_check_phase = "error"
            elif leaderboard.obter_verificacao_qualifica():
                if not profile.obter_nome_jogador():
                    rank_check_phase = "naming"
                    entering_name = True
                    player_name = ""
                    name_entry_context = "gameover_qualify"
                else:
                    rank_check_phase = "submitting"
                    leaderboard.enviar_colocacao_async(profile.obter_id_jogador(), profile.obter_nome_jogador(), score)
            else:
                rank_check_phase = "not_top100" if leaderboard.obter_motivo_verificacao() == "not_top100" else "not_personal_best"

        if rank_check_phase == "submitting" and leaderboard.obter_status_envio() in ("ok", "error"):
            if leaderboard.obter_status_envio() == "ok":
                profile.definir_melhor_pontuacao_enviada(score)
                rank_check_phase = "submitted_ok"
            else:
                rank_check_phase = "submitted_error"

        # expira a transicao de "nivel completo" (ou de rodada bonus) e avanca pro proximo nivel
        if state == "playing" and transitioning and now >= level_transition_until:
            transitioning = False
            level += 1
            bricks = criar_tijolos(level)
            balls = [Ball()]
            powerups = []
            projectiles = []
            particles = []
            paddle_wide_until = 0
            slow_until = 0
            paddle_cannons_until = 0
            last_bonus_gain = 0

        if state == "playing" and not game_over and not transitioning and not paused and not offering_potion:
            elapsed_ms = now - game_start_ticks

            paddle.atualizar(keys)

            # efeito raquete larga (duracao real em ms)
            target_width = int(paddle.base_width * 1.6) if now < paddle_wide_until else paddle.base_width
            paddle.definir_largura(target_width)

            # efeito bola lenta (duracao real em ms)
            speed_factor = SLOW_FACTOR if now < slow_until else 1.0

            for b in balls:
                if b.stuck:
                    b.grudar_em(paddle)
                else:
                    b.atualizar(speed_factor)

            # colisao com a raquete
            for b in balls:
                if not b.stuck and b.retangulo().colliderect(paddle.retangulo()) and b.vy > 0:
                    b.vy *= -1
                    hit_pos = (b.x - paddle.x) / paddle.width - 0.5
                    b.vx += hit_pos * 6
                    b.vx = max(-9, min(9, b.vx))
                    audio.tocar_som("hit_paddle")

            # canhoes (power-up C): disparam projeteis das duas pontas da raquete
            if now < paddle_cannons_until:
                for side in ("left", "right"):
                    if now - cannon_last_fire[side] >= CANNON_FIRE_INTERVAL_MS:
                        cannon_last_fire[side] = now
                        px = paddle.x + 7 if side == "left" else paddle.x + paddle.width - 7
                        projectiles.append(Projectile(px, paddle.y))
                        audio.tocar_som("cannon_fire")

            for proj in projectiles:
                proj.atualizar()
            projectiles[:] = [p for p in projectiles if p.y + p.h > 0]

            if not bonus_active:
                # colisao com tijolos
                for b in balls:
                    if b.stuck:
                        continue
                    for brick in bricks:
                        if brick.alive and b.retangulo().colliderect(brick.rect):
                            destroyed = brick.atingir()
                            b.vy *= -1
                            if destroyed:
                                score += 10
                                shake = 8
                                audio.tocar_som("brick_destroy")
                                for _ in range(18):
                                    particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.base_color))
                                if random.random() < POWERUP_DROP_CHANCE:
                                    kind = random.choice(list(POWERUP_COLORS.keys()))
                                    powerups.append(PowerUp(brick.rect.centerx, brick.rect.centery, kind))
                            else:
                                shake = 4
                                audio.tocar_som("brick_hit")
                            break

                # canhoes atingindo tijolos - mesmo dano/quebra de uma batida de bola
                for proj in projectiles[:]:
                    for brick in bricks:
                        if brick.alive and proj.retangulo().colliderect(brick.rect):
                            destroyed = brick.atingir()
                            if destroyed:
                                score += 10
                                shake = 6
                                audio.tocar_som("brick_destroy")
                                for _ in range(14):
                                    particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.base_color))
                                if random.random() < POWERUP_DROP_CHANCE:
                                    kind = random.choice(list(POWERUP_COLORS.keys()))
                                    powerups.append(PowerUp(brick.rect.centerx, brick.rect.centery, kind))
                            else:
                                audio.tocar_som("brick_hit")
                            projectiles.remove(proj)
                            break

                # queda das bolas no vazio - só perde vida quando TODAS caem
                survivors = [b for b in balls if not (b.y - b.radius > HEIGHT)]
                if not survivors:
                    lives -= 1
                    shake = 15
                    if lives <= 0:
                        if profile.obter_pocoes() > 0:
                            offering_potion = True
                            balls = []
                            audio.tocar_som("lose_life")
                        else:
                            game_over = True
                            rank_check_phase = "checking"
                            leaderboard.verificar_colocacao_async(score, profile.obter_id_jogador())
                            balls = []
                            audio.tocar_som("game_over")
                    else:
                        balls = [Ball()]
                        audio.tocar_som("lose_life")
                else:
                    balls = survivors

                # power-ups caindo / coleta pela raquete
                still_falling = []
                for pu in powerups:
                    pu.atualizar()
                    if pu.retangulo().colliderect(paddle.retangulo()):
                        audio.tocar_som("powerup")
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
                                        b.lancar(direction)
                            source = next((b for b in balls if not b.stuck), None)
                            if source is not None:
                                to_add = min(2, MAX_BALLS - len(balls))
                                for i in range(to_add):
                                    offset = -3 if i == 0 else 3
                                    balls.append(criar_bola_extra(source, offset))
                        continue
                    if pu.y - pu.h / 2 > HEIGHT:
                        continue
                    still_falling.append(pu)
                powerups = still_falling

                if bricks and all(not b.alive for b in bricks):
                    audio.tocar_som("victory")
                    profile.adicionar_moedas(COINS_PER_LEVEL_CLEARED)
                    if level % BONUS_LEVEL_INTERVAL == 0:
                        bonus_active = True
                        bonus_until = now + BONUS_LEVEL_DURATION_MS
                        bonus_coins = criar_moedas_bonus()
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
                        if coin.alive and b.retangulo().colliderect(coin.retangulo()):
                            coin.alive = False
                            score += BONUS_COIN_VALUE
                            bonus_score_gain += BONUS_COIN_VALUE
                            profile.adicionar_moedas(1)
                            shake = 3
                            audio.tocar_som("coin")
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
            p.atualizar()
        particles[:] = [p for p in particles if p.life > 0]

        if shake > 0:
            shake -= 1

        offset_x = random.randint(-shake, shake) if shake > 0 else 0
        offset_y = random.randint(-shake, shake) if shake > 0 else 0

        screen.fill(BLACK)
        draw_surf = pygame.Surface((WIDTH, HEIGHT))

        if state == "menu":
            if menu_view == "credits":
                ui.desenhar_creditos(draw_surf, now)
            elif menu_view == "ranking":
                ui.desenhar_ranking(draw_surf, now)
            elif menu_view == "loja":
                ui.desenhar_loja(draw_surf, now, loja_categoria, loja_idx, loja_msg, loja_msg_until)
            elif menu_view == "inventario":
                ui.desenhar_inventario(draw_surf, now, inv_categoria, inv_idx, inv_msg, inv_msg_until)
            else:
                mouse_pos = pygame.mouse.get_pos()
                loja_hover = ui.obter_retangulo_icone_loja().collidepoint(mouse_pos)
                inv_hover = ui.obter_retangulo_icone_inventario().collidepoint(mouse_pos)
                for i, rect in ui.obter_retangulos_menu().items():
                    if rect.collidepoint(mouse_pos):
                        menu_selected = i
                ui.desenhar_menu(draw_surf, now, menu_selected, loja_hover, inv_hover)
        else:
            ui.desenhar_fundo_estrelado(draw_surf, now)
            if bonus_active:
                for coin in bonus_coins:
                    coin.desenhar(draw_surf)
            else:
                for brick in bricks:
                    brick.desenhar(draw_surf)
            paddle.desenhar(draw_surf, now)
            if raio_secreto_ativo:
                ui.desenhar_raio_secreto(draw_surf, raio_secreto_x, paddle.y, now - raio_secreto_inicio)
            if now < paddle_cannons_until:
                ui.desenhar_canhoes(draw_surf, paddle)
            for b in balls:
                b.desenhar(draw_surf, now)
            for pu in powerups:
                pu.desenhar(draw_surf)
            for proj in projectiles:
                proj.desenhar(draw_surf)
            for p in particles:
                p.desenhar(draw_surf)

            # placar em destaque (fonte maior, cor dourada) - é a info principal do HUD
            score_text = score_font.render(f"PONTOS: {score}", True, SCORE_COLOR)
            level_label = "RODADA BONUS" if bonus_active else f"NIVEL: {level}"
            level_color = (255, 215, 0) if bonus_active else WHITE
            level_text = font.render(level_label, True, level_color)
            lives_text = font.render(f"VIDAS: {lives}", True, WHITE)
            time_text = font.render(ui.formatar_tempo(elapsed_ms), True, WHITE)
            draw_surf.blit(score_text, (20, 14))
            draw_surf.blit(level_text, (20, 58))
            draw_surf.blit(lives_text, (WIDTH - 150, 20))
            draw_surf.blit(time_text, (WIDTH // 2 - time_text.get_width() // 2, 20))

            # contagem regressiva dos power-ups ativos / rodada bonus (tempo real, nao frames)
            # só faz sentido mostrar durante o jogo, não na tela de game over
            if not game_over:
                status_y = HEIGHT - 72
                if now < paddle_wide_until:
                    status_y = ui.desenhar_cronometro_powerup(draw_surf, "RAQUETE LARGA", paddle_wide_until, now,
                                                               POWERUP_COLORS["W"], status_y)
                if now < slow_until:
                    status_y = ui.desenhar_cronometro_powerup(draw_surf, "BOLA LENTA", slow_until, now,
                                        POWERUP_COLORS["S"], status_y)
                if now < paddle_cannons_until:
                    status_y = ui.desenhar_cronometro_powerup(draw_surf, "CANHOES", paddle_cannons_until, now,
                                        POWERUP_COLORS["C"], status_y)
                if bonus_active:
                    ui.desenhar_cronometro_powerup(draw_surf, "TEMPO BONUS", bonus_until, now,
                                        (255, 215, 0), status_y)

            if transitioning:
                ui.desenhar_nivel_completo(draw_surf, level, last_bonus_gain)

            if game_over and not entering_name:
                ui.desenhar_mensagem_fim(draw_surf, "GAME OVER", (255, 80, 80), rank_check_phase,
                                          skin_revelada="tempestade" if revelar_skin_lendaria else None,
                                          now_ms=now)

            if paused:
                mouse_pos = pygame.mouse.get_pos()
                for i, rect in ui.obter_retangulos_menu_pausa().items():
                    if rect.collidepoint(mouse_pos):
                        pause_selected = i
                ui.desenhar_menu_pausa(draw_surf, now, pause_selected, audio.sound_volume)

        if entering_name:
            if name_entry_context == "rename":
                ui.desenhar_entrada_nome(draw_surf, player_name, "ALTERAR NOME", (0, 220, 255), "Digite o novo nome:")
            else:
                ui.desenhar_entrada_nome(draw_surf, player_name)

        if offering_potion:
            ui.desenhar_oferta_pocao(draw_surf, profile.obter_pocoes())

        if now < codigo_secreto_msg_until:
            ui.desenhar_notificacao(draw_surf, codigo_secreto_msg)

        screen.blit(draw_surf, (offset_x, offset_y))
        pygame.display.flip()
        clock.tick(FPS)
