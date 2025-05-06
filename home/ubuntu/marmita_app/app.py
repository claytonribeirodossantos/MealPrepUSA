import streamlit as st
import database as db
import os

# --- Page Config (MUST be the first Streamlit command) ---
st.set_page_config(
    page_title="Gestão Marmitas App",
    page_icon="🍲",
    layout="wide"
)

# --- Conexão e Criação de Tabelas ---
# Cria conexão no início do script
conn = db.create_connection()

# Cria tabelas se não existirem (importante na primeira execução)
# Isso também adiciona o usuário admin padrão se necessário
if conn:
    db.create_tables(conn)
else:
    # Se a conexão falhar aqui, o app não pode continuar
    st.error("Falha crítica: Não foi possível conectar ao banco de dados principal.")
    st.stop()

# --- Autenticação Functions ---
def login_page():
    st.title("Login - Gestão de Marmitas")
    st.info("Use usuário 	'admin	' e senha 	'admin	' no primeiro acesso.")
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        if submitted:
            if db.verify_user(conn, username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                # Não mostrar mensagem de sucesso aqui, apenas fazer o rerun
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

def main_app_content():
    """Função que renderiza o conteúdo principal do app após o login."""
    
    # --- Logout Button --- 
    with st.sidebar:
        st.write(f"Usuário: {st.session_state.get(	'username	', 	'N/A	')}")
        if st.button("Sair"):
            # Limpar estado da sessão relacionado ao login
            st.session_state["logged_in"] = False
            if "username" in st.session_state: del st.session_state["username"]
            # Limpar outros estados de sessão que possam persistir entre logins (opcional)
            # Ex: st.session_state.pop("itens_pedido_atual", None)
            st.rerun() # Recarrega para mostrar a tela de login

    # --- Interface Principal --- 
    st.title("🍲 Gestão de Marmitas Simplificada")

    st.markdown("""
    Bem-vindo ao seu sistema de gerenciamento de marmitas!

    Use o menu na barra lateral esquerda para navegar entre as seções:

    *   **Semanas:** Defina as semanas de trabalho/entrega.
    *   **Clientes:** Cadastre, consulte, edite e remova seus clientes.
    *   **Marmitas:** Gerencie seu cardápio e defina a disponibilidade semanal.
    *   **Pedidos:** Registre novos pedidos (associados a uma semana) e consulte o histórico.
    *   **Relatórios:** Visualize informações filtradas por semana.
    """)

    # Exibir logo
    try:
        # Tenta construir o caminho relativo ao diretório do script app.py
        base_dir = os.path.dirname(__file__)
        logo_path = os.path.join(base_dir, "assets", "logo.jpeg")
        if os.path.exists(logo_path):
             st.sidebar.image(logo_path, use_column_width=True)
        else:
             # Não mostra erro se o logo não for encontrado, apenas não exibe
             # st.sidebar.warning(f"Logo não encontrado em: {logo_path}")
             pass
    except Exception as e:
        st.sidebar.error(f"Erro ao carregar logo: {e}")

    st.sidebar.success("Navegue pelas seções acima.")

    # Resumo geral ou dashboard
    st.divider()
    st.subheader("Resumo Rápido")
    try:
        # Usar a conexão global 'conn' que já foi estabelecida
        total_clientes = len(db.get_all_clientes(conn))
        pedidos_df_total = db.get_all_pedidos_info(conn) # Sem filtro para contagem total
        total_pedidos = len(pedidos_df_total)

        col1, col2 = st.columns(2)
        col1.metric("Total de Clientes", total_clientes)
        col2.metric("Total de Pedidos Registrados", total_pedidos)

    except Exception as e:
        st.error(f"Erro ao buscar dados para o resumo: {e}")

# --- Controle de Fluxo Principal (Login/App) ---
# Garante que o estado de login exista
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Verifica o estado e mostra a página apropriada
if st.session_state["logged_in"]:
    main_app_content() # Mostra o conteúdo principal do app
else:
    login_page() # Mostra a tela de login

# Fechar conexão no final do script (opcional, mas pode ser útil)
# finally:
#     if conn:
#         conn.close()
#         print("Connection closed in app.py")

