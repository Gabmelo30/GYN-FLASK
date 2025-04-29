from calendar import c
import sqlite3
from sqlite3 import Error
from tkinter import messagebox, ttk
import pandas as pd
import os
import sys
from calendar import c 

def resource_path(relative_path):
    """Obtém o caminho absoluto para o recurso, funciona para dev e para o PyInstaller"""
    try:
        # PyInstaller cria um temp folder e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_application_path():
    """Obtém o caminho base da aplicação, funcionando tanto em desenvolvimento quanto compilado"""
    if getattr(sys, "frozen", False):
        # Se estiver rodando como executável (compilado)
        application_path = os.path.dirname(sys.executable)
    else:
        # Se estiver rodando em desenvolvimento
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path


class DatabaseManager:
    def __init__(self, db_file="app_rest_gyn.db"):
        # Definir o caminho do banco de dados
        app_path = get_application_path()
        # Se estiver compilado, usar a pasta 'app' dentro do diretório do executável
        if getattr(sys, "frozen", False):
            self.db_file = os.path.join(app_path, "app", db_file)
        else:
            self.db_file = os.path.join(app_path, db_file)

        print(f"Caminho do banco de dados: {self.db_file}")  # Debug
        self.create_tables()
        self.populate_default_data()
        
    def create_connection(self):
        try:
            # Garantir que o diretório existe
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
            conn = sqlite3.connect(self.db_file)
            return conn
        except Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            return None

    def create_tables(self):
        conn = self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()

                # Criar tabela de configuração do tomador
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tb_config_tomador (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        razao_social TEXT NOT NULL,
                        cnpj TEXT NOT NULL,
                        cae_inscricao TEXT NOT NULL,
                        usuario_prefeitura TEXT NOT NULL,
                        data_atualizacao TEXT
                    )
                """
                )

                # Criar tabela UF (sem alterações)
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tb_uf (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        UF TEXT UNIQUE NOT NULL
                    )
                """
                )

                # Corrigido tb_tipo_de_servico - removida vírgula extra
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tb_tipo_de_servico (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        descricao TEXT NOT NULL
                    )
                """
                )

                # Criar tabela Tipo de Recolhimento (sem alterações)
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tb_tipo_de_recolhimento (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recolhimento TEXT UNIQUE NOT NULL
                    )
                """
                )

                # Criar tabela Código Município (sem alterações)
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tb_cod_municipio (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        UF TEXT,
                        municipio TEXT,
                        cod_municipio TEXT,
                        FOREIGN KEY (UF) REFERENCES tb_uf (UF)
                    )
                """
                )

                # Criar tabela de Fornecedores (sem alterações)
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tb_fornecedores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        CNPJ TEXT UNIQUE,
                        descricao_fornecedor TEXT,
                        UF TEXT,
                        municipio TEXT,
                        cod_municipio TEXT,
                        fora_pais TEXT DEFAULT 'Não',
                        cadastrado_goiania TEXT DEFAULT 'Não',
                        FOREIGN KEY (UF) REFERENCES tb_uf (UF)
                    )
                """
                )

                # Corrigido tb_notas_fiscais
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tb_notas_fiscais (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        Referencia TEXT,
                        cadastrado_goiania TEXT,
                        fora_pais TEXT,  -- Novo campo
                        cnpj TEXT,
                        fornecedor_id INTEGER,
                        inscricao_municipal TEXT,
                        tipo_servico TEXT,
                        numero_nf TEXT,
                        dt_emissao TEXT,
                        dt_pagamento TEXT,
                        aliquota REAL,
                        valor_nf REAL,
                        recolhimento_id INTEGER,
                        recibo TEXT,
                        uf TEXT,
                        municipio TEXT,
                        cod_municipio TEXT,
                        FOREIGN KEY (fornecedor_id) REFERENCES tb_fornecedores (id),
                        FOREIGN KEY (recolhimento_id) REFERENCES tb_tipo_de_recolhimento (id)
                    )
                """
                )

                # Se a tabela já existir, adicionar a nova coluna
                try:
                    c.execute(
                        "ALTER TABLE tb_fornecedores ADD COLUMN fora_pais TEXT DEFAULT 'Não'"
                    )
                    c.execute("ALTER TABLE tb_notas_fiscais ADD COLUMN fora_pais TEXT")
                    c.execute(
                        "ALTER TABLE tb_fornecedores ADD COLUMN cadastrado_goiania TEXT DEFAULT 'Não'"
                    )
                except:
                    pass  # Coluna já existe

                # Verificar se já existe configuração
                c.execute("SELECT COUNT(*) FROM tb_config_tomador")
                if c.fetchone()[0] == 0:
                    # Inserir registro vazio para ser atualizado posteriormente
                    c.execute(
                        """
                        INSERT INTO tb_config_tomador 
                        (razao_social, cnpj, cae_inscricao, usuario_prefeitura, data_atualizacao)
                        VALUES (?, ?, ?, ?, datetime('now'))
                    """,
                        ("", "", "", ""),
                    )

                conn.commit()
            except Error as e:
                print(f"Erro ao criar tabelas: {e}")
            finally:
                conn.close()

    def populate_default_data(self):
        conn = self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()

                # UFs - sem alterações
                ufs = [
                    "AC",
                    "AL",
                    "AP",
                    "AM",
                    "BA",
                    "CE",
                    "DF",
                    "ES",
                    "GO",
                    "MA",
                    "MT",
                    "MS",
                    "MG",
                    "PA",
                    "PB",
                    "PR",
                    "PE",
                    "PI",
                    "RJ",
                    "RN",
                    "RS",
                    "RO",
                    "RR",
                    "SC",
                    "SP",
                    "SE",
                    "TO",
                ]
                c.executemany(
                    "INSERT OR IGNORE INTO tb_uf (UF) VALUES (?)", [(uf,) for uf in ufs]
                )

                # Tipos de Serviço - mantido formato original
                tipos_servico = [
                    "00 - Normal",
                    "02 - Imune",
                    "03 - Art 54 do CTM",
                    "04 - Liminar",
                    "05 - Simples Nacional",
                    "07 - ISS Estimado",
                    "08 - Não Incidência",
                    "09 - Isento",
                    "10 - Imposto Fixo",
                ]
                bases_calculo = [
                        "00 - Base de cálculo normal",
                        "01 - Publicidade e propaganda",
                        "02 - Representação comercial",
                        "03 - Corretagem de seguro", 
                        "04 - Construção civil",
                        "05 - Call Center",
                        "06 - Estação Digital",
                        "07 - Serviços de saúde (órtese e prótese)"
                    ]
                c.executemany(
                    "INSERT OR IGNORE INTO tb_tipo_de_servico (descricao) VALUES (?)",
                    [(tipo,) for tipo in tipos_servico],
                )
                c.executemany(
                    "INSERT OR IGNORE INTO tb_base_calculo (descricao) VALUES (?)",
                    [(base,) for base in bases_calculo]
                )

                # Tipos de Recolhimento - sem alterações
                recolhimentos = ["A Recolher pelo tomador", "Recolhido pelo prestador"]
                c.executemany(
                    "INSERT OR IGNORE INTO tb_tipo_de_recolhimento (recolhimento) VALUES (?)",
                    [(rec,) for rec in recolhimentos],
                )

                conn.commit()
            except Error as e:
                print(f"Erro ao popular dados: {e}")
            finally:
                conn.close()

    def get_all_bases_calculo(self):
        """Retorna todas as bases de cálculo do sistema"""
        conn = self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute("SELECT descricao FROM tb_base_calculo ORDER BY id")
                return [row[0] for row in c.fetchall()]
            except Exception as e:
                print(f"Erro ao buscar bases de cálculo: {e}")
                return []
            finally:
                conn.close()
        return []

    def get_all_tipos_servico(self):
        conn = self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute("SELECT descricao FROM tb_tipo_de_servico ORDER BY id")
                return [row[0] for row in c.fetchall()]
            except Exception as e:
                print(f"Erro ao buscar tipos de serviço: {e}")
                return []
            finally:
                conn.close()
        return []

    def get_all_ufs(self):
        conn = self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute("SELECT UF FROM tb_uf ORDER BY UF")
                return [row[0] for row in c.fetchall()]
            finally:
                conn.close()
        return []

    def get_all_recolhimentos(self):
        conn = self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute("SELECT recolhimento FROM tb_tipo_de_recolhimento")
                return [row[0] for row in c.fetchall()]
            finally:
                conn.close()
        return []

    def get_municipios_by_uf(self, uf):
        conn = self.create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT municipio, cod_municipio 
                    FROM tb_cod_municipio 
                    WHERE UF = ? 
                    ORDER BY municipio
                """,
                    (uf,),
                )
                return cursor.fetchall()
            finally:
                conn.close()
        return []

    def get_fornecedor_by_cnpj(self, cnpj):
        conn = self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute(
                    """
                    SELECT descricao_fornecedor, UF, municipio, cod_municipio
                    FROM tb_fornecedores 
                    WHERE CNPJ = ?
                """,
                    (cnpj,),
                )
                return c.fetchone()
            finally:
                conn.close()
        return None

    def get_cod_municipio(self, uf, municipio):
        conn = self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute(
                    """
                    SELECT cod_municipio 
                    FROM tb_cod_municipio 
                    WHERE UF = ? AND municipio = ?
                """,
                    (uf, municipio),
                )
                result = c.fetchone()
                return result[0] if result else None
            finally:
                conn.close()
        return None

    def insert_fornecedor(
        self,
        cnpj,
        descricao,
        uf,
        municipio,
        cod_municipio,
        fora_pais,
        cadastrado_goiania,
    ):
        conn = self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute(
                    """
                    SELECT id FROM tb_fornecedores 
                    WHERE CNPJ = ?
                """,
                    (cnpj,),
                )

                existing_supplier = c.fetchone()

                if existing_supplier:
                    c.execute(
                        """
                        UPDATE tb_fornecedores 
                        SET descricao_fornecedor = ?,
                            UF = ?,
                            municipio = ?,
                            cod_municipio = ?,
                            fora_pais = ?,
                            cadastrado_goiania = ?
                        WHERE CNPJ = ?
                    """,
                        (
                            descricao,
                            uf,
                            municipio,
                            cod_municipio,
                            fora_pais,
                            cadastrado_goiania,
                            cnpj,
                        ),
                    )
                    fornecedor_id = existing_supplier[0]
                else:
                    c.execute(
                        """
                        INSERT INTO tb_fornecedores 
                        (CNPJ, descricao_fornecedor, UF, municipio, cod_municipio, fora_pais, cadastrado_goiania)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            cnpj,
                            descricao,
                            uf,
                            municipio,
                            cod_municipio,
                            fora_pais,
                            cadastrado_goiania,
                        ),
                    )
                    fornecedor_id = c.lastrowid

                conn.commit()
                return fornecedor_id

            except Exception as e:
                print(f"Erro ao inserir/atualizar fornecedor: {e}")
                conn.rollback()
                return None
            finally:
                conn.close()
        return None

    def insert_nota_fiscal(self, dados):
        conn = self.create_connection()
        if conn is not None:
            try:
                # Validar e limpar o campo 'Referencia'
                referencia = dados.get('referencia', '').strip()
                if not referencia:
                    print("Erro: Referência não pode ser vazia")
                    return False

                cursor = conn.cursor()
                query = """
                INSERT INTO tb_notas_fiscais (
                    referencia, cadastrado_goiania, fora_pais, cnpj, fornecedor_id, 
                    inscricao_municipal, tipo_servico, base_calculo, numero_nf, 
                    dt_emissao, dt_pagamento, aliquota, valor_nf, recolhimento_id, 
                    recibo, uf, municipio, cod_municipio
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                        (SELECT id FROM tb_tipo_de_recolhimento WHERE recolhimento = ?), 
                        ?, ?, ?, ?)
                """
                
                # Remover quebras de linha do CNPJ
                cnpj = dados['CNPJ'].strip().replace('\n', '')

                values = (
                    referencia, 
                    dados.get('cadastrado_goiania', 'Não'), 
                    dados.get('fora_pais', 'Não'), 
                    cnpj, 
                    dados['Fornecedor_ID'], 
                    dados.get('Inscrição Municipal', ''), 
                    dados['Tipo de Serviço'], 
                    dados['Base de Cálculo'], 
                    dados['Nº NF'], 
                    dados['Dt. Emissão'], 
                    dados['Dt. Pagamento'], 
                    dados['Aliquota'], 
                    dados['Valor NF'], 
                    dados['Recolhimento'], 
                    dados.get('RECIBO', ''), 
                    dados['UF'], 
                    dados['Município'], 
                    dados['Código Município']
                )

                cursor.execute(query, values)
                conn.commit()
                return True
            except Exception as e:
                print(f"Erro ao inserir nota fiscal: {e}")
                print(f"Dados recebidos: {dados}")
                return False
            finally:
                conn.close()
        return False

    def delete_nota_fiscal(self, id_nota):
        conn = self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                # Exclui usando o ID da nota
                c.execute(
                    """
                    DELETE FROM tb_notas_fiscais 
                    WHERE id = ?
                """,
                    (id_nota,),
                )

                # Verifica se algum registro foi afetado
                affected_rows = c.rowcount
                conn.commit()

                print(f"Registros excluídos: {affected_rows}")
                return affected_rows > 0
            except Exception as e:
                print(f"Erro ao excluir nota fiscal: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False

    def get_all_notas_fiscais(self):
        conn = self.create_connection()
        if conn is not None:
            try:
                # Verificar primeiro se a tabela existe
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='tb_notas_fiscais'"
                )
                table_exists = cursor.fetchone()

                if not table_exists:
                    print("A tabela tb_notas_fiscais não existe.")
                    return pd.DataFrame()

                # Verificar se a tabela está vazia
                cursor.execute("SELECT COUNT(*) FROM tb_notas_fiscais")
                count = cursor.fetchone()[0]

                if count == 0:
                    print("A tabela tb_notas_fiscais está vazia.")
                    # Retornar DataFrame vazio com as colunas corretas
                    return pd.DataFrame(
                        columns=[
                            "id",  # Adicionado ID
                            "referencia",
                            "cadastrado_goiania",
                            "fora_pais",
                            "cnpj",
                            "descricao_fornecedor",
                            "tipo_servico",
                            "numero_nf",
                            "dt_emissao",
                            "dt_pagamento",
                            "aliquota",
                            "valor_nf",
                            "recolhimento",
                        ]
                    )

                # Consulta SQL ajustada para incluir ID
                query = """
                    SELECT 
                        nf.id,
                        nf.referencia,
                        nf.cadastrado_goiania,
                        nf.fora_pais,
                        nf.cnpj,
                        f.descricao_fornecedor,
                        nf.tipo_servico,
                        nf.numero_nf,
                        nf.dt_emissao,
                        nf.dt_pagamento,
                        nf.aliquota,
                        nf.valor_nf,
                        tr.recolhimento
                    FROM tb_notas_fiscais nf
                    LEFT JOIN tb_fornecedores f ON nf.cnpj = f.CNPJ
                    LEFT JOIN tb_tipo_de_recolhimento tr ON nf.recolhimento_id = tr.id
                    ORDER BY nf.dt_emissao DESC
                """

                df = pd.read_sql_query(query, conn)
                return df
            except Exception as e:
                print(f"Erro detalhado na consulta: {str(e)}")
                return pd.DataFrame(
                    columns=[
                        "id",
                        "referencia",
                        "cadastrado_goiania",
                        "fora_pais",
                        "cnpj",
                        "descricao_fornecedor",
                        "tipo_servico",
                        "numero_nf",
                        "dt_emissao",
                        "dt_pagamento",
                        "aliquota",
                        "valor_nf",
                        "recolhimento",
                    ]
                )
            finally:
                conn.close()
        return pd.DataFrame()

    def export_to_excel(self, filename):
        conn = self.create_connection()
        if conn is not None:
            try:
                query = """
                    SELECT 
                        nf.referencia as "Referência",
                        nf.cadastrado_goiania as "Cadastrado em Goiânia",
                        nf.cnpj as "CNPJ",
                        f.descricao_fornecedor as "Fornecedor",
                        f.UF as "UF",
                        f.municipio as "Município",
                        f.cod_municipio as "Código Município",
                        nf.inscricao_municipal as "Inscrição Municipal",
                        nf.tipo_servico as "Tipo de Serviço",
                        nf.numero_nf as "Número NF",
                        nf.dt_emissao as "Data Emissão",
                        nf.dt_pagamento as "Data Pagamento",
                        nf.aliquota as "Alíquota",
                        nf.valor_nf as "Valor NF",
                        tr.recolhimento as "Recolhimento",
                        nf.recibo as "Recibo"
                    FROM tb_notas_fiscais nf
                    LEFT JOIN tb_fornecedores f ON nf.fornecedor_id = f.id
                    LEFT JOIN tb_tipo_de_recolhimento tr ON nf.recolhimento_id = tr.id
                    ORDER BY nf.dt_emissao DESC
                """

                # Ler dados para DataFrame
                df = pd.read_sql_query(query, conn)

                # Formatações
                if "Alíquota" in df.columns:
                    df["Alíquota"] = df["Alíquota"].apply(
                        lambda x: f"{float(x):.2f}" if pd.notnull(x) else ""
                    )
                if "Valor NF" in df.columns:
                    df["Valor NF"] = df["Valor NF"].apply(
                        lambda x: f"{float(x):.2f}" if pd.notnull(x) else ""
                    )

                for col in ["Data Emissão", "Data Pagamento"]:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col]).dt.strftime("%d/%m/%Y")

                # Exportar para Excel
                df.to_excel(filename, index=False, sheet_name="Notas Fiscais")

                # Ajustar largura das colunas
                with pd.ExcelWriter(filename, engine="openpyxl", mode="a") as writer:
                    workbook = writer.book
                    worksheet = workbook["Notas Fiscais"]
                    for idx, col in enumerate(df.columns):
                        max_length = max(
                            df[col].astype(str).apply(len).max(), len(str(col))
                        )
                        worksheet.column_dimensions[chr(65 + idx)].width = (
                            max_length + 2
                        )

                return True
            except Exception as e:
                print(f"Erro ao exportar para Excel: {e}")
                return False
            finally:
                conn.close()
        return False

    def import_municipios_from_txt(self, file_path):
        conn = self.create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                count = 0

                with open(file_path, "r", encoding="utf-8") as file:
                    for line_number, line in enumerate(file, 1):
                        try:
                            # Remove espaços em branco e quebras de linha
                            line = line.strip()

                            if not line:
                                continue

                            # Divide usando ponto e vírgula
                            parts = line.split(";")

                            if len(parts) == 3:
                                cod_municipio, municipio, uf = parts
                                # Remove espaços extras
                                municipio = municipio.strip()
                                uf = uf.strip()
                                cod_municipio = cod_municipio.strip()

                                print(
                                    f"Processando: Código={cod_municipio}, Município={municipio}, UF={uf}"
                                )

                                cursor.execute(
                                    """
                                    INSERT OR IGNORE INTO tb_cod_municipio (UF, municipio, cod_municipio)
                                    VALUES (?, ?, ?)
                                """,
                                    (uf, municipio, cod_municipio),
                                )
                                count += 1
                            else:
                                print(
                                    f"Erro na linha {line_number}: formato inválido - {line}"
                                )
                        except Exception as e:
                            print(f"Erro ao ler arquivo {e}")
                    conn.commit()
                    print(f"Total de municípios importados: {count}")
                    return True

            except Exception as e:
                print(f"Erro detalhado ao importar municípios: {str(e)}")
                raise e
            finally:
                conn.close()
        return False

    def update_nota_fiscal(self, id_nota, dados):
        conn = self.create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()

                # Map the incoming field names to database field names
                field_mapping = {
                    "Referencia": "referencia",
                    "Cadastrado em Goiania": "cadastrado_goiania",
                    "CNPJ": "cnpj",
                    "Inscrição Municipal": "inscricao_municipal",
                    "Tipo de Serviço": "tipo_servico",
                    "Nº NF": "numero_nf",
                    "Dt. Emissão": "dt_emissao",
                    "Dt. Pagamento": "dt_pagamento",
                    "Aliquota": "aliquota",
                    "Valor NF": "valor_nf",
                    "Recolhimento": "recolhimento",
                    "RECIBO": "recibo",
                    "UF": "uf",
                    "Município": "municipio",
                    "Código Município": "cod_municipio",
                    "fora_pais": "fora_pais",
                }

                # Create a new dictionary with mapped field names
                mapped_dados = {}
                for old_key, new_key in field_mapping.items():
                    if old_key in dados:
                        mapped_dados[new_key] = dados[old_key]
                    elif (
                        new_key in dados
                    ):  # Handle cases where the key is already in the new format
                        mapped_dados[new_key] = dados[new_key]

                # Buscar fornecedor_id baseado no CNPJ
                cursor.execute(
                    """
                    SELECT id FROM tb_fornecedores 
                    WHERE CNPJ = ?
                    """,
                    (mapped_dados.get("cnpj", ""),),
                )
                fornecedor_result = cursor.fetchone()
                fornecedor_id = fornecedor_result[0] if fornecedor_result else None

                # Buscar recolhimento_id
                cursor.execute(
                    """
                    SELECT id FROM tb_tipo_de_recolhimento 
                    WHERE recolhimento = ?
                    """,
                    (mapped_dados.get("recolhimento", ""),),
                )
                recolhimento_result = cursor.fetchone()
                recolhimento_id = (
                    recolhimento_result[0] if recolhimento_result else None
                )

                # Update query with proper field names
                cursor.execute(
                    """
                    UPDATE tb_notas_fiscais SET
                        referencia = ?,
                        cadastrado_goiania = ?,
                        fora_pais = ?,
                        cnpj = ?,
                        fornecedor_id = ?,
                        inscricao_municipal = ?,
                        tipo_servico = ?,
                        numero_nf = ?,
                        dt_emissao = ?,
                        dt_pagamento = ?,
                        aliquota = ?,
                        valor_nf = ?,
                        recolhimento_id = ?,
                        recibo = ?,
                        uf = ?,
                        municipio = ?,
                        cod_municipio = ?
                    WHERE id = ?
                    """,
                    (
                        mapped_dados.get("referencia", ""),
                        mapped_dados.get("cadastrado_goiania", "Não"),
                        mapped_dados.get("fora_pais", "Não"),
                        mapped_dados.get("cnpj", ""),
                        fornecedor_id,
                        mapped_dados.get("inscricao_municipal", ""),
                        mapped_dados.get("tipo_servico", ""),
                        mapped_dados.get("numero_nf", ""),
                        mapped_dados.get("dt_emissao", ""),
                        mapped_dados.get("dt_pagamento", ""),
                        mapped_dados.get("aliquota", 0.0),
                        mapped_dados.get("valor_nf", 0.0),
                        recolhimento_id,
                        mapped_dados.get("recibo", ""),
                        mapped_dados.get("uf", ""),
                        mapped_dados.get("municipio", ""),
                        mapped_dados.get("cod_municipio", ""),
                        id_nota,
                    ),
                )

                conn.commit()
                return True
            except Exception as e:
                print(f"Erro na atualização: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False

    def verificar_existencia_registro(self, cnpj, numero_nf):
        conn = self.create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                # Converte para string para garantir comparação correta
                cursor.execute(
                    "SELECT COUNT(*) FROM tb_notas_fiscais WHERE cnpj = ? AND numero_nf = ?",
                    (str(cnpj), str(numero_nf)),
                )
                count = cursor.fetchone()[0]
                print(
                    f"Registros encontrados para CNPJ {cnpj} e NF {numero_nf}: {count}"
                )
                return count > 0
            except Exception as e:
                print(f"Erro ao verificar existência de registro: {e}")
                return False
            finally:
                conn.close()
        return False

    def get_nota_fiscal_by_id(self, id_nota):
        conn = self.create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                query = """
                    SELECT 
                        nf.id,
                        nf.referencia,
                        nf.cadastrado_goiania,
                        nf.fora_pais,
                        nf.cnpj,
                        nf.fornecedor_id,
                        nf.inscricao_municipal,
                        nf.tipo_servico,
                        nf.numero_nf,
                        nf.dt_emissao,
                        nf.dt_pagamento,
                        nf.aliquota,
                        nf.valor_nf,
                        nf.recolhimento_id,
                        f.descricao_fornecedor,
                        f.UF,
                        f.municipio,
                        f.cod_municipio,
                        tr.recolhimento,
                        nf.recibo
                    FROM tb_notas_fiscais nf
                    LEFT JOIN tb_fornecedores f ON nf.fornecedor_id = f.id
                    LEFT JOIN tb_tipo_de_recolhimento tr ON nf.recolhimento_id = tr.id
                    WHERE nf.id = ?
                """
                cursor.execute(query, (id_nota,))
                resultado = cursor.fetchone()
                print("Resultado da query:", resultado)  # Debug
                return resultado
            except Exception as e:
                print(f"Erro ao buscar nota fiscal: {e}")
                return None
            finally:
                conn.close()
        return None

    def get_config_tomador(self):
        conn = self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute("SELECT * FROM tb_config_tomador LIMIT 1")
                return c.fetchone()
            finally:
                conn.close()
        return None

    def update_config_tomador(
        self, razao_social, cnpj, cae_inscricao, usuario_prefeitura
    ):
        conn = self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute(
                    """
                    UPDATE tb_config_tomador
                    SET razao_social = ?,
                        cnpj = ?,
                        cae_inscricao = ?,
                        usuario_prefeitura = ?,
                        data_atualizacao = datetime('now')
                    WHERE id = 1
                """,
                    (razao_social, cnpj, cae_inscricao, usuario_prefeitura),
                )
                conn.commit()
                return True
            except Error as e:
                print(f"Erro ao atualizar configuração: {e}")
                return False
            finally:
                conn.close()
        return False

    def get_all_tomadores(self):
        conn = self.create_connection()
        if conn is not None:
            try:
                c = conn.cursor()
                c.execute("SELECT * FROM tb_config_tomador ORDER BY razao_social")
                return c.fetchall()
            finally:
                conn.close()
        return []

    def delete_tomador(self, tomador_id):
        conn = self.create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM tb_config_tomador WHERE id = ?", (tomador_id,)
                )
                conn.commit()
                return True
            except Exception as e:
                print(f"Erro ao excluir tomador: {e}")
                return False
            finally:
                conn.close()
        return False

    def insert_tomador(self, dados):
        conn = self.create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO tb_config_tomador 
                    (razao_social, cnpj, cae_inscricao, usuario_prefeitura, data_atualizacao)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """,
                    (
                        dados["razao_social"],
                        dados["cnpj"],
                        dados["inscricao"],
                        dados["usuario"],
                    ),
                )
                conn.commit()
                return True
            except Exception as e:
                print(f"Erro ao inserir tomador: {e}")
                return False
            finally:
                conn.close()
        return False

    def update_tomador(self, dados):
        conn = self.create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE tb_config_tomador 
                    SET razao_social = ?,
                        cnpj = ?,
                        cae_inscricao = ?,
                        usuario_prefeitura = ?,
                        data_atualizacao = datetime('now')
                    WHERE id = ?
                """,
                    (
                        dados["razao_social"],
                        dados["cnpj"],
                        dados["inscricao"],
                        dados["usuario"],
                        dados["id"],
                    ),
                )
                conn.commit()
                return True
            except Exception as e:
                print(f"Erro ao atualizar tomador: {e}")
                return False
            finally:
                conn.close()
        return False

    def limpar_notas_fiscais(self):
        conn = self.create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tb_notas_fiscais")
                conn.commit()
                print(f"Registros excluídos: {cursor.rowcount}")
                return True
            except Exception as e:
                print(f"Erro ao limpar tabela de notas fiscais: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
        return False
def criar_campos_servico(self, container):
    campos = [
        ("tipo_servico", "Tipo de Serviço", ttk.Combobox, {"width": 40}),
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
    self.carregar_bases_calculo()  # Novo método

def carregar_bases_calculo(self):
    try:
        bases_calculo = self.db.get_all_bases_calculo()
        if bases_calculo:
            self.entries["base_calculo"]["values"] = bases_calculo
            # Definir a opção padrão
            self.entries["base_calculo"].set(" Base de cálculo normal")
        else:
            print("Nenhuma base de cálculo encontrada no banco de dados")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar bases de cálculo: {str(e)}")
        print(f"Erro detalhado: {e}")


def get_all_bases_calculo(self):
    """Retorna todas as bases de cálculo do sistema"""
    conn = self.create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("SELECT descricao FROM tb_base_calculo ORDER BY id")
            return [row[0] for row in c.fetchall()]
        except Exception as e:
            print(f"Erro ao buscar bases de cálculo: {e}")
            return []
        finally:
            conn.close()
    return []

def populate_default_data(self):
    # Add the new base de cálculo population
    bases_calculo = [
        "00 - Base de cálculo normal",
        "01 - Publicidade e propaganda",
        "02 - Representação comercial", 
        "03 - Corretagem de seguro",
        "04 - Construção civil",
        "05 - Call Center",
        "06 - Estação Digital",
        "07 - Serviços de saúde (órtese e prótese)"
    ]
    c.executemany(
        "INSERT OR IGNORE INTO tb_base_calculo (descricao) VALUES (?)",
        [(base,) for base in bases_calculo]
    )
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

def verificar_tabela_base_calculo(self):
    """Verifica se a tabela tb_base_calculo existe e tem dados"""
    conn = self.create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            
            # Verificar se a tabela existe
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tb_base_calculo'")
            tabela_existe = c.fetchone() is not None
            print(f"Tabela tb_base_calculo existe: {tabela_existe}")
            
            if tabela_existe:
                # Verificar se tem dados
                c.execute("SELECT COUNT(*) FROM tb_base_calculo")
                count = c.fetchone()[0]
                print(f"Quantidade de registros na tabela tb_base_calculo: {count}")
                
                # Listar registros
                if count > 0:
                    c.execute("SELECT id, descricao FROM tb_base_calculo")
                    registros = c.fetchall()
                    print("Registros encontrados:")
                    for registro in registros:
                        print(f" - ID: {registro[0]}, Descrição: {registro[1]}")
            
            return tabela_existe, count if tabela_existe else 0
        except Exception as e:
            print(f"Erro ao verificar tabela tb_base_calculo: {e}")
        finally:
            conn.close()
    return False, 0