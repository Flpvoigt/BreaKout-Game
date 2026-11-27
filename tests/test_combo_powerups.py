"""Matematica do combo e consistencia do catalogo de power-ups. A logica do
combo mora dentro de uma closure em game.py (principal()), entao aqui ela e
reproduzida isolada - e a mesma formula usada la, so sem o estado do jogo."""
import pygame
import pytest

pygame.init()

from constants import (
    COMBO_MULTIPLICADOR_PASSO, COMBO_MULTIPLICADOR_MAX, COMBO_MENSAGENS,
    POWERUP_COLORS, POWERUP_WEIGHTS,
)


def multiplicador(combo_contador):
    return min(COMBO_MULTIPLICADOR_MAX, 1 + combo_contador // COMBO_MULTIPLICADOR_PASSO)


@pytest.mark.parametrize("combo,esperado", [
    (0, 1), (1, 1), (2, 1), (3, 2), (5, 2), (6, 3), (9, 4), (12, 5), (100, 5),
])
def test_escalada_do_multiplicador(combo, esperado):
    assert multiplicador(combo) == esperado


def test_multiplicador_nunca_passa_do_maximo():
    assert multiplicador(10_000) == COMBO_MULTIPLICADOR_MAX


def test_mensagens_de_hype_cobrem_do_nivel_2_ao_maximo():
    assert set(COMBO_MENSAGENS.keys()) == set(range(2, COMBO_MULTIPLICADOR_MAX + 1))


def test_toda_cor_de_powerup_tem_peso_de_sorteio():
    assert set(POWERUP_COLORS.keys()) == set(POWERUP_WEIGHTS.keys())


def test_vida_extra_e_fantasma_sao_bem_mais_raros_que_os_comuns():
    """Regressao do pedido real: 'coloca algo pra vida extra ser mais rara,
    senao o player nunca morre'."""
    assert POWERUP_WEIGHTS["L"] < POWERUP_WEIGHTS["W"]
    assert POWERUP_WEIGHTS["F"] < POWERUP_WEIGHTS["W"]
