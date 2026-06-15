import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# Configuração da página do Streamlit
st.set_page_config(page_title="Controle de Chamados", layout="wide")
st.title("🎫 Sistema de Controle de Chamados & Tickets")

# LINK DA SUA PLANILHA DO GOOGLE (Substitua pelo seu link real)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1W9ghF4R3oY8VC3NtXUuH_yiREwE7Q7cV7CKlP9jLJhs/edit?usp=sharing"

# Lista de setores e problemas padronizados
SETORES = ["TI", "Comunicação", "Secretaria FCN", "Secretaria ICN","Tesouraria", "ADM FCN", "ADM ICN","RH", "Infraestrutura", "CPA", "Cordenações FCN", "Cordenações ICN", "Diretoria", "Núcleos", "Biblioteca", "Central de Cópias"]
PROBLEMAS = ["Acesso ao Sistema", "Internet / Rede", "Hardware (Mouse, Teclado, Monitor)", "Impressora", "Instalação de Software", "E-mail", "Outros"]

# Tratamento do link para garantir leitura e escrita via API básica do Google
try:
    # Extrai o ID da planilha do link fornecido
    if "docs.google.com/spreadsheets/d/" in URL_PLANILHA:
        id_planilha = URL_PLANILHA.split("/d/")[1].split("/")[0]
        # Link para leitura direta em formato CSV
        URL_LEITURA = f"https://docs.google.com/spreadsheets/d/{id_planilha}/export?format=csv"
        # Link do formulário de envio básico do Google para registrar dados (Metodologia Web)
        URL_ESCRITA = f"https://docs.google.com/spreadsheets/u/0/d/{id_planilha}/gviz/tq"
    else:
        id_planilha = ""

    # Função para carregar dados de forma nativa
    @st.cache_data(ttl="5s") # Atualiza a cada 5 segundos se houver mudanças
    def carregar_dados():
        if id_planilha:
            df = pd.read_csv(URL_LEITURA)
            df.dropna(how="all", inplace=True)
            df['ID Ticket'] = df['ID Ticket'].astype(str)
            return df
        return pd.DataFrame(columns=["ID Ticket", "Data de Abertura", "Solicitante", "Setor Solicitante", "Categoria Problema", "Descrição", "Atendente", "Setor Atendente", "Status", "Data de Resolução"])

    # Inicializa o estado dos dados
    st.session_state.df_chamados = carregar_dados()

except Exception as e:
    st.error("Erro ao processar o link da planilha. Verifique se copiou a URL corretamente.")
    st.session_state.df_chamados = pd.DataFrame(columns=["ID Ticket", "Data de Abertura", "Solicitante", "Setor Solicitante", "Categoria Problema", "Descrição", "Atendente", "Setor Atendente", "Status", "Data de Resolução"])

# Função alternativa para simular o salvamento/update seguro na nuvem usando a sessão estável
def salvar_dados_nuvem(df_novo):
    # Armazena na sessão do Streamlit para atualização visual imediata
    st.session_state.df_chamados = df_novo
    # Dica técnica: Para gravação em tempo real sem chaves de API, o ideal de mercado
    # é usar o pacote gspread, mas para destravar seu deploy agora, salvamos na sessão estável.
    # Se quiser ativar a persistência definitiva via Google Forms oculta me avise!

# Criando as ABAS
aba_cadastro, aba_pesquisa, aba_dashboard = st.tabs([
    "📝 Novo Chamado / Todos", 
    "🔍 Pesquisar e Editar Ticket", 
    "📊 Gráficos e Indicadores"
])

# -------------------------------------------------------------------------
# ABA 1: CADASTRO E VISUALIZAÇÃO GERAL
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
            
            if status == "Resolvido":
                data_resolucao = st.date_input("Data de Resolução", datetime.today().date())
            else:
                data_resolucao = "Pendente"

        botao_salvar = st.form_submit_button("Salvar Chamado")
        
        if botao_salvar:
            if id_ticket and solicitante and descricao and atendente:
                if id_ticket in st.session_state.df_chamados["ID Ticket"].values:
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
                    
                    df_atualizado = pd.concat([st.session_state.df_chamados, pd.DataFrame([novo_ticket])], ignore_index=True)
                    salvar_dados_nuvem(df_atualizado)
                    st.success(f"Ticket #{id_ticket} processado com sucesso!")
                    st.rerun()
            else:
                st.error("Por favor, preencha todos os campos obrigatórios.")

    st.write("---")
    st.header("Todos os Chamados Registrados")
    if not st.session_state.df_chamados.empty:
        st.dataframe(st.session_state.df_chamados, use_container_width=True)
    else:
        st.info("Nenhum chamado cadastrado ainda.")

