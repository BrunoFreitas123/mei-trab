# Relatório de testes — aplicações do TP1 (Controlo de Transações)

**Data:** 2026-10-22
**Objeto:** as quatro aplicações em Python/Tkinter da pasta `apps/` (Edit, Browser, Log e Log Tempo)

## 1. Objetivo

Confirmar duas coisas antes dos testes manuais com três computadores:

1. As aplicações funcionam: login, leitura, edição, refresh e tratamento de erros.
2. O SQL Server comporta-se como a teoria prevê em cada nível de isolamento: bloqueios, deadlocks, fantasmas e conflitos em SNAPSHOT.

## 2. Ambiente

| Componente | Versão |
|---|---|
| SQL Server | 2022 Developer Edition (16.0.4265.3, CU26), em Docker (Linux), porta 14330 |
| Sistema anfitrião | Windows 11 |
| Python / Tk | 3.14.4 / 8.6 |
| Driver | pymssql 2.4.5 |
| Base de dados | `MEI_TRAB_TESTE`, temporária |

A base de dados `MEI_TRAB_TESTE` foi criada com os scripts do professor (`createTables.sql`, `triggers.sql`, `procs.sql`), mudando apenas o nome da base de dados. Foi preenchida com 5 encomendas através do procedimento `INSERIR_ENCOMENDA` e apagada no fim. A `MEI_TRAB` não foi tocada.

## 3. Método

Os testes foram automáticos, num único computador:

- **Janelas:** um script abriu as janelas reais das aplicações, escondidas, e acionou os botões por código. Cada janela tem a sua sessão no SQL Server (SPID próprio), como nos testes com vários utilizadores.
- **Mensagens de aviso:** foram capturadas para verificação, em vez de aparecerem no ecrã.
- **Verificação do estado da base de dados:** foi feita por uma ligação de administração em READ UNCOMMITTED, para nunca ficar bloqueada.

Ficaram de fora os pontos seguintes, que têm de ser testados à mão:
- a ligação a partir de outros computadores;
- os logins `aluno1` a `aluno3` (os testes usaram o `sa`).

Os testes com o `doWork.sql` a correr ao mesmo tempo que as aplicações estão na secção 7.

## 4. Resultados

Resultado final: **11/11 testes OK** em duas execuções seguidas, depois de corrigido o defeito descrito na secção 5.

| # | Teste | Resultado | Observado |
|---|---|---|---|
| 1 | Login com password errada | OK | Mensagem `Erro 18456: Login failed for user 'sa'.` |
| 2 | Login com nível REPEATABLE READ | OK | O servidor confirma o nível da sessão (`sys.dm_exec_sessions`): `SPID 55 · REPEATABLE READ` |
| 3 | Browser: ordem e linhas | OK | Encomendas por EncID decrescente (5, 4, 3, 2, 1); ao selecionar a 3, mostra as linhas dos produtos 111 e 131 |
| 4 | Edit (READ COMMITTED) contra Browser (READ COMMITTED) | OK | Ver 4.1 |
| 5 | Validação da morada | OK | Uma morada com 31 caracteres é recusada antes de chegar à base de dados |
| 6 | Log e Log Tempo | OK | O registo mais recente do Log é o `U` da encomenda 3, com `TerminalName` = nome do PC. O Log Tempo mostra as duas edições feitas, com o tempo em segundos |
| 7 | Deadlock: dois Edit em REPEATABLE READ | OK | Ver 4.2 |
| 8 | SNAPSHOT desligado | OK | Erro 3952 explicado ao utilizador; o servidor desfez a transação e o registo `'O'` final foi escrito |
| 9 | Conflito em SNAPSHOT | OK | Ver 4.3 |
| 10 | Fantasmas: REPEATABLE READ e SERIALIZABLE | OK | Ver 4.4 |
| 11 | Timer do Browser a 1 ms | OK | Ver 4.5 |

### 4.1 Edit bloqueia o Browser (READ COMMITTED)

1. O Edit abriu a encomenda 3, mudou a morada para `Covilhã — teste` e aplicou o `UPDATE` sem confirmar.
2. A ligação de administração (`NOLOCK`) já via a morada nova. É uma leitura suja, possível só em READ UNCOMMITTED.
3. O Browser em READ COMMITTED fez refresh e **ficou bloqueado**. A barra de estado mostrava `À espera do servidor há 1.3 s (possível bloqueio)`.
4. Assim que o Edit fez `COMMIT`, o Browser desbloqueou e mostrou a morada nova. Os acentos e o travessão foram guardados sem problemas.

