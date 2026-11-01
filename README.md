# Vila em Tempo Real — Salina

Vila cooperativa de produção de sal a partir de água do mar. As regras planejadas estão em [docs/especificacao.md](docs/especificacao.md).

## Estado do projeto

Etapa 8 do Guia de Implementação concluída: tema Salina, cenário próprio, chuva e perda do sal exposto. As etapas 0 a 7 também estão concluídas.

O Mestre abre a temporada. A cada cinco segundos, o servidor capta 10 unidades de água por frente e as transforma em 5 de sal. Há uma frente básica e mais uma por unidade concluída. A água inicial é 50; o sal inicial é 60, protegido no depósito de capacidade 60. O excedente produzido fica exposto.

Cada construção custa 20 de sal e ocupa um dos dois salineiros durante oito segundos. Ao terminar, a unidade fica pronta, libera o salineiro e aumenta captação e refino. A tela reage aos eventos `recurso.produzido`, `sal.refinado` e `construcao.concluida`, sem consultas periódicas ao servidor. O mapa mostra areia, mar, depósito fixo, frente básica e seis espaços de unidades com tanque e secagem. Obras têm canteiro e barra de progresso.

Um único relógio no servidor atende aos prazos das obras, da produção e da chuva. Em prazos iguais, conclui obras, produz e depois aplica a chuva. Captação e refino ocorrem sem intercalação de pedidos. A entrada tardia recebe o estado atual e as obras com seus prazos originais. Sair não cancela obras ou produção. Reiniciar o servidor volta ao estado inicial.

O Mestre pode encerrar a temporada pelo botão. Todos recebem `vila.encerrada`, a vila escurece e as barras das obras ficam congeladas no instante do encerramento. Estoques, obras inacabadas e salineiros ocupados são preservados, sem reembolso. Não há produção ou conclusão posterior, nem reabertura. A entrada tardia recebe essa mesma situação final. Pedidos de construção após encerrar são recusados apenas ao solicitante.

O painel exibe contadores por nome de evento, incluindo pedidos enviados e fatos ou recusas recebidos. Cada aba conta apenas seus próprios registros. A chuva ocorre a cada 30 segundos contados da abertura. `chuva.ocorrida` informa a ocorrência para todos; se houver excedente, `sal.perdido` remove apenas a parte exposta dos lotes e acumula a perda. O depósito protege até 60, priorizando os lotes antigos. Sem excedente, a tela informa perda zero e não há evento de perda. A chuva não afeta água, obras ou salineiros. O contador regressivo é apenas visual; o servidor decide os acontecimentos.

Nos pedidos de abertura, construção e encerramento, o painel identifica o clique como causa e descreve a reação local: enviar a intenção e aguardar confirmação ou recusa do servidor. Pedidos sem conteúdo exibem “Sem dados adicionais”. Essas descrições pertencem ao histórico da tela e não alteram os dados enviados ao servidor.

## Integrantes
- Integrante 1: nome e @usuario-github a preencher.
- Integrante 2: nome e @usuario-github a preencher.

## Como instalar e executar
Pré-requisito: Python 3 instalado. Execute os comandos abaixo no PowerShell, dentro da pasta `salina`.

Na primeira preparação, crie o ambiente e instale as dependências. Se `.venv` já existir, pule a criação:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Inicie o servidor:

```powershell
.\.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```

Abra http://127.0.0.1:8000 no navegador. Não abra o arquivo HTML diretamente. Mantenha o terminal aberto; para parar o servidor, pressione `Ctrl+C`.

Se a porta 8000 estiver ocupada, use `--port 8001` e abra http://127.0.0.1:8001. A verificação desta etapa utilizou essa alternativa porque a porta 8000 já estava ocupada.

A tela carrega suas bibliotecas pela internet. Se a entrada não aparecer ou o cenário não carregar, confira a conexão e o carregamento dos scripts.

## Como testar com duas abas

