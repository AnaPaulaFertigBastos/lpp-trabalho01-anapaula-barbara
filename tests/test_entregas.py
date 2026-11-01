import asyncio
import unittest
from copy import deepcopy
from unittest.mock import AsyncMock, patch
import server


class EntregaTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.original = deepcopy(server.estado)
        self.participantes = deepcopy(server.jogadores)
        server.decisao = asyncio.Lock()
        server.jogadores.update(a={'nome': 'A', 'papel': 'jogador'}, b={'nome': 'B', 'papel': 'jogador'}, m={'nome': 'M', 'papel': 'mestre'})
        server.estado.update(fase='aberta', proxima_producao=105, proxima_chuva=130,
                             concluidas=6, captacao=70, consumo_agua=70, producao=35,
                             construcoes=[{'id': i, 'espaco': i, 'situacao': 'concluida'} for i in range(1, 7)])

    async def asyncTearDown(self):
        server.estado.clear()
        server.estado.update(self.original)
        server.jogadores.clear()
        server.jogadores.update(self.participantes)

    async def test_envio_preserva_estoques_perdas_e_prazos(self):
        antes = deepcopy(server.estado)
        with patch.object(server.sio, 'emit', new_callable=AsyncMock) as emit:
            await server.enviar_lote('a', {'entregas': 999, 'sal': 999})
        esperado = deepcopy(antes)
        esperado.update(entregas=1, ultima_entrega=server.estado['ultima_entrega'], construcoes=[],
                        concluidas=0, em_obra=0, trabalhadores=0, captacao=10, consumo_agua=10, producao=5)
        self.assertEqual(server.estado, esperado)
        emit.assert_awaited_once_with('lote.enviado', server.fato('lote.envio_solicitado', entrega=deepcopy(server.estado['ultima_entrega'])))
        server.acontecimentos_vencidos(105)
        self.assertEqual(server.estado['sal'], antes['sal'] + 5)

    async def test_simultaneos_e_clique_duplo_contam_uma_vez(self):
        async def ceder(*args, **kwargs):
            await asyncio.sleep(0)
        for segundo in ('a', 'b'):
            with self.subTest(segundo=segundo):
                pronto = deepcopy(server.estado)
                with patch.object(server.sio, 'emit', new_callable=AsyncMock, side_effect=ceder) as emit:
                    await asyncio.gather(server.enviar_lote('a'), server.enviar_lote(segundo))
                self.assertEqual([c.args[0] for c in emit.await_args_list], ['lote.enviado', 'operacao.recusada'])
                self.assertEqual(emit.await_args.kwargs, {'to': segundo})
                self.assertEqual(server.estado['entregas'], pronto['entregas'] + 1)
                server.estado.clear()
                server.estado.update(pronto)

    async def test_recusas_individuais_nao_alteram_estado(self):
        for sid, fase in [('ausente', 'aberta'), ('m', 'aberta'), ('a', 'aguardando'), ('a', 'encerrada')]:
            with self.subTest(sid=sid, fase=fase):
                server.estado['fase'] = fase
                antes = deepcopy(server.estado)
                with patch.object(server.sio, 'emit', new_callable=AsyncMock) as emit:
                    await server.enviar_lote(sid)
                self.assertEqual(server.estado, antes)
                self.assertEqual(emit.await_args.args[0], 'operacao.recusada')
                self.assertEqual(emit.await_args.kwargs, {'to': sid})
                self.assertEqual(emit.await_args.args[1]['causa'], 'lote.envio_solicitado')

    async def test_cinco_prontas_e_uma_em_obra_nao_envia(self):
        server.estado['construcoes'][-1].update(situacao='em_obra', conclusao_prevista=108)
        server.estado.update(concluidas=5, em_obra=1, trabalhadores=1)
        antes = deepcopy(server.estado)
        with patch.object(server.sio, 'emit', new_callable=AsyncMock) as emit:
            await server.enviar_lote('a')
        self.assertEqual(server.estado, antes)
        self.assertEqual(emit.await_args.args[1]['motivo'], 'Conclua as seis unidades para enviar um lote')

    async def test_novo_ciclo_com_seis_construcoes_reais(self):
        with patch.object(server.sio, 'emit', new_callable=AsyncMock):
            await server.enviar_lote('a')
            agora = 100
            for _ in range(6):
                while server.estado['sal'] < server.CUSTO:
                    agora += 5
                    server.acontecimentos_vencidos(agora)
                with patch.object(server, 'time', return_value=agora):
                    await server.construir('a')
                agora += 8
                server.acontecimentos_vencidos(agora)
            self.assertEqual(server.estado['concluidas'], 6)
            await server.enviar_lote('b')
        self.assertEqual(server.estado['entregas'], 2)
        self.assertEqual(server.estado['construcoes'], [])

    async def test_sincronizacao_e_encerramento_preservam_entregas(self):
        with patch.object(server.sio, 'emit', new_callable=AsyncMock) as emit:
            await server.enviar_lote('a')
            await server.encerrar_vila('m')
            final = deepcopy(server.estado)
            await server.enviar_lote('b')
            await server.connect('novo', {}, {'papel': 'jogador'})
        self.assertEqual(server.estado, final)
        self.assertEqual(emit.await_args.args[1]['estado']['entregas'], 1)
        self.assertEqual(emit.await_args.args[1]['estado']['ultima_entrega']['por'], 'A')

    async def test_envio_e_encerramento_seguem_ordem_de_decisao(self):
        for primeiro in ('envio', 'encerramento'):
            with self.subTest(primeiro=primeiro):
                pronto = deepcopy(server.estado)
                tarefas = [server.enviar_lote('a'), server.encerrar_vila('m')]
                if primeiro == 'encerramento': tarefas.reverse()
                with patch.object(server.sio, 'emit', new_callable=AsyncMock) as emit:
                    await asyncio.gather(*tarefas)
                self.assertEqual(server.estado['fase'], 'encerrada')
                self.assertEqual(server.estado['entregas'], 1 if primeiro == 'envio' else 0)
                self.assertEqual([c.args[0] for c in emit.await_args_list],
                    ['lote.enviado', 'vila.encerrada'] if primeiro == 'envio' else ['vila.encerrada', 'operacao.recusada'])
                server.estado.clear()
                server.estado.update(pronto)
