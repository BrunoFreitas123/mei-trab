import datetime
import pyodbc
import streamlit as st

st.set_page_config(
    page_title="MEI_TRAB - Aplicação Edit", layout="centered"
)

st.title("MEI_TRAB - Aplicação Edit")

# 1. Ligação e Isolamento
st.subheader("1. Ligação e Isolamento")
col1, col2 = st.columns(2)
with col1:
  # Alterado o padrão para localhost,1433 para ligar diretamente ao container a correr no Mac
  server = st.text_input("Servidor", "localhost,1433")
  user = st.text_input("Utilizador", "sa")
with col2:
  db = st.text_input("Base de Dados", "MEI_TRAB")
  password = st.text_input("Password", "Sgbd2026!", type="password")

isolation = st.selectbox(
    "Nível de Isolamento",
    [
        "READ COMMITTED",
        "READ UNCOMMITTED",
        "REPEATABLE READ",
        "SNAPSHOT",
        "SERIALIZABLE",
    ],
)

# Inicializar variáveis de estado na sessão
if "conn" not in st.session_state:
  st.session_state.conn = None
if "cursor" not in st.session_state:
  st.session_state.cursor = None

if st.button("Conectar e Iniciar"):
  try:
    cstr = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={db};UID={user};PWD={password};Encrypt=no;TrustServerCertificate=yes;LoginTimeout=60;"
    st.session_state.conn = pyodbc.connect(cstr, autocommit=False)
    st.session_state.cursor = st.session_state.conn.cursor()
    
    # Aplicar o nível de isolamento selecionado
    st.session_state.cursor.execute(
        f"SET TRANSACTION ISOLATION LEVEL {isolation}"
    )
    st.session_state.conn.commit()
    st.success("Ligação estabelecida com sucesso!")
  except Exception as e:
    st.error(f"Erro de Ligação: {e}")

# Garantir que temos uma ligação ativa antes de prosseguir
if st.session_state.conn:
  st.markdown("---")
  st.subheader("2. Edição de Encomenda")

  enc_id_str = st.text_input("ID da Encomenda")

  if st.button("Carregar Encomenda"):
    try:
      enc_id = int(enc_id_str)
      cursor = st.session_state.cursor
      ref = f"G1-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"

      cursor.execute(
          "INSERT INTO LogOperations (EventType, Objecto, Valor, Referencia)"
          " VALUES (?, ?, ?, ?)",
          ("O", str(enc_id), str(datetime.datetime.now()), ref),
      )
      st.session_state.conn.commit()

      cursor.execute(
          "SELECT Nome, Morada FROM Encomenda WHERE EncId = ?", (enc_id,)
      )
      row = cursor.fetchone()
      if row:
        st.session_state.enc_id = enc_id
        # Tratar caso a coluna Nome venha a ser necessária ou omitida, salvando a morada
        st.session_state.morada = row.Morada if hasattr(row, "Morada") else row[1]
        st.session_state.ref = ref
        st.success("Encomenda carregada com sucesso!")
        st.rerun()
      else:
        st.warning("Encomenda não encontrada.")
    except Exception as e:
      st.error(f"Erro ao carregar: {e}")

  # 3. Secção de Edição da Morada e Linhas
  if "enc_id" in st.session_state:
    morada = st.text_input("Morada do Cliente", value=st.session_state.morada)

    try:
      cursor = st.session_state.cursor
      cursor.execute(
          "SELECT ProdutoId, Designacao, Preco, Qtd FROM EncLinha WHERE EncId = ?",
          (st.session_state.enc_id,),
      )
      lines = cursor.fetchall()

      st.write("**Linhas da Encomenda:**")
      
      for l in lines:
        c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
        c1.text(f"Prod: {l.ProdutoId}")
        c2.text(l.Designacao)
        c3.text(f"{l.Preco}€")
        
        new_q = c4.number_input(
            "Qtd", 
            value=int(l.Qtd), 
            key=f"q_{l.ProdutoId}", 
            label_visibility="collapsed"
        )

        if c4.button("Atualizar Qtd", key=f"btn_{l.ProdutoId}"):
          try:
            cursor.execute(
                "UPDATE EncLinha SET Qtd = ? WHERE EncId = ? AND ProdutoId = ?",
                (int(new_q), st.session_state.enc_id, l.ProdutoId),
            )
            st.success(f"Quantidade do produto {l.ProdutoId} atualizada localmente!")
          except Exception as e:
            st.error(f"Erro ao atualizar linha: {e}")

    except Exception as e:
      st.error(f"Erro ao procurar linhas da encomenda: {e}")

    st.markdown("---")
    b1, b2 = st.columns(2)
    
    if b1.button("Confirmar (Commit)", type="primary"):
      try:
        # Atualizar a morada final na tabela Encomenda
        cursor.execute(
            "UPDATE Encomenda SET Morada = ? WHERE EncId = ?",
            (morada, st.session_state.enc_id),
        )
        cursor.execute(
            "INSERT INTO LogOperations (EventType, Objecto, Valor, Referencia)"
            " VALUES (?, ?, ?, ?)",
            (
                "O",
                str(st.session_state.enc_id),
                str(datetime.datetime.now()),
                st.session_state.ref,
            ),
        )
        st.session_state.conn.commit()
        st.success("Transação confirmada com sucesso!")
        
        # Limpar estado da encomenda atual
        del st.session_state.enc_id
        if "morada" in st.session_state:
          del st.session_state.morada
        if "ref" in st.session_state:
          del st.session_state.ref
        st.rerun()
        
      except Exception as e:
        st.error(f"Erro no Commit: {e}")

    if b2.button("Descartar (Rollback)"):
      try:
        st.session_state.conn.rollback()
        st.warning("Transação descartada (Rollback efetuado).")
        
        # Limpar estado da encomenda atual
        del st.session_state.enc_id
        if "morada" in st.session_state:
          del st.session_state.morada
        if "ref" in st.session_state:
          del st.session_state.ref
        st.rerun()
        
      except Exception as e:
        st.error(f"Erro no Rollback: {e}")
