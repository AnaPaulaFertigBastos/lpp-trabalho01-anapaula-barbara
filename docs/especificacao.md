# Especificação da Vila Salina

**Trabalho:** Vila em Tempo Real — Programação Orientada a Eventos — 2026/2  
**Integrante(s):** Ana Paula Fertig Bastos (@AnaPaulaFertigBastos) e Bárbara Cristina Kammer (@BarbaraKammer)
**Tipo de vila (sorteio):** Salina 

## 1. Objetivo e base dos requisitos

A Salina é uma vila cooperativa em que os participantes compartilham água do mar, sal, salineiros e construções. A água do mar é captada e transformada em sal. Os jogadores usam sal para construir unidades salineiras e ampliar a produção. Um depósito fixo protege parte do estoque; a chuva destrói o sal exposto.

Este documento estabelece os requisitos que deverão orientar a implementação: regras, eventos, cenários de aceitação e ordem de desenvolvimento.

### 1.1 Referências e decisões

As referências são o enunciado “Trabalho 01 — Programação Orientada a Eventos 2026 Simplificado” e o “Guia de Implementação — Vila em Tempo Real”. O enunciado exige papéis de Mestre e Jogador, estado compartilhado, eventos, produção automática, obras com duração, recusas individuais, disputa por recursos e painel de eventos. Os contadores por evento são obrigatórios para a dupla.

Os recursos e números do exemplo do guia não são regras obrigatórias da Salina. Os valores deste documento são parâmetros de jogo propostos para uma demonstração curta. As quantidades representam unidades abstratas.

Decisões: um único tipo de construção, a unidade salineira, reunindo tanque e área de secagem; depósito inicial fixo; proteção automática; chuva periódica; obras pagas em sal. O depósito não é construído nem ampliado.

### 1.2 Adaptação prevista

A implementação deverá adaptar a estrutura de entrada, a tela, o desenho da vila, as animações e o painel de eventos do material inicial ao tema Salina. Deverão ser definidos os tratamentos dos eventos, substituídos os textos genéricos de toras e casas e preenchidos os modelos de documentação conforme os requisitos deste documento.

### 1.3 Limites do escopo

Não estão incluídos: contas com senha, histórico permanente, várias vilas, comércio, missões, níveis, ampliação do depósito, armazenamento manual, cancelamento de obras, fila de construção, vitória ou derrota automática e publicação na internet. O visual pode ser simples; arte elaborada não é requisito.

## 2. Requisitos funcionais

| ID | Requisito |
|---|---|
| RF01 | Permitir entrada por nome e papel e apresentar a situação atual da vila compartilhada. |
| RF02 | Permitir ao Mestre abrir e encerrar a temporada. |
| RF03 | Permitir ao Jogador solicitar uma unidade salineira por pedido. |
| RF04 | Validar cada pedido antes de cobrar recursos, reservar espaço ou ocupar salineiros. |
| RF05 | Captar água do mar e refiná-la em sal automaticamente durante a temporada. |
| RF06 | Concluir obras após seu prazo, liberar salineiros e ampliar a produção. |
| RF07 | Proteger sal automaticamente até a capacidade do depósito e perder o excedente na chuva. |
| RF08 | Apresentar os resultados compartilhados a todos sem recarregar a página. |
| RF09 | Comunicar recusas somente a quem pediu, sem alterar a vila. |
| RF10 | Mostrar eventos enviados e recebidos, horário, causa, dados e reação da tela. |
| RF11 | Exibir contadores por evento para atender à modalidade em dupla. |
| RF12 | Mostrar os nomes dos dois integrantes no rodapé. |

## 3. Fluxo simplificado

1. A vila começa com 60 de sal e 50 de água do mar.
2. Cada construção custa 20 de sal. Ela ocupa 1 salineiro por 8 segundos. Não gasta água para construir.
3. Quando fica pronta, libera o salineiro e aumenta a produção em 5 de sal a cada 5 segundos.
4. A produção usa água do mar, captada automaticamente. O saldo de água normalmente continua em 50.
5. Ao concluir as 6 construções, vocês podem clicar em “Enviar lote”.
6. O envio soma 1 entrega coletiva, libera os seis espaços e retorna a produção ao valor inicial.

