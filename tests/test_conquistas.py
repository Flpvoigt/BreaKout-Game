"""Logica de conquistas: niveis das trilhas, idempotencia do aviso e a
conquista especial. Usa o fixture 'perfil_limpo' (ver conftest.py) - nunca
toca no player_profile.json de verdade."""
import pygame

pygame.init()

import conquistas


def test_nivel_da_trilha_sobe_a_cada_limiar(perfil_limpo):
    trilha = conquistas.TRILHAS[0]
    stats = {trilha["stat"]: 0}
    assert conquistas.nivel_da_trilha(trilha, stats) == 0

    stats[trilha["stat"]] = trilha["niveis"][0]
    assert conquistas.nivel_da_trilha(trilha, stats) == 1

    stats[trilha["stat"]] = trilha["niveis"][-1]
    assert conquistas.nivel_da_trilha(trilha, stats) == 5


def test_nivel_trava_em_5_mesmo_passando_muito_do_ultimo_limiar():
    trilha = conquistas.TRILHAS[0]
    stats = {trilha["stat"]: trilha["niveis"][-1] * 1000}
    assert conquistas.nivel_da_trilha(trilha, stats) == 5
    _valor, proximo = conquistas.progresso_da_trilha(trilha, stats)
    assert proximo is None


def test_verificar_novas_e_idempotente(perfil_limpo):
    trilha = conquistas.TRILHAS[0]
    perfil_limpo.incrementar_estatistica(trilha["stat"], trilha["niveis"][0])

    novas = conquistas.verificar_novas()
    assert len(novas) >= 1
    assert any(nivel == 1 for _nome, nivel in novas if nivel is not None)

    novas_de_novo = conquistas.verificar_novas()
    assert novas_de_novo == []


def test_pular_varios_niveis_de_uma_vez_anuncia_so_o_mais_alto(perfil_limpo):
    trilha = conquistas.TRILHAS[0]
    perfil_limpo.incrementar_estatistica(trilha["stat"], trilha["niveis"][2])

    novas = conquistas.verificar_novas()
    desta_trilha = [nivel for nome, nivel in novas if trilha["nome"] in nome]
    assert desta_trilha == [3]


def test_conquista_especial_lendario(perfil_limpo):
    assert conquistas.verificar_novas() == []

    perfil_limpo.desbloquear_skin_raquete("tempestade")
    novas = conquistas.verificar_novas()
    assert ("Lendario", None) in novas

    # nao anuncia de novo
    assert conquistas.verificar_novas() == []
