import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# Configuração da página do Streamlit
st.set_page_config(page_title="Controle de Chamados", layout="wide")
st.title("🎫 Sistema de Controle de Chamados & Tickets")

# Nome do arquivo onde os dados serão salvos
ARQUIVO_DADOS = "dados_chamados.csv"

# Lista de setores e problemas padronizados para o formulário e gráficos
SETORES = ["TI", "ADM FCN", "ADM ICN", "Biblioteca", "Central de Cópias", "Comunicação", "CPA", "Coordenações FCN", "Coordenações ICN", "Diretoria", "Eng. Elétrica", "Infraestrutura",  "Núcleos", "Prof. FCN", "Prof. Icn",  "Núcleos", "RH", "Secretaria FCN", "Secretaria ICN", "Tesouraria"]
PROBLEMAS = ["Acesso ao Sistema", "Internet / Rede", "Hardware (Mouse, Teclado, Monitor)", "Impressora", "Instalação de Software", "E-mail", "Outros"]

# Função para carregar os dados salvos
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        df = pd.read_csv(ARQUIVO_DADOS)
        # Garante que as datas sejam lidas corretamente
        df['Data de Abertura'] = pd.to_datetime(df['Data de Abertura']).dt.date
        return df
    else:
        # Se o arquivo não existir, cria um DataFrame vazio com as colunas necessárias
        return pd.DataFrame(columns=[
            "ID Ticket", "Data de Abertura", "Solicitante", "Setor Solicitante", 
            "Categoria Problema", "Descrição", "Atendente", "Setor Atendente", 
            "Status", "Data de Resolução"
        ])

# Função para salvar os dados
def salvar_dados(df):
    df.to_csv(ARQUIVO_DADOS, index=False)

# Inicializa o estado dos dados no Streamlit
if 'df_chamados' not in st.session_state:
    st.session_state.df_chamados = carregar_dados()

# Criando abas no sistema: uma para gerenciar e outra para ver os gráficos
aba_cadastro, aba_dashboard = st.tabs(["📝 Novo Chamado / Gerenciar", "📊 Gráficos e Indicadores"])

