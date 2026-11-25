"""Ranking online (Firebase Realtime Database, gratuito). A URL abaixo nao e
um segredo: qualquer um que clonar o repo acessa o mesmo placar compartilhado
(ver README e as regras do banco). A identidade do jogador (id/nome) vive em
profile.py - este modulo so cuida da comunicacao com o Firebase."""
import json
import ssl
import sys
import threading
import urllib.request
import urllib.error

# No macOS, o Python do instalador oficial costuma nao vir com os
# certificados SSL do sistema configurados - toda chamada HTTPS falha com
# "CERTIFICATE_VERIFY_FAILED" (viramos "erro"/"sem internet?" aqui, sem isso).
# certifi resolve isso de forma portavel; se nao estiver instalado, tenta
# instalar sozinho (mesmo padrao usado pro numpy em audio.py).
try:
    import certifi
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "certifi"], check=False)
    try:
        import certifi
    except ImportError:
        certifi = None

_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where()) if certifi else None

LEADERBOARD_BASE_URL = "https://breakoutgame-daf77-default-rtdb.firebaseio.com/leaderboard"
LEADERBOARD_TOP_N = 10        # quantos nomes aparecem na tela de ranking
LEADERBOARD_QUALIFY_N = 100   # precisa superar o 100o colocado pra "entrar" pela 1a vez
LEADERBOARD_TIMEOUT = 4
MAX_NAME_LEN = 12

_leaderboard_cache = {"status": "idle", "entries": []}  # status: idle/loading/ok/error
_rank_check_cache = {"status": "idle"}  # status: idle/checking/done/error
_rank_submit_cache = {"status": "idle"}  # status: idle/sending/ok/error


def _buscar_todas_entradas():
    """Baixa o node 'leaderboard' inteiro: {player_id: {name, score}, ...}."""
    with urllib.request.urlopen(f"{LEADERBOARD_BASE_URL}.json", timeout=LEADERBOARD_TIMEOUT,
                                 context=_SSL_CONTEXT) as resp:
        raw = json.loads(resp.read().decode("utf-8") or "null")
    entries = {}
    if isinstance(raw, dict):
        for key, item in raw.items():
            if isinstance(item, dict) and "name" in item and "score" in item:
                entries[key] = {"name": str(item["name"])[:MAX_NAME_LEN], "score": int(item["score"])}
    return entries


def _trabalhador_buscar_ranking():
    try:
        entries = _buscar_todas_entradas()
        ranked = sorted(entries.values(), key=lambda e: e["score"], reverse=True)
        _leaderboard_cache["entries"] = [(e["name"], e["score"]) for e in ranked[:LEADERBOARD_TOP_N]]
        _leaderboard_cache["status"] = "ok"
    except Exception:
        _leaderboard_cache["status"] = "error"


def buscar_ranking_async():
    """Busca o top do ranking em background pra nao travar o loop do jogo esperando a rede."""
    if _leaderboard_cache["status"] == "loading":
        return
    _leaderboard_cache["status"] = "loading"
    threading.Thread(target=_trabalhador_buscar_ranking, daemon=True).start()


def _trabalhador_verificar_colocacao(score, player_id):
    """Decide se 'score' merece ir ao ranking: ou e melhora do proprio recorde
    (se o jogador ja tem entrada) ou supera o 100o colocado (se ainda nao tem)."""
    try:
        entries = _buscar_todas_entradas()
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


def verificar_colocacao_async(score, player_id):
    """Verifica em background se a pontuacao entra no ranking, sem travar o jogo."""
    _rank_check_cache["status"] = "checking"
    threading.Thread(target=_trabalhador_verificar_colocacao, args=(score, player_id), daemon=True).start()


def _trabalhador_enviar_colocacao(player_id, name, score):
    try:
        url = f"{LEADERBOARD_BASE_URL}/{player_id}.json"
        body = json.dumps({"name": name, "score": score}).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="PUT",
                                      headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=LEADERBOARD_TIMEOUT, context=_SSL_CONTEXT)
        _rank_submit_cache["status"] = "ok"
    except Exception:
        _rank_submit_cache["status"] = "error"


def enviar_colocacao_async(player_id, name, score):
    """Grava/atualiza a pontuacao do jogador sempre na mesma chave (player_id):
    uma unica posicao no ranking, que so sobe conforme ele joga."""
    _rank_submit_cache["status"] = "sending"
    threading.Thread(target=_trabalhador_enviar_colocacao, args=(player_id, name, score), daemon=True).start()


# ---- Acesso de leitura/escrita pro resto do jogo (game.py / ui.py), sem
# precisar mexer direto nos caches/perfil internos acima. ----

def obter_status_ranking():
    return _leaderboard_cache["status"]


def obter_entradas_ranking():
    return _leaderboard_cache["entries"]


def obter_status_verificacao():
    return _rank_check_cache.get("status")


def obter_verificacao_qualifica():
    return _rank_check_cache.get("qualifies")


def obter_motivo_verificacao():
    return _rank_check_cache.get("reason")


def obter_status_envio():
    return _rank_submit_cache.get("status")
