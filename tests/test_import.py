"""Sanidade basica: todo modulo tem sintaxe valida e o jogo inteiro importa
sem erro. Esse e o teste que teria pego praticamente todo bug de digitacao
cometido ao longo deste projeto."""
import ast
import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MODULOS = sorted(p.name for p in RAIZ.glob("*.py") if p.name != "conftest.py")


@pytest.mark.parametrize("nome_arquivo", MODULOS)
def test_sintaxe_valida(nome_arquivo):
    caminho = RAIZ / nome_arquivo
    ast.parse(caminho.read_text(encoding="utf-8"))


def test_jogo_importa_sem_erro():
    import main  # noqa: F401 - so testando que a importacao nao explode