# -------------------------------------------------------------------------
# ABA 1: CADASTRO E GERENCIAMENTO
# -------------------------------------------------------------------------
with aba_cadastro:
    st.header("Registrar Novo Ticket")
    
    # Formulário de entrada de dados
    with st.form("form_chamado", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            id_ticket = st.text_input("ID do Ticket (Digite manualmente)") # <-- ADICIONADO AQUI
            solicitante = st.text_input("Nome do Solicitante")
            setor_solicitante = st.selectbox("Setor do Solicitante", SETORES)
            categoria = st.selectbox("Categoria do Problema", PROBLEMAS)
            descricao = st.text_area("Descrição detalhada do chamado")
            
        with col2:
            atendente = st.text_input("Nome do Atendente")
            setor_atendente = st.selectbox("Setor do Atendente", SETORES)
            status = st.selectbox("Status Inicial", ["Aberto", "Em Andamento", "Resolvido"])
            data_abertura = st.date_input("Data de Abertura", datetime.today().date())
            
            # Se já nascer resolvido, pede a data de resolução
            if status == "Resolvido":
                data_resolucao = st.date_input("Data de Resolução", datetime.today().date())
            else:
                data_resolucao = ""

        botao_salvar = st.form_submit_button("Salvar Chamado")
        
        if botao_salvar:
            # Validando se o ID também foi digitado
            if id_ticket and solicitante and descricao and atendente:
                             
                # Criar nova linha utilizando a variável id_ticket digitada
                novo_ticket = {
                    "ID Ticket": id_ticket, # <-- CORRIGIDO AQUI
                    "Data de Abertura": data_abertura,
                    "Solicitante": solicitante,
                    "Setor Solicitante": setor_solicitante,
                    "Categoria Problema": categoria,
                    "Descrição": descricao,
                    "Atendente": atendente,
                    "Setor Atendente": setor_atendente,
                    "Status": status,
                    "Data de Resolução": data_resolucao if status == "Resolvido" else "Pendente"
                }
                
                # Adicionar aos dados e salvar
                st.session_state.df_chamados = pd.concat([st.session_state.df_chamados, pd.DataFrame([novo_ticket])], ignore_index=True)
                salvar_dados(st.session_state.df_chamados)
                st.success(f"Ticket #{id_ticket} criado com sucesso!") # <-- CORRIGIDO AQUI
                st.rerun()
            else:
                st.error("Por favor, preencha os campos obrigatórios (ID do Ticket, Solicitante, Atendente e Descrição).")

    # Exibição da tabela de chamados atuais
    st.write("---")
    st.header("Todos os Chamados Registrados")
    if not st.session_state.df_chamados.empty:
        st.dataframe(st.session_state.df_chamados, use_container_width=True)
        
        # Opção simples para limpar os dados se necessário
        if st.button("Limpar todos os registros (Resetar sistema)"):
            st.session_state.df_chamados = pd.DataFrame(columns=st.session_state.df_chamados.columns)
            if os.path.exists(ARQUIVO_DADOS):
                os.remove(ARQUIVO_DADOS)
            st.rerun()
    else:
        st.info("Nenhum chamado cadastrado ainda.")

# -------------------------------------------------------------------------
# ABA 2: DASHBOARD (TODOS OS GRÁFICOS PEDIDOS)
# -------------------------------------------------------------------------
with aba_dashboard:
    st.header("Painel de Indicadores (Dashboard)")
    
    df = st.session_state.df_chamados
    
    if df.empty:
        st.warning("Adicione chamados na primeira aba para visualizar os gráficos aqui.")
    else:
        # Métricas Rápidas no Topo
        total_tickets = len(df)
        abertos = len(df[df["Status"] == "Aberto"])
        resolvidos = len(df[df["Status"] == "Resolvido"])
        em_andamento = len(df[df["Status"] == "Em Andamento"])
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total de Chamados", total_tickets)
        m2.metric("🟢 Abertos", abertos)
        m3.metric("🟡 Em Andamento", em_andamento)
        m4.metric("🔵 Solucionados", resolvidos)
        
        st.write("---")
        
        # 1. Gráfico de Tickets por Status (Abertos vs Solucionados)
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("Situação dos Tickets (Status)")
            fig_status = px.pie(df, names="Status", title="Proporção de Tickets por Status", hole=0.4,
                                color_discrete_map={"Aberto": "#EF553B", "Em Andamento": "#FECB52", "Resolvido": "#636EFA"})
            st.plotly_chart(fig_status, use_container_width=True)
            
        with col_g2:
            # 2. Gráfico de mais problemas que foram abertos (Gargalos)
            st.subheader("Mais Problemas (Categorias)")
            df_prob = df["Categoria Problema"].value_counts().reset_index()
            df_prob.columns = ["Problema", "Quantidade"]
            fig_prob = px.bar(df_prob, x="Quantidade", y="Problema", orientation='h', 
                             title="Principais Problemas Relatados", text_auto=True)
            st.plotly_chart(fig_prob, use_container_width=True)

        st.write("---")
        
        col_g3, col_g4 = st.columns(2)
        
        with col_g3:
            # 3. Gráfico de setores que mais abrem chamados
            st.subheader("Setores que mais abrem chamados")
            df_setor_sol = df["Setor Solicitante"].value_counts().reset_index()
            df_setor_sol.columns = ["Setor Solicitante", "Quantidade"]
            fig_sol = px.bar(df_setor_sol, x="Setor Solicitante", y="Quantidade", 
                             title="Demandas por Setor Solicitante", text_auto=True, color="Quantidade")
            st.plotly_chart(fig_sol, use_container_width=True)
            
        with col_g4:
            # 4. Gráfico de setor do atendente
            st.subheader("Chamados por Setor do Atendente")
            df_setor_at = df["Setor Atendente"].value_counts().reset_index()
            df_setor_at.columns = ["Setor Atendente", "Quantidade"]
            fig_at = px.pie(df_setor_at, names="Setor Atendente", values="Quantidade", 
                            title="Volume de Trabalho por Setor de Atendimento")
            st.plotly_chart(fig_at, use_container_width=True)

        st.write("---")
        
        # 5. Análise da Descrição dos Chamados
        st.subheader("📋 Detalhes das Descrições dos Chamados")
        st.write("Como a 'Descrição' é um campo de texto livre, listamos abaixo os termos e chamados para análise direta:")
        st.dataframe(df[["ID Ticket", "Categoria Problema", "Descrição", "Status"]], use_container_width=True)