## 4. Regras de negócio

### RN01 — Recursos e parâmetros iniciais

| Parâmetro | Valor |
|---|---|
| Recurso primário | Água do mar |
| Recurso refinado | Sal |
| Fase inicial | Aguardando |
| Água do mar inicial | 50 unidades |
| Sal inicial | 60 unidades, todas protegidas |
| Capacidade fixa do depósito | 60 unidades de sal |
| Sal exposto inicial | 0 |
| Sal perdido acumulado inicial | 0 |
| Limite de salineiros | 2 |
| Salineiros ocupados inicialmente | 0 |
| Unidades concluídas inicialmente | 0 |
| Obras em andamento inicialmente | 0 |
| Espaços para novas unidades | 6 |
| Custo por unidade salineira | 20 unidades de sal |
| Duração de cada obra | 8 segundos |
| Salineiros ocupados por obra | 1 |
| Intervalo de produção | 5 segundos |
| Intervalo de chuva | 30 segundos desde a abertura |

A vila possui uma operação básica de captação e secagem desde o início, permitindo produzir antes de novas construções. Ela e o depósito inicial não ocupam os seis espaços. O sal inicial é a reserva comunitária usada para financiar as obras. Recursos e construções pertencem à vila, não a jogadores individuais.

### RN02 — Papéis e permissões

- O Mestre abre e encerra a temporada e acompanha os resultados. Não constrói.
- O Jogador solicita construções e acompanha os resultados. Não abre nem encerra a temporada.
- O papel é escolhido na entrada. Um papel inválido não autoriza ações.
- Não há exclusividade de Mestre. Se vários participantes escolherem esse papel, todos seguem as mesmas permissões e regras de fase.
- Nome em branco é apresentado como “Anônimo”.
- As permissões são verificadas em cada pedido, mesmo que a tela esconda ações indisponíveis.

### RN03 — Ciclo da temporada

A sequência permitida é **aguardando → aberta → encerrada**.

Em aguardando, não ocorrem produção, chuva ou construção. Um pedido válido do Mestre abre a temporada e inicia os prazos de produção e chuva. Pedidos posteriores de abertura são recusados, sem reiniciar prazos.

Em aberta, pedidos válidos, produção, conclusão de obras e chuva podem alterar a vila. Não há encerramento automático.

Ao confirmar o encerramento, cessam produção, chuva e conclusão de obras. Novas construções são recusadas. Estoques, perdas e construções permanecem visíveis na situação final. Obras inacabadas ficam registradas como estavam, com seus salineiros ocupados e sem devolução do custo.

Uma temporada encerrada não pode ser reaberta. Reiniciar a aplicação inicia uma nova sessão com os valores iniciais, sem recuperar a anterior.

### RN04 — Pedido e início de construção

Cada pedido solicita uma unidade salineira. As condições são verificadas nesta ordem:

1. Participante identificado e com papel de Jogador.
2. Temporada aberta.
3. Espaço livre entre os seis disponíveis.
4. Pelo menos 20 unidades de sal.
5. Pelo menos um salineiro livre.

Se uma condição falhar, o pedido é recusado com o primeiro motivo encontrado, sem alterar a vila. Motivos: participante não identificado; somente Jogadores podem construir; temporada não está aberta; não há espaço disponível; sal insuficiente; não há salineiro livre.

Se todas forem atendidas, uma única decisão desconta 20 unidades de sal, ocupa um salineiro, reserva o primeiro espaço livre e registra a obra com conclusão prevista para oito segundos depois. Todos recebem o fato de início.

Obras em andamento e unidades prontas ocupam espaços. Não há demolição de espaços. Cada novo clique representa um novo pedido sujeito às mesmas validações. Não há fila de espera nem cancelamento.

### RN05 — Conclusão da obra

