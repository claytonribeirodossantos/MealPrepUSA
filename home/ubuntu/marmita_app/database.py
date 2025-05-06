import streamlit as st
import sqlite3
import pandas as pd
import os
import hashlib # For basic password hashing
from datetime import datetime

DB_FILE = ".streamlit/marmita_data.db"

# --- Conexão e Criação de Tabelas ---

def create_connection():
    conn = None
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE, check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.execute("PRAGMA foreign_keys = ON;") # Enable foreign key constraints
        print(f"SQLite connection to {DB_FILE} established.")
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        st.error(f"Erro ao conectar ao banco de dados: {e}")
    except OSError as e:
        print(f"Error creating directory for DB: {e}")
        st.error(f"Erro de permissão ou sistema de arquivos ao tentar criar diretório para DB: {e}")
    return conn

def create_tables(conn):
    if not conn:
        st.error("Conexão com banco de dados inválida para criar tabelas.")
        return
    try:
        cursor = conn.cursor()
        # Tabela de Usuários (para login)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        );
        """)
        # Tabela de Semanas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS semanas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_semana TEXT NOT NULL UNIQUE, -- Ex: "Semana 05/Mai a 11/Mai"
            data_inicio DATE,
            data_fim DATE
        );
        """)
        # Tabela de Clientes
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            endereco TEXT,
            complemento TEXT,
            telefone TEXT UNIQUE
        );
        """)
        # Tabela de Marmitas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS marmitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            descricao TEXT,
            preco REAL,
            categoria TEXT,
            disponivel_semana BOOLEAN DEFAULT TRUE,
            imagem_path TEXT
        );
        """)
        # Tabela de Pedidos (com FK para semana)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            semana_id INTEGER, -- Adicionado
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            valor_total REAL,
            forma_pagamento TEXT,
            status_pagamento TEXT DEFAULT 'Pendente',
            status_entrega TEXT DEFAULT 'Pendente',
            FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE SET NULL,
            FOREIGN KEY (semana_id) REFERENCES semanas (id) ON DELETE SET NULL -- Ou ON DELETE CASCADE?
        );
        """)
        # Tabela de Itens do Pedido
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            marmita_id INTEGER,
            quantidade INTEGER,
            preco_unitario REAL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id) ON DELETE CASCADE,
            FOREIGN KEY (marmita_id) REFERENCES marmitas (id) ON DELETE SET NULL
        );
        """)
        conn.commit()
        print("Tables checked/created successfully.")
        # Adicionar usuário admin padrão se não existir
        add_default_admin(conn)
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
        st.error(f"Erro ao criar/verificar tabelas no banco de dados: {e}")

# --- Funções de Autenticação --- 

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(conn, username, password):
    if not conn: return False
    password_hash = hash_password(password)
    sql = 'INSERT INTO usuarios(username, password_hash) VALUES(?,?)'
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (username, password_hash))
        conn.commit()
        print(f"User {username} added.")
        return True
    except sqlite3.IntegrityError:
        print(f"Username {username} already exists.")
        return False # Usuário já existe
    except sqlite3.Error as e:
        print(f"Error adding user: {e}")
        return False

def add_default_admin(conn):
    # Adiciona admin/admin se não houver usuários
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        print("No users found. Adding default admin user 'admin' with password 'admin'.")
        add_user(conn, "admin", "admin")

def verify_user(conn, username, password):
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password_hash FROM usuarios WHERE username=?", (username,))
        result = cursor.fetchone()
        if result:
            stored_hash = result[0]
            if stored_hash == hash_password(password):
                return True # Senha correta
    except sqlite3.Error as e:
        print(f"Error verifying user: {e}")
    return False # Usuário não encontrado ou senha incorreta

# --- Funções CRUD para Semanas ---

