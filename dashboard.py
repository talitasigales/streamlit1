import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide"
)

# Estilo personalizado
st.markdown("""
    <style>
    .main {
        padding: 20px;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.title("📊 Dashboard Interativo")

# Sidebar
with st.sidebar:
    st.header("Configurações")
    uploaded_file = st.file_uploader("Upload do arquivo CSV", type=['csv'])

# Layout principal
if uploaded_file is not None:
    # Leitura dos dados
    df = pd.read_csv(uploaded_file)
    
    # Métricas principais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Registros", len(df))
    with col2:
        st.metric("Número de Colunas", len(df.columns))
    with col3:
        st.metric("Período de Dados", f"{len(df)} períodos")

    # Tabs para diferentes visualizações
    tab1, tab2, tab3 = st.tabs(["📈 Gráficos", "🗃 Dados", "📊 Análise"])
    
    with tab1:
        st.subheader("Visualização de Dados")
        # Seletor de colunas para o gráfico
        colunas_numericas = df.select_dtypes(include=['float64', 'int64']).columns
        coluna_selecionada = st.selectbox("Selecione uma coluna para análise:", colunas_numericas)
        
        # Gráfico de linha
        fig = px.line(df, y=coluna_selecionada, title=f'Evolução de {coluna_selecionada}')
        st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de barras
        fig2 = px.bar(df, y=coluna_selecionada, title=f'Distribuição de {coluna_selecionada}')
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.subheader("Dados Brutos")
        st.dataframe(df, use_container_width=True)
        
        # Botão de download
        st.download_button(
            label="Download dos dados",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name='dados.csv',
            mime='text/csv'
        )
    
    with tab3:
        st.subheader("Análise Estatística")
        st.write("Estatísticas Descritivas:")
        st.write(df.describe())

else:
    # Mensagem quando nenhum arquivo foi carregado
    st.info("👆 Por favor, faça upload de um arquivo CSV para começar a análise")
    
    # Exemplo de como os dados devem estar formatados
    st.markdown("""
    ### Como usar este dashboard:
    1. Prepare seus dados em formato CSV
    2. Use o botão de upload no menu lateral
    3. Explore as visualizações nas diferentes abas
    
    #### Formato esperado do CSV:
    - Dados organizados em colunas
    - Primeira linha com os nomes das colunas
    - Valores numéricos para análise
    """)

# Rodapé
st.markdown("---")
st.markdown("Dashboard criado com Streamlit • Desenvolvido por [Grou]")
