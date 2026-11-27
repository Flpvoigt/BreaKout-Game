"""Catalogo de skins consistente e cada skin desenha sem crashar."""
import pygame
import pytest

pygame.init()

import skins


def test_toda_skin_de_bola_na_ordem_existe_no_catalogo():
    for skin_id in skins.BALL_SKIN_ORDER:
        assert skin_id in skins.BALL_SKINS


def test_toda_skin_de_raquete_na_ordem_existe_no_catalogo():
    for skin_id in skins.PADDLE_SKIN_ORDER:
        assert skin_id in skins.PADDLE_SKINS


def test_skin_padrao_e_gratis_e_sempre_existe():
    assert skins.BALL_SKINS["padrao"]["preco"] == 0
    assert skins.PADDLE_SKINS["padrao"]["preco"] == 0


def test_tempestade_fica_fora_da_loja_de_proposito():
    """So existe pelo codigo secreto - nao pode aparecer como compravel."""
    assert "tempestade" not in skins.PADDLE_SKIN_ORDER
    assert "tempestade" in skins.PADDLE_SKINS


@pytest.mark.parametrize("skin_id", list(skins.BALL_SKINS.keys()))
def test_toda_skin_de_bola_desenha_sem_erro(skin_id):
    surf = pygame.Surface((80, 80))
    skins.desenhar_bola(surf, 40, 40, 20, skin_id, now_ms=1234,
                         trail=[(30, 40), (35, 40)])


@pytest.mark.parametrize("skin_id", list(skins.PADDLE_SKINS.keys()))
def test_toda_skin_de_raquete_desenha_sem_erro(skin_id):
    surf = pygame.Surface((140, 30))
    rect = pygame.Rect(10, 5, 110, 16)
    skins.desenhar_raquete(surf, rect, skin_id, now_ms=1234)


def test_raridades_so_referenciam_skins_que_existem():
    for skin_id in skins.RARIDADE_LENDARIA:
        assert skin_id in skins.BALL_SKINS or skin_id in skins.PADDLE_SKINS
    for skin_id in skins.RARIDADE_SECRETA:
        assert skin_id in skins.BALL_SKINS or skin_id in skins.PADDLE_SKINS
