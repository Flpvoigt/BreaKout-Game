"""Perfil local do jogador: identidade usada no ranking (id/nome/recorde
enviado) e progresso persistente da loja (moedas, skins compradas/equipadas,
pocoes). Guardado em player_profile.json, no mesmo diretorio do jogo, fora
do git."""
import json
import os
import uuid

PROFILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "player_profile.json")

DEFAULT_PROFILE = {
    "player_id": None,
    "name": None,
    "best_submitted_score": 0,
    "coins": 0,
    "owned_ball_skins": ["padrao"],
    "owned_paddle_skins": ["padrao"],
    "equipped_ball_skin": "padrao",
    "equipped_paddle_skin": "padrao",
    "potions": 0,
}


def _salvar_em_disco(data):
    try:
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def _carregar_ou_criar():
    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "player_id" in data:
            for key, value in DEFAULT_PROFILE.items():
                data.setdefault(key, value)
            return data
    except Exception:
        pass
    data = dict(DEFAULT_PROFILE)
    data["player_id"] = uuid.uuid4().hex
    _salvar_em_disco(data)
    return data


_profile = _carregar_ou_criar()


def salvar():
    _salvar_em_disco(_profile)


# ---- identidade / ranking ----

def obter_id_jogador():
    return _profile["player_id"]


def obter_nome_jogador():
    return _profile.get("name")


def definir_nome_jogador(name):
    _profile["name"] = name
    salvar()


def obter_melhor_pontuacao_enviada():
    return _profile.get("best_submitted_score", 0)


def definir_melhor_pontuacao_enviada(score):
    _profile["best_submitted_score"] = score
    salvar()


# ---- moedas ----

def obter_moedas():
    return _profile.get("coins", 0)


def adicionar_moedas(amount):
    _profile["coins"] = obter_moedas() + amount
    salvar()


def gastar_moedas(amount):
    """Tenta gastar 'amount' moedas. Retorna True e debita se tinha saldo."""
    if obter_moedas() < amount:
        return False
    _profile["coins"] = obter_moedas() - amount
    salvar()
    return True


# ---- skins ----

def obter_skins_bola_possuidas():
    return list(_profile.get("owned_ball_skins", ["padrao"]))


def obter_skins_raquete_possuidas():
    return list(_profile.get("owned_paddle_skins", ["padrao"]))


def possui_skin_bola(skin_id):
    return skin_id in obter_skins_bola_possuidas()


def possui_skin_raquete(skin_id):
    return skin_id in obter_skins_raquete_possuidas()


def desbloquear_skin_bola(skin_id):
    skins_list = obter_skins_bola_possuidas()
    if skin_id not in skins_list:
        skins_list.append(skin_id)
        _profile["owned_ball_skins"] = skins_list
        salvar()


def desbloquear_skin_raquete(skin_id):
    skins_list = obter_skins_raquete_possuidas()
    if skin_id not in skins_list:
        skins_list.append(skin_id)
        _profile["owned_paddle_skins"] = skins_list
        salvar()


def obter_skin_bola_equipada():
    return _profile.get("equipped_ball_skin", "padrao")


def equipar_skin_bola(skin_id):
    _profile["equipped_ball_skin"] = skin_id
    salvar()


def obter_skin_raquete_equipada():
    return _profile.get("equipped_paddle_skin", "padrao")


def equipar_skin_raquete(skin_id):
    _profile["equipped_paddle_skin"] = skin_id
    salvar()


# ---- pocoes ----

def obter_pocoes():
    return _profile.get("potions", 0)


def adicionar_pocao():
    _profile["potions"] = obter_pocoes() + 1
    salvar()


def usar_pocao():
    """Consome 1 pocao se houver. Retorna True se consumiu."""
    if obter_pocoes() <= 0:
        return False
    _profile["potions"] = obter_pocoes() - 1
    salvar()
    return True