**Interpretação:** em READ COMMITTED com trincos, o `SELECT` precisa de um trinco S em cada linha. A linha 3 tinha um trinco X do Edit, que só foi libertado no `COMMIT`.

### 4.2 Deadlock entre dois Edit (REPEATABLE READ)

1. Os Edit A e B abriram a encomenda 2. Cada um ficou com trincos S nas linhas lidas, que em REPEATABLE READ se mantêm até ao fim da transação.
2. Cada um mudou a quantidade do produto 111 (A para 7, B para 9) e carregou em Aplicar.
3. Cada `UPDATE` precisava de passar a um trinco X, mas a outra sessão tinha o trinco S. Formou-se um ciclo de espera.

| Execução | Deteção do deadlock | Vítima |
|---|---|---|
| 1 | 5,2 s | B |
| 2 | 5,1 s | — |
| 3 | 4,9 s | — |

- A vítima recebeu o erro 1205. A aplicação explicou o que aconteceu, fechou a transação e escreveu o registo `'O'` final.
- O sobrevivente guardou: a quantidade final ficou **7.00**, o valor de A.
- Todos os registos `'O'` ficaram aos pares (início e fim).

**Interpretação:** a deteção demora cerca de 5 s porque o *lock monitor* do SQL Server procura deadlocks a cada 5 s, por omissão.

### 4.3 Conflito em SNAPSHOT

Com `ALLOW_SNAPSHOT_ISOLATION ON`:

1. O Edit X (SNAPSHOT) abriu a encomenda 4.
2. O Edit Y (READ COMMITTED) abriu a mesma encomenda, mudou a morada para `Porto` e fez `COMMIT`.
3. O X voltou a ler e **continuou a ver `Lisboa`**, a versão do início da sua transação.
4. Quando o X tentou mudar a morada para `Braga`, recebeu o **erro 3960** (*update conflict*) e a transação foi desfeita.
5. A morada final ficou `Porto`.

**Interpretação:** o SNAPSHOT dá uma leitura consistente sem bloquear e deteta o *lost update* no momento da escrita, em vez de o impedir com trincos.

### 4.4 Fantasmas

Um Edit abriu a encomenda 5 (2 linhas). Noutra sessão, tentou-se inserir uma linha nova nessa encomenda, com `LOCK_TIMEOUT` de 1,5 s. Depois o Edit voltou a ler.

| Nível do Edit | INSERT da outra sessão | Linhas ao reler |
|---|---|---|
| REPEATABLE READ | passou | 2 → 3 (**fantasma**) |
| SERIALIZABLE | bloqueado (erro 1222, *lock timeout*) | 3 → 3 |

**Interpretação:** o REPEATABLE READ só protege as linhas já lidas. O SERIALIZABLE usa *key-range locks* sobre o intervalo `EncId = 5` da chave primária `(EncId, ProdutoID)`, o que impede inserções nesse intervalo.

### 4.5 Timer de 1 ms (pergunta do enunciado, 4.2)

O Browser correu durante 4 s com o timer configurado para 1 ms:

| Medição | Execução 1 | Execução 2 |
|---|---|---|
| Intervalo real médio entre ticks | 14,5 ms | 15,4 ms |
| Intervalo mínimo | 1,0 ms | — |
| Duração de cada refresh | ~42 ms | ~42 ms |
| Refreshes concluídos | 93 | 92 |
| Ticks saltados (refresh anterior ainda em curso) | 171 | 174 |

**Interpretação:** pode configurar-se 1 ms, mas na prática o intervalo fica em ~15 ms, que é a resolução por omissão do relógio do Windows (15,6 ms). Além disso, cada refresh demora ~42 ms, por isso a maioria dos ticks chega com o anterior ainda em curso. Sem a regra de saltar ticks, os pedidos acumular-se-iam na sessão. Um intervalo abaixo da duração da consulta só gera carga, não dados mais recentes.

## 5. Defeitos encontrados e corrigidos

