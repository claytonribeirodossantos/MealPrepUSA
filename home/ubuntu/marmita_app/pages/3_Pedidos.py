import streamlit as st
import database as db
import pandas as pd
from datetime import datetime

# --- Autenticação ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("⚠️ Você precisa fazer login para acessar esta página.")
    st.stop()

# --- Conexão com Banco de Dados ---
conn = db.create_connection()
if not conn:
    st.error("Falha crítica: Não foi possível conectar ao banco de dados nesta página.")
    st.stop()

st.set_page_config(page_title="Registrar Pedidos", page_icon="🛒", layout="wide")

st.title("🛒 Registrar e Gerenciar Pedidos")

# --- Formulário para Novo Pedido ---
st.subheader("Registrar Novo Pedido")

# Carregar dados necessários
clientes = db.get_all_clientes(conn)
marmitas_disponiveis = db.get_marmitas_disponiveis(conn)
semanas = db.get_all_semanas(conn)

# Validações
if not clientes:
    st.warning("Nenhum cliente cadastrado. Cadastre clientes primeiro na seção 	'Clientes'.")
    st.stop()
if not marmitas_disponiveis:
    st.warning("Nenhuma marmita marcada como 	'Disponível esta Semana'. Verifique o cadastro em 	'Marmitas'.")
    st.stop()
if not semanas:
    st.warning("Nenhuma semana cadastrada. Cadastre semanas primeiro na seção 	'Semanas'.")
    st.stop()

# Mapeamentos para facilitar
cliente_options = {f"{c[1]} ({c[4]})": c[0] for c in clientes} # "Nome (Telefone)": ID
marmita_options = {f"{m[1]} (${m[2]:.2f})": {"id": m[0], "preco": m[2]} for m in marmitas_disponiveis} # "Nome ($Preco)": {id, preco}
semana_options = {s[1]: s[0] for s in semanas} # "Nome Semana": ID

# Garantir inicialização do estado da sessão para itens do pedido
if "itens_pedido_atual" not in st.session_state:
    st.session_state.itens_pedido_atual = []

with st.form("pedido_form"):
    col_form1, col_form2 = st.columns(2)
    with col_form1:
        cliente_selecionado_nome = st.selectbox("Selecione o Cliente", options=cliente_options.keys())
    with col_form2:
        semana_selecionada_nome = st.selectbox("Selecione a Semana do Pedido", options=semana_options.keys())

    st.write("**Itens do Pedido:**")

    cols_item = st.columns([3, 1, 1])
    marmita_selecionada_nome = cols_item[0].selectbox("Selecione a Marmita (Disponível)", options=marmita_options.keys(), key="marmita_select")
    quantidade = cols_item[1].number_input("Quantidade", min_value=1, value=1, step=1, key="qtd_select")

    # Botão Adicionar Item fora do loop de exibição
    if cols_item[2].button("Adicionar Item", key="add_item_btn"):
        if marmita_selecionada_nome:
            marmita_info = marmita_options[marmita_selecionada_nome]
            # Verificar se o item já existe na lista
            item_existente_index = -1
            for index, item in enumerate(st.session_state.itens_pedido_atual):
                if item["marmita_id"] == marmita_info["id"]:
                    item_existente_index = index
                    break
            
            if item_existente_index != -1:
                # Atualiza quantidade se item já existe
                st.session_state.itens_pedido_atual[item_existente_index]["quantidade"] += quantidade
            else:
                # Adiciona novo item
                st.session_state.itens_pedido_atual.append({
                    "marmita_id": marmita_info["id"],
                    "nome": marmita_selecionada_nome.split(" ($")[0], # Pega só o nome
                    "quantidade": quantidade,
                    "preco_unitario": marmita_info["preco"]
                })
            st.rerun() # Recarrega para mostrar item adicionado/atualizado

    # Exibir itens adicionados e permitir remoção
    valor_total_calculado = 0.0
    indices_para_remover = []
    if st.session_state.itens_pedido_atual:
        st.write("Itens adicionados:")
        for i, item in enumerate(st.session_state.itens_pedido_atual):
            cols_show = st.columns([4, 1, 1, 1])
            item_total = item["quantidade"] * item["preco_unitario"]
            valor_total_calculado += item_total
            cols_show[0].write(f"- {item['nome']} (${item['preco_unitario']:.2f})")
            cols_show[1].write(f"Qtd: {item['quantidade']}")
            cols_show[2].write(f"Sub: ${item_total:.2f}")
            # Botão Remover - Apenas marca para remover depois do loop
            if cols_show[3].button(f"Remover", key=f"rem_{i}"):
                indices_para_remover.append(i)
        
        # Remover itens marcados (fora do loop de exibição)
        if indices_para_remover:
            # Remover pelos índices em ordem reversa para não afetar os índices restantes
            for index in sorted(indices_para_remover, reverse=True):
                del st.session_state.itens_pedido_atual[index]
            st.rerun() # Recarrega após remover

        st.markdown(f"**Valor Total: ${valor_total_calculado:.2f}**")
    else:
        st.write("Nenhum item adicionado ainda.")

    # Outros campos do pedido
    forma_pagamento = st.selectbox("Forma de Pagamento", ["Dinheiro", "Cartão", "Pix", "Outro"])
    status_pagamento = st.selectbox("Status Pagamento", ["Pendente", "Pago"])
    status_entrega = st.selectbox("Status Entrega", ["Pendente", "Em Preparo", "Saiu para Entrega", "Entregue", "Cancelado"])

    submitted = st.form_submit_button("Registrar Pedido")

    if submitted:
        # Verificar se a lista de itens existe e não está vazia ANTES de acessá-la
        if "itens_pedido_atual" not in st.session_state or not st.session_state.itens_pedido_atual:
             st.warning("Adicione pelo menos um item ao pedido.")
        elif not cliente_selecionado_nome:
            st.warning("Selecione um cliente.")
        elif not semana_selecionada_nome:
             st.warning("Selecione a semana do pedido.")
        else:
            # Agora é seguro acessar st.session_state.itens_pedido_atual
            cliente_id = cliente_options[cliente_selecionado_nome]
            semana_id = semana_options[semana_selecionada_nome]
            pedido_id = db.add_pedido(conn, cliente_id, semana_id, valor_total_calculado, forma_pagamento, status_pagamento, status_entrega, st.session_state.itens_pedido_atual)
            if pedido_id:
                st.success(f"Pedido #{pedido_id} registrado com sucesso para a {semana_selecionada_nome}!")
                # Limpar itens do estado da sessão após sucesso
                st.session_state.itens_pedido_atual = [] 
                st.rerun() # Recarrega para limpar form e atualizar histórico
            # else: Erro já é mostrado pela função db

