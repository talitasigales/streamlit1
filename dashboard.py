import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Grou - OKRs 2025", layout="wide")

# Configurações do Google Sheets
SHEET_ID = '1g-6qI3WKVJ97TzSH61vCjcUuyEUTFxNVGCk9UlCRIqk'  # Seu ID da planilha
RANGE_NAME = 'MarketingDashboard!A1:F1000'  # Ajuste o range conforme sua planilha

# Função para ler dados do Google Sheets
@st.cache_data(ttl=600)
def load_data():
    try:
        # Configurar credenciais
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        
        # Criar serviço
        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()
        
        # Ler dados
        result = sheet.values().get(
            spreadsheetId=SHEET_ID,
            range=RANGE_NAME
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            st.error('Nenhum dado encontrado na planilha.')
            return None
            
        # Converter para DataFrame
        df = pd.DataFrame(values[1:], columns=values[0])
        
        # Converter colunas numéricas
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass
                
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

# Interface do Dashboard
st.title("📊 Grou - OKRs 2025")

# Carregar dados
df = load_data()

if df is not None:
    # Sidebar com filtros
    st.sidebar.header("Filtros")
    
    # Selecionar colunas para análise
    colunas_numericas = df.select_dtypes(include=['float64', 'int64']).columns
    coluna_selecionada = st.sidebar.selectbox("Selecione uma métrica:", colunas_numericas)
    
    # Layout principal
    col1, col2, col3 = st.columns(3)
    
    # Métricas principais
    with col1:
        st.metric("Total de Registros", len(df))
    with col2:
        if coluna_selecionada:
            st.metric("Média", f"{df[coluna_selecionada].mean():.2f}")
    with col3:
        if coluna_selecionada:
            st.metric("Total", f"{df[coluna_selecionada].sum():.2f}")
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3 = st.tabs(["📈 Gráficos", "🗃 Dados", "📊 Análise"])
    
    with tab1:
        if coluna_selecionada:
            # Gráfico de linha
            fig1 = px.line(df, y=coluna_selecionada, 
                          title=f'Evolução de {coluna_selecionada}')
            st.plotly_chart(fig1, use_container_width=True)
            
            # Gráfico de barras
            fig2 = px.bar(df, y=coluna_selecionada, 
                         title=f'Distribuição de {coluna_selecionada}')
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.dataframe(df, use_container_width=True)
        
        # Botão de download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download CSV",
            csv,
            "dados.csv",
            "text/csv",
            key='download-csv'
        )
    
    with tab3:
        st.write("Estatísticas Descritivas:")
        st.write(df.describe())

# Rodapé
st.markdown("---")
st.markdown("Dashboard conectado ao Google Sheets")