| Defeito | Causa | Correção |
|---|---|---|
| Referência do Edit repetida | Duas janelas do Edit abriram uma encomenda no mesmo milissegundo e geraram a mesma referência (`G1-20261022152504154`). O Log Tempo juntou 4 registos `'O'` com essa referência, e a grelha falhou com chave duplicada. | A referência passou a incluir o SPID da sessão (`G1-AAAAMMDDhhmmssmmm-S<SPID>`), que é único entre sessões ativas. A grelha passou a aceitar chaves repetidas. |
| Mensagem de erro de login ilegível | O pymssql devolve os erros de ligação num tuplo dentro de outro tuplo, e a mensagem aparecia em bruto. | O tratamento de erros passou a desembrulhar o tuplo. Quando o servidor não responde (IP ou porta errados, firewall), mostra uma mensagem clara. |

O primeiro defeito só apareceu na segunda execução, porque depende de as duas janelas abrirem exatamente no mesmo milissegundo. Isto mostra que vale a pena repetir os testes concorrentes.

## 6. Cobertura face ao plano de testes do TP1

Relação com os testes T1 a T8 do ficheiro `TP1_o_que_fazer.md`:

| Teste do plano | Coberto aqui? |
|---|---|
| T1: Browser enquanto há alterações por confirmar | Sim, nos 5 níveis (8) |
| T2: dois Edit na mesma encomenda | Só a variante SNAPSHOT (4.3). O *lost update* em READ COMMITTED foi observado nos testes reais com três computadores (`monitorizacao/eventos.log`) |
| T3: deadlock em REPEATABLE READ | Sim (4.2) |
| T4: Edit contra o doWork | Sim (7.1) |
| T5: fantasmas | Sim (4.4) |
| T6: duas sessões com o doWork | Sim (7.2) |
| T7: taxas de refresh | Sim: 1 ms (4.5) e 0,5 s, 2 s e 5 s com o doWork a alterar dados (7.3) |
| T8: app Log bloqueada | Sim (7.1) |

## 7. Testes com o doWork.sql

Feitos numa base de dados temporária com 20 encomendas. Foram usadas três versões do script:

| Versão | Pausa entre operações | Duração |
|---|---|---|
| **Original** (o ficheiro do professor; só muda o nome da base de dados) | 15 s | 15 min |
| **Cópia rápida** | 0,5 s | 20 s |
| **Cópia sem pausa** (teste de esforço) | 0 s | 10 s |

Antes de cada execução definiu-se o nível de isolamento do doWork com `SET TRANSACTION ISOLATION LEVEL`, tal como se faz no SSMS.

### 7.1 Edit contra o doWork (T4); Log e Browser bloqueados (T8)

| Montagem | Resultado |
|---|---|
| O Edit (READ COMMITTED) aplica uma morada na encomenda mais recente (20), sem guardar. O doWork original, o Log e o Browser correm em READ COMMITTED | O doWork **fica bloqueado** logo na primeira operação (`INSERIR`, ao ler o `MAX(EncId)`), com `LCK_M_S`. O Log e o Browser também ficam bloqueados |
| O Edit faz `COMMIT` | O doWork insere a encomenda 21 **51 ms depois**; o Log e o Browser desbloqueiam |
| Repete-se com o doWork em READ UNCOMMITTED | O doWork **não bloqueia**: faz um `ACTUALIZAR` à encomenda 8 enquanto a 20 continua por confirmar |

**Interpretação:**
- Em READ COMMITTED, as leituras do doWork precisam de trincos S e ficam à espera do trinco X do Edit. Estão em causa o `MAX(EncId)` do `INSERIR` e o `COUNT(*)` e `ROW_NUMBER()` do `ACTUALIZAR` e do `APAGAR`.
- Em READ UNCOMMITTED, essas leituras não pedem trincos. As escritas continuam a pedir X, mas noutras linhas, porque o doWork nunca escolhe a encomenda mais recente para alterar ou apagar.

**Nota:** o SQL Server indicou como bloqueadora da sessão do doWork outra sessão que **também estava à espera** (a fila do recurso), e não o Edit. Para encontrar quem tem o trinco, é preciso seguir a cadeia até à sessão que não espera por ninguém. É o que o monitor faz.

### 7.2 Duas sessões com o doWork em simultâneo (T6)

| Versão do doWork | Nível | Operações (sessão 1 / sessão 2) | Violações de PK (2627) | Deadlocks (1205) |
|---|---|---|---|---|
| Cópia rápida | READ COMMITTED | 39 / 39 | 0 | 0 |
| Cópia rápida | SERIALIZABLE | 40 / 40 | 0 | 0 |
| Sem pausa | READ COMMITTED | 1 422 / 1 423 | 30 / 41 | 0 |
| Sem pausa | SERIALIZABLE | **2** / 1 326 | 0 | **1** (a sessão 1 parou aos 2,7 s) |