Após oito segundos, se a temporada continuar aberta, a obra passa a concluída, libera seu salineiro e acrescenta uma frente produtiva. Todos são informados. O aumento vale para o próximo ciclo, inclusive um ciclo com o mesmo prazo da conclusão, conforme RN09.

Cada obra tem identificação própria, espaço, solicitante, momento de início e prazo. A conclusão afeta a obra correspondente, sem depender da ordem dos desenhos na tela. Sair da vila não cancela a obra solicitada.

### RN06 — Captação e transformação

A primeira produção ocorre cinco segundos após a abertura e se repete a cada cinco segundos enquanto a temporada estiver aberta.

Se N é o número de unidades concluídas, existem **1 + N frentes produtivas**, incluindo a operação básica. Cada frente capta 10 unidades de água do mar, consome 10 unidades no refino e produz 5 unidades de sal por ciclo.

Primeiro a captação acrescenta água ao estoque; em seguida, o refino consome água e gera sal. Como captação e consumo são iguais, o saldo de água permanece em 50 nas condições normais desta versão. A tela informa os volumes captados e consumidos para tornar a transformação visível.

| Unidades concluídas | Frentes | Água captada por ciclo | Água consumida por ciclo | Sal produzido por ciclo |
|---|---:|---:|---:|---:|
| 0 | 1 | 10 | 10 | 5 |
| 1 | 2 | 20 | 20 | 10 |
| 2 | 3 | 30 | 30 | 15 |
| 6 | 7 | 70 | 70 | 35 |

Os dois salineiros disponíveis representam a equipe de obras. A produção automática não ocupa essa equipe e continua mesmo com ambos em construção. Não há limite de estoque de água nem de sal exposto.

### RN07 — Lotes, proteção e consumo

Cada ciclo de refino cria um lote identificado, com quantidade e momento de produção. A reserva inicial também é um lote. Um lote pode ficar parcialmente protegido.

- O depósito protege até 60 unidades no total; o excedente fica exposto automaticamente.
- Lotes mais antigos recebem proteção primeiro. Em empate de momento, prevalece a ordem de criação.
- O custo de uma obra consome primeiro sal exposto e depois protegido. Dentro de cada grupo, usa primeiro os lotes mais antigos.
- Após produção ou consumo, a distribuição entre protegido e exposto é recalculada automaticamente.
- A mesma quantidade nunca é contada como protegida e exposta ao mesmo tempo.
- Lotes totalmente consumidos ou perdidos deixam de compor o estoque disponível.

As relações obrigatórias são:

- **Sal total = sal protegido + sal exposto.**
- **Sal protegido = o menor valor entre sal total e 60.**
- **Sal exposto = o maior valor entre sal total − 60 e zero.**

### RN08 — Chuva e expiração

A chuva ocorre aos 30, 60, 90 segundos e assim sucessivamente desde a abertura. É um acontecimento instantâneo, não um período de paralisação.

Cada chuva elimina todo o sal exposto naquele momento. A parte protegida permanece intacta. Em lote parcialmente protegido, somente a parte exposta é perdida. A perda acumulada aumenta na quantidade efetivamente removida.

Água do mar, obras, unidades prontas, salineiros e capacidade do depósito não são afetados. A produção continua em seus intervalos normais.

Sem sal exposto, a chuva ainda é comunicada, com perda zero. Não se emite fato de perda quando nada foi perdido. A expiração depende da exposição à chuva, não da idade do lote; não existe outro prazo de validade.

### RN09 — Concorrência e acontecimentos coincidentes

O servidor decide sobre a vila. Pedidos são processados na ordem de chegada, considerando o estado resultante das decisões anteriores. Validação, cobrança e reserva ocorrem juntas, sem permitir que outro pedido use os mesmos recursos ou salineiros.

Se dois jogadores disputarem recursos suficientes para apenas uma obra, um pedido é aceito e o outro recusado. Não existe preferência por nome ou histórico.

Quando acontecimentos automáticos têm exatamente o mesmo prazo, a ordem é:

1. Conclusão de obras; entre elas, ordem de início.
2. Captação e refino.
3. Chuva e perda de sal exposto.