1. Reinicie o servidor e abra o endereço em duas abas, entrando como Mestre e Jogador.
2. Antes da abertura, confira água 50, sal 60, salineiros 0/2 e fase `aguardando`. Esperar não muda esses valores.
3. Peça uma construção antes da abertura: somente o Jogador recebe recusa, sem cobrança.
4. O Mestre abre a temporada. Ambas recebem `vila.iniciada` e a faixa muda para **Temporada aberta**. Uma segunda abertura é recusada apenas ao Mestre.
5. Sem construir, aguarde cinco segundos: aparecem `recurso.produzido` e `sal.refinado`. A água volta a 50; o sal passa a 65, com 60 protegidos e 5 expostos. Cada novo ciclo acrescenta mais 5.
6. O Jogador constrói: ambas descontam 20 do saldo atual, ocupam um salineiro e mostram o canteiro. O painel identifica o pedido e o fato de início.
7. Oito segundos após o pedido aceito, ambas recebem `construcao.concluida`: o canteiro vira unidade pronta, o salineiro fica livre e a capacidade passa a 10 de sal por ciclo. A produção continua em paralelo à obra.
8. Inicie duas obras rapidamente: a ocupação chega a 2/2. Antes de elas terminarem, tente uma terceira: somente quem pediu recebe **Não há salineiro livre**, sem cobrança. Quando terminarem, os salineiros ficam livres novamente.
9. Recarregue uma aba durante uma obra e entre de novo. A obra reaparece no mesmo espaço, com o prazo restante; os recursos não reiniciam e a conclusão chega às duas abas.
10. Cada unidade pronta acrescenta 10 à captação/consumo de água e 5 à produção de sal por ciclo. Com duas unidades prontas, são 30 de água captada e consumida e 15 de sal a cada cinco segundos.

Os saldos variam com os ciclos de produção entre os cliques. Compare a cobrança de 20 com o saldo imediatamente anterior e acompanhe os eventos para distinguir produção de consumo.

## Encerramento e disputa da Etapa 6

### Encerramento com obra pendente

1. Abra a temporada, inicie uma obra e encerre pelo Mestre antes dos oito segundos.
2. Ambas as abas mostram `encerrada`, o aviso e a vila escurecida. O Mestre registra `vila.encerramento_solicitado`; todos recebem `vila.encerrada` com esse pedido como causa.
3. Anote os estoques, a ocupação e as obras. Aguarde pelo menos dez segundos: os valores e o progresso visual permanecem iguais; não há novos fatos de produção ou conclusão.
4. Peça outra construção: somente o Jogador recebe **A temporada não está aberta**, sem desconto.
5. Tente abrir novamente ou encerrar outra vez: apenas o solicitante recebe recusa.
6. Recarregue uma aba e entre novamente: veja a mesma situação final, incluindo o progresso congelado da obra. Uma nova temporada requer reiniciar o servidor.

### Disputa pelo último salineiro

1. Reinicie o servidor e entre em três abas: Mestre, Jogador A e Jogador B.
2. Abra a temporada e inicie uma obra, deixando ocupação 1/2.
3. Antes de ela terminar, A e B pedem outra obra quase simultaneamente.
4. Apenas um pedido é aceito. Todos recebem o fato da obra aceita; somente quem perdeu recebe **Não há salineiro livre**. A ocupação não ultrapassa 2/2.
5. As obras aceitas terminam normalmente se a temporada continuar aberta. Se o Mestre encerrar, as pendentes ficam preservadas na situação final.

A decisão de encerramento usa a mesma fila das construções e dos acontecimentos automáticos. Fatos já confirmados permanecem válidos; depois de `vila.encerrada` não há novas alterações. Os botões permitem visualizar as recusas, mas o servidor impede ações incompatíveis com a fase.

## Validações da Etapa 4

Antes de qualquer cobrança, o servidor verifica nesta ordem: identificação, papel de Jogador, temporada aberta, espaço disponível, sal suficiente e salineiro livre. Apenas o primeiro motivo inválido é comunicado. O pedido não pode escolher seu próprio custo ou alterar os limites.

A recusa emite somente `operacao.recusada`, com `motivo` e `causa`, para a conexão que pediu. Não altera estoques, lotes, salineiros, construções ou prazos. O cliente mostra o aviso vermelho, registra o evento e faz a reação visual da vila, sem substituir seu estado por dados da recusa. Os demais participantes não recebem esse aviso.

Validação e reserva são feitas sem espera entre elas, para que pedidos concorrentes não usem o mesmo saldo ou salineiro. O servidor é responsável por essa decisão, independentemente dos botões da tela.

### Como conferir a recusa individual

Peça duas obras e tente uma terceira antes dos oito segundos. Só a aba solicitante recebe `operacao.recusada`, com causa `construcao.solicitada`. A recusa não cobra sal. Eventos de produção continuam chegando a todos independentemente da recusa.

O teste de sal insuficiente usa sal zero e 19 em estados isolados, sem alterar os parâmetros da aplicação.

## Contadores da Etapa 7

