import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from models import DatabaseManager
import os


class ImportadorMunicipios:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Importador de Municípios")
        self.root.geometry("600x400")
        self.centralizar_janela()

        self.db = DatabaseManager()
        self.arquivo_selecionado = None
        self.setup_interface()

    def centralizar_janela(self):
        # Centralizar na tela
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = 600
        height = 400
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.root.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

    def setup_interface(self):
        # Frame principal
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Configuração do grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Título
        title_frame = ttk.Frame(self.main_frame)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ttk.Label(
            title_frame, text="Importador de Municípios", font=("Helvetica", 14, "bold")
        ).pack(side="left")

        # Frame de seleção de arquivo
        file_frame = ttk.LabelFrame(self.main_frame, text="Arquivo", padding="10")
        file_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        file_frame.grid_columnconfigure(1, weight=1)

        self.file_label = ttk.Label(file_frame, text="Nenhum arquivo selecionado")
        self.file_label.grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Button(
            file_frame, text="Selecionar Arquivo", command=self.selecionar_arquivo
        ).grid(row=0, column=0, padx=5)

        # Frame de status
        self.status_frame = ttk.LabelFrame(self.main_frame, text="Status", padding="10")
        self.status_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_rowconfigure(0, weight=1)

        self.status_text = tk.Text(self.status_frame, height=10, wrap=tk.WORD)
        self.status_text.grid(row=0, column=0, sticky="nsew")

        # Scrollbar para o status
        scrollbar = ttk.Scrollbar(
            self.status_frame, orient="vertical", command=self.status_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.status_text.configure(yscrollcommand=scrollbar.set)

        # Frame de botões
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.grid(row=3, column=0, sticky="e")

        ttk.Button(
            btn_frame, text="Importar", command=self.importar_arquivo, state="disabled"
        ).grid(row=0, column=0, padx=5)

        self.btn_importar = btn_frame.winfo_children()[0]

    def adicionar_log(self, mensagem):
        self.status_text.insert(tk.END, mensagem + "\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()

    def selecionar_arquivo(self):
        filename = filedialog.askopenfilename(
            title="Selecione o arquivo de municípios",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )

        if filename:
            self.arquivo_selecionado = filename
            self.file_label.config(text=os.path.basename(filename))
            self.btn_importar.config(state="normal")
            self.adicionar_log(f"Arquivo selecionado: {os.path.basename(filename)}")

    def importar_arquivo(self):
        if not self.arquivo_selecionado:
            messagebox.showwarning("Aviso", "Selecione um arquivo primeiro!")
            return

        try:
            self.status_text.delete(1.0, tk.END)
            self.adicionar_log("Iniciando importação...")
            self.root.update_idletasks()

            if self.db.import_municipios_from_txt(self.arquivo_selecionado):
                self.adicionar_log("Importação concluída com sucesso!")
                messagebox.showinfo("Sucesso", "Municípios importados com sucesso!")
            else:
                self.adicionar_log("Erro: Não foi possível importar os municípios")
                messagebox.showerror("Erro", "Não foi possível importar os municípios")

        except Exception as e:
            erro = str(e)
            self.adicionar_log(f"Erro durante a importação: {erro}")
            messagebox.showerror("Erro", f"Erro ao importar municípios: {erro}")
        finally:
            self.btn_importar.config(state="disabled")
            self.arquivo_selecionado = None
            self.file_label.config(text="Nenhum arquivo selecionado")


if __name__ == "__main__":
    app = ImportadorMunicipios()
    app.root.mainloop()
