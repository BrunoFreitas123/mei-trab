# Relatório TP1 – Controlo de Transacções, Concorrência e Bloqueios em Microsoft SQL Server

**Unidade Curricular:** Sistemas de Gestão de Bases de Dados (SGBD) · Mestrado em Engenharia Informática · UBI **Grupo:** \[G\_\_\] · **Autores:** \[Nome 1 (nº)\], \[Nome 2 (nº)\] **Data:** \[dd/mm/aaaa\]

---

## Resumo

&#91;3 a 5 linhas: objectivo do trabalho, ambiente usado, principais resultados observados (ex.: diferenças entre níveis de isolamento, deadlock, limite do polling) e conclusão principal.\]

## 1. Introdução e Fundamentação

&#91;Parágrafo de enquadramento: porque é que o controlo de concorrência é necessário num SGBD relacional e o que se pretende demonstrar experimentalmente.\]

### 1.1. Propriedades ACID

&#91;Atomicidade, Consistência, Isolamento e Durabilidade: definição de cada uma e papel do log de transacções.\]

### 1.2. Anomalias de concorrência

&#91;Definir, com um pequeno exemplo cada: leitura suja (dirty read), leitura não repetível, leitura fantasma, actualização perdida (lost update).\]

### 1.3. Níveis de isolamento

| Nível | Dirty read | Não repetível | Fantasma | Mecanismo no SQL Server |
| --- | --- | --- | --- | --- |
| READ UNCOMMITTED | \[ \] | \[ \] | \[ \] | \[ \] |
| READ COMMITTED | \[ \] | \[ \] | \[ \] | \[ \] |
| REPEATABLE READ | \[ \] | \[ \] | \[ \] | \[ \] |
| SNAPSHOT | \[ \] | \[ \] | \[ \] | \[ \] |
| SERIALIZABLE | \[ \] | \[ \] | \[ \] | \[ \] |

### 1.4. Trincagem pessimista vs. versionamento de linhas

&#91;Diferença entre locking e row versioning (SNAPSHOT / READ\_COMMITTED\_SNAPSHOT), custo no tempdb e conflitos de actualização (erro 3960).\]

## 2. Arquitectura das Aplicações

### 2.1. Ambiente de teste

&#91;SQL Server (versão) em Docker no \[macOS/Windows\], porta 1433, máquinas/processos clientes, linguagem e bibliotecas das aplicações (ex.: Python, tkinter, pyodbc, ODBC Driver 18).\]

### 2.2. Modelo de dados e scripts de apoio

&#91;Descrever Encomenda, EncLinha e LogOperations; triggers de auditoria (I/U/D) e procedimentos INSERIR/ACTUALIZAR/APAGAR\_ENCOMENDA; script de carga DoWork.sql. Referir quaisquer alterações aos scripts originais (ex.: caminho Linux em Create\_Tables.sql).\]

### 2.3. Componentes desenvolvidos

- **Edit** – \[descrição do fluxo da transacção longa e dos registos 'O'\]
- **Browser** – \[mestre-detalhe, refresh manual e por timer\]
- **Log Tempo** – \[query de correlação por Referencia\]
- **Log Monitor** – \[eventos I/U/D da LogOperations\]

### 2.4. Diagrama de módulos / classes

&#91;Inserir diagrama: camada de interface, módulo de ligação (credenciais + nível de isolamento), acesso a dados.\]

### 2.5. Estratégia de conectividade

&#91;Credenciais pedidas no arranque (Host/IP, BD, utilizador, palavra-passe), selecção do nível de isolamento por sessão, gestão de ligações e autocommit.\]

## 3. Análise de Trincos (Locks)

### 3.1. Metodologia de observação

&#91;Query a sys.dm\_tran\_locks usada, momento das capturas e sessões observadas.\]

### 3.2. Modos de trinco observados

| Modo | Significado | Quando foi observado (ensaio/fase) |
| --- | --- | --- |
| S (Shared) | \[ \] | \[ \] |
| U (Update) | \[ \] | \[ \] |
| X (Exclusive) | \[ \] | \[ \] |
| IS / IX / SIX (intenção) | \[ \] | \[ \] |
| RangeS-S / RangeX-X (intervalo de chave) | \[ \] | \[ \] |

### 3.3. Hierarquia e ciclo de vida

