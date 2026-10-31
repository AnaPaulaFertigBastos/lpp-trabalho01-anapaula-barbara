import asyncio
from functools import wraps
from copy import deepcopy
from time import time

import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = socketio.ASGIApp(sio, static_files={
    "/": "client/index.html",
    "/assets/tileset-salina.svg": {"filename": "client/assets/tileset-salina.svg",
                                   "content_type": "image/svg+xml"},
    "/assets": "client/assets",      # mapa, tileset e sprites da vila
})

# Etapa 1: o estado pertence à vila e é compartilhado por todos.
CUSTO = 20
TEMPO_OBRA = 8
INTERVALO = 5
INTERVALO_CHUVA = 30

estado = {
    "fase": "aguardando",
    "encerrada_em": None,
    "agua_mar": 50,
    "sal": 60,
    "sal_protegido": 60,
    "sal_exposto": 0,
    "sal_perdido": 0,
    "capacidade_deposito": 60,
    "trabalhadores": 0,
    "limite": 2,
    "limite_construcoes": 6,
    "concluidas": 0,
    "em_obra": 0,
    "captacao": 10,
    "consumo_agua": 10,
    "producao": 5,
    "intervalo": INTERVALO,
    "tempo_obra": TEMPO_OBRA,
    "custo": CUSTO,
    "intervalo_chuva": INTERVALO_CHUVA,
    "proxima_producao": None,
    "proxima_chuva": None,
    "proximo_lote_id": 2,
    "construcoes": [],
    "lotes_sal": [{"id": 1, "origem": "reserva_inicial", "produzido_em": None,
                   "quantidade": 60, "protegido": 60, "exposto": 0}],
}
jogadores = {}
decisao = asyncio.Lock()


def serializado(funcao):
    """Mantém a ordem das decisões e dos fatos enviados aos participantes."""
    @wraps(funcao)
    async def executar(*args, **kwargs):
        async with decisao:
            return await funcao(*args, **kwargs)
    return executar


def fato(causa, **extras):
    """Retrato independente do estado no momento do acontecimento."""
    return {"estado": deepcopy(estado), "causa": causa, **extras}


@sio.event
@serializado
async def connect(sid, environ, auth=None):
    # Escuta a entrada, identifica o participante e sincroniza só quem chegou.
    auth = auth if isinstance(auth, dict) else {}
    papel = auth.get("papel", "jogador")
    if papel not in ("mestre", "jogador"):
        raise socketio.exceptions.ConnectionRefusedError("Papel inválido")
    nome = auth.get("nome", "")
    nome = nome.strip() if isinstance(nome, str) else ""
    jogadores[sid] = {"nome": nome or "Anônimo", "papel": papel}
    # Não é uma transmissão para todos: os demais já conhecem o estado.
    await sio.emit("estado.sincronizado", fato("conexao"), to=sid)


@sio.event
async def disconnect(sid, reason=None):
    # Sair remove apenas o participante, nunca os recursos da vila.
    jogadores.pop(sid, None)


async def recusar(sid, motivo, causa):
    # A recusa responde apenas a quem pediu e não altera a vila.
    await sio.emit("operacao.recusada", {"motivo": motivo, "causa": causa}, to=sid)


@sio.on("vila.abertura_solicitada")
@serializado
async def abrir_vila(sid, dados=None):
    # Escuta o pedido; só o servidor confirma a abertura para todos.
    pedido = "vila.abertura_solicitada"
    participante = jogadores.get(sid)
    if participante is None:
        await recusar(sid, "Participante não identificado", pedido)
        return
    if participante["papel"] != "mestre":
        await recusar(sid, "Só o Mestre pode abrir a temporada", pedido)
        return
    if estado["fase"] != "aguardando":
        await recusar(sid, "A temporada já foi aberta", pedido)
        return

    # Sem espera entre verificar e alterar: duas aberturas não são aceitas.
    estado["fase"] = "aberta"
    abertura = time()
    estado["proxima_producao"] = abertura + INTERVALO
    estado["proxima_chuva"] = abertura + INTERVALO_CHUVA
    await sio.emit("vila.iniciada", fato(pedido))
    sio.start_background_task(passagem_do_tempo)


