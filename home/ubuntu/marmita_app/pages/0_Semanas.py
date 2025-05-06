# Adicionar página para gerenciar Semanas
import streamlit as st
import database as db
import pandas as pd
from datetime import date

# --- Autenticação (copiado de app.py para segurança em cada página) ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("⚠️ Você precisa fazer login para acessar esta página.")
    st.stop()

# --- Conexão com Banco de Dados ---
conn = db.create_connection()
if not conn:
    st.error("Falha crítica: Não foi possível conectar ao banco de dados nesta página.")
    st.stop()

st.set_page_config(page_title="Gerenciar Semanas", page_icon="🗓️", layout="wide")

st.title("🗓️ Gerenciar Semanas de Trabalho/Entrega")

st.info("Cadastre as semanas para associar aos pedidos e filtrar relatórios. Use um nome descritivo, ex: \"Semana 05/Mai a 11/Mai\".")

# --- Formulário para Adicionar Semana ---
st.subheader("Adicionar Nova Semana")

with st.form("semana_form", clear_on_submit=True):
    nome_semana = st.text_input("Nome da Semana (Ex: Semana 05/Mai a 11/Mai)")
    # Opcional: datas de início e fim
    # col1, col2 = st.columns(2)
    # data_inicio = col1.date_input("Data Início (Opcional)", value=None)
    # data_fim = col2.date_input("Data Fim (Opcional)", value=None)

    submitted = st.form_submit_button("Adicionar Semana")

    if submitted:
        if not nome_semana:
            st.warning("O nome da semana é obrigatório.")
        else:
            # Por enquanto, não vamos obrigar/usar datas de início/fim
            data_inicio = None
            data_fim = None
            last_id = db.add_semana(conn, nome_semana, data_inicio, data_fim)
            if last_id:
                st.success(f"Semana 	"{nome_semana}	" adicionada com sucesso! ID: {last_id}")
                st.rerun()
            # else: Erro já é mostrado pela função db

# --- Tabela de Semanas Cadastradas ---
st.divider()
st.subheader("Semanas Cadastradas")

semanas = db.get_all_semanas(conn)

if semanas:
    # id, nome_semana, data_inicio, data_fim
    df_semanas = pd.DataFrame(semanas, columns=["ID", "Nome da Semana", "Data Início", "Data Fim"])
    # Ocultar datas se não estiverem sendo usadas
    df_display = df_semanas[["ID", "Nome da Semana"]]
    st.dataframe(df_display, hide_index=True, use_container_width=True)

    st.subheader("Ações")
    semana_id_action = st.selectbox("Selecione o ID da Semana para Excluir", options=[""] + df_semanas["ID"].tolist())

    if semana_id_action:
        # Botão Excluir (Editar não implementado nesta versão)
        if st.button("❌ Excluir Semana Selecionada", key=f"del_s_{semana_id_action}"):
            # Adicionar confirmação?
            # Verificar se a semana tem pedidos associados antes de excluir?
            if db.delete_semana(conn, semana_id_action):
                st.success(f"Semana ID {semana_id_action} excluída com sucesso.")
                st.rerun()
            # else: Erro já é mostrado pela função db
else:
    st.info("Nenhuma semana cadastrada ainda.")

# Fechar conexão no final do script (opcional)
# finally:
#     if conn:
#         conn.close()
#         print("Connection closed in 0_Semanas.py")

