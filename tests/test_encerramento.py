import asyncio
import unittest
from copy import deepcopy
from unittest.mock import AsyncMock, patch

import server


class EncerramentoTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.original = deepcopy(server.estado)
        self.participantes = deepcopy(server.jogadores)
        server.decisao = asyncio.Lock()
        server.estado.update(fase="aberta", proxima_producao=5)
        server.jogadores.update(m={"nome": "M", "papel": "mestre"},
                                a={"nome": "A", "papel": "jogador"})

    async def asyncTearDown(self):
        server.estado.clear()
        server.estado.update(self.original)
        server.jogadores.clear()
        server.jogadores.update(self.participantes)

    async def test_encerra_com_obra_sem_reembolso_ou_conclusao_posterior(self):
        with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit, patch.object(server, "time", return_value=1):
            await server.construir("a")
            antes = deepcopy(server.estado)
            await server.encerrar_vila("m")
        antes.update(fase="encerrada", encerrada_em=1, proxima_producao=None, proxima_chuva=None)
        self.assertEqual(server.estado, antes)
        self.assertEqual(emit.await_args.args, ("vila.encerrada", {"estado": antes, "causa": "vila.encerramento_solicitado"}))
        self.assertEqual(emit.await_args.kwargs, {})
        self.assertEqual(server.acontecimentos_vencidos(1000), [])
        self.assertEqual(server.estado, antes)

    async def test_recusas_individuais_sem_alteracao(self):
        for sid, fase, motivo in [
            ("ausente", "aberta", "Participante não identificado"),
            ("a", "aberta", "Só o Mestre pode encerrar a temporada"),
            ("m", "aguardando", "A temporada não está aberta"),
            ("m", "encerrada", "A temporada não está aberta"),
        ]:
            with self.subTest(sid=sid, fase=fase):
                server.estado["fase"] = fase
                antes = deepcopy(server.estado)
                with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
                    await server.encerrar_vila(sid)
                emit.assert_awaited_once_with("operacao.recusada", {
                    "motivo": motivo, "causa": "vila.encerramento_solicitado"}, to=sid)
                self.assertEqual(server.estado, antes)

    async def test_apos_encerrar_nao_constroi_nem_reabre_e_sincroniza_final(self):
        with patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
            await server.encerrar_vila("m")
            final = deepcopy(server.estado)
            await server.construir("a")
            await server.abrir_vila("m")
            await server.connect("novo", {}, {"papel": "jogador"})
        self.assertEqual(server.estado, final)
        self.assertEqual([c.args[0] for c in emit.await_args_list],
                         ["vila.encerrada", "operacao.recusada", "operacao.recusada", "estado.sincronizado"])
        self.assertEqual(emit.await_args.args[1]["estado"], final)

    async def test_relogio_pendente_para_apos_encerramento_real(self):
        async def encerrar(_):
            await server.encerrar_vila("m")
        with patch.object(server.sio, "sleep", side_effect=encerrar), patch.object(server.sio, "emit", new_callable=AsyncMock) as emit:
            await server.passagem_do_tempo()
        self.assertEqual([c.args[0] for c in emit.await_args_list], ["vila.encerrada"])
        self.assertEqual(server.estado["sal"], 60)

    async def test_dois_encerramentos_confirmam_apenas_um(self):
        async def enviar(*args, **kwargs):
            await asyncio.sleep(0)
        with patch.object(server.sio, "emit", new_callable=AsyncMock, side_effect=enviar) as emit:
            await asyncio.gather(server.encerrar_vila("m"), server.encerrar_vila("m"))
        self.assertEqual([c.args[0] for c in emit.await_args_list], ["vila.encerrada", "operacao.recusada"])