@sio.on("vila.encerramento_solicitado")
@serializado
async def encerrar_vila(sid, dados=None):
    # Usa a mesma fila de decisões da produção e das obras.
    pedido = "vila.encerramento_solicitado"
    participante = jogadores.get(sid)
    if participante is None:
        motivo = "Participante não identificado"
    elif participante["papel"] != "mestre":
        motivo = "Só o Mestre pode encerrar a temporada"
    elif estado["fase"] != "aberta":
        motivo = "A temporada não está aberta"
    else:
        motivo = None
    if motivo:
        await recusar(sid, motivo, pedido)
        return
    estado["fase"] = "encerrada"
    estado["encerrada_em"] = time()
    estado["proxima_producao"] = None
    estado["proxima_chuva"] = None
    # Preserva estoques, obras pendentes e salineiros; não há reembolso.
    # O relógio revalida a fase ao despertar e termina sem novos fatos.
    await sio.emit("vila.encerrada", fato(pedido))


def consumir_sal(quantidade):
    """Consome exposto antes de protegido e preserva a ordem dos lotes."""
    lotes = sorted(estado["lotes_sal"], key=lambda lote: (lote["produzido_em"] or 0, lote["id"]))
    restante = quantidade
    for grupo in ("exposto", "protegido"):
        for lote in lotes:
            usado = min(restante, lote[grupo])
            lote[grupo] -= usado
            lote["quantidade"] -= usado
            restante -= usado
    estado["lotes_sal"] = [lote for lote in lotes if lote["quantidade"] > 0]
    capacidade = estado["capacidade_deposito"]
    for lote in estado["lotes_sal"]:
        lote["protegido"] = min(capacidade, lote["quantidade"])
        lote["exposto"] = lote["quantidade"] - lote["protegido"]
        capacidade -= lote["protegido"]
    estado["sal"] = sum(lote["quantidade"] for lote in estado["lotes_sal"])
    estado["sal_protegido"] = sum(lote["protegido"] for lote in estado["lotes_sal"])
    estado["sal_exposto"] = estado["sal"] - estado["sal_protegido"]


@sio.on("construcao.solicitada")
@serializado
async def construir(sid, dados=None):
    # Etapa 4: valida tudo antes de cobrar, sem espera entre validar e reservar.
    # O pedido não escolhe custo, prazo, trabalhador ou espaço: a vila decide.
    pedido = "construcao.solicitada"
    participante = jogadores.get(sid)
    if participante is None:
        motivo = "Participante não identificado"
    elif participante["papel"] != "jogador":
        motivo = "Somente Jogadores podem construir"
    elif estado["fase"] != "aberta":
        motivo = "A temporada não está aberta"
    elif len(estado["construcoes"]) >= estado["limite_construcoes"]:
        motivo = "Não há espaço disponível"
    elif estado["sal"] < CUSTO:
        motivo = "Sal insuficiente"
    elif estado["trabalhadores"] >= estado["limite"]:
        motivo = "Não há salineiro livre"
    else:
        motivo = None
    if motivo:
        await recusar(sid, motivo, pedido)
        return

    # Validar e reservar sem espera impede dois pedidos de gastar o mesmo sal.
    usados = {obra["espaco"] for obra in estado["construcoes"]}
    espaco = next(i for i in range(1, estado["limite_construcoes"] + 1) if i not in usados)
    agora = time()
    obra = {
        "id": max((item["id"] for item in estado["construcoes"]), default=0) + 1,
        "espaco": espaco,
        "tipo": "unidade_salineira",
        "situacao": "em_obra",
        "solicitante": participante["nome"],
        "iniciada_em": agora,
        "conclusao_prevista": agora + TEMPO_OBRA,
    }
    consumir_sal(CUSTO)
    estado["trabalhadores"] += 1
    estado["em_obra"] += 1
    estado["construcoes"].append(obra)
    # Confirma a obra para todos; o relógio da vila cuidará da conclusão.
    await sio.emit("construcao.iniciada", fato(pedido, por=participante["nome"],
                                              construcao=deepcopy(obra)))