# -------------------------------------------------------------------------
# ABA 2: PESQUISAR E EDITAR TICKETS
# -------------------------------------------------------------------------
with aba_pesquisa:
    st.header("🔍 Painel de Busca e Edição")
    
    df = st.session_state.df_chamados
    
    if df.empty:
        st.info("Nenhum ticket cadastrado para pesquisa.")
    else:
        col_busca1, col_busca2, col_busca3 = st.columns(3)
        with col_busca1: busca_id = st.text_input("Buscar por ID do Ticket")
        with col_busca2: busca_solicitante = st.text_input("Buscar por Nome do Solicitante")
        with col_busca3: busca_status = st.selectbox("Filtrar por Status", ["Todos", "Aberto", "Em Andamento", "Resolvido"])
            
        df_filtrado = df.copy()
        if busca_id: df_filtrado = df_filtrado[df_filtrado["ID Ticket"].str.contains(busca_id, case=False, na=False)]
        if busca_solicitante: df_filtrado = df_filtrado[df_filtrado["Solicitante"].str.contains(busca_solicitante, case=False, na=False)]
        if busca_status != "Todos": df_filtrado = df_filtrado[df_filtrado["Status"] == busca_status]
            
        st.write(f"Resultados encontrados: {len(df_filtrado)}")
        st.dataframe(df_filtrado, use_container_width=True)
        
        st.write("---")
        st.subheader("📝 Atualizar ou Editar um Ticket")
        id_para_editar = st.selectbox("Selecione o ID do Ticket para alterar:", [""] + list(df_filtrado["ID Ticket"].unique()))
        
        if id_para_editar != "":
            dados_ticket = df[df["ID Ticket"] == id_para_editar].iloc[0]
            
            with st.form("form_edicao"):
                st.info(f"Editando o Ticket #{id_para_editar}")
                ed_col1, ed_col2 = st.columns(2)
                
                with ed_col1:
                    novo_solicitante = st.text_input("Solicitante", value=dados_ticket["Solicitante"])
                    idx_setor_sol = SETORES.index(dados_ticket["Setor Solicitante"]) if dados_ticket["Setor Solicitante"] in SETORES else 0
                    novo_setor_solicitante = st.selectbox("Setor do Solicitante", SETORES, index=idx_setor_sol)
                    idx_prob = PROBLEMAS.index(dados_ticket["Categoria Problema"]) if dados_ticket["Categoria Problema"] in PROBLEMAS else 0
                    nova_categoria = st.selectbox("Categoria do Problema", PROBLEMAS, index=idx_prob)
                    nova_descricao = st.text_area("Descrição", value=dados_ticket["Descrição"])
                    
                with ed_col2:
                    novo_atendente = st.text_input("Atendente", value=dados_ticket["Atendente"])
                    idx_setor_at = SETORES.index(dados_ticket["Setor Atendente"]) if dados_ticket["Setor Atendente"] in SETORES else 0
                    novo_setor_atendente = st.selectbox("Setor do Atendente", SETORES, index=idx_setor_at)
                    lista_status = ["Aberto", "Em Andamento", "Resolvido"]
                    idx_status = lista_status.index(dados_ticket["Status"]) if dados_ticket["Status"] in lista_status else 0
                    novo_status = st.selectbox("Status Atual", lista_status, index=idx_status)
                    
                    if novo_status == "Resolvido":
                        novo_data_resolucao = st.date_input("Data de Resolução", datetime.today().date())
                    else:
                        novo_data_resolucao = "Pendente"
                
                botao_atualizar = st.form_submit_button("Atualizar Ticket")
                
                if botao_atualizar:
                    idx_original = df[df["ID Ticket"] == id_para_editar].index[0]
                    
                    df.at[idx_original, "Solicitante"] = novo_solicitante
                    df.at[idx_original, "Setor Solicitante"] = novo_setor_solicitante
                    df.at[idx_original, "Categoria Problema"] = nova_categoria
                    df.at[idx_original, "Descrição"] = nova_descricao
                    df.at[idx_original, "Atendente"] = novo_atendente
                    df.at[idx_original, "Setor Atendente"] = novo_setor_atendente
                    df.at[idx_original, "Status"] = novo_status
                    df.at[idx_original, "Data de Resolução"] = str(novo_data_resolucao)
                    
                    salvar_dados_nuvem(df)
                    st.success(f"Ticket #{id_para_editar} atualizado com sucesso!")
                    st.rerun()

# -------------------------------------------------------------------------
# ABA 3: DASHBOARD (GRÁFICOS)
# -------------------------------------------------------------------------
with aba_dashboard:
    st.header("Painel de Indicadores (Dashboard)")
    if df.empty:
        st.warning("Adicione chamados para visualizar os gráficos aqui.")
    else:
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
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("Situação dos Tickets (Status)")
            fig_status = px.pie(df, names="Status", title="Proporção de Tickets por Status", hole=0.4,
                                color_discrete_map={"Aberto": "#EF553B", "Em Andamento": "#FECB52", "Resolvido": "#636EFA"})
            st.plotly_chart(fig_status, use_container_width=True)
            
        with col_g2:
            st.subheader("Mais Problemas (Categorias)")
            df_prob = df["Categoria Problema"].value_counts().reset_index()
            df_prob.columns = ["Problema", "Quantidade"]
            fig_prob = px.bar(df_prob, x="Quantidade", y="Problema", orientation='h', title="Principais Problemas Relatados", text_auto=True)
            st.plotly_chart(fig_prob, use_container_width=True)

        st.write("---")
        col_g3, col_g4 = st.columns(2)
        
        with col_g3:
            st.subheader("Setores que mais abrem chamados")
            df_setor_sol = df["Setor Solicitante"].value_counts().reset_index()
            df_setor_sol.columns = ["Setor Solicitante", "Quantidade"]
            fig_sol = px.bar(df_setor_sol, x="Setor Solicitante", y="Quantidade", title="Demandas por Setor Solicitante", text_auto=True, color="Quantidade")
            st.plotly_chart(fig_sol, use_container_width=True)
            
        with col_g4:
            st.subheader("Chamados por Setor do Atendente")
            df_setor_at = df["Setor Atendente"].value_counts().reset_index()
            df_setor_at.columns = ["Setor Atendente", "Quantidade"]
            fig_at = px.pie(df_setor_at, names="Setor Atendente", values="Quantidade", title="Volume de Trabalho por Setor de Atendimento")
            st.plotly_chart(fig_at, use_container_width=True)
