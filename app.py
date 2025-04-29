import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pandas as pd
from tkcalendar import DateEntry
from models import DatabaseManager  # Alterado para importar a classe


class AppNotasFiscais:
    def __init__(self, root):
        self.root = root
        self.root.title("KBL ACCOUTING - REST GOIÂNIA")

        self.root.geometry("1366x768")

        # Definir estilo
        self.style = ttk.Style()

        # Inicializar gerenciador do banco de dados
        self.db = DatabaseManager()

        # Configurar interface
        self.setup_interface()

        # Carregar dados iniciais
        self.carregar_dados()

    def criar_campo_grupo(self, container, campos):
        for row, (campo, label, widget_class, widget_args) in enumerate(campos):
            ttk.Label(container, text=label).grid(
                row=row, column=0, padx=5, pady=5, sticky="w"
            )
            self.entries[campo] = widget_class(container, **widget_args)
            self.entries[campo].grid(row=row, column=1, padx=5, pady=5, sticky="ew")

    def criar_campos_nota(self, container):
        campos = [
            ("referencia", "Referência", ttk.Entry, {"width": 20}),
            ("num_nf", "Nº NF", ttk.Entry, {"width": 20}),
            (
                "dt_emissao",
                "Data de Emissão",
                DateEntry,
                {"width": 20, "date_pattern": "dd/mm/yyyy", "locale": "pt_BR"},
            ),
            (
                "dt_pagamento",
                "Data de Pagamento",
                DateEntry,
                {"width": 20, "date_pattern": "dd/mm/yyyy", "locale": "pt_BR"},
            ),
            ("recibo", "Recibo", ttk.Entry, {"width": 20}),
        ]
        self.criar_campo_grupo(container, campos)

    def criar_campos_fornecedor(self, container):
        campos = [
            ("cnpj", "CPF/CNPJ", ttk.Entry, {"width": 20}),
            ("fornecedor", "Fornecedor", ttk.Entry, {"width": 40}),
            (
                "cadastrado_goiania",
                "Cadastrado em Goiânia",
                ttk.Combobox,
                {"values": ["Sim", "Não"], "width": 20},
            ),
            (
                "fora_pais",
                "Fora do País",
                ttk.Combobox,
                {"values": ["Sim", "Não"], "width": 20},
            ),
            ("uf", "UF", ttk.Combobox, {"width": 20}),
            ("municipio", "Município", ttk.Combobox, {"width": 20}),
            (
                "cod_municipio",
                "Código do Município",
                ttk.Entry,
                {"width": 20, "state": "readonly"},
            ),
            ("inscricao_municipal", "Inscrição Municipal", ttk.Entry, {"width": 20}),
        ]
        self.criar_campo_grupo(container, campos)

        # Configurar eventos
        self.entries["cnpj"].bind("<FocusOut>", self.buscar_fornecedor)
        self.entries["uf"].bind("<<ComboboxSelected>>", self.atualizar_municipios)
        self.entries["municipio"].bind("<KeyRelease>", self.filtrar_municipios)
        self.entries["municipio"].bind(
            "<<ComboboxSelected>>", self.atualizar_cod_municipio
        )
        self.entries["cadastrado_goiania"].bind(
            "<<ComboboxSelected>>", self.atualizar_dados_goiania
        )
       

        # Configurações iniciais
        self.entries["fora_pais"].set("Não")
        self.entries["cadastrado_goiania"].set("Não")

        self.carregar_ufs()

    def criar_campos_servico(self, container):
        campos = [
            ("tipo_servico", "Tipo de Serviço", ttk.Combobox, {"width": 40}),
            ("base_calculo", "base de calculo", ttk.Combobox, {"width": 40},)
        ]
        self.criar_campo_grupo(container, campos)
        self.carregar_tipos_servico()
        self.carregar_bases_calculo()

    def criar_campos_financeiros(self, container):
        # Primeiro campo - Alíquota
        row = 0
        ttk.Label(container, text="Alíquota").grid(
            row=row, column=0, padx=5, pady=5, sticky="w"
        )
        self.entries["aliquota"] = ttk.Entry(container, width=20)
        self.entries["aliquota"].grid(row=row, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(container, text="(Ex: 5.00)", foreground="gray").grid(
            row=row, column=2, padx=5, pady=5, sticky="w"
        )

        # Segundo campo - Valor NF
        row += 1
        ttk.Label(container, text="Valor NF").grid(
            row=row, column=0, padx=5, pady=5, sticky="w"
        )
        self.entries["valor_nf"] = ttk.Entry(container, width=20)
        self.entries["valor_nf"].grid(row=row, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(container, text="(Ex: 1000.00)", foreground="gray").grid(
            row=row, column=2, padx=5, pady=5, sticky="w"
        )

        # Terceiro campo - Recolhimento
        row += 1
        ttk.Label(container, text="Recolhimento").grid(
            row=row, column=0, padx=5, pady=5, sticky="w"
        )
        self.entries["recolhimento"] = ttk.Combobox(container, width=40)
        self.entries["recolhimento"].grid(
            row=row, column=1, columnspan=2, padx=5, pady=5, sticky="w"
        )

        # Configurar validações e formatação para os campos numéricos
        for campo in ["aliquota", "valor_nf"]:
            self.entries[campo].config(
                validate="key",
                validatecommand=(self.root.register(self.validar_numero), "%P"),
            )
            self.entries[campo].bind(
                "<FocusOut>", lambda e, c=campo: self.formatar_numero(campo=c)
            )

        self.carregar_tipos_recolhimento()

    def criar_campos(self):
        # Dados do Fornecedor (esquerda)
        dados_fornecedor = ttk.LabelFrame(
            self.form_frame, text="Dados do Fornecedor", padding=10
        )
        dados_fornecedor.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Dados da Nota (direita)
        dados_nf = ttk.LabelFrame(self.form_frame, text="Dados da Nota", padding=10)
        dados_nf.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # Dados do Serviço (esquerda)
        dados_servico = ttk.LabelFrame(
            self.form_frame, text="Dados do Serviço", padding=10
        )
        dados_servico.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Dados Financeiros (direita)
        dados_financeiros = ttk.LabelFrame(
            self.form_frame, text="Dados Financeiros", padding=10
        )
        dados_financeiros.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        # Configurar grid
        self.form_frame.grid_columnconfigure(0, weight=1)
        self.form_frame.grid_columnconfigure(1, weight=1)

        # Criar campos em cada seção
        self.criar_campos_fornecedor(dados_fornecedor)
        self.criar_campos_nota(dados_nf)
        self.criar_campos_servico(dados_servico)
        self.criar_campos_financeiros(dados_financeiros)

    def setup_interface(self):
        # Criar frame para título e subtítulo
        titulo_frame = ttk.Frame(self.root)
        titulo_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        # Título principal
        ttk.Label(
            titulo_frame,
            text="Sistema de Notas Fiscais",
            style="Title.TLabel",
            font=("Helvetica", 14, "bold"),
        ).grid(row=0, column=0, sticky="w")

        # Subtítulo
        ttk.Label(
            titulo_frame,
            text="Módulo de Cadastro e Gerenciamento de Notas Fiscais",
            font=("Helvetica", 10),
        ).grid(row=1, column=0, sticky="w")

        # Canvas principal com scroll
        self.main_canvas = tk.Canvas(self.root)
        self.scrollbar = ttk.Scrollbar(
            self.root, orient="vertical", command=self.main_canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.main_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(
                scrollregion=self.main_canvas.bbox("all")
            ),
        )

        self.main_canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)

        # Frame para o formulário
        self.form_frame = ttk.Frame(self.scrollable_frame, padding="10")
        self.form_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Frame para a tabela
        self.table_frame = ttk.LabelFrame(
            self.scrollable_frame, text="Notas Fiscais Cadastradas", padding="10"
        )
        self.table_frame.grid(
            row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10
        )

        self.entries = {}
        self.criar_campos()
        self.criar_botoes()
        self.criar_tabela(self.table_frame)

        # Layout
        self.main_canvas.grid(row=1, column=0, sticky="nsew")
        self.scrollbar.grid(row=1, column=1, sticky="ns")
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.criar_rodape()

        # Ajustar configuração do grid para acomodar o rodapé
        self.root.grid_rowconfigure(1, weight=1)  # Canvas principal expande
        self.root.grid_rowconfigure(998, weight=0)  # Separator não expande
        self.root.grid_rowconfigure(999, weight=0)  # Footer não expande
        self.root.grid_columnconfigure(0, weight=1)

    def criar_rodape(self):
        # Criar frame para o rodapé
        footer_frame = ttk.Frame(self.root)
        footer_frame.grid(
            row=999, column=0, columnspan=2, sticky="ew", padx=5, pady=5
        )  # row grande para garantir que fique no final

        # Data atual
        data_atual = datetime.now().strftime("%d/%m/%Y")
        ttk.Label(footer_frame, text=f"Data: {data_atual}", font=("Helvetica", 8)).pack(
            side="left", padx=10
        )

        # Versão
        ttk.Label(footer_frame, text="Versão 1.0", font=("Helvetica", 8)).pack(
            side="right", padx=10
        )

        # Linha separadora acima do rodapé
        separator = ttk.Separator(self.root, orient="horizontal")
        separator.grid(row=998, column=0, columnspan=2, sticky="ew", padx=5)

   
    def criar_botoes(self):
        btn_frame = ttk.Frame(self.form_frame)
        btn_frame.grid(row=len(self.entries) + 1, column=0, columnspan=2, pady=20, sticky='w')

        # Definir cores para os botões
        cores = {
            "salvar": "#4CAF50",    # Verde
            "editar": "#2196F3",    # Azul
            "limpar": "#9C27B0",    # Roxo
            "excluir": "#F44336",   # Vermelho
            "exportar": "#607D8B",  # Cinza azulado
            "gerenciar": "#FF9800"  # Laranja
        }

        # Criando botões com as cores desejadas
        btn_salvar = tk.Button(btn_frame,
                            text="Salvar", width=20, bg=cores["salvar"], fg="white", command=self.salvar)
        btn_editar = tk.Button(btn_frame,
                            text="Editar", width=20, bg=cores["editar"], fg="white", command=self.editar_selecionado)
        btn_limpar = tk.Button(btn_frame,
                            text="Limpar", width=20, bg=cores["limpar"], fg="white", command=self.limpar)
        btn_excluir = tk.Button(btn_frame,
                                text="Excluir Selecionado", width=20, bg=cores["excluir"], fg="white", command=self.excluir_selecionado)
        btn_exportar_excel = tk.Button(btn_frame,
                                    text="Exportar Excel", width=20, bg=cores["exportar"], fg="white", command=self.exportar_excel)
        btn_exportar_txt = tk.Button(btn_frame,
                                    text="Exportar TXT", width=20, bg=cores["exportar"], fg="white", command=self.exportar_txt)
        btn_gerenciar = tk.Button(btn_frame, text="Gerenciar Tomadores", width=20, bg=cores["gerenciar"], fg="black", command=self.abrir_config_tomador)

        # Posicionando os botões em colunas sequenciais, começando da coluna 0 e alinhando à esquerda
        btn_salvar.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        btn_editar.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        btn_limpar.grid(row=0, column=2, padx=5, pady=5, sticky='w')
        btn_excluir.grid(row=0, column=3, padx=5, pady=5, sticky='w')
        btn_exportar_excel.grid(row=0, column=4, padx=5, pady=5, sticky='w')
        btn_exportar_txt.grid(row=0, column=5, padx=5, pady=5, sticky='w')
        btn_gerenciar.grid(row=0, column=6, padx=5, pady=5, sticky='w')

        # Alinhar o frame à esquerda dentro do form_frame
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_rowconfigure(0, weight=1)
        
       
    def exportar_txt(self):
        # Abrir uma caixa de diálogo para salvar o arquivo
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt", 
            filetypes=[("Arquivos de Texto", "*.txt")]
        )
    def carregar_dados(self):
        try:
            df = self.db.get_all_notas_fiscais()
            print("Dados retornados do banco:", df)

            # Limpar tabela atual
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Inserir dados garantindo a ordem correta
            for _, row in df.iterrows():
                values = [
                    row["id"],  # Incluir ID
                    row["referencia"],
                    row["cadastrado_goiania"],
                    row["fora_pais"],
                    row["cnpj"],
                    row["descricao_fornecedor"],
                    row["tipo_servico"],
                    row["numero_nf"],
                    row["dt_emissao"],
                    row["dt_pagamento"],
                    row["aliquota"],
                    row["valor_nf"],
                    row["recolhimento"],
                ]
                print("Valores sendo inseridos:", values)
                self.tree.insert("", "end", values=values)
        except Exception as e:
            print(f"Erro detalhado: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao carregar dados: {str(e)}")

            def criar_cabecalho_tabela(self, container):
                # Frame para cabeçalho da tabela
                header_frame = ttk.Frame(container, style="Header.TFrame")
                header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
                
                # Configurar estilo para o cabeçalho
                self.style.configure("Header.TFrame", background="#f0f0f0")
                self.style.configure("Header.TLabel", background="#f0f0f0", font=("Helvetica", 10, "bold"))
                
                # Título do cabeçalho
                ttk.Label(
                    header_frame, 
                    text="Listagem de Notas Fiscais", 
                    style="Header.TLabel"
                ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
                
                # Adicionar campo de busca
                ttk.Label(
                    header_frame, 
                    text="Buscar:", 
                    style="Header.TLabel"
                ).grid(row=0, column=1, sticky="e", padx=(50, 5), pady=5)
                
                # Campo de busca
                self.busca_entry = ttk.Entry(header_frame, width=30)
                self.busca_entry.grid(row=0, column=2, sticky="w", padx=5, pady=5)
                
                # Botão de busca
                ttk.Button(
                    header_frame,
                    text="Buscar",
                    command=self.buscar_notas
                ).grid(row=0, column=3, sticky="w", padx=5, pady=5)
                
                # Separador
                ttk.Separator(container, orient="horizontal").grid(
                    row=1, column=0, sticky="ew", padx=10, pady=5
                )

    def carregar_ufs(self):
        try:
            ufs = self.db.get_all_ufs()
            self.entries["uf"]["values"] = ufs
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar UFs: {str(e)}")

    def carregar_tipos_servico(self):
        try:
            tipos = self.db.get_all_tipos_servico()
            if tipos:
                self.entries["tipo_servico"]["values"] = tipos
            else:
                print("Nenhum tipo de serviço encontrado no banco de dados")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar tipos de serviço: {str(e)}")
            print(f"Erro detalhado: {e}")

    def carregar_tipos_recolhimento(self):
        try:
            recolhimentos = self.db.get_all_recolhimentos()
            self.entries["recolhimento"]["values"] = recolhimentos
        except Exception as e:
            messagebox.showerror(
                "Erro", f"Erro ao carregar tipos de recolhimento: {str(e)}"
            )

    def atualizar_municipios(self, event=None):
        uf = self.entries["uf"].get()
        if uf:
            try:
                municipios = self.db.get_municipios_by_uf(uf)
                self.entries["municipio"]["values"] = [mun[0] for mun in municipios]
                self.entries["municipio"].set("")
                self.entries["cod_municipio"].configure(state="normal")
                self.entries["cod_municipio"].delete(0, tk.END)
                self.entries["cod_municipio"].configure(state="readonly")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar municípios: {str(e)}")

    def atualizar_cod_municipio(self, event=None):
        uf = self.entries["uf"].get()
        municipio = self.entries["municipio"].get()
        if uf and municipio:
            try:
                cod_municipio = self.db.get_cod_municipio(uf, municipio)
                if cod_municipio:
                    self.entries["cod_municipio"].configure(state="normal")
                    self.entries["cod_municipio"].delete(0, tk.END)
                    self.entries["cod_municipio"].insert(0, cod_municipio)
                    self.entries["cod_municipio"].configure(state="readonly")
            except Exception as e:
                messagebox.showerror(
                    "Erro", f"Erro ao carregar código do município: {str(e)}"
                )

    def atualizar_dados_goiania(self, event=None):
        valor = self.entries["cadastrado_goiania"].get()
        if valor == "Sim":
            try:
                # Desabilitar e setar Fora do País como Não
                self.entries["fora_pais"].set("Não")
                self.entries["fora_pais"].configure(state="disabled")

                # Setar UF como GO
                self.entries["uf"].set("GO")

                # Atualizar lista de municípios
                municipios = self.db.get_municipios_by_uf("GO")
                self.entries["municipio"]["values"] = [mun[0] for mun in municipios]

                # Setar município como GOIÂNIA
                goiania = next(
                    (mun for mun in municipios if mun[0].upper() == "GOIANIA"), None
                )
                if goiania:
                    self.entries["municipio"].set(goiania[0])

                    # Configurar código do município
                    self.entries["cod_municipio"].configure(state="normal")
                    self.entries["cod_municipio"].delete(0, tk.END)
                    self.entries["cod_municipio"].insert(0, goiania[1])
                    self.entries["cod_municipio"].configure(state="readonly")

                # Desabilitar campos
                self.entries["uf"].configure(state="disabled")
                self.entries["municipio"].configure(state="disabled")

            except Exception as e:
                messagebox.showerror(
                    "Erro", f"Erro ao configurar dados de Goiânia: {str(e)}"
                )
        else:
            # Reabilitar campos quando for "Não"
            self.entries["fora_pais"].configure(state="normal")
            self.entries["uf"].configure(state="normal")
            self.entries["municipio"].configure(state="normal")

            # Limpar os campos
            self.entries["uf"].set("")
            self.entries["municipio"].set("")
            self.entries["cod_municipio"].configure(state="normal")
            self.entries["cod_municipio"].delete(0, tk.END)
            self.entries["cod_municipio"].configure(state="readonly")

    def buscar_fornecedor(self, event=None):
        cnpj = self.entries["cnpj"].get()
        if cnpj:
            try:
                result = self.db.get_fornecedor_by_cnpj(cnpj)
                if result:
                    self.entries["fornecedor"].delete(0, tk.END)
                    self.entries["fornecedor"].insert(0, result[0])
                    self.entries["uf"].set(result[1])
                    self.atualizar_municipios()
                    self.entries["municipio"].set(result[2])
                    self.entries["cod_municipio"].configure(state="normal")
                    self.entries["cod_municipio"].delete(0, tk.END)
                    self.entries["cod_municipio"].insert(0, result[3])
                    self.entries["cod_municipio"].configure(state="readonly")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao buscar fornecedor: {str(e)}")

    def validar_numero(self, valor):
        if valor == "" or valor == ".":
            return True

        # Remove qualquer vírgula e substitui por ponto
        valor = valor.replace(",", ".")

        # Garante que só existe um ponto decimal
        if valor.count(".") > 1:
            return False

        try:
            float(valor)
            return True
        except ValueError:
            return False

    def formatar_numero(self, event=None, campo=None):
        """Formata o número quando o campo perde o foco"""
        if not campo:
            return

        valor = self.entries[campo].get()
        if valor:
            try:
                # Converte para float e formata com 2 decimais
                num = float(valor.replace(",", "."))
                valor_formatado = f"{num:.2f}"

                # Atualiza o campo com o valor formatado
                self.entries[campo].delete(0, tk.END)
                self.entries[campo].insert(0, valor_formatado)
            except ValueError:
                pass

    def limpar(self):
        for entry in self.entries.values():
            if hasattr(entry, "delete"):
                entry.delete(0, tk.END)
            elif hasattr(entry, "set"):
                entry.set("")

    def validar_campos(self):
        """Valida os campos obrigatórios baseado no tipo de documento (CPF/CNPJ) e Fora do País"""
        # Obter o CPF/CNPJ e Fora do País
        documento = self.entries["cnpj"].get().strip()
        fora_pais = self.entries["fora_pais"].get() == "Sim"

        # Validar campos básicos sempre obrigatórios
        campos_sempre_obrigatorios = {
            "cnpj": "CPF/CNPJ",
            "valor_nf": "Valor",
            "tipo_servico": "Tipo de Serviço",
            "recolhimento": "Recolhimento",
        }

        for campo, nome in campos_sempre_obrigatorios.items():
            if not self.entries[campo].get():
                messagebox.showwarning("Aviso", f"O campo {nome} é obrigatório!")
                self.entries[campo].focus()
                return False

        # Verificar se é CPF (CPF tem 11 dígitos) ou se é Fora do País
        eh_cpf = len(documento.replace(".", "").replace("-", "").replace("/", "")) <= 11

        if eh_cpf or fora_pais:
            # Para CPF ou Fora do País, recibo é obrigatório
            if not self.entries["recibo"].get():
                messagebox.showwarning("Aviso", "O campo Recibo é obrigatório!")
                self.entries["recibo"].focus()
                return False
        else:
            # Para CNPJ nacional, número da nota fiscal é obrigatório
            if not self.entries["num_nf"].get():
                messagebox.showwarning("Aviso", "O campo Nº NF é obrigatório!")
                self.entries["num_nf"].focus()
                return False

        # Validar campos específicos quando não é Fora do País
        if not fora_pais:
            campos_nacionais = {
                "uf": "UF",
                "municipio": "Município",
            }

            for campo, nome in campos_nacionais.items():
                if not self.entries[campo].get():
                    messagebox.showwarning(
                        "Aviso",
                        f"O campo {nome} é obrigatório para fornecedores nacionais!",
                    )
                    self.entries[campo].focus()
                    return False

        return True
    
    def criar_campos_servico(self, container):
        campos = [
            ("tipo_servico", "Tipo de Serviço", ttk.Combobox, {"width": 40}),
            # Nova linha para o campo Base de Cálculo
            (
                "base_calculo",
                "Base de Cálculo",
                ttk.Combobox,
                {
                    "width": 40,
                    "values": [
                        "00 - Base de cálculo normal",
                        "01 - Publicidade e propaganda",
                        "02 - Representação comercial",
                        "03 - Corretagem de seguro",
                        "04 - Construção civil",
                        "05 - Call Center",
                        "06 - Estação Digital",
                        "07 - Serviços de saúde (órtese e prótese)",
                    ]
                }
            ),
        ]
        self.criar_campo_grupo(container, campos)
        self.carregar_tipos_servico()
        self.carregar_bases_calculo()  # Novo método para carregar as bases de cálculo
        
    # Adicionar um novo método para carregar as bases de cálculo
    def carregar_bases_calculo(self):
        try:
            bases_calculo = self.db.get_all_bases_calculo()
            if bases_calculo:
                self.entries["base_calculo"]["values"] = bases_calculo
                # Definir a opção padrão
                self.entries["base_calculo"].set("00 - Base de cálculo normal")
            else:
                print("Nenhuma base de cálculo encontrada no banco de dados")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar bases de cálculo: {str(e)}")
            print(f"Erro detalhado: {e}")


    def salvar(self):
        if not self.validar_campos():
            return

        dados = {}
        for campo, entry in self.entries.items():
            if hasattr(entry, "get_date"):
                dados[campo] = entry.get_date().strftime("%Y-%m-%d")
            else:
                dados[campo] = entry.get()

        try:
            fornecedor_id = self.db.insert_fornecedor(
                dados["cnpj"],
                dados["fornecedor"],
                dados["uf"],
                dados["municipio"],
                dados["cod_municipio"],
                dados["fora_pais"],
                dados["cadastrado_goiania"],
            )

            if fornecedor_id is None:
                messagebox.showerror("Erro", "Erro ao salvar fornecedor")
                return

            nota_fiscal_data = {
                "referencia": dados["referencia"],
                "CNPJ": dados["cnpj"],
                "Fornecedor_ID": fornecedor_id,
                "Inscrição Municipal": dados["inscricao_municipal"],
                "Tipo de Serviço": dados["tipo_servico"],
                "Base de Cálculo": dados["base_calculo"],  # Novo campo
                "Nº NF": dados["num_nf"],
                "Dt. Emissão": dados["dt_emissao"],
                "Dt. Pagamento": dados["dt_pagamento"],
                "Aliquota": (
                    float(dados["aliquota"].replace(",", "."))
                    if dados["aliquota"]
                    else 0
                ),
                "Valor NF": (
                    float(dados["valor_nf"].replace(",", "."))
                    if dados["valor_nf"]
                    else 0
                ),
                "Recolhimento": dados["recolhimento"],
                "RECIBO": dados["recibo"],
                "UF": dados["uf"],
                "Município": dados["municipio"],
                "Código Município": dados["cod_municipio"],
                "cadastrado_goiania": dados["cadastrado_goiania"],
                "fora_pais": dados["fora_pais"],
            }

            if hasattr(self, "current_editing_id"):
                resultado = self.db.update_nota_fiscal(
                    self.current_editing_id, nota_fiscal_data
                )
                if resultado:
                    mensagem = "Nota fiscal atualizada com sucesso!"
                    delattr(self, "current_editing_id")
                else:
                    messagebox.showerror(
                        "Erro", "Não foi possível atualizar o registro"
                    )
                    return
            else:
                self.db.insert_nota_fiscal(nota_fiscal_data)
                mensagem = "Nota fiscal cadastrada com sucesso!"

                

            messagebox.showinfo("Sucesso", mensagem)
            self.limpar()
            self.carregar_dados()
            self.tree.selection_remove(self.tree.selection())

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar dados: {str(e)}")
            print(f"Erro detalhado: {str(e)}")  # Debug

    def excluir_selecionado(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Por favor, selecione um item para excluir")
            return

        if messagebox.askyesno(
            "Confirmar Exclusão", "Tem certeza que deseja excluir o item selecionado?"
        ):
            try:
                # Obter valores do item selecionado
                item = self.tree.item(selecionado[0])
                valores = item["values"]

                # O ID é o primeiro campo na lista de valores
                id_nota = valores[0]

                if self.db.delete_nota_fiscal(id_nota):
                    messagebox.showinfo("Sucesso", "Nota fiscal excluída com sucesso!")
                    self.carregar_dados()  # Recarrega a tabela
                else:
                    messagebox.showerror(
                        "Erro", "Não foi possível excluir a nota fiscal"
                    )
            except Exception as e:
                print(f"Erro ao excluir nota fiscal: {str(e)}")
                messagebox.showerror("Erro", f"Erro ao excluir nota fiscal: {str(e)}")

    # E no método exportar_excel da classe principal:
    def exportar_excel(self):
        def do_export(inscricao, filename):
            try:
                if self.db.export_to_excel(filename):
                    # Se exportou com sucesso, limpa a tabela
                    if self.db.limpar_notas_fiscais():
                        messagebox.showinfo(
                            "Sucesso",
                            f"Dados exportados com sucesso para o arquivo:\n{filename}\n\nTabela de notas fiscais foi limpa.",
                        )
                        self.carregar_dados()  # Atualiza a visualização da tabela
                    else:
                        messagebox.showwarning(
                            "Atenção",
                            f"Dados foram exportados para:\n{filename}\n\nMas não foi possível limpar a tabela.",
                        )
                else:
                    messagebox.showerror("Erro", "Não foi possível exportar os dados")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar dados: {str(e)}")

        # Confirmar com o usuário antes de prosseguir
        if messagebox.askyesno(
            "Confirmar Exportação",
            "Após a exportação, a tabela de notas fiscais será limpa.\n\nDeseja continuar?",
        ):
            # Abrir janela de seleção do tomador
            ExportSelectionWindow(self.root, self.db, do_export)

    def filtrar_municipios(self, event=None):
        # Pega o texto digitado
        texto_digitado = self.entries["municipio"].get().upper()
        uf = self.entries["uf"].get()

        if uf:
            try:
                # Busca todos os municípios da UF
                municipios = self.db.get_municipios_by_uf(uf)
                # Filtra os municípios que contêm o texto digitado
                municipios_filtrados = [
                    mun[0] for mun in municipios if texto_digitado in mun[0].upper()
                ]
                # Atualiza a lista do combobox
                self.entries["municipio"]["values"] = municipios_filtrados

                # Mantém o dropdown aberto
                self.entries["municipio"].event_generate("<Down>")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao filtrar municípios: {str(e)}")

    def criar_tabela(self, container):
        # Frame para a tabela com altura fixa
        frame_tabela = ttk.Frame(container)
        frame_tabela.grid(sticky="nsew", padx=10, pady=10)

        # Configurar o grid do container
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # Configurar as colunas - Adicionando ID como primeira coluna
        colunas = [
            ("id", "ID", 50),
            ("referencia", "Referência", 100),
            ("cadastrado_goiania", "Cad. Goiânia", 100),
            ("fora_pais", "Fora do País", 100),
            ("cnpj", "CNPJ/CPF", 140),
            ("descricao_fornecedor", "Fornecedor", 250),
            ("tipo_servico", "Tipo Serviço", 150),
            ("base_calculo", "Base de Cálculo", 150),  # Nova coluna
            ("numero_nf", "Nº NF", 100),
            ("dt_emissao", "Emissão", 100),
            ("dt_pagamento", "Pagamento", 100),
            ("aliquota", "Alíquota", 80),
            ("valor_nf", "Valor NF", 100),
            ("recolhimento", "Recolhimento", 150),
        ]

        # Criar Treeview com scrollbars
        self.tree = ttk.Treeview(
            frame_tabela,
            columns=[col[0] for col in colunas],
            show="headings",
            height=15,
        )

        # Configurar cabeçalhos e larguras
        for col, header, width in colunas:
            self.tree.heading(col, text=header)
            if col == "id":
                # Configurar coluna ID como oculta
                self.tree.column(col, width=0, stretch=False)
            else:
                self.tree.column(col, width=width, minwidth=width)

        # Scrollbars
        vsb = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
          
        # Grid
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        
        
        # Configurar expansão do frame da tabela
        frame_tabela.grid_columnconfigure(0, weight=1)
        frame_tabela.grid_rowconfigure(0, weight=1)
        self.tree.bind("<Double-1>", self.editar_registro)
       
    def editar_registro(self, event=None):
        item_selecionado = self.tree.selection()
        if item_selecionado:
            self.editar_selecionado()

    def editar_selecionado(self):
        item_selecionado = self.tree.selection()
        if not item_selecionado:
            messagebox.showwarning(
                "Aviso", "Por favor, selecione um registro para editar"
            )
            return

        # Obter valores do item selecionado
        valores = self.tree.item(item_selecionado[0])["values"]
        self.current_editing_id = valores[0]  # ID é o primeiro campo

        # Buscar dados completos da nota fiscal
        nota_fiscal = self.db.get_nota_fiscal_by_id(self.current_editing_id)
        if not nota_fiscal:
            messagebox.showerror(
                "Erro", "Não foi possível carregar os dados da nota fiscal"
            )
            return

        # Limpar formulário antes
        self.limpar()

        try:
            # Remover quebras de linha de strings que possam ter \n
            def limpar_string(valor):
                return str(valor).strip().replace("\n", "") if valor is not None else ""

            # Preencher campos da nota
            self.entries["referencia"].insert(0, limpar_string(nota_fiscal[1]))
            self.entries["cadastrado_goiania"].set(limpar_string(nota_fiscal[2]))
            self.entries["fora_pais"].set(limpar_string(nota_fiscal[3]))
            self.entries["num_nf"].insert(0, limpar_string(nota_fiscal[7]))
           
            # Datas com tratamento de erro
            try:
                dt_emissao = datetime.strptime(
                    limpar_string(nota_fiscal[9]), "%Y-%m-%d"
                )
                dt_pagamento = datetime.strptime(
                    limpar_string(nota_fiscal[10]), "%Y-%m-%d"
                )
                self.entries["dt_emissao"].set_date(dt_emissao)
                self.entries["dt_pagamento"].set_date(dt_pagamento)
            except Exception as e:
                print(f"Erro ao converter datas: {e}")
                # Usar data atual como fallback
                hoje = datetime.now()
                self.entries["dt_emissao"].set_date(hoje)
                self.entries["dt_pagamento"].set_date(hoje)

            # Dados do fornecedor
            self.entries["cnpj"].insert(0, limpar_string(nota_fiscal[4]))
            self.entries["fornecedor"].insert(0, limpar_string(nota_fiscal[14]))
            self.entries["inscricao_municipal"].insert(0, limpar_string(nota_fiscal[6]))

            # UF e Município
            self.entries["uf"].set(limpar_string(nota_fiscal[15]))
            if nota_fiscal[15]:  # Se tem UF, atualiza lista de municípios
                self.atualizar_municipios()
            self.entries["municipio"].set(limpar_string(nota_fiscal[16]))

            # Código do município
            self.entries["cod_municipio"].configure(state="normal")
            self.entries["cod_municipio"].delete(0, tk.END)
            self.entries["cod_municipio"].insert(0, limpar_string(nota_fiscal[17]))
            self.entries["cod_municipio"].configure(state="readonly")

            # Tipo de serviço e valores
            self.entries["tipo_servico"].set(limpar_string(nota_fiscal[7]))
            self.entries["base_calculo"].set(limpar_string(nota_fiscal[7]))

            # Formatar valores numéricos com tratamento de erro
            def formatar_numero(valor):
                try:
                    return f"{float(valor):.2f}" if valor is not None else "0.00"
                except (ValueError, TypeError):
                    return "0.00"

            # Campos numéricos
            self.entries["aliquota"].insert(0, formatar_numero(nota_fiscal[11]))
            self.entries["valor_nf"].insert(0, formatar_numero(nota_fiscal[12]))

            self.entries["recolhimento"].set(limpar_string(nota_fiscal[18]))

            # Recibo
            recibo_valor = limpar_string(nota_fiscal[19]) if nota_fiscal[19] else ""
            self.entries["recibo"].insert(0, recibo_valor)

        except Exception as e:
            print(f"Erro ao preencher campos: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar dados: {str(e)}")
            print("Estrutura do registro:", nota_fiscal)  # Debug

    def abrir_config_tomador(self):
        ConfigTomadorWindow(self.root, self.db)

    def gerenciar_tomadores(self):
        GerenciarTomadoresWindow(self.root, self.db)

        def atualizar_fora_pais(self, event=None):
            """Atualiza configurações quando o campo Fora do País é alterado"""
        valor = self.entries["fora_pais"].get()
        if valor == "Sim":
            # Setar tipo de serviço para "00 - Normal"
            self.entries["tipo_servico"].set("00 - Normal")
            # Setar base de cálculo para padrão
            self.entries["base_calculo"].set("00 - Base de cálculo normal")

            # Desabilitar e limpar campos
            campos_desabilitar = ["uf", "municipio", "inscricao_municipal"]
            for campo in campos_desabilitar:
                self.entries[campo].configure(state="disabled")
                (
                    self.entries[campo].set("")
                    if hasattr(self.entries[campo], "set")
                    else self.entries[campo].delete(0, tk.END)
                )

            # Limpar e desabilitar código do município
            self.entries["cod_municipio"].configure(state="normal")
            self.entries["cod_municipio"].delete(0, tk.END)
            self.entries["cod_municipio"].configure(state="disabled")

        else:
            # Reabilitar campos
            campos_habilitar = ["uf", "municipio", "inscricao_municipal"]
            for campo in campos_habilitar:
                self.entries[campo].configure(state="normal")

            # Reabilitar código do município como readonly
            self.entries["cod_municipio"].configure(state="readonly")

            # Limpar tipo de serviço para permitir escolha
            self.entries["tipo_servico"].set("")
            self.entries["base_calculo"].set("")


# Ajustar a janela de configuração do tomador para suportar edição
class ConfigTomadorWindow:
    def __init__(self, parent, db, tomador_data=None, callback=None):
        self.window = tk.Toplevel(parent)
        self.window.title("Configuração do Tomador")
        self.window.geometry("500x300")
        self.db = db
        self.callback = callback
        self.tomador_data = tomador_data  # Dados do tomador para edição

        # Criar interface
        self.create_widgets()

        # Se for edição, preencher campos
        if tomador_data:
            self.fill_fields()

    def create_widgets(self):
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Campos
        ttk.Label(main_frame, text="Razão Social:").grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.razao_social = ttk.Entry(main_frame, width=50)
        self.razao_social.grid(row=0, column=1, sticky="w", pady=5)

        ttk.Label(main_frame, text="CNPJ:").grid(row=1, column=0, sticky="w", pady=5)
        self.cnpj = ttk.Entry(main_frame, width=20)
        self.cnpj.grid(row=1, column=1, sticky="w", pady=5)

        ttk.Label(main_frame, text="CAE/Inscrição:").grid(
            row=2, column=0, sticky="w", pady=5
        )
        self.inscricao = ttk.Entry(main_frame, width=20)
        self.inscricao.grid(row=2, column=1, sticky="w", pady=5)

        ttk.Label(main_frame, text="Usuário Prefeitura:").grid(
            row=3, column=0, sticky="w", pady=5
        )
        self.usuario = ttk.Entry(main_frame, width=30)
        self.usuario.grid(row=3, column=1, sticky="w", pady=5)

        # Botões
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Salvar", command=self.save_data).grid(
            row=0, column=0, padx=5
        )
        ttk.Button(btn_frame, text="Cancelar", command=self.window.destroy).grid(
            row=0, column=1, padx=5
        )

    def fill_fields(self):
        # Preencher campos com dados existentes
        self.razao_social.insert(0, self.tomador_data[1])
        self.cnpj.insert(0, self.tomador_data[2])
        self.inscricao.insert(0, self.tomador_data[3])
        self.usuario.insert(0, self.tomador_data[4])

    def save_data(self):
        try:
            dados = {
                "razao_social": self.razao_social.get(),
                "cnpj": self.cnpj.get(),
                "inscricao": self.inscricao.get(),
                "usuario": self.usuario.get(),
            }

            if self.tomador_data:  # Se for edição
                dados["id"] = self.tomador_data[0]
                result = self.db.update_tomador(dados)
                mensagem = "Tomador atualizado com sucesso!"
            else:  # Se for novo
                result = self.db.insert_tomador(dados)
                mensagem = "Tomador cadastrado com sucesso!"

            if result:
                messagebox.showinfo("Sucesso", mensagem)
                if self.callback:
                    self.callback()
                self.window.destroy()
            else:
                messagebox.showerror("Erro", "Não foi possível salvar os dados")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {str(e)}")


class ExportSelectionWindow:
    def __init__(self, parent, db, callback):
        self.window = tk.Toplevel(parent)
        self.window.title("Selecione o Tomador")
        self.window.geometry("500x300")
        self.db = db
        self.callback = callback

        # Tornar a janela modal
        self.window.transient(parent)
        self.window.grab_set()

        # Criar interface
        self.create_widgets()

        # Carregar tomadores
        self.load_tomadores()

    def create_widgets(self):
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Lista de tomadores
        ttk.Label(main_frame, text="Selecione o Tomador:").grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        # Criar Treeview para tomadores
        self.tree = ttk.Treeview(
            main_frame,
            columns=("razao", "cnpj", "inscricao"),
            show="headings",
            height=8,
        )
        self.tree.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        # Configurar colunas
        self.tree.heading("razao", text="Razão Social")
        self.tree.heading("cnpj", text="CNPJ")
        self.tree.heading("inscricao", text="CAE/Inscrição")

        self.tree.column("razao", width=200)
        self.tree.column("cnpj", width=120)
        self.tree.column("inscricao", width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            main_frame, orient="vertical", command=self.tree.yview
        )
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Frame para botões
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Exportar", command=self.confirm_export).grid(
            row=0, column=0, padx=5
        )
        ttk.Button(btn_frame, text="Cancelar", command=self.window.destroy).grid(
            row=0, column=1, padx=5
        )
        ttk.Button(btn_frame, text="Novo Tomador", command=self.add_tomador).grid(
            row=0, column=2, padx=5
        )

    def load_tomadores(self):
        tomadores = self.db.get_all_tomadores()  # Precisamos criar este método
        for tomador in tomadores:
            self.tree.insert("", "end", values=(tomador[1], tomador[2], tomador[3]))

    def add_tomador(self):
        ConfigTomadorWindow(self.window, self.db)
        # Recarregar lista após adicionar
        self.refresh_list()

    def refresh_list(self):
        # Limpar lista atual
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Recarregar dados
        self.load_tomadores()

    def confirm_export(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Por favor, selecione um tomador")
            return

        # Obter apenas o CAE/Inscrição do tomador selecionado
        tomador_data = self.tree.item(selected[0])["values"]
        inscricao = tomador_data[2]  # índice do CAE/Inscrição

        # Gerar nome sugerido para o arquivoa

class GerenciarTomadoresWindow:
    def __init__(self, parent, db):
        self.window = tk.Toplevel(parent)
        self.window.title("Gerenciar Tomadores")
        self.window.geometry("700x400")
        self.db = db

        # Tornar a janela modal
        self.window.transient(parent)
        self.window.grab_set()

        # Criar interface
        self.create_widgets()

        # Carregar tomadores
        self.load_tomadores()

    def create_widgets(self):
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Lista de tomadores
        ttk.Label(
            main_frame, text="Tomadores Cadastrados:", font=("Helvetica", 10, "bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        # Frame para a tabela com scrollbar
        table_frame = ttk.Frame(main_frame)
        table_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        # Criar Treeview para tomadores
        self.tree = ttk.Treeview(
            table_frame,
            columns=("id", "razao", "cnpj", "inscricao", "usuario"),
            show="headings",
            height=10,
        )

        # Configurar colunas
        self.tree.heading("id", text="ID")
        self.tree.heading("razao", text="Razão Social")
        self.tree.heading("cnpj", text="CNPJ")
        self.tree.heading("inscricao", text="CAE/Inscrição")
        self.tree.heading("usuario", text="Usuário Prefeitura")

        # Configurar larguras
        self.tree.column("id", width=50)
        self.tree.column("razao", width=250)
        self.tree.column("cnpj", width=130)
        self.tree.column("inscricao", width=120)
        self.tree.column("usuario", width=150)

        # Ocultar coluna ID
        self.tree.column("id", width=0, stretch=False)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid da tabela e scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Frame para botões
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, pady=10)

        ttk.Button(btn_frame, text="Novo Tomador", command=self.add_tomador).grid(
            row=0, column=0, padx=5
        )
        ttk.Button(btn_frame, text="Editar", command=self.edit_tomador).grid(
            row=0, column=1, padx=5
        )
        ttk.Button(btn_frame, text="Excluir", command=self.delete_tomador).grid(
            row=0, column=2, padx=5
        )
        ttk.Button(btn_frame, text="Fechar", command=self.window.destroy).grid(
            row=0, column=3, padx=5
        )

        # Double-click para editar
        self.tree.bind("<Double-1>", lambda e: self.edit_tomador())

    def load_tomadores(self):
        # Limpar lista atual
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Carregar tomadores do banco
        tomadores = self.db.get_all_tomadores()
        for tomador in tomadores:
            self.tree.insert("", "end", values=tomador)

    def add_tomador(self):
        ConfigTomadorWindow(self.window, self.db, callback=self.load_tomadores)

    def edit_tomador(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Aviso", "Por favor, selecione um tomador para editar"
            )
            return

        tomador_data = self.tree.item(selected[0])["values"]
        ConfigTomadorWindow(
            self.window,
            self.db,
            tomador_data=tomador_data,
            callback=self.load_tomadores,
        )

    def delete_tomador(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Aviso", "Por favor, selecione um tomador para excluir"
            )
            return

        tomador_data = self.tree.item(selected[0])["values"]
        if messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o tomador:\n{tomador_data[1]}?",
        ):
            if self.db.delete_tomador(tomador_data[0]):
                messagebox.showinfo("Sucesso", "Tomador excluído com sucesso!")
                self.load_tomadores()
            else:
                messagebox.showerror("Erro", "Não foi possível excluir o tomador")

        

if __name__ == "__main__":
    root = tk.Tk()
    app = AppNotasFiscais(root)
    root.mainloop()