def proximo_prazo():
    prazos = [estado["proxima_producao"], estado["proxima_chuva"]]
    prazos.extend(o["conclusao_prevista"] for o in estado["construcoes"] if o["situacao"] == "em_obra")
    return min(p for p in prazos if p is not None)


def acontecimentos_vencidos(agora):
    """Aplica prazos em ordem: conclusão, produção e chuva, em caso de empate."""
    eventos = []
    while estado["fase"] == "aberta" and proximo_prazo() <= agora:
        prazo = proximo_prazo()
        obras = sorted((o for o in estado["construcoes"]
                        if o["situacao"] == "em_obra" and o["conclusao_prevista"] == prazo),
                       key=lambda o: (o["iniciada_em"], o["id"]))
        for obra in obras:
            obra["situacao"] = "concluida"
            obra["concluida_em"] = prazo
            estado["trabalhadores"] -= 1
            estado["em_obra"] -= 1
            estado["concluidas"] += 1
            frentes = 1 + estado["concluidas"]
            estado.update(captacao=10 * frentes, consumo_agua=10 * frentes, producao=5 * frentes)
            eventos.append(("construcao.concluida", fato("construcao.iniciada (temporizador)",
                           por=obra["solicitante"], construcao=deepcopy(obra))))
        if estado["proxima_producao"] == prazo:
            estado["proxima_producao"] += INTERVALO
            estado["agua_mar"] += estado["captacao"]
            eventos.append(("recurso.produzido", fato("temporizador", quantidade=estado["captacao"],
                                                     ciclo_em=prazo)))
            # Captação e refino são uma decisão indivisível para outros pedidos.
            estado["agua_mar"] -= estado["consumo_agua"]
            lote = {"id": estado["proximo_lote_id"], "origem": "refino", "produzido_em": prazo,
                    "quantidade": estado["producao"], "protegido": 0, "exposto": estado["producao"]}
            estado["proximo_lote_id"] += 1
            estado["lotes_sal"].append(lote)
            consumir_sal(0)  # Recalcula a proteção e os totais, sem consumo.
            eventos.append(("sal.refinado", fato("recurso.produzido", quantidade=estado["producao"],
                            agua_consumida=estado["consumo_agua"], lote=deepcopy(lote), ciclo_em=prazo)))
        if estado["proxima_chuva"] == prazo:
            estado["proxima_chuva"] += INTERVALO_CHUVA
            eventos.append(("chuva.ocorrida", fato("temporizador", ocorrida_em=prazo)))
            perdas = [{"id": lote["id"], "quantidade": lote["exposto"]}
                      for lote in estado["lotes_sal"] if lote["exposto"] > 0]
            quantidade = sum(lote["quantidade"] for lote in perdas)
            if quantidade:
                # Só a parte exposta se perde; o mesmo lote pode ter parte protegida.
                for lote in estado["lotes_sal"]:
                    lote["quantidade"] -= lote["exposto"]
                    lote["exposto"] = 0
                estado["sal_perdido"] += quantidade
                consumir_sal(0)
                eventos.append(("sal.perdido", fato("chuva.ocorrida", quantidade=quantidade,
                                                   lotes=perdas, ocorrida_em=prazo)))
    return eventos


async def passagem_do_tempo():
    # Dorme até o próximo acontecimento, sem bloquear conexões ou pedidos.
    while estado["fase"] == "aberta":
        await sio.sleep(max(0, proximo_prazo() - time()))
        async with decisao:
            # Revalida a fase após esperar; uma temporada encerrada não progride.
            for evento, dados in acontecimentos_vencidos(time()):
                await sio.emit(evento, dados)
