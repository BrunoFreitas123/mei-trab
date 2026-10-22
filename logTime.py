import tkinter as tk
from tkinter import messagebox, ttk
import pyodbc


class LogTempoApp:

  def __init__(self, root):
    self.root = root
    self.root.title("MEI_TRAB - Aplicação Log Tempo")
    self.root.geometry("700x450")

    self.conn = None
    self.cursor = None
    self.timer_id = None

    self.create_conn_frame()

  def create_conn_frame(self):
    frame = ttk.LabelFrame(
        self.root, text=" Ligação - Log Tempo ", padding=15
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

    ttk.Button(frame, text="Conectar", command=self.connect_db).grid(
        row=5, column=0, columnspan=2, pady=20
    )

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
      self.create_ui()
    except Exception as e:
      messagebox.showerror("Erro", f"Erro de ligação:\n{e}")

  def create_ui(self):
    for w in self.root.winfo_children():
      w.destroy()

    main_frame = ttk.Frame(self.root, padding=10)
    main_frame.pack(fill="both", expand=True)

    ctrl = ttk.Frame(main_frame)
    ctrl.pack(fill="x", pady=5)
    ttk.Button(ctrl, text="Atualizar Dados", command=self.load_log_tempo).pack(
        side="left"
    )

    self.tree = ttk.Treeview(
        main_frame, columns=("UserId", "EncId", "Tempo"), show="headings"
    )
    self.tree.heading("UserId", text="Utilizador")
    self.tree.heading("EncId", text="ID Encomenda")
    self.tree.heading("Tempo", text="Tempo de Edição (Segundos)")
    self.tree.pack(fill="both", expand=True, pady=10)

    self.load_log_tempo()

  def load_log_tempo(self):
    for item in self.tree.get_children():
      self.tree.delete(item)

    try:
      # Query exata especificada no enunciado adaptada para agrupar por referência ativa
      query = """
                SELECT LO1.UserId, LO1.Objecto as EncId, DATEDIFF(SS, LO1.Valor, LO2.Valor) as Tempo
                FROM LogOperations LO1
                JOIN LogOperations LO2 ON LO1.Referencia = LO2.Referencia 
                WHERE LO1.EventType = 'O' AND LO2.EventType = 'O' 
                  AND LO1.DCriacao < LO2.DCriacao
                ORDER BY LO2.DCriacao DESC
            """
      self.cursor.execute(query)
      for r in self.cursor.fetchall():
        self.tree.insert("", "end", values=(r.UserId, r.EncId, r.Tempo))
    except Exception as e:
      print(f"Erro ao carregar log tempo: {e}")


if __name__ == "__main__":
  root = tk.Tk()
  app = LogTempoApp(root)
  root.mainloop()
