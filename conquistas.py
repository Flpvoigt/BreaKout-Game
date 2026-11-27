"""Conquistas de longo prazo. A maioria e organizada em trilhas com 5 niveis
(Bronze -> Prata -> Ouro -> Platina -> Diamante) baseadas em estatisticas
acumuladas do jogador (ver player_profile.obter_estatisticas); algumas sao
especiais, sem nivel, ligadas a um evento unico (tipo desbloquear a skin
secreta). A insignia de cada trilha muda de desenho conforme o nivel - ver
ui.py (_desenhar_insignia_conquista)."""
import player_profile as profile

NIVEL_NOMES = {1: "Bronze", 2: "Prata", 3: "Ouro", 4: "Platina", 5: "Diamante"}

TRILHAS = [
    {"id": "tijolos", "nome": "Destruidor de Tijolos", "stat": "tijolos_destruidos",
     "niveis": [100, 1000, 10000, 50000, 200000]},
    {"id": "fases", "nome": "Explorador de Fases", "stat": "maior_nivel",
     "niveis": [10, 25, 50, 100, 200]},
    {"id": "moedas", "nome": "Colecionador de Moedas", "stat": "moedas_total_ganhas",
     "niveis": [500, 2500, 10000, 50000, 200000]},
    {"id": "vidas_extras", "nome": "Sortudo", "stat": "vidas_extras_coletadas",
     "niveis": [1, 5, 15, 30, 50]},
    {"id": "fantasmas", "nome": "Cacador de Fantasmas", "stat": "fantasmas_coletados",
     "niveis": [1, 5, 15, 30, 50]},
    {"id": "partidas", "nome": "Sobrevivente", "stat": "partidas_jogadas",
     "niveis": [1, 10, 30, 75, 150]},
]

ESPECIAIS = [
    {"id": "lendario", "nome": "Lendario",
     "desc": "Desbloqueie a skin ultra-rara Tempestade pelo codigo secreto.",
     "special": "tempestade"},
]


def nivel_da_trilha(trilha, stats=None):
    """Quantos dos limiares da trilha o jogador ja alcancou (0 a 5)."""
    stats = stats if stats is not None else profile.obter_estatisticas()
    valor = stats.get(trilha["stat"], 0)
    nivel = 0
    for limiar in trilha["niveis"]:
        if valor >= limiar:
            nivel += 1
    return nivel


def progresso_da_trilha(trilha, stats=None):
    """(valor_atual, proximo_limiar) - proximo_limiar e None se ja esta no
    nivel maximo (5/5)."""
    stats = stats if stats is not None else profile.obter_estatisticas()
    valor = stats.get(trilha["stat"], 0)
    nivel = nivel_da_trilha(trilha, stats)
    if nivel >= len(trilha["niveis"]):
        return valor, None
    return valor, trilha["niveis"][nivel]


def verificar_novas():
    """Chama depois de qualquer evento que pode ter avancado uma estatistica
    (tijolo destruido, fase concluida, moeda ganha, etc). Idempotente: so
    retorna de novo se o nivel realmente avancar - o 'ja notificado' fica
    persistido no perfil. Retorna uma lista de (nome_exibicao, nivel_ou_None)
    das conquistas recem-desbloqueadas nesta chamada."""
    stats = profile.obter_estatisticas()
    notificados = profile.obter_niveis_notificados()
    novas = []

    for trilha in TRILHAS:
        nivel_atual = nivel_da_trilha(trilha, stats)
        nivel_notificado = notificados.get(trilha["id"], 0)
        if nivel_atual > nivel_notificado:
            novas.append((f"{trilha['nome']} ({NIVEL_NOMES[nivel_atual]})", nivel_atual))
            profile.definir_nivel_notificado(trilha["id"], nivel_atual)

    desbloqueadas = set(profile.obter_conquistas_especiais())
    for especial in ESPECIAIS:
        if especial["id"] in desbloqueadas:
            continue
        conquistou = especial.get("special") == "tempestade" and profile.possui_skin_raquete("tempestade")
        if conquistou:
            profile.desbloquear_conquista_especial(especial["id"])
            novas.append((especial["nome"], None))

    return novas