Assim, uma unidade concluída no prazo do ciclo já participa da produção, e o sal produzido no instante da chuva já está sujeito à perda. Captação e refino formam um ciclo indivisível para pedidos de jogadores. Também não se aceita construção entre a determinação da chuva e a aplicação da perda correspondente.

Um encerramento já confirmado impede qualquer alteração posterior. Acontecimentos concluídos antes dessa confirmação permanecem válidos.

### RN10 — Entrada, saída e continuidade

Quem entra recebe fase, estoques, proteção, perdas, salineiros, construções, capacidade produtiva e prazos atuais. Entrar não reinicia a temporada ou seus acontecimentos.

Desconectar não devolve recursos nem libera salineiros de obras pendentes. Enquanto a aplicação permanecer ativa, a temporada continua mesmo sem participantes conectados.

Ao reconectar, a situação atual substitui a visão anterior, sem duplicar construções. Obras já iniciadas mostram seu tempo restante, não a duração completa.

### RN11 — Condições que sempre devem ser respeitadas

- Água, sal, perdas e contagens nunca são negativos.
- Salineiros ocupados ficam entre zero e dois; cada obra em andamento ocupa um.
- Obras em andamento mais unidades concluídas nunca ultrapassam seis.
- Cada construção ocupa um único espaço exclusivo.
- Sal protegido nunca ultrapassa 60 e, somado ao exposto, corresponde ao sal total.
- Pedidos recusados não alteram a vila.
- Somente a temporada aberta admite produção e construção.
- Depois do encerramento, o estado final permanece inalterado.

## 5. Catálogo de eventos

Pedidos expressam intenções e não alteram a vila por si mesmos. Fatos comunicam decisões ou acontecimentos confirmados. “Todos” significa todos os participantes conectados, incluindo quem pediu. As causas devem estar visíveis no painel.

| Evento | Emite | Recebe | Causa | O que muda no estado |
|---|---|---|---|---|
| `estado.sincronizado` | Servidor | Participante que entrou | Entrada ou reconexão | Não altera a vila; entrega sua situação atual. |
| `vila.abertura_solicitada` | Mestre | Servidor | Ação de abrir | Nada; é um pedido. |
| `vila.iniciada` | Servidor | Todos | `vila.abertura_solicitada` aceita | Fase passa a aberta e começam os prazos de produção e chuva. |
| `construcao.solicitada` | Jogador | Servidor | Ação de construir | Nada; pede uma unidade salineira. |
| `construcao.iniciada` | Servidor | Todos | `construcao.solicitada` aceita | Desconta 20 de sal, ocupa um salineiro e reserva espaço e prazo da obra. |
| `operacao.recusada` | Servidor | Somente quem pediu | Pedido que não atende às regras | Nada; informa pedido e motivo da recusa. |
| `recurso.produzido` | Servidor | Todos | Prazo de produção | Acrescenta a água captada e informa a quantidade. |
| `sal.refinado` | Servidor | Todos | `recurso.produzido` do mesmo ciclo | Consome água, cria lote de sal e atualiza a proteção. |
| `construcao.concluida` | Servidor | Todos | Prazo da obra de `construcao.iniciada` | Conclui a obra identificada, libera salineiro e amplia a produção. |
| `chuva.ocorrida` | Servidor | Todos | Prazo de chuva | Registra ocorrência e identifica quantidade exposta; não remove sal por si só. |
| `sal.perdido` | Servidor | Todos | `chuva.ocorrida` com sal exposto | Remove a parte exposta dos lotes e aumenta a perda acumulada. |
| `vila.encerramento_solicitado` | Mestre | Servidor | Ação de encerrar | Nada; é um pedido. |
| `vila.encerrada` | Servidor | Todos | `vila.encerramento_solicitado` aceita | Fase passa a encerrada e congela a situação final. |

Os eventos de um ciclo apresentam resultados coerentes, na ordem definida. Comunicar os passos de captação e refino não permite intercalar pedidos entre eles. O mesmo vale para chuva e perda.

