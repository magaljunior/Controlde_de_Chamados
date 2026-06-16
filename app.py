import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import urllib.parse

# Configuração da página do Streamlit
st.set_page_config(page_title="Controle de Chamados", layout="wide")
st.title("🎫 Sistema de Controle de Chamados & Tickets")

# LINK DA SUA PLANILHA DO GOOGLE (Cole o link completo da sua planilha aqui)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1iYHbKKbFhZJ57FdHz9eHQdRvIVt9Y69SoHddZCkTcCQ/edit?gid=0#gid=0"

# Lista de setores e problemas padronizados (Corrigido o erro de sintaxe anterior)
SETORES = ["TI", "ADM FCN", "ADM ICN", "Biblioteca", "Central de Cópias", "Comunicação", "CPA", "Coordenações FCN", "Coordenações ICN", "Diretoria", "Eng. Elétrica", "Infraestrutura", "Núcleos", "Prof. FCN", "Prof. Icn", "RH", "Secretaria FCN", "Secretaria ICN", "Tesouraria"]
PROBLEMAS = ["Acesso ao Sistema", "Internet / Rede", "Hardware (Mouse, Teclado, Monitor)", "Impressora", "Instalação de Software", "E-mail", "Outros"]
COLUNAS_PADRAO = ["ID Ticket", "Data de Abertura", "Solicitante", "Setor Solicitante", "Categoria Problema", "Descrição", "Atendente", "Setor Atendente", "Status", "Data de Resolução"]

# Conversão do link para formato de exportação CSV nativo (Ignora travas de bibliotecas)
def obter_url_csv(url):
    if "docs.google.com/spreadsheets/d/" in url:
        id_planilha = url.split("/d/")[1].split("/")[0]
        return f"https://docs.google.com/spreadsheets/d/{id_planilha}/export?format=csv"
    return ""

# Função estável de leitura de dados
def carregar_dados():
    url_csv = obter_url_csv(URL_PLANILHA)
    if url_csv:
        try:
            # ttl="0" simulado limpando o cache do pandas nativamente
            df = pd.read_csv(url_csv, keep_default_na=False)
            if df.empty or "ID Ticket" not in df.columns:
                return pd.DataFrame(columns=COLUNAS_PADRAO)
            df['ID Ticket'] = df['ID Ticket'].astype(str)
            return df
        except Exception:
            return pd.DataFrame(columns=COLUNAS_PADRAO)
    return pd.DataFrame(columns=COLUNAS_PADRAO)

# Inicializa ou recarrega os dados na sessão do Streamlit
if 'df_chamados' not in st.session_state or st.sidebar.button("🔄 Atualizar Banco de Dados"):
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
                    
                    # Atualiza em tempo real na tela do usuário
                    st.session_state.df_chamados = pd.concat([df, pd.DataFrame([novo_ticket])], ignore_index=True)
                    
                    st.success(f"Ticket #{id_ticket} processado com sucesso!")
                    st.warning("⚠️ Nota: Para persistência definitiva na nuvem gratuita, use o download do CSV abaixo para atualizar sua planilha oficial se o app reiniciar.")
                    st.rerun()
            else:
                st.error("Por favor, preencha todos os campos obrigatórios.")

    st.write("---")
    st.header("Todos os Chamados Registrados")
    st.dataframe(st.session_state.df_chamados, use_container_width=True)
    
    # Botão de segurança para você nunca perder seu trabalho
    csv_backup = st.session_state.df_chamados.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Backup dos Dados (Excel/CSV)", csv_backup, "backup_chamados.csv", "text/csv")

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
                    st.session_state.df_chamados = df
                    st.success("Ticket atualizado temporariamente na sessão!")
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
