import unittest
from copy import deepcopy
from unittest.mock import AsyncMock, patch
import asyncio
import server


class ChuvaTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.original = deepcopy(server.estado)
        self.jogadores = deepcopy(server.jogadores)
        server.decisao = asyncio.Lock()
        server.estado.update(fase="aberta", proxima_producao=5, proxima_chuva=30)

    async def asyncTearDown(self):
        server.estado.clear()
        server.estado.update(self.original)
        server.jogadores.clear()
        server.jogadores.update(self.jogadores)

    async def test_primeira_chuva_apos_seis_ciclos_e_sem_duplicacao(self):
        eventos = server.acontecimentos_vencidos(30)
        self.assertEqual([e for e, _ in eventos][-4:],
                         ["recurso.produzido", "sal.refinado", "chuva.ocorrida", "sal.perdido"])
        chuva, perda = eventos[-2][1], eventos[-1][1]
        self.assertEqual(chuva["estado"]["sal"], 90)
        self.assertEqual(perda["quantidade"], 30)
        self.assertEqual(perda["causa"], "chuva.ocorrida")
        self.assertEqual(sum(l["quantidade"] for l in perda["lotes"]), 30)
        self.assertEqual((server.estado["sal"], server.estado["sal_protegido"], server.estado["sal_exposto"]), (60, 60, 0))
        self.assertEqual(server.estado["agua_mar"], 50)
        self.assertEqual(server.estado["proxima_chuva"], 60)
        self.assertEqual(server.acontecimentos_vencidos(30), [])

    async def test_sem_excedente_nao_emite_perda(self):
        server.consumir_sal(20)
        server.estado["proxima_producao"] = 35
        eventos = server.acontecimentos_vencidos(30)
        self.assertEqual([e for e, _ in eventos], ["chuva.ocorrida"])
        self.assertEqual(server.estado["sal"], 40)
        self.assertEqual(server.estado["sal_perdido"], 0)

    async def test_lote_parcialmente_protegido_preserva_identidade_e_parte_protegida(self):
        server.consumir_sal(3)
        server.acontecimentos_vencidos(5)
        server.estado["proxima_producao"] = 35
        eventos = server.acontecimentos_vencidos(30)
        self.assertEqual(eventos[-1][1]["lotes"], [{"id": 2, "quantidade": 2}])
        self.assertEqual(server.estado["lotes_sal"][1], {"id": 2, "origem": "refino", "produzido_em": 5,
                         "quantidade": 3, "protegido": 3, "exposto": 0})

    async def test_atraso_processa_duas_chuvas_em_ordem(self):
        eventos = server.acontecimentos_vencidos(60)
        perdas = [d for e, d in eventos if e == "sal.perdido"]
        self.assertEqual([d["ocorrida_em"] for d in perdas], [30, 60])
        self.assertEqual([d["quantidade"] for d in perdas], [30, 30])
        self.assertEqual([d["estado"]["sal_perdido"] for d in perdas], [30, 60])
        self.assertEqual(server.estado["sal"], 60)

    async def test_conclusao_producao_chuva_no_mesmo_instante(self):
        server.acontecimentos_vencidos(20)
        server.jogadores["a"] = {"nome": "A", "papel": "jogador"}
        with patch.object(server, "time", return_value=22), patch.object(server.sio, "emit", new_callable=AsyncMock):
            await server.construir("a")
        server.acontecimentos_vencidos(25)
        eventos = server.acontecimentos_vencidos(30)
        self.assertEqual([e for e, _ in eventos], ["construcao.concluida", "recurso.produzido", "sal.refinado", "chuva.ocorrida", "sal.perdido"])
        self.assertEqual(eventos[-1][1]["quantidade"], 15)
        self.assertEqual(server.estado["concluidas"], 1)
        self.assertEqual(server.estado["trabalhadores"], 0)
        self.assertEqual(server.estado["producao"], 10)

    async def test_chuva_nao_altera_obra_ou_salineiro(self):
        server.acontecimentos_vencidos(25)
        server.jogadores["a"] = {"nome": "A", "papel": "jogador"}
        with patch.object(server, "time", return_value=29), patch.object(server.sio, "emit", new_callable=AsyncMock):
            await server.construir("a")
        obras = deepcopy(server.estado["construcoes"])
        server.acontecimentos_vencidos(30)
        self.assertEqual(server.estado["construcoes"], obras)
        self.assertEqual(server.estado["trabalhadores"], 1)
        self.assertEqual(server.estado["agua_mar"], 50)

    async def test_encerrada_nao_tem_chuva(self):
        server.estado["fase"] = "encerrada"
        antes = deepcopy(server.estado)
        self.assertEqual(server.acontecimentos_vencidos(90), [])
        self.assertEqual(server.estado, antes)
