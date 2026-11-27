"""Smoke tests: so garantem que as telas principais desenham sem lancar
excecao. Nao verificam pixel nenhum (isso ja foi conferido visualmente a mao
durante o desenvolvimento) - o objetivo aqui e pegar erro bobo de digitacao
(nome de variavel errado, parametro faltando) antes de ir pra producao."""
import pygame

pygame.init()

import ui


def _surf():
    return pygame.Surface((800, 600))


def test_desenhar_menu(perfil_limpo):
    ui.desenhar_menu(_surf(), now_ms=1000, selected=0)


def test_desenhar_creditos():
    ui.desenhar_creditos(_surf(), now_ms=1000)


def test_desenhar_ranking():
    ui.desenhar_ranking(_surf(), now_ms=1000)


def test_desenhar_loja_bolas_e_raquetes(perfil_limpo):
    ui.desenhar_loja(_surf(), now_ms=1000, categoria="bolas", idx=0)
    ui.desenhar_loja(_surf(), now_ms=1000, categoria="raquetes", idx=0)


def test_desenhar_inventario_todas_as_abas(perfil_limpo):
    for categoria in ("bolas", "raquetes", "conquistas"):
        ui.desenhar_inventario(_surf(), now_ms=1000, categoria=categoria, idx=0)


def test_desenhar_mensagem_fim_com_e_sem_skin_revelada():
    ui.desenhar_mensagem_fim(_surf(), "GAME OVER", (255, 80, 80))
    ui.desenhar_mensagem_fim(_surf(), "GAME OVER", (255, 80, 80),
                              rank_phase="submitted_ok", skin_revelada="tempestade", now_ms=500)


def test_desenhar_menu_pausa():
    ui.desenhar_menu_pausa(_surf(), now_ms=1000, selected=0, volume=0.7)


def test_desenhar_notificacao_quebra_linha_texto_longo():
    ui.desenhar_notificacao(_surf(), "Um texto bem comprido pra forcar a quebra de linha no banner")


def test_desenhar_combo_flash():
    ui.desenhar_combo_flash(_surf(), "IMPARAVEL!", (255, 70, 130), now_ms=1000, until_ms=2000)


def test_desenhar_raio_secreto():
    ui.desenhar_raio_secreto(_surf(), x=400, target_y=560, elapsed_ms=300)