### 5.1 Informações dos acontecimentos

- Fatos compartilhados apresentam causa, resultado e estado correspondente.
- Início e conclusão identificam a construção, o espaço e o solicitante.
- Produção informa água captada; refino informa água consumida, sal gerado, lote e proteção.
- Chuva informa ocorrência e quantidade exposta; perda informa lotes afetados, quantidade removida e total perdido acumulado.
- Recusa informa o pedido e o motivo, somente ao solicitante.
- Sincronização informa a situação atual, incluindo prazos restantes e próxima chuva.
- Pedidos não escolhem custos, saldos, rendimentos ou duração: esses valores pertencem às regras.

## 6. Apresentação e painel de eventos

A tela mostra fase, nome e papel; água do mar; sal total, protegido e exposto; capacidade do depósito; perda acumulada; salineiros ocupados e limite; obras e unidades prontas; produção por ciclo; tempo restante das obras e próxima chuva.

| Acontecimento | Reação esperada |
|---|---|
| Sincronização | Apresentar a situação atual sem duplicar construções. |
| Abertura | Mostrar temporada aberta e próximos acontecimentos. |
| Início de obra | Mostrar obra, custo pago e salineiro ocupado. |
| Conclusão | Mostrar unidade pronta, salineiro livre e nova produção. |
| Captação e refino | Mostrar água captada e consumida, sal gerado e proteção atualizada. |
| Chuva | Avisar a ocorrência, inclusive sem perda. |
| Perda | Destacar a quantidade perdida e atualizar estoques e perda acumulada. |
| Recusa | Mostrar o motivo somente a quem pediu. |
| Encerramento | Mostrar situação final e impedir ações incompatíveis. |

O painel registra cada evento enviado ou recebido pelo participante, com nome, horário, direção, causa, dados e reação. Pedidos, fatos e recusas são distinguíveis. A reação a um pedido é o envio da intenção, sem antecipar seu resultado.

Cada evento tem um contador local, incrementado uma vez por envio ou recebimento registrado. Filtrar a exibição de eventos frequentes não altera os contadores. Histórico e contadores começam novamente ao reconectar; não representam um histórico global da vila.

Os nomes dos dois integrantes aparecem no rodapé. Textos e representação visual usam o tema Salina.

## 7. Cenários de aceitação

Cada cenário é independente e parte das condições descritas. Produção ou chuva só interferem quando houver passagem de tempo indicada. Disputas são avaliadas antes do próximo acontecimento automático.

### CA01 — Recusa antes da abertura

**Dado** que a temporada aguarda abertura e há um Jogador conectado, **quando** ele emite `construcao.solicitada`, **então** somente ele recebe `operacao.recusada` por temporada não aberta. Sal, espaços e salineiros não mudam.

### CA02 — Permissões

**Dado** um Jogador conectado, **quando** emite `vila.abertura_solicitada` ou `vila.encerramento_solicitado`, **então** recebe `operacao.recusada` por falta de permissão, sem mudar a fase. **Dado** um Mestre, **quando** emite `construcao.solicitada`, **então** recebe recusa por papel, sem cobrança.

### CA03 — Abertura e repetição

**Dado** que a vila aguarda abertura, **quando** um Mestre emite `vila.abertura_solicitada`, **então** todos recebem `vila.iniciada` e a fase passa a aberta. **Quando** chega outra solicitação de abertura, **então** seu solicitante recebe `operacao.recusada`, sem reiniciar prazos.

### CA04 — Construção válida

**Dado** temporada aberta, sal 60, ocupação 0/2 e seis espaços livres, **quando** um Jogador emite `construcao.solicitada`, **então** todos recebem `construcao.iniciada`, sal passa a 40, ocupação a 1/2 e uma obra reserva o primeiro espaço por oito segundos.

### CA05 — Passagem do tempo

**Dado** temporada recém-aberta, água 50, sal 60 e nenhuma unidade concluída, **quando** passam cinco segundos sem ações, **então** todos recebem `recurso.produzido` com captação de 10, seguido de `sal.refinado` com consumo de 10 de água e geração de 5 de sal. Água termina em 50, sal em 65, protegido em 60 e exposto em 5.