- Ao entrar, o painel apresenta `estado.sincronizado ×1`.
- Cada envio ou recebimento aumenta uma vez o contador daquele nome. Por exemplo, dois pedidos recusados resultam em `construcao.solicitada ×2` e `operacao.recusada ×2` na aba solicitante.
- Um pedido enviado pelo Mestre não aparece no contador do Jogador; o fato compartilhado aparece nos dois. Recusas permanecem individuais.
- O filtro de `recurso.produzido` só oculta linhas do histórico; não altera os contadores, que continuam crescendo com os novos eventos.
- Os totais não dependem do limite de 40 registros visíveis do histórico.
- Recarregar e entrar novamente, ou reconectar, inicia novos contadores locais, começando com a nova sincronização.

Para conferir, entre em duas abas e compare seus contadores. Na temporada encerrada, faça dois pedidos de construção pelo Jogador: somente ele deve acumular os pedidos e recusas. Marque e desmarque o filtro e confirme que os totais permanecem iguais. Recarregue essa aba, entre novamente e confira apenas `estado.sincronizado ×1`.

## Testes automatizados

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os 45 testes verificam sincronização individual, entrada tardia, saída sem perda de recursos, nome em branco, papel inválido, independência do retrato enviado, abertura válida, recusa de Jogador ou participante desconhecido, impedimento de reabertura e dois Mestres tentando abrir ao mesmo tempo. Também verificam cobrança e reserva da obra, recusas sem alteração de estado, disputa pelo último salineiro ou sal, consumo prioritário do excedente, limite de espaços e preservação da obra após saída e nova entrada. A Etapa 4 acrescenta a conferência integral do estado após recusa por saldo zero ou 19 de sal, recusa do terceiro pedido com destino individual e prioridade dos motivos quando mais de uma condição é inválida.

Os testes de tempo também verificam o primeiro ciclo, criação e proteção de lotes, conclusão e liberação, aumento da produção, coincidência de prazos, atraso do relógio, saída do solicitante, um único relógio por abertura e bloqueio dos acontecimentos se a fase deixar de ser aberta.

Os testes de encerramento cobrem permissões, fases inválidas, obra pendente sem reembolso, bloqueio de produção e conclusão, construção e reabertura recusadas, entrada tardia na situação final e dois pedidos de encerramento concorrentes.

## Perguntas
1. Quais eventos o seu sistema emite e escuta?
   O servidor escuta conexão, desconexão, `vila.abertura_solicitada`, `construcao.solicitada` e `vila.encerramento_solicitado` e `lote.envio_solicitado`; emite `estado.sincronizado`, `vila.iniciada`, `construcao.iniciada`, `recurso.produzido`, `sal.refinado`, `construcao.concluida`, `chuva.ocorrida`, `sal.perdido`, `vila.encerrada`, `lote.enviado` e `operacao.recusada`. O cliente envia pedidos de abertura, construção, encerramento e envio coletivo e escuta os fatos para atualizar sua apresentação.
2. Como o sistema sabe quando deve atualizar os outros jogadores?
   A entrada envia o estado só ao recém-chegado. Uma abertura aceita emite `vila.iniciada` para todos. Uma recusa é enviada apenas a quem pediu. Uma construção aceita emite `construcao.iniciada` para todos. Os prazos do servidor emitem os fatos de produção e conclusão para todos, e cada tela reage ao recebê-los.
3. Que parte do código mostra claramente o uso do paradigma orientado a eventos?
   Em `server.py`, a conexão emite `estado.sincronizado` e o tratamento de `vila.abertura_solicitada` emite o fato ou a recusa. Em `client/index.html`, `pedir(...)` envia a intenção e `ouvir(...)` reage aos fatos atualizando o painel e o desenho.

## Uso de IA
Foi utilizado o Codex para auxiliar na elaboração da especificação com as decisões da dupla e verificar as etapas 0 a 8. Ao implementar as funcionalidades, era solicitado para a I.A também auxiliar na criação dos testes automatizados, e atualizar as instruções de uso. A I.A foi usada para ajustar o visual e auxiliar nas dúvidas que surgiam da dupla, já existiam algumas dúvidas sobre como um RPG funciona.

## Chuva e cenário da Etapa 8

