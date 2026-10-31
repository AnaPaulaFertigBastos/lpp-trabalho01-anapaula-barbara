import asyncio
import unittest
from copy import deepcopy
from unittest.mock import AsyncMock, patch

import socketio

import server


class SincronizacaoTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        server.decisao = asyncio.Lock()
        self.relogio = patch.object(server.sio, "start_background_task")
        self.relogio.start()
        self.addCleanup(self.relogio.stop)
        self.estado_original = deepcopy(server.estado)
        self.jogadores_originais = deepcopy(server.jogadores)
        server.jogadores.clear()

    async def asyncTearDown(self):
        server.estado.clear()
        server.estado.update(self.estado_original)
        server.jogadores.clear()
        server.jogadores.update(self.jogadores_originais)

    async def test_duas_entradas_recebem_estado_somente_no_proprio_destino(self):
        with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
            await server.connect("a", {}, {"nome": "A", "papel": "mestre"})
            await server.connect("b", {}, {"nome": "B", "papel": "jogador"})
        self.assertEqual(emit.await_count, 2)
        for chamada, destino in zip(emit.await_args_list, ["a", "b"]):
            self.assertEqual(chamada.args[0], "estado.sincronizado")
            self.assertEqual(chamada.kwargs, {"to": destino})
            self.assertEqual(chamada.args[1]["estado"], self.estado_original)
            self.assertEqual(chamada.args[1]["causa"], "conexao")

    async def test_entrada_tardia_recebe_estado_atual_sem_reiniciar(self):
        server.estado["sal"] = 40
        server.estado["sal_protegido"] = 40
        with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
            await server.connect("novo", {}, {"nome": "  ", "papel": "jogador"})
        self.assertEqual(emit.await_args.args[1]["estado"]["sal"], 40)
        self.assertEqual(server.jogadores["novo"]["nome"], "Anônimo")
        await server.disconnect("novo")
        self.assertNotIn("novo", server.jogadores)
        self.assertEqual(server.estado["sal"], 40)

    async def test_papel_invalido_nao_recebe_estado(self):
        with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
            with self.assertRaises(socketio.exceptions.ConnectionRefusedError):
                await server.connect("invalido", {}, {"papel": "administrador"})
        emit.assert_not_awaited()
        self.assertNotIn("invalido", server.jogadores)

    async def test_fato_preserva_retrato_dos_lotes(self):
        retrato = server.fato("conexao")
        server.estado["lotes_sal"][0]["quantidade"] = 0
        self.assertEqual(retrato["estado"]["lotes_sal"][0]["quantidade"], 60)


if __name__ == "__main__":
    unittest.main()
