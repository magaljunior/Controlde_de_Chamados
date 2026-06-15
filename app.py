import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# Configuração da página do Streamlit
st.set_page_config(page_title="Controle de Chamados", layout="wide")
st.title("🎫 SIG Chamados & Tickets")

# Lista de setores e problemas padronizados
SETORES = ["TI", "ADM FCN", "ADM ICN", "Biblioteca", "Central de Cópias", "Comunicação", "CPA", "Coordenações FCN", "Coordenações ICN", "Diretoria", "Eng. Elétrica", "Infraestrutura",  "Núcleos", "Prof. FCN", "Prof. Icn",  "Núcleos", "RH", "Secretaria FCN", "Secretaria ICN", "Tesouraria"]PROBLEMAS = ["Acesso ao Sistema", "Internet / Rede", "Hardware (Mouse, Teclado, Monitor)", "Impressora", "Instalação de Software", "E-mail", "Outros"]
COLUNAS_PADRAO = ["ID Ticket", "Data de Abertura", "Solicitante", "Setor Solicitante", "Categoria Problema", "Descrição", "Atendente", "Setor Atendente", "Status", "Data de Resolução"]

# Conexão Nativa do Streamlit com o Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Carrega os dados direto da planilha configurada nos Secrets
    def carregar_dados():
        # ttl="0" garante que ele busque dados novos do Google a cada atualização da página
        df = conn.read(ttl="0")
        if df.empty:
            return pd.DataFrame(columns=COLUNAS_PADRAO)
        df.dropna(how="all", inplace=True)
        df['ID Ticket'] = df['ID Ticket'].astype(str)
        return df

    st.session_state.df_chamados = carregar_dados()
    df = st.session_state.df_chamados

except Exception as e:
    st.error(f"Erro ao conectar com o Google Sheets: {e}")
    df = pd.DataFrame(columns=COLUNAS_PADRAO)

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
                if id_ticket in df["ID Ticket"].values:
                    st.error(f"O ID Ticket #{id_ticket} já existe!")
                else:
                    novo_ticket = {
                        "ID Ticket": str(id_ticket),
                        "Data de Abertura": str(data_abertura),
                        "Solicitante": solicitante,
                        "Setor Solicitante": setor_solicitante,
                        "Categoria Problema": categoria,
                        "Descrição": descricao,
                        "Atendente": atendente,
                        "Setor Atendente": setor_atendente,
                        "Status": status,
                        "Data de Resolução": str(data_resolucao) if status == "Resolvido" else "Pendente"
                    }
                    
                    # Junta o chamado novo com os antigos
                    df_atualizado = pd.concat([df, pd.DataFrame([novo_ticket])], ignore_index=True)
                    
                    # Salva a planilha inteira de volta no Google Sheets de forma segura
                    conn.update(data=df_atualizado)
                    st.success(f"Ticket #{id_ticket} gravado com sucesso na nuvem do Google!")
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
                    idx_original = df[df["ID Ticket"] == id_para_editar].index[0]
                    df.at[idx_original, "Status"] = novo_status
                    df.at[idx_original, "Data de Resolução"] = nova_data_res
                    
                    # Envia a atualização para a nuvem
                    conn.update(data=df)
                    st.success("Ticket atualizado no Google Sheets!")
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