### CA06 — Conclusão automática

**Dado** uma obra em andamento e nenhuma unidade concluída, **quando** seu prazo de oito segundos vence com a temporada aberta, **então** todos recebem `construcao.concluida`, a obra correta fica pronta e a ocupação cai de 1/2 para 0/2. O próximo ciclo produz 10 de sal, captando e consumindo 20 de água.

### CA07 — Disputa pelo último salineiro

**Dado** temporada aberta, ocupação 1/2, pelo menos 40 de sal e dois espaços livres, **quando** A e B emitem `construcao.solicitada` simultaneamente, **então** um pedido gera `construcao.iniciada` para todos e o outro gera `operacao.recusada` somente para quem perdeu a disputa. Apenas 20 de sal são cobrados; ocupação final 2/2.

### CA08 — Disputa pelo último recurso

**Dado** temporada aberta, sal 20, ocupação 0/2 e dois espaços livres, **quando** A e B emitem `construcao.solicitada` simultaneamente, **então** um pedido gera `construcao.iniciada` e o outro `operacao.recusada` por sal insuficiente. Sal termina em zero, com uma nova obra e um salineiro ocupado.

### CA09 — Limite de espaços

**Dado** seis espaços ocupados por obras ou unidades prontas, **quando** chega `construcao.solicitada`, **então** o solicitante recebe `operacao.recusada` por falta de espaço, sem cobrança ou ocupação adicional.

### CA10 — Proteção parcial na chuva

**Dado** sal 75, protegido 60, exposto 15 e perda acumulada zero no instante da chuva, **quando** ocorre `chuva.ocorrida`, **então** ocorre `sal.perdido` de 15. Restam 60 protegidos, zero expostos e perda acumulada 15. Partes protegidas dos lotes permanecem intactas.

### CA11 — Chuva sem perda

**Dado** sal 40, todo protegido no instante da chuva, **quando** ocorre `chuva.ocorrida`, **então** é informada perda zero, não ocorre `sal.perdido` e o estoque permanece 40.

### CA12 — Consumo do excedente

**Dado** temporada aberta, sal 75, sendo 15 expostos, espaço e salineiro livres, **quando** `construcao.solicitada` é aceita, **então** `construcao.iniciada` corresponde ao consumo de 15 expostos e 5 protegidos. As 55 unidades restantes ficam protegidas, respeitando a ordem dos lotes.

### CA13 — Produção coincidente com chuva

**Dado** sal 60 protegido e nenhuma unidade concluída antes de um prazo comum de produção e chuva, **quando** esse prazo chega, **então** ocorrem `recurso.produzido` e `sal.refinado`, gerando 5 de sal, seguidos de `chuva.ocorrida` e `sal.perdido`, removendo essas 5 unidades expostas. Restam 60 protegidos.

### CA14 — Conclusão coincidente com produção

**Dado** nenhuma unidade pronta e uma obra cujo término coincide com um ciclo de produção, **quando** chega o prazo comum, **então** `construcao.concluida` ocorre antes de `recurso.produzido` e `sal.refinado`. Esse ciclo capta e consome 20 de água e produz 10 de sal.

### CA15 — Encerramento com obra pendente

**Dado** temporada aberta e uma obra pendente, **quando** um Mestre emite `vila.encerramento_solicitado` e ocorre `vila.encerrada`, **então** todos veem a fase encerrada e a situação final. Após os antigos prazos, não ocorrem produção, chuva ou conclusão. Obra e salineiro permanecem registrados, sem reembolso.

### CA16 — Ações após encerramento

**Dado** temporada encerrada, **quando** chegam pedidos de construção, abertura ou encerramento, **então** cada solicitante recebe `operacao.recusada` e a situação final não muda.

### CA17 — Entrada tardia e reconexão

**Dado** temporada aberta com estoque e obra em andamento, **quando** outro participante entra ou alguém reconecta, **então** recebe `estado.sincronizado` com valores e prazos restantes atuais. Nenhum prazo reinicia e nenhuma construção aparece duplicada.

