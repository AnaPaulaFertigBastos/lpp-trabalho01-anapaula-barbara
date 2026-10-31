import asyncio
import unittest
from copy import deepcopy
from unittest.mock import AsyncMock, patch

import server


class ConstrucaoTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        server.decisao = asyncio.Lock()
        self.relogio = patch.object(server.sio, "start_background_task")
        self.relogio.start()
        self.addCleanup(self.relogio.stop)
        self.original = deepcopy(server.estado)
        self.participantes = deepcopy(server.jogadores)
        server.estado["fase"] = "aberta"
        server.jogadores.clear()
        server.jogadores.update({
            "a": {"nome": "A", "papel": "jogador"},
            "b": {"nome": "B", "papel": "jogador"},
            "m": {"nome": "Mestre", "papel": "mestre"},
        })

    async def asyncTearDown(self):
        server.estado.clear()
        server.estado.update(self.original)
        server.jogadores.clear()
        server.jogadores.update(self.participantes)

    async def test_construcao_cobra_reserva_e_informa_todos(self):
        with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit, patch.object(server, "time", return_value=1000):
            await server.construir("a", {"custo": 0, "espaco": 6})
        self.assertEqual(server.estado["sal"], 40)
        self.assertEqual(server.estado["sal_protegido"], 40)
        self.assertEqual(server.estado["trabalhadores"], 1)
        self.assertEqual(server.estado["em_obra"], 1)
        obra = server.estado["construcoes"][0]
        self.assertEqual((obra["espaco"], obra["conclusao_prevista"]), (1, 1008))
        self.assertEqual(emit.await_args.args[0], "construcao.iniciada")
        self.assertEqual(emit.await_args.kwargs, {})
        self.assertEqual(emit.await_args.args[1]["causa"], "construcao.solicitada")

    async def test_recusas_nao_modificam_estado(self):
        for sid, fase in [("m", "aberta"), ("ausente", "aberta"), ("a", "aguardando"), ("a", "encerrada")]:
            with self.subTest(sid=sid, fase=fase):
                server.estado["fase"] = fase
                antes = deepcopy(server.estado)
                with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
                    await server.construir(sid)
                self.assertEqual(server.estado, antes)
                self.assertEqual(emit.await_args.args[0], "operacao.recusada")
                self.assertEqual(emit.await_args.kwargs, {"to": sid})

    async def test_disputa_pelo_ultimo_salineiro(self):
        with patch.object(server.sio, "emit", new_callable=AsyncMock):
            await server.construir("a")
        async def enviar(*args, **kwargs):
            await asyncio.sleep(0)
        with patch.object(server.sio, "emit", new_callable=AsyncMock, side_effect=enviar) as emit:
            await asyncio.gather(server.construir("a"), server.construir("b"))
        self.assertEqual([c.args[0] for c in emit.await_args_list].count("construcao.iniciada"), 1)
        self.assertEqual(server.estado["sal"], 20)
        self.assertEqual(server.estado["trabalhadores"], 2)
        self.assertEqual([c["espaco"] for c in server.estado["construcoes"]], [1, 2])
        self.assertEqual(emit.await_args_list[-1].kwargs, {"to": "b"})

    async def test_disputa_pelo_ultimo_sal(self):
        server.consumir_sal(40)
        with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
            await asyncio.gather(server.construir("a"), server.construir("b"))
        self.assertEqual(server.estado["sal"], 0)
        self.assertEqual(server.estado["lotes_sal"], [])
        self.assertEqual(server.estado["em_obra"], 1)
        self.assertEqual(emit.await_args.args[1]["motivo"], "Sal insuficiente")

    async def test_consume_exposto_antes_de_protegido(self):
        server.estado["lotes_sal"].append({"id": 2, "produzido_em": 100, "quantidade": 15, "protegido": 0, "exposto": 15})
        server.estado.update(sal=75, sal_exposto=15)
        with patch.object(server.sio, "emit", new_callable=AsyncMock):
            await server.construir("a")
        self.assertEqual(server.estado["sal"], 55)
        self.assertEqual(server.estado["sal_protegido"], 55)
        self.assertEqual(server.estado["sal_exposto"], 0)
        self.assertEqual(len(server.estado["lotes_sal"]), 1)
        self.assertEqual(server.estado["lotes_sal"][0]["id"], 1)

    async def test_sem_espaco_recusa_sem_cobranca(self):
        server.estado["construcoes"] = [{"id": i, "espaco": i, "situacao": "concluida"} for i in range(1, 7)]
        server.estado["concluidas"] = 6
        antes = deepcopy(server.estado)
        with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
            await server.construir("a")
        self.assertEqual(server.estado, antes)
        self.assertEqual(emit.await_args.args[1]["motivo"], "Não há espaço disponível")

    async def test_saida_e_entrada_tardia_preservam_obra(self):
        with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
            await server.construir("a")
            obra = deepcopy(server.estado["construcoes"][0])
            await server.disconnect("a")
            await server.connect("novo", {}, {"papel": "jogador"})
        self.assertEqual(emit.await_args.args[1]["estado"]["construcoes"], [obra])
        self.assertEqual(server.estado["trabalhadores"], 1)

    async def test_sal_insuficiente_recusa_sem_alterar_lotes_ou_reservas(self):
        for saldo in (0, 19):
            with self.subTest(saldo=saldo):
                server.estado.update(sal=saldo, sal_protegido=saldo, sal_exposto=0)
                server.estado["lotes_sal"] = (
                    [{"id": 1, "produzido_em": None, "quantidade": saldo,
                      "protegido": saldo, "exposto": 0}] if saldo else [])
                antes = deepcopy(server.estado)
                with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
                    await server.construir("a")
                self.assertEqual(server.estado, antes)
                emit.assert_awaited_once_with("operacao.recusada", {
                    "motivo": "Sal insuficiente", "causa": "construcao.solicitada"}, to="a")

    async def test_terceiro_pedido_recusa_sem_cobrar_nem_avisar_outros(self):
        with patch.object(server.sio, "emit", new_callable=AsyncMock):
            await server.construir("a")
            await server.construir("b")
        antes = deepcopy(server.estado)
        with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
            await server.construir("a")
        self.assertEqual(server.estado, antes)
        emit.assert_awaited_once_with("operacao.recusada", {
            "motivo": "Não há salineiro livre", "causa": "construcao.solicitada"}, to="a")

    async def test_primeiro_motivo_segue_ordem_da_especificacao(self):
        server.estado.update(fase="aguardando", sal=0, sal_protegido=0, trabalhadores=2)
        server.estado["lotes_sal"] = []
        server.estado["construcoes"] = [{"id": i, "espaco": i} for i in range(1, 7)]
        casos = [
            ("ausente", "Participante não identificado"),
            ("m", "Somente Jogadores podem construir"),
            ("a", "A temporada não está aberta"),
        ]
        for sid, motivo in casos:
            antes = deepcopy(server.estado)
            with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
                await server.construir(sid)
            self.assertEqual(server.estado, antes)
            emit.assert_awaited_once_with("operacao.recusada", {
                "motivo": motivo, "causa": "construcao.solicitada"}, to=sid)
        server.estado["fase"] = "aberta"
        for motivo in ("Não há espaço disponível", "Sal insuficiente"):
            antes = deepcopy(server.estado)
            with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
                await server.construir("a")
            self.assertEqual(server.estado, antes)
            emit.assert_awaited_once_with("operacao.recusada", {
                "motivo": motivo, "causa": "construcao.solicitada"}, to="a")
            server.estado["construcoes"] = []
