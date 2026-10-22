import tkinter as tk
from tkinter import messagebox, ttk
import pyodbc


class LogApp:

  def __init__(self, root):
    self.root = root
    self.root.title("MEI_TRAB - Aplicação Log Geral")
    self.root.geometry("850x500")

    self.conn = None
    self.cursor = None
    self.timer_id = None

    self.create_conn_frame()

  def create_conn_frame(self):
    frame = ttk.LabelFrame(
        self.root, text=" Ligação - Log de Operações ", padding=15
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

    ttk.Label(ctrl, text="Mostrar N mais recentes:").pack(
        side="left", padx=5
    )
    self.limit_entry = ttk.Entry(ctrl, width=10)
    self.limit_entry.insert(0, "50")
    self.limit_entry.pack(side="left", padx=5)

    ttk.Button(ctrl, text="Atualizar", command=self.load_logs).pack(
        side="left", padx=10
    )

    columns = (
        "NumReg",
        "EventType",
        "Objecto",
        "Valor",
        "Referencia",
        "UserId",
        "TerminalId",
        "DCriacao",
    )
    self.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
      self.tree.heading(col, text=col)
      self.tree.column(col, width=90, stretch=True)

    self.tree.pack(fill="both", expand=True, pady=10)
    self.load_logs()

  def load_logs(self):
    for item in self.tree.get_children():
      self.tree.delete(item)

    try:
      limit = int(self.limit_entry.get())
    except ValueError:
      limit = 50

    try:
      query = f"""
                SELECT TOP ({limit}) NumReg, EventType, Objecto, Valor, Referencia, UserId, TerminalId, DCriacao
                FROM LogOperations
                WHERE EventType IN ('I', 'U', 'D')
                ORDER BY NumReg DESC
            """
      self.cursor.execute(query)
      for r in self.cursor.fetchall():
        self.tree.insert(
            "",
            "end",
            values=(
                r.NumReg,
                r.EventType,
                r.Objecto,
                r.Valor,
                r.Referencia,
                r.UserId,
                r.TerminalId,
                r.DCriacao,
            ),
        )
    except Exception as e:
      print(f"Erro ao carregar logs: {e}")


if __name__ == "__main__":
  root = tk.Tk()
  app = LogApp(root)
  root.mainloop()
