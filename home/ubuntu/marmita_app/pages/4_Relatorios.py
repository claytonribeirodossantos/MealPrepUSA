import streamlit as st
import database as db
import pandas as pd

# --- Autenticação ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("⚠️ Você precisa fazer login para acessar esta página.")
    st.stop()

# --- Conexão com Banco de Dados ---
conn = db.create_connection()
if not conn:
    st.error("Falha crítica: Não foi possível conectar ao banco de dados nesta página.")
    st.stop()

st.set_page_config(page_title="Relatórios", page_icon="📊", layout="wide")

st.title("📊 Relatórios de Gestão")

# --- Filtro Global por Semana ---
st.subheader("Filtro de Semana")
semanas = db.get_all_semanas(conn)
semana_id_filtro = None
semana_filtro_options = {"Todas as Semanas": None} # Opção para ver dados gerais
semana_filtro_options.update({s[1]: s[0] for s in semanas})
semana_selecionada_filtro_nome = st.selectbox(
    "Selecione a Semana para filtrar os relatórios (ou Todas as Semanas):",
    options=semana_filtro_options.keys(),
    key="report_week_filter"
)
semana_id_filtro = semana_filtro_options[semana_selecionada_filtro_nome]

st.divider()

# --- Seleção de Relatório ---
report_type = st.selectbox("Selecione o tipo de relatório:", [
    "Vendas por Cliente",
    "Marmitas por Cliente",
    "Vendas Gerais (por Dia)",
    "Marmitas Mais Vendidas"
])

st.divider()

# --- Exibição do Relatório (com filtro de semana aplicado) ---

filtro_aplicado_msg = f" para 	'{semana_selecionada_filtro_nome}	'" if semana_id_filtro else " (Geral)"

if report_type == "Vendas por Cliente":
    st.subheader(f"Vendas por Cliente{filtro_aplicado_msg}")
    df_vendas_cliente = db.get_vendas_por_cliente(conn, semana_id_filter=semana_id_filtro)
    if not df_vendas_cliente.empty:
        st.dataframe(df_vendas_cliente, hide_index=True, use_container_width=True)
        try:
            total_geral = df_vendas_cliente["Total Gasto ($)"].sum()
            st.metric(f"Total Vendido{filtro_aplicado_msg}", f"${total_geral:.2f}")
        except KeyError:
            st.warning("Coluna 	'Total Gasto ($)	' não encontrada.")
        except Exception as e:
            st.error(f"Erro ao calcular total: {e}")
    else:
        st.info(f"Nenhum pedido registrado para gerar este relatório{filtro_aplicado_msg}.")

elif report_type == "Marmitas por Cliente":
    st.subheader(f"Marmitas Consumidas por Cliente{filtro_aplicado_msg}")
    clientes = db.get_all_clientes(conn)
    if clientes:
        cliente_options = {f"{c[1]} ({c[4]})": c[0] for c in clientes}
        cliente_selecionado_nome = st.selectbox("Selecione o Cliente:", options=cliente_options.keys(), key="marmita_cliente_select")
        if cliente_selecionado_nome:
            cliente_id = cliente_options[cliente_selecionado_nome]
            df_marmitas_cliente = db.get_marmitas_por_cliente(conn, cliente_id, semana_id_filter=semana_id_filtro)
            if not df_marmitas_cliente.empty:
                st.dataframe(df_marmitas_cliente, hide_index=True, use_container_width=True)
            else:
                st.info(f"Nenhum pedido encontrado para o cliente 	'{cliente_selecionado_nome.split(	' (	')[0]}	'{filtro_aplicado_msg}.")
    else:
        st.warning("Nenhum cliente cadastrado para gerar este relatório.")

elif report_type == "Vendas Gerais (por Dia)":
    st.subheader(f"Vendas Gerais por Dia{filtro_aplicado_msg}")
    df_vendas_geral = db.get_vendas_geral(conn, semana_id_filter=semana_id_filtro)
    if not df_vendas_geral.empty:
        st.dataframe(df_vendas_geral, hide_index=True, use_container_width=True)
        try:
            chart_data = df_vendas_geral.rename(columns={	'Dia	': 	'index	'}).set_index(	'index	')["Vendas ($)"]
            st.line_chart(chart_data)
            total_geral = df_vendas_geral["Vendas ($)"].sum()
            st.metric(f"Total Vendido{filtro_aplicado_msg}", f"${total_geral:.2f}")
        except KeyError:
             st.warning("Coluna 	'Vendas ($)	' ou 	'Dia	' não encontrada.")
        except Exception as e:
            st.error(f"Erro ao gerar gráfico ou calcular total: {e}")
    else:
        st.info(f"Nenhum pedido registrado para gerar este relatório{filtro_aplicado_msg}.")

elif report_type == "Marmitas Mais Vendidas":
    st.subheader(f"Marmitas Mais Vendidas{filtro_aplicado_msg}")
    df_mais_vendidas = db.get_marmitas_mais_vendidas(conn, semana_id_filter=semana_id_filtro)
    if not df_mais_vendidas.empty:
        st.dataframe(df_mais_vendidas, hide_index=True, use_container_width=True)
        try:
            chart_data = df_mais_vendidas.rename(columns={	'Marmita	': 	'index	'}).set_index(	'index	')["Quantidade"]
            st.bar_chart(chart_data)
        except KeyError:
            st.warning("Coluna 	'Marmita	' ou 	'Quantidade	' não encontrada.")
        except Exception as e:
            st.error(f"Erro ao gerar gráfico: {e}")
    else:
        st.info(f"Nenhum item de pedido registrado para gerar este relatório{filtro_aplicado_msg}.")

# Fechar conexão no final do script (opcional)
# finally:
#     if conn:
#         conn.close()
#         print("Connection closed in 4_Relatorios.py")