1. Reinicie, entre como Mestre e abra a temporada sem construir. Aos 30 segundos, o sexto refino leva o estoque a 90, com 30 expostos. A chuva remove esses 30: restam 60 protegidos e a perda acumulada fica em 30.
2. Confira no painel a sequência `recurso.produzido` → `sal.refinado` → `chuva.ocorrida` → `sal.perdido`. A animação é breve e não pausa a produção. O próximo prazo de chuva avança 30 segundos.
3. Entre em outra aba: ela recebe os mesmos saldos, perdas e próximo prazo. Os contadores começam nessa conexão; a animação de chuvas passadas não se repete.
4. Construa: os tanques e a secagem substituem o canteiro quando o servidor confirma a conclusão. O depósito e a frente básica sempre existem e não ocupam os seis espaços.
5. Encerre antes de uma chuva: não haverá nova perda ou chuva. O estado final permanece preservado.

Os testes adicionais verificam perda zero, preservação de parte protegida de um lote, chuvas atrasadas processadas em ordem, empate entre conclusão/produção/chuva, preservação das obras e dos salineiros e bloqueio após encerramento. O teste de abertura confere os primeiros prazos de produção e chuva.

### Arte e créditos

O mapa `client/assets/vila.json` foi adaptado do kit da disciplina. O novo `tileset-salina.svg` e as formas de tanque, secagem, depósito e chuva foram desenhados no código para este projeto com auxílio do Codex, sem imagens comerciais externas. Os arquivos de arte originais do kit foram preservados; seus créditos estão em `client/assets/LEIA-ME.txt`. O painel de eventos e os contadores foram mantidos.

Os nomes dos dois integrantes e seus usuários do GitHub ainda precisam ser preenchidos no README e no rodapé.

## Revisão visual da Salina

O cenário foi ampliado e redesenhado com formas vetoriais: armazém com sacos de sal protegido, pátio com montes de sal exposto, canal de captação, tanques azuis, cristais na secagem e andaimes nas obras. Os estoques desenhados acompanham cada estado recebido, inclusive chuva e reconexão. Sacos e montes são símbolos proporcionais com quantidade limitada; os rótulos indicam os valores exatos. Cada unidade tem tanque e secagem; todas as unidades ampliáveis têm a mesma função.

Os seis espaços continuam definidos na camada de objetos do mapa Tiled, agora ampliado. A arte do cenário é desenhada pelo Phaser em `client/index.html`; as imagens e o tileset anteriores foram preservados como referência. As regras e o painel de eventos continuam os mesmos.


## Extra opcional implementado — entregas coletivas

Este extra pode ser feito além do escopo mínimo do enunciado. As regras foram registradas primeiro na seção 9 de `docs/especificacao.md`, antes da alteração do código deste extra.

Após concluir as seis unidades, qualquer Jogador pode apertar **Enviar lote**. O servidor confirma uma entrega para a vila inteira, libera os seis espaços e retorna a produção a 5 de sal por ciclo (capta e consome 10 de água). O estoque, a proteção, a perda acumulada e os prazos de chuva e produção são preservados, sem cobrança adicional ou reembolso. O lote enviado representa o ciclo de seis construções e não é um lote do estoque de refino. Não há navio desenhado ou viagem com duração: apenas confirmação escrita.

Todos, inclusive o Mestre, veem **Entregas da vila**, o progresso de 0 a 6 conclusões e a identificação da última entrega. Não existe pontuação individual. A sincronização recupera esses dados e o encerramento preserva o total. Reiniciar o servidor retorna a zero. Os espaços liberados permitem repetir o ciclo sem limite.

### Conferência do extra

1. Entre como Mestre e dois Jogadores; abra a temporada. Antes das seis conclusões, tente enviar: somente quem pediu recebe recusa, sem mudança de estoque ou de entregas.
2. Conclua as seis construções. Obras em andamento não contam. Peça o envio: todos recebem `lote.enviado`, o contador aumenta uma vez, o mapa fica com seis espaços livres e a produção volta à capacidade básica.
3. Acompanhe o painel: `lote.envio_solicitado` tem causa e reação, e `lote.enviado` aponta esse pedido como causa. Os contadores por evento também incluem os novos eventos.
4. Complete outro ciclo e tente enviar nas duas abas quase simultaneamente: apenas um pedido é aceito e o outro recebe recusa individual. Um clique repetido após um envio também não conta outra entrega.
5. Recarregue e entre novamente: o total e a última entrega permanecem. Encerre pelo Mestre: pedidos posteriores são recusados e o contador permanece igual.

Os testes adicionais cobrem preservação integral dos estoques e prazos, retorno à produção básica, permissões e fases, obra pendente, concorrência e clique duplo, segundo ciclo real, sincronização e disputa com encerramento.