def add_semana(conn, nome_semana, data_inicio=None, data_fim=None):
    if not conn: return None
    sql = 'INSERT INTO semanas(nome_semana, data_inicio, data_fim) VALUES(?,?,?)'
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (nome_semana, data_inicio, data_fim))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        st.error(f"Erro: Semana com nome '{nome_semana}' já existe.")
        return None
    except sqlite3.Error as e:
        print(f"Error adding semana: {e}")
        st.error(f"Erro inesperado ao adicionar semana: {e}")
        return None

def get_all_semanas(conn):
    if not conn: return []
    cursor = conn.cursor()
    try:
        # Ordenar por data de início talvez? Ou nome?
        cursor.execute("SELECT id, nome_semana, data_inicio, data_fim FROM semanas ORDER BY data_inicio DESC, nome_semana")
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Erro ao buscar semanas: {e}")
        return []

# ... (Update e Delete para Semanas podem ser adicionados se necessário)

def delete_semana(conn, semana_id):
    if not conn: return False
    # ON DELETE SET NULL na FK de pedidos deve tratar a referência
    sql = 'DELETE FROM semanas WHERE id=?'
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (semana_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting semana: {e}")
        st.error(f"Erro ao excluir semana: {e}")
        return False

# --- Funções CRUD para Clientes (sem alterações) ---

def add_cliente(conn, nome, endereco, complemento, telefone):
    if not conn: return None
    sql = 'INSERT INTO clientes(nome, endereco, complemento, telefone) VALUES(?,?,?,?)'
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (nome, endereco, complemento, telefone))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        st.error(f"Erro: Telefone '{telefone}' já cadastrado.")
        return None
    except sqlite3.Error as e:
        print(f"Error adding cliente: {e}")
        st.error(f"Erro inesperado ao adicionar cliente: {e}")
        return None

def get_all_clientes(conn):
    if not conn: return []
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, nome, endereco, complemento, telefone FROM clientes ORDER BY nome")
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Erro ao buscar clientes: {e}")
        return []

def get_cliente_by_id(conn, cliente_id):
    if not conn: return None
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, nome, endereco, complemento, telefone FROM clientes WHERE id=?", (cliente_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        st.error(f"Erro ao buscar cliente por ID: {e}")
        return None