**Interpretação:**
- **Com pausas** entre operações, as transações do doWork (que duram milissegundos) quase nunca se sobrepõem, por isso não houve conflitos. Com o doWork original (15 s de pausa), a probabilidade é ainda menor.
- **Sem pausa, em READ COMMITTED,** houve 71 colisões no `MAX(EncId)+1`: as duas sessões calcularam o mesmo EncId. O ciclo de tentativas do `INSERIR_ENCOMENDA` resolveu-as todas, e todas as inserções acabaram por ser feitas.
- **Sem pausa, em SERIALIZABLE,** os trincos de intervalo do `MAX(EncId)` e do `COUNT(*)` chocam com as inserções da outra sessão e provocam um deadlock aos 2,7 s. A vítima recebeu o erro 1205, que **aborta o batch inteiro**, e o ciclo do doWork terminou. A outra sessão continuou normalmente.

### 7.3 Taxas de refresh do Browser com o doWork a alterar dados (T7)

Cópia rápida do doWork (cerca de 2 alterações por segundo), Browser em READ COMMITTED, 15 s por taxa:

| Refresh | Refreshes | Intervalo real | Duração da consulta | Alterações feitas pelo doWork | Vezes que o Browser viu a lista mudar | Atraso máximo dos dados |
|---|---|---|---|---|---|---|
| 500 ms | 30 | 516 ms | 41 ms | 30 | 29 | ≈ 0,5 s |
| 2000 ms | 8 | 2009 ms | 41 ms | 30 | 7 | ≈ 2 s |
| 5000 ms | 3 | 5013 ms | 42 ms | 30 | 2 | ≈ 5 s |

**Interpretação:**
- Os dados mostrados podem ter um atraso até ao intervalo de refresh mais a duração da consulta.
- Com refresh lento, várias alterações ficam juntas num só refresh: o utilizador vê o estado final, mas não as alterações intermédias. É o risco de decidir com dados desatualizados de que fala o enunciado.
- Com refresh rápido, o Browser acompanha o doWork, mas faz mais consultas ao servidor e, em READ COMMITTED, fica mais vezes sujeito a bloqueios.
- Abaixo da duração da consulta (~40 ms) não se ganha nada (ver 4.5).

## 8. Níveis de isolamento do Browser (T1)

Outra sessão alterou a morada e uma quantidade da encomenda 3, sem confirmar. O Browser mudou de nível pelo seletor e fez refresh:

| Nível do Browser | Durante a alteração por confirmar | Depois do ROLLBACK |
|---|---|---|
| READ UNCOMMITTED | não bloqueia; mostra os valores por confirmar (**leitura suja**) | valores originais |
| READ COMMITTED | **bloqueia** até a alteração terminar | valores originais |
| REPEATABLE READ | **bloqueia** | valores originais |
| SERIALIZABLE | **bloqueia** | valores originais |
| SNAPSHOT (desligado na base de dados) | erro 3952, com explicação | — |
| SNAPSHOT (ligado na base de dados) | não bloqueia; mostra a última versão confirmada | valores originais |

Em todos os casos, o servidor confirmou o nível escolhido (`sys.dm_exec_sessions`).

Mais duas verificações:
- **Trincos entre refreshes:** em REPEATABLE READ e SERIALIZABLE, o Browser não prende trincos entre refreshes. Cada `SELECT` corre em autocommit, e logo a seguir outra sessão consegue escrever na mesma linha.
- **Mudar de nível com o Browser bloqueado:** a mudança fica na fila atrás da consulta bloqueada. Aparece o aviso "só muda quando a consulta em curso terminar", e o nível novo é aplicado, com refresh automático, assim que a consulta termina.

## 9. Próximos passos

1. Documentar os testes reais feitos com **três computadores** a 22/10 (*lost update*, bloqueios de leitura e de escrita, leitura suja e queda de rede a meio de uma transação), a partir de `monitorizacao/eventos.log`.
2. Repetir com três computadores os cenários que ainda não foram feitos assim: deadlock em REPEATABLE READ, SNAPSHOT e o Edit contra o doWork original no SSMS.
3. Em cada teste, guardar provas: o resultado de `sys.dm_tran_locks` e `sys.dm_exec_requests` e, nos deadlocks, o grafo `.xdl` gravado pelo monitor.
