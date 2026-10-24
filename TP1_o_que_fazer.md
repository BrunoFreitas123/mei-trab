# TP1 — Controlo de Transações: o que fazer

## 1. Preparar o servidor

- [ ] SQL Server com TCP/IP ativo, porta 1433 aberta na firewall e autenticação mista
- [ ] Criar a base de dados `MEI_TRAB` no SSMS (o `createTables.sql` não a cria)
- [ ] Correr por esta ordem: `createTables.sql` → `triggers.sql` → `procs.sql`
- [ ] Ativar SNAPSHOT (confirmar com o professor)
- [ ] Criar um login por pessoa, sem sysadmin (senão o `UserID` aparece sempre como `dbo`)

```sql
ALTER DATABASE MEI_TRAB SET ALLOW_SNAPSHOT_ISOLATION ON;

USE master;
CREATE LOGIN aluno1 WITH PASSWORD = 'MudarEsta#1';
USE MEI_TRAB;
CREATE USER aluno1 FOR LOGIN aluno1;
ALTER ROLE db_datareader ADD MEMBER aluno1;
ALTER ROLE db_datawriter ADD MEMBER aluno1;
```

## 2. Construir as aplicações

**Comum a todas:** janela de login (host, base de dados, utilizador, password) e escolha do nível de isolamento. Pôr `Workstation ID=PCx-NomeApp` na connection string para identificar a app no log.

- [ ] **Edit**
  1. Registo `'O'` inicial, fora da transação (`Valor = CONVERT(varchar(23), GETDATE(), 126)`, `Referencia = G<n>-<timestamp>`)
  2. `BEGIN TRAN` e SELECT do cabeçalho e das linhas
  3. Botão **Aplicar**: UPDATE só dos campos alterados (a transação continua aberta)
  4. **Guardar** = `COMMIT`; **Descartar** = `ROLLBACK`
  5. Registo `'O'` final
  - Validar: `Morada` com 1 a 30 caracteres; `Qtd` ≥ 0 e < 10 000 000
  - Verificar as linhas afetadas (a encomenda pode ter sido apagada)
  - Tratar os erros 1205 (deadlock) e 3960 (conflito em SNAPSHOT)
- [ ] **Browser:** duas grelhas (encomendas e linhas), `EncId` decrescente, botão de refresh e timer configurável. Correr a query de forma assíncrona para a janela não congelar.
- [ ] **Log Tempo:** generalizar a query do enunciado (tirar a referência fixa, filtrar `EventType = 'O'`) e acrescentar um timer.
- [ ] **Log:** `TOP (N)` com eventos I/U/D por `NumReg` decrescente, mais um timer. A coluna chama-se **`TerminalD`**, não `TerminalId`.

## 3. Testar (3 computadores: SSMS + Edit + Browser)

| # | Montagem | Esperado |
|---|---|---|
| T1 | Edit A aplica sem guardar; Browser faz refresh | RU: dados sujos · RC: bloqueia · SNAPSHOT: versão confirmada |
| T2 | Edit A aplica sem guardar; Edit B abre a mesma encomenda | RU: dados sujos · RC: bloqueia · SNAPSHOT: erro 3960 se A guardar |
| T3 | Edit A e B leem a mesma encomenda em RR e ambos aplicam | Deadlock (1205) |
| T4 | Edit A altera a morada sem guardar, com o doWork a correr | O doWork fica parado |
| T5 | Edit A lê a encomenda k; no SSMS insere-se uma linha em k; A relê | RR: fantasma · SERIALIZABLE: o INSERT bloqueia |
| T6 | Duas janelas com o doWork | RC: violações de PK e novas tentativas · SERIALIZABLE: deadlocks |
| T7 | Browser com refresh de 0,1 s, 1 s, 5 s e 30 s | Idade dos dados (pela `Morada`) vs. carga |
| T8 | Edit A aplica sem guardar; app Log em RC | Bloqueia |

Para recolher provas durante os testes:

```sql
-- Trincos ativos
SELECT request_session_id, resource_type, resource_description, request_mode, request_status
FROM sys.dm_tran_locks WHERE resource_database_id = DB_ID('MEI_TRAB');

-- Quem está bloqueado por quem
SELECT session_id, blocking_session_id, wait_type, wait_time
FROM sys.dm_exec_requests WHERE blocking_session_id <> 0;
```

Os grafos de deadlock ficam na sessão Extended Events `system_health`.

## 4. Atenção

- As transações do doWork duram milissegundos. A "encomenda não confirmada" tem de vir do Edit.
- O doWork nunca altera nem apaga a encomenda mais recente. Para testar conflitos, usem encomendas mais abaixo na lista.
- Um deadlock termina o ciclo do doWork. Usem `SET DEADLOCK_PRIORITY HIGH` no SSMS para ele sobreviver.
- Não alterar os scripts originais. Se precisarem de variantes (p. ex. um `WAITFOR` mais curto), façam cópias e documentem-nas.

## 5. Relatório (tópicos obrigatórios)

- [ ] Objetivos gerais e descrição do trabalho
- [ ] Objetivos de cada aplicação
- [ ] Transações: gestão, controlo, níveis de isolamento e recuperação
- [ ] Tipos de trincos (S, U, X, de intenção, key-range; granularidade; escalation)
- [ ] Testes e análise por nível de isolamento:
  - Edit sobre uma encomenda não confirmada
  - Vários utilizadores a editar a mesma encomenda
  - Browser com várias taxas de refresh (incluir: é possível um timer de 1 ms?)
- [ ] Conclusões: o que foi e o que não foi conseguido, e porquê
- [ ] Sugestões de melhoria (p. ex. `TRY/CATCH` no doWork, fórmula aleatória, tamanhos das variáveis nos triggers de delete)

## 6. Perguntar ao professor

- [ ] Prazo, tamanho do grupo e critérios de avaliação
- [ ] A linguagem das aplicações é livre?
- [ ] Pode-se ativar SNAPSHOT/RCSI?
- [ ] Este enunciado (2025/26, Draft 1.0) é a versão deste ano?
