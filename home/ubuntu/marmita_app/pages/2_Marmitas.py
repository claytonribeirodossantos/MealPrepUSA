import streamlit as st
import database as db
import pandas as pd
import os

# --- Conexão com Banco de Dados ---
conn = db.create_connection()
if not conn:
    st.error("Falha crítica: Não foi possível conectar ao banco de dados nesta página.")
    st.stop()

st.set_page_config(page_title="Gerenciar Marmitas", page_icon="🍲", layout="wide")

st.title("🍲 Gerenciar Cardápio Semanal")

st.info("Cadastre todas as suas opções de marmitas aqui. Use a caixa de seleção \"Disponível esta Semana\" para definir o cardápio semanal.")

# --- Formulário para Adicionar/Editar Marmita ---
st.subheader("Adicionar Nova Marmita ou Editar Existente")

marmita_id_edit = st.session_state.get("marmita_id_edit", None)

if marmita_id_edit:
    marmita_data = db.get_marmita_by_id(conn, marmita_id_edit)
    if not marmita_data:
        st.error("Marmita não encontrada para edição.")
        st.session_state.marmita_id_edit = None
        marmita_id_edit = None
else:
    marmita_data = None

# Diretório para salvar imagens das marmitas (opcional, não implementado upload)
# IMAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "marmitas")
# os.makedirs(IMAGE_DIR, exist_ok=True)

with st.form("marmita_form", clear_on_submit=True):
    nome = st.text_input("Nome da Marmita", value=marmita_data[1] if marmita_data else "")
    descricao = st.text_area("Descrição/Ingredientes", value=marmita_data[2] if marmita_data else "")
    preco = st.number_input("Preço (USD $)", min_value=0.01, format="%.2f", value=float(marmita_data[3]) if marmita_data else 10.00)
    categoria = st.text_input("Categoria (Ex: Tradicional, Fit, Vegetariana)", value=marmita_data[4] if marmita_data else "")
    disponivel = st.checkbox("Disponível esta Semana?", value=bool(marmita_data[5]) if marmita_data else True)
    # imagem_path = marmita_data[6] if marmita_data else None # Path da imagem (não usado no upload)

    submitted = st.form_submit_button("Salvar Marmita" if not marmita_id_edit else "Atualizar Marmita")

    if submitted:
        if not nome or preco <= 0:
            st.warning("Nome e Preço (maior que zero) são obrigatórios.")
        else:
            imagem_path = None # Upload de imagem não implementado nesta versão
            if marmita_id_edit:
                # Atualizar marmita
                success = db.update_marmita(conn, marmita_id_edit, nome, descricao, preco, categoria, disponivel, imagem_path)
                if success:
                    st.success(f"Marmita 	'{nome}' atualizada com sucesso!")
                    st.session_state.marmita_id_edit = None
                    st.rerun()
                # else: Erro já é mostrado pela função db
            else:
                # Adicionar nova marmita
                last_id = db.add_marmita(conn, nome, descricao, preco, categoria, disponivel, imagem_path)
                if last_id:
                    st.success(f"Marmita 	'{nome}' adicionada com sucesso! ID: {last_id}")
                    st.rerun()
                # else: Erro já é mostrado pela função db

# Botão para cancelar edição
if marmita_id_edit:
    if st.button("Cancelar Edição"):
        st.session_state.marmita_id_edit = None
        st.rerun()

# --- Tabela de Marmitas ---
st.divider()
st.subheader("Lista de Marmitas Cadastradas")

marmitas = db.get_all_marmitas(conn)

if marmitas:
    # id, nome, descricao, preco, categoria, disponivel_semana, imagem_path
    df_marmitas = pd.DataFrame(marmitas, columns=["ID", "Nome", "Descrição", "Preço ($)", "Categoria", "Disponível", "Imagem Path"])
    df_marmitas["Disponível"] = df_marmitas["Disponível"].apply(lambda x: "Sim" if x else "Não")
    df_marmitas["Preço ($)"] = df_marmitas["Preço ($)"].apply(lambda x: f"{x:.2f}")

    # Selecionar colunas para exibir
    df_display = df_marmitas[["ID", "Nome", "Descrição", "Preço ($)", "Categoria", "Disponível"]]

    st.dataframe(df_display, hide_index=True, use_container_width=True)

    st.subheader("Ações")
    marmita_id_action = st.selectbox("Selecione o ID da Marmita para Editar ou Excluir", options=[""] + df_marmitas["ID"].tolist())

    if marmita_id_action:
        col1, col2 = st.columns(2)
        # Botão Editar
        if col1.button("✏️ Editar Marmita Selecionada", key=f"edit_m_{marmita_id_action}"):
            st.session_state.marmita_id_edit = marmita_id_action
            st.rerun()

        # Botão Excluir
        if col2.button("❌ Excluir Marmita Selecionada", key=f"del_m_{marmita_id_action}"):
            marmita_info = db.get_marmita_by_id(conn, marmita_id_action)
            if marmita_info:
                # Adicionar confirmação?
                if db.delete_marmita(conn, marmita_id_action):
                    st.success(f"Marmita 	'{marmita_info[1]}' excluída com sucesso.")
                    if st.session_state.get("marmita_id_edit") == marmita_id_action:
                         st.session_state.marmita_id_edit = None
                    st.rerun()
                # else: Erro já é mostrado pela função db
            else:
                st.error("Marmita não encontrada para exclusão.")

else:
    st.info("Nenhuma marmita cadastrada ainda.")

# Fechar conexão no final do script (opcional)
# finally:
#     if conn:
#         conn.close()
#         print("Connection closed in 2_Marmitas.py")

