import asyncio
import unittest
from copy import deepcopy
from unittest.mock import AsyncMock, patch

import server


class TempoTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.original = deepcopy(server.estado)
        self.jogadores = deepcopy(server.jogadores)
        server.decisao = asyncio.Lock()
        server.estado.update(fase="aberta", proxima_producao=5)
        server.jogadores["a"] = {"nome": "A", "papel": "jogador"}

    async def asyncTearDown(self):
        server.estado.clear()
        server.estado.update(self.original)
        server.jogadores.clear()
        server.jogadores.update(self.jogadores)

    async def criar_obra(self, instante):
        with patch.object(server, "time", return_value=instante), patch.object(server.sio, "emit", new_callable=AsyncMock):
            await server.construir("a")

    async def test_primeiro_ciclo_cria_lote_e_protege_ate_capacidade(self):
        self.assertEqual(server.acontecimentos_vencidos(4), [])
        eventos = server.acontecimentos_vencidos(5)
        self.assertEqual([e for e, _ in eventos], ["recurso.produzido", "sal.refinado"])
        self.assertEqual(eventos[0][1]["estado"]["agua_mar"], 60)
        self.assertEqual(server.estado["agua_mar"], 50)
        self.assertEqual((server.estado["sal"], server.estado["sal_protegido"], server.estado["sal_exposto"]), (65, 60, 5))
        self.assertEqual(server.estado["proxima_producao"], 10)
        self.assertEqual(server.acontecimentos_vencidos(5), [])

    async def test_conclusao_libera_e_aumenta_proximo_ciclo(self):
        await self.criar_obra(0)
        server.acontecimentos_vencidos(5)
        self.assertEqual(server.estado["em_obra"], 1)
        eventos = server.acontecimentos_vencidos(8)
        self.assertEqual(eventos[0][0], "construcao.concluida")
        self.assertEqual(server.estado["trabalhadores"], 0)
        self.assertEqual(server.estado["concluidas"], 1)
        self.assertEqual(server.estado["producao"], 10)
        server.acontecimentos_vencidos(10)
        self.assertEqual(server.estado["sal"], 55)

    async def test_empate_conclui_antes_de_produzir(self):
        await self.criar_obra(2)
        server.acontecimentos_vencidos(5)
        eventos = server.acontecimentos_vencidos(10)
        self.assertEqual([e for e, _ in eventos], ["construcao.concluida", "recurso.produzido", "sal.refinado"])
        self.assertEqual(eventos[-1][1]["quantidade"], 10)

    async def test_atraso_preserva_ordem_e_rendimento_historico(self):
        await self.criar_obra(0)
        eventos = server.acontecimentos_vencidos(15)
        self.assertEqual([d["quantidade"] for e, d in eventos if e == "sal.refinado"], [5, 10, 10])
        self.assertEqual(server.estado["sal"], 65)
        self.assertEqual(server.estado["proxima_producao"], 20)

    async def test_duas_obras_concluem_uma_vez_apos_saida(self):
        await self.criar_obra(0)
        await self.criar_obra(0)
        await server.disconnect("a")
        eventos = server.acontecimentos_vencidos(8)
        ids = [d["construcao"]["id"] for e, d in eventos if e == "construcao.concluida"]
        self.assertEqual(ids, [1, 2])
        self.assertEqual(server.estado["trabalhadores"], 0)
        self.assertEqual(server.estado["producao"], 15)
        self.assertEqual(server.acontecimentos_vencidos(8), [])

    async def test_encerramento_durante_espera_nao_produz(self):
        async def encerrar(_):
            server.estado["fase"] = "encerrada"
        with patch.object(server.sio, "sleep", side_effect=encerrar), patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
            await server.passagem_do_tempo()
        emit.assert_not_awaited()
        self.assertEqual(server.estado["sal"], 60)

    async def test_abertura_inicia_um_unico_relogio(self):
        server.estado["fase"] = "aguardando"
        server.jogadores["m"] = {"nome": "M", "papel": "mestre"}
        with patch.object(server.sio, "start_background_task") as iniciar, patch.object(server.sio, "emit", new_callable=AsyncMock), patch.object(server, "time", return_value=100):
            await server.abrir_vila("m")
            await server.abrir_vila("m")
        iniciar.assert_called_once_with(server.passagem_do_tempo)
        self.assertEqual(server.estado["proxima_producao"], 105)
        self.assertEqual(server.estado["proxima_chuva"], 130)
