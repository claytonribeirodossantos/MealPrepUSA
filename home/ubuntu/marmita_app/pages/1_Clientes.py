import streamlit as st
import database as db
import pandas as pd

# --- Conexão com Banco de Dados ---
conn = db.create_connection()
if not conn:
    st.error("Falha crítica: Não foi possível conectar ao banco de dados nesta página.")
    st.stop()

st.set_page_config(page_title="Gerenciar Clientes", page_icon="👤", layout="wide")

st.title("👤 Gerenciar Clientes")

# --- Formulário para Adicionar/Editar Cliente ---
st.subheader("Adicionar Novo Cliente ou Editar Existente")

cliente_id_edit = st.session_state.get("cliente_id_edit", None)

if cliente_id_edit:
    cliente_data = db.get_cliente_by_id(conn, cliente_id_edit)
    if not cliente_data:
        st.error("Cliente não encontrado para edição.")
        st.session_state.cliente_id_edit = None # Limpa o estado
        cliente_id_edit = None # Reseta a variável local
else:
    cliente_data = None

with st.form("cliente_form", clear_on_submit=True):
    nome = st.text_input("Nome Completo", value=cliente_data[1] if cliente_data else "")
    endereco = st.text_input("Endereço (Rua, Número, Bairro/Cidade, Estado, CEP)", value=cliente_data[2] if cliente_data else "")
    complemento = st.text_input("Complemento/Apto/Referência", value=cliente_data[3] if cliente_data else "")
    telefone = st.text_input("Telefone (formato recomendado: +1 XXX-XXX-XXXX)", value=cliente_data[4] if cliente_data else "")

    submitted = st.form_submit_button("Salvar Cliente" if not cliente_id_edit else "Atualizar Cliente")

    if submitted:
        if not nome or not telefone:
            st.warning("Nome e Telefone são obrigatórios.")
        else:
            if cliente_id_edit:
                # Atualizar cliente
                success = db.update_cliente(conn, cliente_id_edit, nome, endereco, complemento, telefone)
                if success:
                    st.success(f"Cliente 	'{nome}	' atualizado com sucesso!")
                    st.session_state.cliente_id_edit = None # Limpa o estado após sucesso
                    st.rerun() # Recarrega para limpar o form e atualizar a lista
                # else: Erro já é mostrado pela função db
            else:
                # Adicionar novo cliente
                last_id = db.add_cliente(conn, nome, endereco, complemento, telefone)
                if last_id:
                    st.success(f"Cliente 	'{nome}	' adicionado com sucesso! ID: {last_id}")
                    st.rerun() # Recarrega para atualizar a lista
                # else: Erro já é mostrado pela função db

# Botão para cancelar edição
if cliente_id_edit:
    if st.button("Cancelar Edição"):
        st.session_state.cliente_id_edit = None
        st.rerun()

# --- Tabela de Clientes ---
st.divider()
st.subheader("Lista de Clientes Cadastrados")

clientes = db.get_all_clientes(conn)

if clientes:
    df_clientes = pd.DataFrame(clientes, columns=["ID", "Nome", "Endereço", "Complemento", "Telefone"])

    # Usar st.dataframe para melhor visualização e performance
    st.dataframe(df_clientes, hide_index=True, use_container_width=True)

    st.subheader("Ações")
    cliente_id_action = st.selectbox("Selecione o ID do Cliente para Editar ou Excluir", options=[""] + df_clientes["ID"].tolist())

    if cliente_id_action:
        col1, col2 = st.columns(2)
        # Botão Editar
        if col1.button("✏️ Editar Cliente Selecionado", key=f"edit_{cliente_id_action}"):
            st.session_state.cliente_id_edit = cliente_id_action
            st.rerun()

        # Botão Excluir
        if col2.button("❌ Excluir Cliente Selecionado", key=f"del_{cliente_id_action}"):
            cliente_info = db.get_cliente_by_id(conn, cliente_id_action)
            if cliente_info:
                # Adicionar confirmação antes de excluir?
                # st.warning(f"Tem certeza que deseja excluir {cliente_info[1]}?")
                # if st.button("Confirmar Exclusão"): ...
                if db.delete_cliente(conn, cliente_id_action):
                    st.success(f"Cliente 	'{cliente_info[1]}	' excluído com sucesso.")
                    if st.session_state.get("cliente_id_edit") == cliente_id_action:
                         st.session_state.cliente_id_edit = None # Limpa se estava editando o excluído
                    st.rerun()
                # else: Erro já é mostrado pela função db
            else:
                st.error("Cliente não encontrado para exclusão.")

else:
    st.info("Nenhum cliente cadastrado ainda.")

# Fechar conexão no final do script (opcional)
# finally:
#     if conn:
#         conn.close()
#         print("Connection closed in 1_Clientes.py")

