import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client

# Configuração da página do Streamlit
st.set_page_config(page_title="Controle de Chamados", layout="wide")
st.title("🎫 Sistema de Controle de Chamados & Tickets (Banco de Dados Cloud)")

# Inicialização segura das credenciais do Supabase através do st.secrets
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    st.error("Erro: Credenciais do Supabase não configuradas nos Secrets do Streamlit.")
    st.stop()

# Lista de setores e problemas padronizados
SETORES = ["TI", "ADM FCN", "ADM ICN", "Biblioteca", "Central de Cópias", "Comunicação", "CPA", "Coordenações FCN", "Coordenações ICN", "Diretoria", "Eng. Elétrica", "Infraestrutura", "Núcleos", "Prof. FCN", "Prof. Icn", "RH", "Secretaria FCN", "Secretaria ICN", "Tesouraria"]
PROBLEMAS = ["Acesso ao Sistema", "Internet / Rede", "Hardware (Mouse, Teclado, Monitor)", "Impressora", "Instalação de Software", "E-mail", "Outros"]

# Função para carregar os dados diretamente do banco de dados na nuvem
def carregar_dados():
    try:
        # Busca todas as linhas da tabela 'chamados' ordenadas pela data de abertura
        resposta = supabase.table("chamados").select("*").execute()
        if not resposta.data:
            return pd.DataFrame(columns=["ID Ticket", "Data de Abertura", "Solicitante", "Setor Solicitante", "Categoria Problema", "Descrição", "Atendente", "Setor Atendente", "Status", "Data de Resolução"])
        
        # Converte o retorno para DataFrame e renomeia para manter o padrão visual
        df_banco = pd.DataFrame(resposta.data)
        df_banco.columns = ["ID Ticket", "Data de Abertura", "Solicitante", "Setor Solicitante", "Categoria Problema", "Descrição", "Atendente", "Setor Atendente", "Status", "Data de Resolução"]
        df_banco['ID Ticket'] = df_banco['ID Ticket'].astype(str)
        return df_banco
    except Exception as e:
        st.error(f"Erro ao ler banco de dados: {e}")
        return pd.DataFrame()

# Mantém os dados sincronizados na sessão
if 'df_chamados' not in st.session_state:
    st.session_state.df_chamados = carregar_dados()

df = st.session_state.df_chamados

# Criando as ABAS
aba_cadastro, aba_pesquisa, aba_dashboard = st.tabs([
    "📝 Novo Chamado / Todos", 
    "🔍 Pesquisar e Editar Ticket", 
    "📊 Gráficos e Indicadores"
])

# -------------------------------------------------------------------------
# ABA 1: CADASTRO
# -------------------------------------------------------------------------
with aba_cadastro:
    st.header("Registrar Novo Ticket")
    
    with st.form("form_chamado", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            id_ticket = st.text_input("ID do Ticket (Digite manualmente)")
            solicitante = st.text_input("Nome do Solicitante")
            setor_solicitante = st.selectbox("Setor do Solicitante", SETORES)
            categoria = st.selectbox("Categoria do Problema", PROBLEMAS)
            descricao = st.text_area("Descrição detalhada do chamado")
        with col2:
            atendente = st.text_input("Nome do Atendente")
            setor_atendente = st.selectbox("Setor do Atendente", SETORES)
            status = st.selectbox("Status Inicial", ["Aberto", "Em Andamento", "Resolvido"])
            data_abertura = st.date_input("Data de Abertura", datetime.today().date())
            data_resolucao = st.date_input("Data de Resolução", datetime.today().date()) if status == "Resolvido" else "Pendente"

        botao_salvar = st.form_submit_button("Salvar Chamado")
        
        if botao_salvar:
            if id_ticket and solicitante and descricao and atendente:
                if not df.empty and id_ticket in df["ID Ticket"].values:
                    st.error(f"O ID Ticket #{id_ticket} já existe no banco de dados!")
                else:
                    # Formata os dados no padrão do banco SQL (nomes das colunas idênticos ao SQL)
                    novo_registro = {
                        "id_ticket": str(id_ticket),
                        "data_abertura": str(data_abertura),
                        "solicitante": solicitante,
                        "setor_solicitante": setor_solicitante,
                        "categoria_problema": categoria,
                        "descricao": descricao,
                        "atendente": atendente,
                        "setor_atendente": setor_atendente,
                        "status": status,
                        "data_resolucao": str(data_resolucao)
                    }
                    # Insere permanentemente no banco online
                    supabase.table("chamados").insert(novo_registro).execute()
                    st.success(f"Ticket #{id_ticket} gravado permanentemente na nuvem!")
                    
                    # Força a atualização dos dados na tela
                    st.session_state.df_chamados = carregar_dados()
                    st.rerun()
            else:
                st.error("Por favor, preencha todos os campos obrigatórios.")

    st.write("---")
    st.header("Todos os Chamados Registrados")
    st.dataframe(df, use_container_width=True)

# -------------------------------------------------------------------------
# ABA 2: PESQUISAR E EDITAR
# -------------------------------------------------------------------------
with aba_pesquisa:
    st.header("🔍 Painel de Busca e Edição")
    if df.empty:
        st.info("Nenhum ticket cadastrado para pesquisa.")
    else:
        col_busca1, col_busca2 = st.columns(2)
        with col_busca1: busca_id = st.text_input("Buscar por ID")
        with col_busca2: busca_solicitante = st.text_input("Buscar por Solicitante")
            
        df_filtrado = df.copy()
        if busca_id: df_filtrado = df_filtrado[df_filtrado["ID Ticket"].str.contains(busca_id, case=False)]
        if busca_solicitante: df_filtrado = df_filtrado[df_filtrado["Solicitante"].str.contains(busca_solicitante, case=False)]
        
        st.dataframe(df_filtrado, use_container_width=True)
        
        st.write("---")
        id_para_editar = st.selectbox("Selecione o ID para atualizar:", [""] + list(df_filtrado["ID Ticket"].unique()))
        
        if id_para_editar != "":
            dados_ticket = df[df["ID Ticket"] == id_para_editar].iloc[0]
            with st.form("form_edicao"):
                novo_status = st.selectbox("Mudar Status", ["Aberto", "Em Andamento", "Resolvido"], index=["Aberto", "Em Andamento", "Resolvido"].index(dados_ticket["Status"]))
                nova_data_res = str(st.date_input("Nova Data Resolução", datetime.today().date())) if novo_status == "Resolvido" else "Pendente"
                
                if st.form_submit_button("Confirmar Atualização"):
                    # Faz o UPDATE direto na linha correspondente no Supabase
                    supabase.table("chamados").update({
                        "status": novo_status,
                        "data_resolucao": nova_data_res
                    }).eq("id_ticket", id_para_editar).execute()
                    
                    st.success("Ticket atualizado com sucesso no banco de dados!")
                    st.session_state.df_chamados = carregar_dados()
                    st.rerun()

# -------------------------------------------------------------------------
# ABA 3: DASHBOARD
# -------------------------------------------------------------------------
with aba_dashboard:
    st.header("Painel de Indicadores (Dashboard)")
    if not df.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.plotly_chart(px.pie(df, names="Status", title="Proporção por Status", hole=0.4), use_container_width=True)
        with col_g2:
            st.plotly_chart(px.bar(df["Categoria Problema"].value_counts().reset_index(), x="count", y="Categoria Problema", orientation='h', title="Problemas"), use_container_width=True)
