# Aplicativo de Gestão de Marmitas (Streamlit)

Este é um aplicativo web simples criado com Streamlit para ajudar a gerenciar clientes, cardápio semanal de marmitas, pedidos, semanas de trabalho e relatórios para sua empresa.

**Novidades (v4 - Correções):**
*   **Correção de Login:** Ajustado o fluxo para garantir que a tela de login seja exibida corretamente ao acessar o app.
*   **Correção de Pedidos:** Corrigido o erro que ocorria ao adicionar/registrar itens no pedido (`KeyError: \'itens_pedido_atual\'`).
*   **Login:** É necessário fazer login para acessar o sistema. O usuário padrão é `admin` com senha `admin`.
*   **Gestão de Semanas:** Seção "Semanas" para cadastrar as semanas de trabalho/entrega.
*   **Pedidos por Semana:** Registro de pedidos associado a uma semana.
*   **Filtro Semanal:** Histórico de pedidos e relatórios filtráveis por semana.

## Funcionalidades

*   **Login:** Acesso seguro ao sistema com usuário e senha.
*   **Semanas:** Cadastro e exclusão de semanas de trabalho.
*   **Clientes:** Cadastro, consulta, edição e exclusão de clientes.
*   **Marmitas:** Cadastro, consulta, edição e exclusão de marmitas. Permite marcar quais estão disponíveis na semana atual.
*   **Pedidos:** Registro manual de novos pedidos, associando-os a um cliente e a uma semana. Consulta de histórico de pedidos (filtrável por semana) e atualização de status.
*   **Relatórios:** Visualização de vendas por cliente, marmitas por cliente, vendas gerais e marmitas mais vendidas, todos filtráveis por semana.

## Estrutura do Projeto

```
marmita_app/
├── .streamlit/             # Diretório para configuração e banco de dados no deploy
│   └── marmita_data.db     # Banco de dados SQLite
├── assets/
│   └── logo.jpeg           # Logo da sua empresa
├── pages/
│   ├── 0_Semanas.py        # Página de gestão de semanas
│   ├── 1_Clientes.py       # Página de gestão de clientes
│   ├── 2_Marmitas.py       # Página de gestão de marmitas/cardápio
│   ├── 3_Pedidos.py        # Página de registro e gestão de pedidos
│   └── 4_Relatorios.py     # Página de relatórios
├── app.py                  # Arquivo principal com login e navegação
├── database.py             # Funções para interagir com o banco de dados
├── requirements.txt        # Dependências Python do projeto
└── README.md               # Este arquivo
```

## Como Executar Localmente

1.  **Pré-requisitos:** Python 3.8+.
2.  **Descompacte:** Extraia `marmita_app_v4.zip`.
3.  **Navegue até a Pasta:** `cd caminho/para/marmita_app`
4.  **Crie Ambiente Virtual (Recomendado):**
    ```bash
    python -m venv venv
    # Windows: venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    ```
5.  **Instale Dependências:** `pip install -r requirements.txt`
6.  **Execute:** `streamlit run app.py`
7.  Acesse pelo navegador e faça login com `admin` / `admin`.

## Como Fazer Deploy Gratuito no Streamlit Community Cloud

Os passos são os mesmos das versões anteriores, mas **certifique-se de enviar todos os arquivos atualizados** (da v4) para o seu repositório GitHub antes de fazer o deploy ou redeploy no Streamlit Cloud.

1.  **GitHub:** Crie um repositório público e envie todo o conteúdo da pasta `marmita_app` (extraída do `marmita_app_v4.zip`). Use a interface web ou comandos `git`.
2.  **Streamlit Cloud:** Acesse [streamlit.io/cloud](https://streamlit.io/cloud), conecte sua conta GitHub.
3.  **Deploy:** Clique "New app", selecione o repositório, branch (`main`) e arquivo (`app.py`). Clique "Deploy!". Se já existia, vá nas configurações do app e reinicie ou mande buscar as atualizações do GitHub.

**Importante:** O banco de dados `marmita_data.db` armazena todos os dados. No Streamlit Cloud, ele é persistente.

## Próximos Passos e Melhorias (Sugestões)

*   Implementar funcionalidade para alterar a senha do administrador.
*   Adicionar suporte a múltiplos usuários com diferentes permissões.
*   Melhorar a interface de cadastro de semanas (ex: seleção de datas).
*   Adicionar upload de imagens para marmitas.
*   Criar backups periódicos do banco de dados.

