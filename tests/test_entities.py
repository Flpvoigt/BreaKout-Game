"""Fisica da bola, dano de tijolo e geracao de fases."""
import pygame
import pytest

pygame.init()

from constants import LEVEL_PATTERNS, BALL_MIN_VX
from entities import Ball, Brick, criar_tijolos, _padrao_presente


def test_bola_nunca_fica_quase_vertical():
    """Reproduz o bug real: bola com vx=0 batendo entre teto e raquete ficava
    presa num loop infinito, porque nada no jogo mudava vx ao rebater em
    tijolo/teto. garantir_vx_minimo() e a defesa contra isso."""
    b = Ball()
    b.stuck = False
    b.vx, b.vy = 0.0, -5.0
    b.garantir_vx_minimo()
    assert abs(b.vx) >= BALL_MIN_VX


def test_bola_com_vx_ja_forte_nao_e_alterada():
    b = Ball()
    b.stuck = False
    b.vx, b.vy = 7.0, -5.0
    b.garantir_vx_minimo()
    assert b.vx == 7.0


def test_tijolo_quebra_depois_do_numero_certo_de_batidas():
    tijolo = Brick(0, 0, 50, 20, (255, 0, 0), lives=3)
    assert tijolo.atingir() is False
    assert tijolo.atingir() is False
    assert tijolo.atingir() is True
    assert tijolo.alive is False


def test_tijolo_destruido_nao_quebra_de_novo():
    tijolo = Brick(0, 0, 50, 20, (255, 0, 0), lives=1)
    assert tijolo.atingir() is True
    assert tijolo.atingir() is False  # ja estava morto, nao conta de novo


def test_nivel_1_e_sempre_a_grade_classica_cheia():
    tijolos = criar_tijolos(1)
    assert len(tijolos) == 5 * 10


@pytest.mark.parametrize("pattern", range(LEVEL_PATTERNS))
@pytest.mark.parametrize("rows", range(5, 9))
def test_nenhum_padrao_de_fase_fica_vazio(pattern, rows):
    """Bug real ja encontrado numa revisao: se um padrao deixasse uma fase
    sem nenhum tijolo, 'bricks and all(...)' nunca fica True e o jogador
    trava pra sempre sem conseguir passar de fase."""
    cols = 10
    qtd = sum(
        1
        for row in range(rows)
        for col in range(cols)
        if _padrao_presente(pattern, row, col, rows, cols)
    )
    assert qtd > 0


@pytest.mark.parametrize("level", range(1, 31))
def test_criar_tijolos_sempre_tem_tijolo(level):
    assert len(criar_tijolos(level)) > 0
