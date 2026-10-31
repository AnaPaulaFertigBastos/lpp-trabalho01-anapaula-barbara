import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = socketio.ASGIApp(sio, static_files={
    "/": "client/index.html",
    "/assets": "client/assets",      # mapa, tileset e sprites da vila
})

CUSTO = 50          # toras por construção
TEMPO_OBRA = 8      # segundos até a obra terminar
INTERVALO = 5       # segundos entre as produções


estado = {
    "fase": "aguardando",     # aguardando -> aberta -> encerrada
    "toras": 150,
    "trabalhadores": 0,       # ocupados agora
    "limite": 2,              # máximo de trabalhadores
    "producao": 10,           # toras produzidas a cada INTERVALO
    "intervalo": INTERVALO,
    "tempo_obra": TEMPO_OBRA,
    "custo": CUSTO,
    "concluidas": 0,
    "em_obra": 0,
}

jogadores = {}                # sid -> {"nome": ..., "papel": ...}




def fato(causa, **extras):
    """Monta o payload de um FATO: o estado atual, a CAUSA (o evento ou o
    temporizador que gerou o fato) e dados extras."""
    return {"estado": dict(estado), "causa": causa, **extras}




@sio.event
async def connect(sid, environ, auth):
    auth = auth or {}
    jogadores[sid] = {
        "nome": auth.get("nome", "Anônimo"),
        "papel": auth.get("papel", "jogador"),
    }
    # servidor -> UM cliente: entrega o estado atual
    await sio.emit("estado.sincronizado", fato("conexao"), to=sid)




@sio.event
async def disconnect(sid):
    jogadores.pop(sid, None)