### CA18 — Saída do solicitante

**Dado** uma construção aceita, **quando** seu solicitante sai e o prazo vence durante a temporada aberta, **então** `construcao.concluida` ainda ocorre para os conectados, liberando o salineiro e ampliando a produção.

### CA19 — Painel e contadores da dupla

**Dado** um participante conectado, **quando** envia ou recebe evento do catálogo, **então** o painel registra nome, horário, direção, causa, dados e reação aplicáveis, aumentando o contador uma vez. **Quando** filtra eventos frequentes, **então** as contagens permanecem iguais. **Quando** reconecta, **então** inicia novo histórico local e registra a nova sincronização.

### CA20 — Recusa individual e fato compartilhado

**Dado** Mestre, Jogador A e Jogador B conectados, **quando** A faz um pedido inválido, **então** somente A recebe `operacao.recusada`. **Quando** A faz um pedido válido, **então** todos recebem o fato correspondente e apresentam o mesmo resultado, sem recarregar a página.

## 8. Ordem futura de implementação

A especificação deve ser registrada no histórico antes da implementação. Cada etapa futura deve ter seu próprio registro e ser verificada com pelo menos duas abas. Disputas usam Mestre, Jogador A e Jogador B.

| Ordem | Etapa | Critério para avançar |
|---|---|---|
| 1 | Formalizar a especificação | Regras, parâmetros, eventos e cenários documentados antes da implementação. |
| 2 | Estado e entrada | Duas abas mostram valores iniciais iguais; entradas posteriores recebem o estado atual. |
| 3 | Abertura e permissões | Mestre abre uma única vez; ações de papel inválido são recusadas. |
| 4 | Construção e recusas | Cobrança, espaço e salineiro respeitam regras; disputas não duplicam recursos. |
| 5 | Tempo e produção | Obras concluem e água vira sal automaticamente; lotes são identificados. |
| 6 | Depósito e chuva | Proteção, consumo, perda e coincidência de prazos atendem aos cenários. |
| 7 | Encerramento e reconexão | Situação final não muda; reconexão recupera a visão atual sem duplicações. |
| 8 | Revisão da apresentação | Tema Salina, reações, painel, contadores e nomes no rodapé completos. |
| 9 | Envio de lote (opcional) | Poderá ser implementado após a conclusão das etapas anteriores, conforme o prazo disponível. Deverá permitir o envio após as seis conclusões, liberar os espaços e contabilizar uma entrega coletiva. |


## 9. Extra opcional — envio coletivo de lote

Este extra **poderá ser implementado** como uma "Etapa 9", caso haja prazo disponível após a conclusão das etapas anteriores.
Consiste em permitir novos ciclos após ocupar os seis espaços. Não é uma exigência do enunciado. 

### EX01 — Ciclo e significado do lote

O ciclo é: construir seis unidades → aguardar as seis conclusões → solicitar envio de lote → liberar os seis espaços → construir novamente. Um lote enviado representa o resultado coletivo de um ciclo de seis construções já financiadas. Não corresponde a um novo saldo de sal nem aos lotes de refino usados para controlar proteção e chuva.

### EX02 — Permissões e validação

O botão “Enviar lote” fica disponível para Jogadores, inclusive antes das seis conclusões, permitindo visualizar a recusa. O Mestre acompanha o contador coletivo e mantém a função de abrir e encerrar. O pedido é verificado nesta ordem: participante identificado; papel de Jogador; temporada aberta; seis unidades concluídas, sem obra pendente. Se falhar, somente quem pediu recebe o primeiro motivo, sem alterar recursos, construções, produção, prazos ou entregas. Se houver menos de seis concluídas, a mensagem é “Conclua as seis unidades para enviar um lote”.

### EX03 — Confirmação e novo ciclo