# --- Histórico de Pedidos ---
# (O restante do código permanece o mesmo, pois o erro estava no registro)
st.divider()
st.subheader("Histórico de Pedidos")

# Filtro por Semana
semana_id_filtro = None
semana_filtro_options = {"Todas as Semanas": None} # Adiciona opção para ver tudo
semana_filtro_options.update({s[1]: s[0] for s in semanas})
semana_selecionada_filtro = st.selectbox("Filtrar por Semana:", options=semana_filtro_options.keys())
semana_id_filtro = semana_filtro_options[semana_selecionada_filtro]

# Passar o filtro para a função que busca os pedidos
pedidos_df = db.get_all_pedidos_info(conn, semana_id_filter=semana_id_filtro)

if not pedidos_df.empty:
    # Formatar valor total
    pedidos_df["valor_total"] = pedidos_df["valor_total"].apply(lambda x: f"${x:.2f}")
    # Renomear e reordenar colunas
    pedidos_df = pedidos_df.rename(columns={
        "id": "ID",
        "data_hora": "Data/Hora",
        "nome_cliente": "Cliente",
        "nome_semana": "Semana", # Adicionado
        "valor_total": "Total ($)",
        "forma_pagamento": "Pagamento",
        "status_pagamento": "Status Pgto",
        "status_entrega": "Status Entrega"
    })
    # Definir ordem desejada das colunas
    col_order = ["ID", "Data/Hora", "Semana", "Cliente", "Total ($)", "Pagamento", "Status Pgto", "Status Entrega"]
    pedidos_df = pedidos_df[col_order]

    st.dataframe(pedidos_df, hide_index=True, use_container_width=True)

    st.subheader("Detalhes e Ações")
    # Filtrar IDs disponíveis com base no filtro de semana
    ids_disponiveis = pedidos_df["ID"].tolist()
    pedido_id_detalhe = st.selectbox("Selecione o ID do Pedido para ver detalhes ou alterar status", options=[""] + ids_disponiveis)

    if pedido_id_detalhe:
        itens = db.get_pedido_itens(conn, pedido_id_detalhe)
        st.write("**Itens do Pedido:**")
        if itens:
            for item in itens:
                st.write(f"- {item[0]}x {item[1]} (${item[2]:.2f} cada)")
        else:
            st.write("Nenhum item encontrado para este pedido (ou itens/marmitas foram excluídos).")

        # Atualizar Status
        st.write("**Atualizar Status:**")
        # Buscar dados do pedido novamente para garantir que temos o mais recente
        pedido_atual_data = pedidos_df[pedidos_df["ID"] == pedido_id_detalhe].iloc[0]
        pgto_options = ["Pendente", "Pago"]
        entrega_options = ["Pendente", "Em Preparo", "Saiu para Entrega", "Entregue", "Cancelado"]
        try:
            pgto_index = pgto_options.index(pedido_atual_data["Status Pgto"])
        except ValueError:
            pgto_index = 0
        try:
            entrega_index = entrega_options.index(pedido_atual_data["Status Entrega"])
        except ValueError:
            entrega_index = 0

        novo_status_pgto = st.selectbox("Status Pagamento", pgto_options, index=pgto_index, key=f"pgto_{pedido_id_detalhe}")
        novo_status_entrega = st.selectbox("Status Entrega", entrega_options, index=entrega_index, key=f"entrega_{pedido_id_detalhe}")

        if st.button("Salvar Status", key=f"save_status_{pedido_id_detalhe}"):
            if db.update_pedido_status(conn, pedido_id_detalhe, novo_status_pgto, novo_status_entrega):
                st.success(f"Status do Pedido #{pedido_id_detalhe} atualizado.")
                st.rerun()
            # else: Erro já é mostrado pela função db

        # Excluir Pedido
        if st.button("Excluir Pedido", key=f"delete_pedido_{pedido_id_detalhe}"):
            # Adicionar confirmação?
            if db.delete_pedido(conn, pedido_id_detalhe):
                st.success(f"Pedido #{pedido_id_detalhe} excluído com sucesso.")
                st.rerun()
            # else: Erro já é mostrado pela função db

else:
    st.info("Nenhum pedido registrado ainda" + (f" para a {semana_selecionada_filtro}." if semana_id_filtro else "."))

# Fechar conexão no final do script (opcional)
# finally:
#     if conn:
#         conn.close()
#         print("Connection closed in 3_Pedidos.py")

