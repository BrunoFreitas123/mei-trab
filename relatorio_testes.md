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
- o script `doWork.sql`;
- a ligação a partir de outros computadores;
- os logins `aluno1` a `aluno3` (os testes usaram o `sa`).

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
| T1: Browser enquanto o Edit tem alterações por confirmar | Só em READ COMMITTED (4.1). Faltam READ UNCOMMITTED e SNAPSHOT |
| T2: dois Edit na mesma encomenda | Só a variante SNAPSHOT (4.3). Faltam READ UNCOMMITTED e READ COMMITTED (*lost update*) |
| T3: deadlock em REPEATABLE READ | Sim (4.2) |
| T4: Edit contra o doWork | Não |
| T5: fantasmas | Sim (4.4) |
| T6: duas janelas com o doWork | Não |
| T7: taxas de refresh | Só 1 ms (4.5). Faltam 0,1 s, 1 s, 5 s e 30 s |
| T8: app Log bloqueada | Não |

## 7. Próximos passos

1. Repetir os cenários com **três computadores** e os logins `aluno1` a `aluno3`, como pede o enunciado.
2. Fazer os testes em falta (T1, T2, T4, T6, T7 e T8), com o `doWork.sql` a correr no SSMS.
3. Em cada teste, guardar provas para o relatório: o resultado de `sys.dm_tran_locks` e `sys.dm_exec_requests` e, nos deadlocks, o grafo da sessão `system_health`.