Uma única decisão confirma uma entrega, aumenta em um o contador coletivo inicialmente zero, registra o nome do solicitante para a mensagem e libera os seis espaços. As contagens de unidades prontas, obras e salineiros ocupados voltam a zero. A captação e o consumo voltam a 10 de água por ciclo e a produção a 5 de sal por ciclo. A frente básica e o depósito permanecem disponíveis.

Não há cobrança adicional ou reembolso. Água, sal, proteção, lotes de refino e perda acumulada permanecem iguais. Os prazos de produção e chuva não reiniciam. O envio é imediato; não ocupa salineiro. Todos recebem “Lote enviado! Os espaços estão disponíveis para um novo ciclo”. O contador pertence à vila, sem pontuação individual e sem limite de ciclos.

### EX04 — Concorrência, continuidade e encerramento

Se dois Jogadores pedirem o envio das mesmas seis unidades, só um pedido é aceito. O outro encontra os espaços liberados, recebe recusa individual e não aumenta a contagem. Cliques repetidos seguem a mesma regra. Envio, construção, acontecimentos por prazo e encerramento seguem uma única ordem de decisões: um envio já confirmado preserva sua entrega; um encerramento já confirmado impede o envio. Não há perda de entrega pela chuva.

Quem entra ou reconecta recebe o contador coletivo, a identificação da última entrega e o ciclo de construções atual. A situação final preserva o total de entregas e não permite novos envios. Reiniciar a sessão retorna a zero.

### EX05 — Eventos e apresentação

| Evento | Emite | Recebe | Causa | O que muda |
|---|---|---|---|---|
| `lote.envio_solicitado` | Jogador | Servidor | Clique em Enviar lote | Nada; solicita encerrar o ciclo de seis unidades. |
| `lote.enviado` | Servidor | Todos | `lote.envio_solicitado` aceito | Soma uma entrega, libera os seis espaços e restaura a produção básica. |
| `operacao.recusada` | Servidor | Somente solicitante | `lote.envio_solicitado` inválido | Nada; comunica o motivo. |

O contador “Entregas da vila” aparece para todos, incluindo o Mestre. O progresso mostra quantas das seis unidades já terminaram. A confirmação remove os desenhos das seis unidades, restaura os espaços disponíveis e atualiza a produção. O painel registra os novos pedidos e fatos com horário, direção, causa, dados e reação, além de seus contadores locais.

### Cenários de aceitação do extra

- **EX-CA01:** **Dado** cinco unidades prontas e uma em obra, **quando** um Jogador pede envio, **então** recebe recusa individual e o estado permanece igual.
- **EX-CA02:** **Dado** seis unidades prontas, **quando** um Jogador pede envio, **então** todos recebem uma entrega confirmada, contador acrescido em um, seis espaços livres e produção básica, com estoques, perdas e prazos preservados.
- **EX-CA03:** **Dado** seis unidades prontas, **quando** A e B pedem envio simultaneamente, **então** há um único fato de envio e uma recusa só ao outro, com apenas uma entrega contabilizada.
- **EX-CA04:** **Dado** envio aceito, **quando** o mesmo pedido é repetido antes de completar outro ciclo, **então** é recusado sem aumentar a contagem.
- **EX-CA05:** **Dado** participante desconhecido, Mestre ou temporada aguardando/encerrada, **quando** pede envio, **então** recebe recusa individual sem alterar a vila.
- **EX-CA06:** **Dado** uma entrega confirmada, **quando** os participantes constroem novamente, **então** os espaços podem ser ocupados e um segundo ciclo completo permite a segunda entrega.
- **EX-CA07:** **Dado** entregas já feitas, **quando** alguém entra ou reconecta, **então** recebe total, última entrega e construções atuais. **Quando** a temporada encerra, **então** o total permanece preservado.
- **EX-CA08:** **Dado** envio e encerramento concorrentes, **quando** o encerramento é confirmado primeiro, **então** o envio é recusado; na ordem inversa, a entrega integra a situação final.

Ordem deste extra: registrar estas regras → adaptar estado, validação e envio → integrar botão, contador, mensagem e desenho → validar concorrência, repetição, novos ciclos, sincronização e encerramento.
