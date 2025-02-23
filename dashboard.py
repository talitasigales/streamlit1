import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="Dashboard OKRs - GROU", layout="wide")

# Configurações do Google Sheets
SHEET_ID = '1w8ciieZ_r3nYkYROZ0RpubATJZ6NWdDOmDZQMUV4Mac'
TIMES = ['Marketing', 'Comercial', 'Trainers', 'SDR', 'ADM', 'CS']

def load_data(aba):
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()
        
        # Range configurado para ler:
        # A: Coluna de KRs/Objetivos
        # B: Descrição
        # C: Valor Inicial
        # D: Valor Atual
        # E: Meta
        # F: Observações (se houver)
        RANGE_NAME = f"{aba}!A1:F50"
        
        result = sheet.values().get(
            spreadsheetId=SHEET_ID,
            range=RANGE_NAME
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            st.error(f'Nenhum dado encontrado na aba {aba}')
            return None
            
        # Criar DataFrame com estrutura específica para OKRs
        data = []
        current_objective = None
        
        for row in values[1:]:  # Pular cabeçalho
            if len(row) > 0:  # Verificar se a linha não está vazia
                if 'OBJETIVO' in row[0]:
                    current_objective = row[1] if len(row) > 1 else row[0]
                elif row[0].strip().startswith('KR'):  # Identificar linhas de KR
                    # Garantir que todas as colunas existam
                    while len(row) < 5:
                        row.append('')
                    
                    data.append({
                        'Objetivo': current_objective,
                        'KR': row[0],
                        'Descrição': row[1],
                        'Valor Inicial': row[2],
                        'Valor Atual': row[3],
                        'Meta': row[4]
                    })
        
        df = pd.DataFrame(data)
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

# Interface do Dashboard
st.title("📊 Dashboard OKRs GROU 2025")

# Botão de atualização no canto superior direito
col1, col2, col3 = st.columns([1,1,1])
with col3:
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

# Seletor de Time na sidebar
selected_team = st.sidebar.selectbox("Selecione o Time", TIMES)

# Carregar dados do time selecionado
df = load_data(selected_team)

if df is not None:
    # Mostrar progresso geral do time
    st.header(f"OKRs - Time {selected_team}")
    
    # Para cada objetivo
    for objetivo in df['Objetivo'].unique():
        st.subheader(objetivo)
        
        # Filtrar KRs do objetivo atual
        krs_obj = df[df['Objetivo'] == objetivo]
        
        # Definir número máximo de colunas por linha
        max_cols = 3  # Você pode ajustar este número
        
        # Criar grupos de KRs para distribuir em linhas
        for i in range(0, len(krs_obj), max_cols):
            # Pegar um grupo de KRs
            krs_grupo = krs_obj.iloc[i:i+max_cols]
            
            # Criar colunas para este grupo
            cols = st.columns(max_cols)
            
            # Preencher as colunas com os KRs
            for idx, (_, kr) in enumerate(krs_grupo.iterrows()):
                with cols[idx]:
                    try:
                        # Converter valores para numéricos, removendo símbolos
                        valor_atual = kr['Valor Atual'].replace('%', '').replace('R$', '').replace('.', '').replace(',', '.') if kr['Valor Atual'] else '0'
                        meta = kr['Meta'].replace('%', '').replace('R$', '').replace('.', '').replace(',', '.') if kr['Meta'] else '0'
                        
                        # Converter para float se não estiver vazio
                        valor_atual = float(valor_atual) if valor_atual else 0
                        meta = float(meta) if meta else 0
                        
                        # Calcular progresso
                        progresso = (valor_atual / meta * 100) if meta != 0 else 0
                        progresso = min(progresso, 100)  # Limitar a 100%
                        
                        # Determinar se o valor é percentual ou monetário
                        is_percentage = '%' in str(kr['Meta'])
                        is_monetary = 'R$' in str(kr['Meta'])
                        
                        # Formatar valor atual e meta
                        if is_percentage:
                            valor_display = f"{valor_atual:.1f}%"
                            meta_display = f"{meta:.1f}%"
                        elif is_monetary:
                            valor_display = f"R$ {valor_atual:,.2f}"
                            meta_display = f"R$ {meta:,.2f}"
                        else:
                            valor_display = f"{valor_atual:,.0f}"
                            meta_display = f"{meta:,.0f}"
                        
                        # Mostrar métrica
                        st.metric(
                            f"KR {kr['KR']}",
                            valor_display,
                            f"Meta: {meta_display}"
                        )
                        
                        # Barra de progresso
                        st.progress(progresso/100)
                        
                        # Descrição do KR
                        st.write(kr['Descrição'])
                    except Exception as e:
                        st.write(f"KR {kr['KR']}: {kr['Descrição']}")
                        st.write(f"Erro no processamento dos valores: {str(e)}")
    
    # Visão geral em tabela
    st.subheader("Visão Geral dos KRs")
    st.dataframe(df, use_container_width=True)
    
    # Gráfico de progresso
    try:
        fig = go.Figure()
        
        for _, kr in df.iterrows():
            try:
                valor_atual = float(kr['Valor Atual'].replace('%', '').replace('R$', '').replace('.', '').replace(',', '.') if kr['Valor Atual'] else '0')
                meta = float(kr['Meta'].replace('%', '').replace('R$', '').replace('.', '').replace(',', '.') if kr['Meta'] else '0')
                progresso = (valor_atual / meta * 100) if meta != 0 else 0
                progresso = min(progresso, 100)  # Limitar a 100%
                
                fig.add_trace(go.Bar(
                    name=kr['KR'],
                    x=[kr['Descrição'][:50] + '...'],  # Truncar descrições muito longas
                    y=[progresso],
                    text=f"{progresso:.1f}%",
                    textposition='auto',
                ))
            except:
                continue
        
        fig.update_layout(
            title=f"Progresso dos KRs - {selected_team}",
            yaxis_title="Progresso (%)",
            yaxis_range=[0, 100],
            height=400,
            showlegend=False,
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar gráfico: {str(e)}")

# Rodapé
st.markdown("---")
st.markdown("Dashboard OKRs GROU • Atualizado automaticamente")
