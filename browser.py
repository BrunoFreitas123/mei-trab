import tkinter as tk
from tkinter import messagebox, ttk
import pyodbc


class BrowserApp:

  def __init__(self, root):
    self.root = root
    self.root.title("MEI_TRAB - Aplicação Browser")
    self.root.geometry("800x600")

    self.conn = None
    self.cursor = None
    self.timer_id = None

    self.create_connection_frame()

  def create_connection_frame(self):
    for w in self.root.winfo_children():
      w.destroy()

    frame = ttk.LabelFrame(
        self.root, text=" Configuração de Ligação - Browser ", padding=15
    )
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    fields = [
        ("Servidor:", "localhost"),
        ("Base de Dados:", "MEI_TRAB"),
        ("Utilizador:", "sa"),
        ("Password:", ""),
    ]

    self.entries = {}
    for i, (label, default) in enumerate(fields):
      ttk.Label(frame, text=label).grid(
          row=i, column=0, sticky="w", pady=5, padx=5
      )
      e = ttk.Entry(
          frame, width=30, show="*" if "Password" in label else None
      )
      e.insert(0, default)
      e.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
      self.entries[label] = e

    ttk.Label(frame, text="Nível de Isolamento:").grid(
        row=4, column=0, sticky="w", pady=5, padx=5
    )
    self.isolation_var = tk.StringVar(value="READ UNCOMMITTED")
    iso_combo = ttk.Combobox(
        frame,
        textvariable=self.isolation_var,
        values=[
            "READ UNCOMMITTED",
            "READ COMMITTED",
            "REPEATABLE READ",
            "SNAPSHOT",
            "SERIALIZABLE",
        ],
        state="readonly",
    )
    iso_combo.grid(row=4, column=1, sticky="ew", pady=5, padx=5)

    ttk.Button(
        frame, text="Conectar e Abrir Browser", command=self.connect_db
    ).grid(row=5, column=0, columnspan=2, pady=20)

  def connect_db(self):
    try:
      conn_str = (
          f"DRIVER={{ODBC Driver 17 for SQL Server}};"
          f"SERVER={self.entries['Servidor:'].get()};"
          f"DATABASE={self.entries['Base de Dados:'].get()};"
          f"UID={self.entries['Utilizador:'].get()};"
          f"PWD={self.entries['Password:'].get()}"
      )
      self.conn = pyodbc.connect(conn_str, autocommit=True)
      self.cursor = self.conn.cursor()
      self.cursor.execute(
          f"SET TRANSACTION ISOLATION LEVEL {self.isolation_var.get()}"
      )
      self.create_browser_ui()
    except Exception as e:
      messagebox.showerror("Erro", f"Falha na ligação:\n{e}")

  def create_browser_ui(self):
    for w in self.root.winfo_children():
      w.destroy()

    main_frame = ttk.Frame(self.root, padding=10)
    main_frame.pack(fill="both", expand=True)

    # Controlo de Refresh por Timer
    top_control = ttk.Frame(main_frame)
    top_control.pack(fill="x", pady=5)

    ttk.Button(top_control, text="Refresh Manual", command=self.refresh_data).pack(
        side="left", padx=5
    )
    ttk.Label(top_control, text="Intervalo Timer (ms):").pack(
        side="left", padx=(20, 5)
    )
    self.interval_entry = ttk.Entry(top_control, width=10)
    self.interval_entry.insert(0, "2000")  # 2 segundos por defeito
    self.interval_entry.pack(side="left", padx=5)

    self.btn_timer = ttk.Button(
        top_control, text="Ligar Timer", command=self.toggle_timer
    )
    self.btn_timer.pack(side="left", padx=5)

    # Grelha de Encomendas
    ttk.Label(
        main_frame,
        text="Encomendas (Ordenadas por EncId decrescente):",
        font=("Arial", 10, "bold"),
    ).pack(anchor="w", pady=(10, 2))

    self.tree_enc = ttk.Treeview(
        main_frame,
        columns=("EncId", "ClienteId", "Nome", "Morada"),
        show="headings",
        height=7,
    )
    for col in ("EncId", "ClienteId", "Nome", "Morada"):
      self.tree_enc.heading(col, text=col)
    self.tree_enc.pack(fill="x", expand=False)
    self.tree_enc.bind("<<TreeviewSelect>>", self.on_select_encomenda)

    # Grelha de Linhas da Encomenda Selecionada
    ttk.Label(
        main_frame,
        text="Linhas da Encomenda Selecionada:",
        font=("Arial", 10, "bold"),
    ).pack(anchor="w", pady=(15, 2))

    self.tree_lin = ttk.Treeview(
        main_frame,
        columns=("ProdutoId", "Designacao", "Preco", "Qtd"),
        show="headings",
        height=7,
    )
    for col in ("ProdutoId", "Designacao", "Preco", "Qtd"):
      self.tree_lin.heading(col, text=col)
    self.tree_lin.pack(fill="both", expand=True)

    self.refresh_data()

  def refresh_data(self):
    try:
      # Manter ID selecionado se possível
      selected_items = self.tree_enc.selection()
      selected_enc = None
      if selected_items:
        selected_enc = self.tree_enc.item(selected_items[0], "values")[0]

      for i in self.tree_enc.get_children():
        self.tree_enc.delete(i)

      self.cursor.execute(
          "SELECT EncId, ClienteId, Nome, Morada FROM Encomenda ORDER BY EncId"
          " DESC"
      )
      rows = self.cursor.fetchall()
      for r in rows:
        item_id = self.tree_enc.insert(
            "", "end", values=(r.EncId, r.ClienteId, r.Nome, r.Morada)
        )
        if selected_enc and str(r.EncId) == str(selected_enc):
          self.tree_enc.selection_set(item_id)

      if not selected_items and rows:
        self.tree_enc.selection_set(self.tree_enc.get_children()[0])
        self.on_select_encomenda(None)

    except Exception as e:
      print(f"Erro no refresh: {e}")

  def on_select_encomenda(self, event):
    selected = self.tree_enc.selection()
    if not selected:
      return
    enc_id = self.tree_enc.item(selected[0], "values")[0]

    for i in self.tree_lin.get_children():
      self.tree_lin.delete(i)

    try:
      self.cursor.execute(
          "SELECT ProdutoId, Designacao, Preco, Qtd FROM EncLinha WHERE EncId ="
          " ?",
          (enc_id,),
      )
      for r in self.cursor.fetchall():
        self.tree_lin.insert(
            "", "end", values=(r.ProdutoId, r.Designacao, r.Preco, r.Qtd)
        )
    except Exception as e:
      print(e)

  def toggle_timer(self):
    if self.timer_id:
      self.root.after_cancel(self.timer_id)
      self.timer_id = None
      self.btn_timer.config(text="Ligar Timer")
    else:
      try:
        interval = int(self.interval_entry.get())
        if interval < 100:
          messagebox.showwarning(
              "Aviso", "Intervalo muito baixo. Recomenda-se >= 500ms."
          )
        self.run_timer(interval)
        self.btn_timer.config(text="Desligar Timer")
      except ValueError:
        messagebox.showerror("Erro", "Insira um valor numérico válido em ms.")

  def run_timer(self, interval):
    self.refresh_data()
    self.timer_id = self.root.after(interval, lambda: self.run_timer(interval))


if __name__ == "__main__":
  root = tk.Tk()
  app = BrowserApp(root)
  root.mainloop()
