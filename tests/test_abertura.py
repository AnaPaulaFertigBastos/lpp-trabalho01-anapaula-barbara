import asyncio
import unittest
from copy import deepcopy
from unittest.mock import AsyncMock, patch

import server


class AberturaTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        server.decisao = asyncio.Lock()
        self.relogio = patch.object(server.sio, "start_background_task")
        self.relogio.start()
        self.addCleanup(self.relogio.stop)
        self.original = deepcopy(server.estado)
        self.participantes = deepcopy(server.jogadores)
        server.estado["fase"] = "aguardando"
        server.jogadores.clear()
        server.jogadores.update({
            "m1": {"nome": "Mestre 1", "papel": "mestre"},
            "m2": {"nome": "Mestre 2", "papel": "mestre"},
            "j": {"nome": "Jogador", "papel": "jogador"},
        })

    async def asyncTearDown(self):
        server.estado.clear()
        server.estado.update(self.original)
        server.jogadores.clear()
        server.jogadores.update(self.participantes)

    async def test_mestre_abre_para_todos_sem_alterar_estoques(self):
        antes = deepcopy(server.estado)
        with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
            await server.abrir_vila("m1")
        antes["fase"] = "aberta"
        antes["proxima_chuva"] = server.estado["proxima_chuva"]
        antes["proxima_producao"] = server.estado["proxima_producao"]
        self.assertIsNotNone(antes["proxima_producao"])
        self.assertEqual(server.estado, antes)
        emit.assert_awaited_once_with("vila.iniciada", {
            "estado": antes, "causa": "vila.abertura_solicitada"})

    async def test_jogador_e_desconhecido_recebem_recusa_individual(self):
        for sid in ["j", "desconhecido"]:
            with self.subTest(sid=sid):
                antes = deepcopy(server.estado)
                with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
                    await server.abrir_vila(sid, {"papel": "mestre"})
                self.assertEqual(server.estado, antes)
                self.assertEqual(emit.await_args.args[0], "operacao.recusada")
                self.assertEqual(emit.await_args.kwargs, {"to": sid})
                self.assertEqual(emit.await_args.args[1]["causa"], "vila.abertura_solicitada")

    async def test_temporada_aberta_ou_encerrada_nao_reabre(self):
        for fase in ["aberta", "encerrada"]:
            with self.subTest(fase=fase):
                server.estado["fase"] = fase
                antes = deepcopy(server.estado)
                with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
                    await server.abrir_vila("m1")
                self.assertEqual(server.estado, antes)
                self.assertEqual(emit.await_args.args[0], "operacao.recusada")
                self.assertEqual(emit.await_args.kwargs, {"to": "m1"})

    async def test_dois_mestres_abrem_apenas_uma_vez(self):
        async def enviar(*args, **kwargs):
            await asyncio.sleep(0)

        with patch.object(server.sio, "emit", new_callable=AsyncMock, side_effect=enviar) as emit:
            await asyncio.gather(server.abrir_vila("m1"), server.abrir_vila("m2"))
        eventos = [c.args[0] for c in emit.await_args_list]
        self.assertEqual(eventos.count("vila.iniciada"), 1)
        self.assertEqual(eventos.count("operacao.recusada"), 1)
        self.assertEqual(server.estado["fase"], "aberta")

    async def test_entrada_apos_abertura_recebe_fase_aberta(self):
        with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
            await server.abrir_vila("m1")
            await server.connect("novo", {}, {"papel": "jogador"})
        chamada = emit.await_args_list[-1]
        self.assertEqual(chamada.args[0], "estado.sincronizado")
        self.assertEqual(chamada.args[1]["estado"]["fase"], "aberta")
        self.assertEqual(chamada.kwargs, {"to": "novo"})