def update_cliente(conn, cliente_id, nome, endereco, complemento, telefone):
    if not conn: return False
    sql = 'UPDATE clientes SET nome = ?, endereco = ?, complemento = ?, telefone = ? WHERE id = ?'
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (nome, endereco, complemento, telefone, cliente_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error(f"Erro: Telefone '{telefone}' já pertence a outro cliente.")
        return False
    except sqlite3.Error as e:
        print(f"Error updating cliente: {e}")
        st.error(f"Erro inesperado ao atualizar cliente: {e}")
        return False

def delete_cliente(conn, cliente_id):
    if not conn: return False
    sql = 'DELETE FROM clientes WHERE id=?'
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (cliente_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting cliente: {e}")
        st.error(f"Erro ao excluir cliente: {e}")
        return False

# --- Funções CRUD para Marmitas (sem alterações) ---

def add_marmita(conn, nome, descricao, preco, categoria, disponivel_semana, imagem_path=None):
    if not conn: return None
    sql = 'INSERT INTO marmitas(nome, descricao, preco, categoria, disponivel_semana, imagem_path) VALUES(?,?,?,?,?,?)'
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (nome, descricao, preco, categoria, disponivel_semana, imagem_path))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        st.error(f"Erro: Marmita com nome '{nome}' já existe.")
        return None
    except sqlite3.Error as e:
        print(f"Error adding marmita: {e}")
        st.error(f"Erro inesperado ao adicionar marmita: {e}")
        return None

def get_all_marmitas(conn):
    if not conn: return []
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, nome, descricao, preco, categoria, disponivel_semana, imagem_path FROM marmitas ORDER BY nome")
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Erro ao buscar marmitas: {e}")
        return []

def get_marmitas_disponiveis(conn):
    if not conn: return []
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, nome, preco FROM marmitas WHERE disponivel_semana = TRUE ORDER BY nome")
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Erro ao buscar marmitas disponíveis: {e}")
        return []

def get_marmita_by_id(conn, marmita_id):
    if not conn: return None
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, nome, descricao, preco, categoria, disponivel_semana, imagem_path FROM marmitas WHERE id=?", (marmita_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        st.error(f"Erro ao buscar marmita por ID: {e}")
        return None

def update_marmita(conn, marmita_id, nome, descricao, preco, categoria, disponivel_semana, imagem_path):
    if not conn: return False
    sql = 'UPDATE marmitas SET nome = ?, descricao = ?, preco = ?, categoria = ?, disponivel_semana = ?, imagem_path = ? WHERE id = ?'
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (nome, descricao, preco, categoria, disponivel_semana, imagem_path, marmita_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error(f"Erro: Marmita com nome '{nome}' já existe.")
        return False
    except sqlite3.Error as e:
        print(f"Error updating marmita: {e}")
        st.error(f"Erro inesperado ao atualizar marmita: {e}")
        return False

def delete_marmita(conn, marmita_id):
    if not conn: return False
    sql = 'DELETE FROM marmitas WHERE id=?'
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (marmita_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting marmita: {e}")
        st.error(f"Erro ao excluir marmita: {e}")
        return False

# --- Funções CRUD para Pedidos (adicionar semana_id) ---

def add_pedido(conn, cliente_id, semana_id, valor_total, forma_pagamento, status_pagamento, status_entrega, itens):
    if not conn: return None
    conn.execute('BEGIN TRANSACTION')
    try:
        sql_pedido = 'INSERT INTO pedidos(cliente_id, semana_id, valor_total, forma_pagamento, status_pagamento, status_entrega) VALUES(?,?,?,?,?,?)'
        cursor = conn.cursor()
        cursor.execute(sql_pedido, (cliente_id, semana_id, valor_total, forma_pagamento, status_pagamento, status_entrega))
        pedido_id = cursor.lastrowid

        sql_item = 'INSERT INTO itens_pedido(pedido_id, marmita_id, quantidade, preco_unitario) VALUES(?,?,?,?)'
        for item in itens:
            cursor.execute(sql_item, (pedido_id, item['marmita_id'], item['quantidade'], item['preco_unitario']))

        conn.commit()
        return pedido_id
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error adding pedido: {e}")
        st.error(f"Erro inesperado ao adicionar pedido: {e}")
        return None

def get_all_pedidos_info(conn, semana_id_filter=None):
    if not conn: return pd.DataFrame()
    base_sql = """
    SELECT
        p.id, strftime('%Y-%m-%d %H:%M', p.data_hora) as data_hora,
        COALESCE(c.nome, 'Cliente Excluído') as nome_cliente,
        COALESCE(s.nome_semana, 'Semana Excluída') as nome_semana, -- Adicionado
        p.valor_total, p.forma_pagamento, p.status_pagamento, p.status_entrega
    FROM pedidos p
    LEFT JOIN clientes c ON p.cliente_id = c.id
    LEFT JOIN semanas s ON p.semana_id = s.id -- Adicionado
    """
    params = []
    if semana_id_filter:
        base_sql += " WHERE p.semana_id = ?"
        params.append(semana_id_filter)

    base_sql += " ORDER BY p.data_hora DESC"

    try:
        df = pd.read_sql_query(base_sql, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Erro ao buscar histórico de pedidos: {e}")
        return pd.DataFrame()

def get_pedido_itens(conn, pedido_id):
    # Sem alterações aqui
    if not conn: return []
    sql = """
    SELECT
        ip.quantidade, COALESCE(m.nome, 'Marmita Excluída') as nome_marmita, ip.preco_unitario
    FROM itens_pedido ip
    LEFT JOIN marmitas m ON ip.marmita_id = m.id
    WHERE ip.pedido_id = ?
    """
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (pedido_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Erro ao buscar itens do pedido {pedido_id}: {e}")
        return []

def update_pedido_status(conn, pedido_id, status_pagamento, status_entrega):
    # Sem alterações aqui
    if not conn: return False
    sql = 'UPDATE pedidos SET status_pagamento = ?, status_entrega = ? WHERE id = ?'
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (status_pagamento, status_entrega, pedido_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating pedido status: {e}")
        st.error(f"Erro inesperado ao atualizar status do pedido: {e}")
        return False

def delete_pedido(conn, pedido_id):
    # Sem alterações aqui
    if not conn: return False
    sql = 'DELETE FROM pedidos WHERE id=?'
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (pedido_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting pedido: {e}")
        st.error(f"Erro ao excluir pedido: {e}")
        return False

# --- Funções para Relatórios (adicionar filtro de semana) ---

def get_vendas_por_cliente(conn, semana_id_filter=None):
    if not conn: return pd.DataFrame()
    sql = """
    SELECT COALESCE(c.nome, 'Cliente Excluído') as Cliente, COUNT(p.id) as "Pedidos", SUM(p.valor_total) as "Total Gasto ($)"
    FROM pedidos p
    LEFT JOIN clientes c ON p.cliente_id = c.id
    """
    params = []
    if semana_id_filter:
        sql += " WHERE p.semana_id = ?"
        params.append(semana_id_filter)

    sql += " GROUP BY p.cliente_id ORDER BY \"Total Gasto ($)\" DESC"

    try:
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Erro ao gerar relatório de vendas por cliente: {e}")
        return pd.DataFrame()

def get_marmitas_por_cliente(conn, cliente_id, semana_id_filter=None):
    if not conn: return pd.DataFrame()
    sql = """
    SELECT COALESCE(m.nome, 'Marmita Excluída') as Marmita, SUM(ip.quantidade) as Quantidade
    FROM itens_pedido ip
    JOIN pedidos p ON ip.pedido_id = p.id
    LEFT JOIN marmitas m ON ip.marmita_id = m.id
    WHERE p.cliente_id = ?
    """
    params = [cliente_id]
    if semana_id_filter:
        sql += " AND p.semana_id = ?"
        params.append(semana_id_filter)

    sql += " GROUP BY ip.marmita_id ORDER BY Quantidade DESC"

    try:
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Erro ao gerar relatório de marmitas para o cliente: {e}")
        return pd.DataFrame()

def get_vendas_geral(conn, semana_id_filter=None):
    if not conn: return pd.DataFrame()
    sql = """
    SELECT
        strftime('%Y-%m-%d', p.data_hora) as Dia,
        COUNT(p.id) as Pedidos,
        SUM(p.valor_total) as "Vendas ($)"
    FROM pedidos p
    """
    params = []
    if semana_id_filter:
        sql += " WHERE p.semana_id = ?"
        params.append(semana_id_filter)

    sql += " GROUP BY Dia ORDER BY Dia DESC"

    try:
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Erro ao gerar relatório geral de vendas: {e}")
        return pd.DataFrame()

def get_marmitas_mais_vendidas(conn, semana_id_filter=None):
    if not conn: return pd.DataFrame()
    sql = """
    SELECT COALESCE(m.nome, 'Marmita Excluída') as Marmita, SUM(ip.quantidade) as Quantidade
    FROM itens_pedido ip
    """
    params = []
    if semana_id_filter:
        sql += " JOIN pedidos p ON ip.pedido_id = p.id WHERE p.semana_id = ?"
        params.append(semana_id_filter)

    sql += " LEFT JOIN marmitas m ON ip.marmita_id = m.id GROUP BY ip.marmita_id ORDER BY Quantidade DESC"

    try:
        # Need to adjust the join if filter is not applied
        if not semana_id_filter:
             sql = sql.replace("LEFT JOIN marmitas", " JOIN pedidos p ON ip.pedido_id = p.id LEFT JOIN marmitas")

        df = pd.read_sql_query(sql, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Erro ao gerar relatório de marmitas mais vendidas: {e}")
        return pd.DataFrame()

