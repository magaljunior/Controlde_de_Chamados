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
        # Força o ID Ticket a ser tratado como texto para evitar problemas de busca
        df['ID Ticket'] = df['ID Ticket'].astype(str)
        return df
    else:
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

# Criando as ABAS no sistema (Agora com a aba de pesquisa)
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
                # Verifica se o ID já existe para não duplicar na aba de cadastro
                if id_ticket in st.session_state.df_chamados["ID Ticket"].values:
                    st.error(f"O ID Ticket #{id_ticket} já existe! Use outro ID ou edite-o na aba de Pesquisa.")
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
                    
                    st.session_state.df_chamados = pd.concat([st.session_state.df_chamados, pd.DataFrame([novo_ticket])], ignore_index=True)
                    salvar_dados(st.session_state.df_chamados)
                    st.success(f"Ticket #{id_ticket} criado com sucesso!")
                    st.rerun()
            else:
                st.error("Por favor, preencha os campos obrigatórios (ID do Ticket, Solicitante, Atendente e Descrição).")

    st.write("---")
    st.header("Todos os Chamados Registrados")
    if not st.session_state.df_chamados.empty:
        st.dataframe(st.session_state.df_chamados, use_container_width=True)
        
        if st.button("Limpar todos os registros (Resetar sistema)"):
            st.session_state.df_chamados = pd.DataFrame(columns=st.session_state.df_chamados.columns)
            if os.path.exists(ARQUIVO_DADOS):
                os.remove(ARQUIVO_DADOS)
            st.rerun()
    else:
        st.info("Nenhum chamado cadastrado ainda.")


# -------------------------------------------------------------------------
# NOVA ABA 2: PESQUISAR E EDITAR TICKETS
# -------------------------------------------------------------------------
with aba_pesquisa:
    st.header("🔍 Painel de Busca e Edição")
    
    if st.session_state.df_chamados.empty:
        st.info("Nenhum ticket cadastrado para pesquisa.")
    else:
        # Filtros de pesquisa no topo
        col_busca1, col_busca2, col_busca3 = st.columns(3)
        
        with col_busca1:
            busca_id = st.text_input("Buscar por ID do Ticket")
        with col_busca2:
            busca_solicitante = st.text_input("Buscar por Nome do Solicitante")
        with col_busca3:
            busca_status = st.selectbox("Filtrar por Status", ["Todos", "Aberto", "Em Andamento", "Resolvido"])
            
        # Aplicando os filtros no banco de dados
        df_filtrado = st.session_state.df_chamados.copy()
        
        if busca_id:
            df_filtrado = df_filtrado[df_filtrado["ID Ticket"].str.contains(busca_id, case=False, na=False)]
        if busca_solicitante:
            df_filtrado = df_filtrado[df_filtrado["Solicitante"].str.contains(busca_solicitante, case=False, na=False)]
        if busca_status != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Status"] == busca_status]
            
        st.write(f"Resultados encontrados: {len(df_filtrado)}")
        st.dataframe(df_filtrado, use_container_width=True)
        
        # 🛠️ SEÇÃO PARA EDITAR UM TICKET ESPECÍFICO
        st.write("---")
        st.subheader("📝 Atualizar ou Editar um Ticket")
        
        id_para_editar = st.selectbox("Selecione o ID do Ticket que deseja alterar:", [""] + list(df_filtrado["ID Ticket"].unique()))
        
        if id_para_editar != "":
            # Puxa os dados atuais do ticket selecionado
            dados_ticket = st.session_state.df_chamados[st.session_state.df_chamados["ID Ticket"] == id_para_editar].iloc[0]
            
            # Cria um formulário preenchido com as informações atuais para edição
            with st.form("form_edicao"):
                st.info(f"Editando o Ticket #{id_para_editar} (Aberto em: {dados_ticket['Data de Abertura']})")
                
                ed_col1, ed_col2 = st.columns(2)
                
                with ed_col1:
                    novo_solicitante = st.text_input("Solicitante", value=dados_ticket["Solicitante"])
                    # Encontra a posição atual do setor na lista para deixar selecionado
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
                    
                    # Logica da data de resolução na edição
                    data_res_atual = datetime.today().date()
                    if novo_status == "Resolvido":
                        novo_data_resolucao = st.date_input("Data de Resolução", data_res_atual)
                    else:
                        novo_data_resolucao = "Pendente"
                
                botao_atualizar = st.form_submit_button("Atualizar Ticket")
                
                if botao_atualizar:
                    # Encontra o índice da linha original no banco de dados e atualiza os campos
                    idx_original = st.session_state.df_chamados[st.session_state.df_chamados["ID Ticket"] == id_para_editar].index[0]
                    
                    st.session_state.df_chamados.at[idx_original, "Solicitante"] = novo_solicitante
                    st.session_state.df_chamados.at[idx_original, "Setor Solicitante"] = novo_setor_solicitante
                    st.session_state.df_chamados.at[idx_original, "Categoria Problema"] = nova_categoria
                    st.session_state.df_chamados.at[idx_original, "Descrição"] = nova_descricao
                    st.session_state.df_chamados.at[idx_original, "Atendente"] = novo_atendente
                    st.session_state.df_chamados.at[idx_original, "Setor Atendente"] = novo_setor_atendente
                    st.session_state.df_chamados.at[idx_original, "Status"] = novo_status
                    st.session_state.df_chamados.at[idx_original, "Data de Resolução"] = str(novo_data_resolucao)
                    
                    salvar_dados(st.session_state.df_chamados)
                    st.success(f"Ticket #{id_para_editar} atualizado com sucesso!")
                    st.rerun()


# -------------------------------------------------------------------------
# ABA 3: DASHBOARD (GRÁFICOS)
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
        
        # 1. Gráfico de Tickets por Status
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("Situação dos Tickets (Status)")
            fig_status = px.pie(df, names="Status", title="Proporção de Tickets por Status", hole=0.4,
                                color_discrete_map={"Aberto": "#EF553B", "Em Andamento": "#FECB52", "Resolvido": "#636EFA"})
            st.plotly_chart(fig_status, use_container_width=True)
            
        with col_g2:
            # 2. Gráfico de mais problemas
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

