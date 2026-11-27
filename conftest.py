"""Configuracao compartilhada dos testes (pytest). Roda antes de qualquer
import de pygame - por isso forca o driver de video/audio 'dummy', senao os
testes quebram num ambiente sem tela (CI, por exemplo)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest


@pytest.fixture
def perfil_limpo(monkeypatch):
    """Perfil do jogador isolado em memoria pra cada teste - nunca le nem
    escreve o player_profile.json de verdade (nem o de alguem rodando os
    testes, nem o do CI)."""
    import player_profile as profile

    novo_perfil = {
        **profile.DEFAULT_PROFILE,
        "player_id": "teste",
        "owned_ball_skins": ["padrao"],
        "owned_paddle_skins": ["padrao"],
        "stats": dict(profile.DEFAULT_STATS),
        "niveis_conquista_notificados": {},
        "conquistas_especiais": [],
    }
    monkeypatch.setattr(profile, "_profile", novo_perfil)
    monkeypatch.setattr(profile, "salvar", lambda: None)
    return profile
