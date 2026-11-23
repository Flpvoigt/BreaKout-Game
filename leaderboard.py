"""Ranking online (Firebase Realtime Database, gratuito). A URL abaixo nao e
um segredo: qualquer um que clonar o repo acessa o mesmo placar compartilhado
(ver README e as regras do banco)."""
import json
import os
import uuid
import threading
import urllib.request
import urllib.error

LEADERBOARD_BASE_URL = "https://breakoutgame-daf77-default-rtdb.firebaseio.com/leaderboard"
LEADERBOARD_TOP_N = 10        # quantos nomes aparecem na tela de ranking
LEADERBOARD_QUALIFY_N = 100   # precisa superar o 100o colocado pra "entrar" pela 1a vez
LEADERBOARD_TIMEOUT = 4
MAX_NAME_LEN = 12

# Perfil local (1 arquivo por maquina/clone do repo) - guarda um id unico e o
# nome escolhido, pra cada jogador ocupar sempre a MESMA posicao no ranking
# (upsert), em vez de uma entrada nova a cada Game Over.
PROFILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "player_profile.json")

_leaderboard_cache = {"status": "idle", "entries": []}  # status: idle/loading/ok/error
_rank_check_cache = {"status": "idle"}  # status: idle/checking/done/error
_rank_submit_cache = {"status": "idle"}  # status: idle/sending/ok/error


def save_profile(profile):
    try:
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile, f)
    except Exception:
        pass


def load_or_create_profile():
    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "player_id" in data:
            data.setdefault("name", None)
            data.setdefault("best_submitted_score", 0)
            return data
    except Exception:
        pass
    profile = {"player_id": uuid.uuid4().hex, "name": None, "best_submitted_score": 0}
    save_profile(profile)
    return profile


_player_profile = load_or_create_profile()


def _fetch_all_entries():
    """Baixa o node 'leaderboard' inteiro: {player_id: {name, score}, ...}."""
    with urllib.request.urlopen(f"{LEADERBOARD_BASE_URL}.json", timeout=LEADERBOARD_TIMEOUT) as resp:
        raw = json.loads(resp.read().decode("utf-8") or "null")
    entries = {}
    if isinstance(raw, dict):
        for key, item in raw.items():
            if isinstance(item, dict) and "name" in item and "score" in item:
                entries[key] = {"name": str(item["name"])[:MAX_NAME_LEN], "score": int(item["score"])}
    return entries


def _fetch_leaderboard_worker():
    try:
        entries = _fetch_all_entries()
        ranked = sorted(entries.values(), key=lambda e: e["score"], reverse=True)
        _leaderboard_cache["entries"] = [(e["name"], e["score"]) for e in ranked[:LEADERBOARD_TOP_N]]
        _leaderboard_cache["status"] = "ok"
    except Exception:
        _leaderboard_cache["status"] = "error"


def fetch_leaderboard_async():
    """Busca o top do ranking em background pra nao travar o loop do jogo esperando a rede."""
    if _leaderboard_cache["status"] == "loading":
        return
    _leaderboard_cache["status"] = "loading"
    threading.Thread(target=_fetch_leaderboard_worker, daemon=True).start()


def _rank_check_worker(score, player_id):
    """Decide se 'score' merece ir ao ranking: ou e melhora do proprio recorde
    (se o jogador ja tem entrada) ou supera o 100o colocado (se ainda nao tem)."""
    try:
        entries = _fetch_all_entries()
        already_in = player_id in entries
        if already_in and entries[player_id]["score"] >= score:
            qualifies, reason = False, "not_personal_best"
        else:
            scores_sorted = sorted((e["score"] for e in entries.values()), reverse=True)
            if already_in or len(scores_sorted) < LEADERBOARD_QUALIFY_N:
                qualifies, reason = True, "ok"
            else:
                cutoff = scores_sorted[LEADERBOARD_QUALIFY_N - 1]
                qualifies = score > cutoff
                reason = "ok" if qualifies else "not_top100"
        _rank_check_cache.update(status="done", qualifies=qualifies, reason=reason)
    except Exception:
        _rank_check_cache.update(status="error", qualifies=False, reason="error")


def check_rank_async(score, player_id):
    """Verifica em background se a pontuacao entra no ranking, sem travar o jogo."""
    _rank_check_cache["status"] = "checking"
    threading.Thread(target=_rank_check_worker, args=(score, player_id), daemon=True).start()


def _submit_rank_worker(player_id, name, score):
    try:
        url = f"{LEADERBOARD_BASE_URL}/{player_id}.json"
        body = json.dumps({"name": name, "score": score}).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="PUT",
                                      headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=LEADERBOARD_TIMEOUT)
        _rank_submit_cache["status"] = "ok"
    except Exception:
        _rank_submit_cache["status"] = "error"


def submit_rank_async(player_id, name, score):
    """Grava/atualiza a pontuacao do jogador sempre na mesma chave (player_id):
    uma unica posicao no ranking, que so sobe conforme ele joga."""
    _rank_submit_cache["status"] = "sending"
    threading.Thread(target=_submit_rank_worker, args=(player_id, name, score), daemon=True).start()


# ---- Acesso de leitura/escrita pro resto do jogo (game.py / ui.py), sem
# precisar mexer direto nos caches/perfil internos acima. ----

def get_leaderboard_status():
    return _leaderboard_cache["status"]


def get_leaderboard_entries():
    return _leaderboard_cache["entries"]


def get_rank_check_status():
    return _rank_check_cache.get("status")


def get_rank_check_qualifies():
    return _rank_check_cache.get("qualifies")


def get_rank_check_reason():
    return _rank_check_cache.get("reason")


def get_rank_submit_status():
    return _rank_submit_cache.get("status")


def get_player_id():
    return _player_profile["player_id"]


def get_player_name():
    return _player_profile.get("name")


def get_best_submitted_score():
    return _player_profile.get("best_submitted_score", 0)


def set_player_name(name):
    _player_profile["name"] = name
    save_profile(_player_profile)


def set_best_submitted_score(score):
    _player_profile["best_submitted_score"] = score
    save_profile(_player_profile)