&#91;RID/KEY, PAGE, OBJECT, DATABASE: como evolui durante BEGIN, leitura, UPDATE e COMMIT/ROLLBACK. Incluir capturas das DMVs por fase.\]

### 3.4. Trincos adquiridos pelos triggers

&#91;Impacto dos inserts em LogOperations feitos dentro da transacção do utilizador (trinco X retido até ao fim) e efeito sobre o Log Monitor.\]

## 4. Resultados dos Ensaios Experimentais

### 4.1. E1 – Leitura suja (READ UNCOMMITTED vs. READ COMMITTED)

- **Objectivo:** \[ \]
- **Configuração:** \[níveis, EncId usado, apps envolvidas\]
- **Procedimento:** \[passos\]
- **Resultados:** \[tempos, capturas de ecrã, estado dos trincos\]
- **Análise:** \[ \]

### 4.2. E2 – Conflito de actualização concorrente (READ COMMITTED, REPEATABLE READ, SNAPSHOT)

- **Objectivo:** \[ \]
- **Configuração:** \[ \]
- **Procedimento:** \[duas instâncias do Edit sobre o mesmo EncId\]
- **Resultados:** \[tempo de espera por nível, comportamento após COMMIT/ROLLBACK, erro 3960 em SNAPSHOT\]
- **Análise:** \[ \]

### 4.3. E3 – Leituras não repetíveis e fantasmas (READ COMMITTED, REPEATABLE READ, SERIALIZABLE)

- **Objectivo:** \[ \]
- **Configuração:** \[ \]
- **Procedimento:** \[leituras sucessivas de COUNT/agregações durante o DoWork.sql\]
- **Resultados:** \[discrepâncias observadas por nível, trincos de intervalo\]
- **Análise:** \[ \]

### 4.4. E4 – Bloqueio mútuo (Deadlock)

- **Objectivo:** \[ \]
- **Configuração:** \[ \]
- **Procedimento:** \[acessos cruzados Encomenda/EncLinha\]
- **Resultados:** \[sessão vítima, tempo até à detecção, grafo XML de deadlock (excerto, completo em anexo)\]
- **Análise:** \[recursos em conflito, ordem de acesso, como prevenir (ordem consistente, trinco U, transacções curtas)\]

### 4.5. E5 – Impacto do refrescamento por polling

| Intervalo (ms) | Latência média da query | CPU (cliente/servidor) | Trincos / contenção | Observações |
| --- | --- | --- | --- | --- |
| 5000 | \[ \] | \[ \] | \[ \] | \[ \] |
| 1000 | \[ \] | \[ \] | \[ \] | \[ \] |
| 100 | \[ \] | \[ \] | \[ \] | \[ \] |
| \[mínimo exequível\] | \[ \] | \[ \] | \[ \] | \[ \] |

&#91;Análise dos resultados e gráfico (opcional).\]

### 4.6. Discussão específica: temporizadores de 1 ms e alternativas baseadas em eventos

&#91;Viabilidade técnica de 1 ms (latência de rede, parse/execução, granularidade do timer, custo de trincos partilhados repetidos) e alternativas: Push / WebSockets, notificações de consulta, Change Tracking, camada aplicacional de eventos. Vantagens e limitações de cada uma.\]

## 5. Conclusões e Lições Aprendidas

### 5.1. Objectivos alcançados

&#91;Síntese por ensaio.\]

### 5.2. Dificuldades encontradas

&#91;Ambiente (Docker/ODBC), concorrência, reprodutibilidade dos ensaios, etc.\]

### 5.3. Propostas de optimização para edições futuras

&#91;Transacções curtas sem interacção humana, controlo optimista, row versioning, índices, etc.\]

## Bibliografia

- Garcia-Molina, H., Ullman, J. D., & Widom, J. – *Database Systems: The Complete Book*. Pearson.
- Microsoft Learn – *Transaction Locking and Row Versioning Guide*.
- Microsoft Learn – *SET TRANSACTION ISOLATION LEVEL (Transact-SQL)*.
- &#91;Outras fontes\]

## Anexos

- **A.** Scripts modificados (Create\_Tables.sql, etc.)
- **B.** Código-fonte das aplicações
- **C.** Grafos XML de deadlock completos
- **D.** Capturas de ecrã adicionais
