import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import plotly.express as px
import plotly.graph_objects as go

# Cores da marca
CORES = {
    'primary': '#2a2b66',    # Azul escuro
    'secondary': '#5abebe',  # Verde água
    'dark': '#1b1938',      # Azul mais escuro
    'light': '#e5e4e7',     # Cinza claro
    'progress_good': '#5abebe',    # Verde água para progresso bom
    'progress_medium': '#2a2b66',  # Azul para progresso médio
    'progress_bad': '#1b1938'      # Azul escuro para progresso ruim
}

# Configuração da página
st.set_page_config(page_title="Dashboard OKRs - GROU", layout="wide")

# Estilos CSS atualizados com as cores da marca
st.markdown(f"""
    <style>
    .main {{
        background-color: {CORES['dark']};
    }}
    .metric-card {{
        background-color: {CORES['primary']};
        padding: 20px;
        border-radius: 10px;
        border: 1px solid {CORES['secondary']};
        margin: 10px 0;
    }}
    .objective-header {{
        background-color: {CORES['primary']};
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0;
        border-left: 5px solid {CORES['secondary']};
    }}
    .kr-title {{
        color: {CORES['secondary']};
        font-size: 1.1em;
        margin-bottom: 10px;
        font-weight: bold;
    }}
    .progress-label {{
        color: {CORES['light']};
        font-size: 0.9em;
        margin-top: 5px;
    }}
    .stProgress > div > div {{
        background-color: {CORES['secondary']};
    }}
    .status-indicator {{
        font-size: 24px;
        margin-top: 10px;
    }}
    .metric-value {{
        font-size: 1.8em;
        font-weight: bold;
        margin: 10px 0;
        color: {CORES['light']};
    }}
    .metric-target {{
        font-size: 1em;
        color: {CORES['secondary']};
    }}
    .description-text {{
        color: {CORES['light']};
        font-size: 0.9em;
        opacity: 0.8;
    }}
    .stSelectbox {{
        background-color: {CORES['primary']};
    }}
    .stMarkdown {{
        color: {CORES['light']};
    }}
    </style>
    """, unsafe_allow_html=True)

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
        
        RANGE_NAME = f"{aba}!A1:E50"
        
        result = sheet.values().get(
            spreadsheetId=SHEET_ID,
            range=RANGE_NAME
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            st.error(f'Nenhum dado encontrado na aba {aba}')
            return None
            
        data = []
        current_objective = None
        
        for row in values:
            if len(row) > 0:
                if 'OBJETIVO' in str(row[0]).upper():
                    current_objective = row[1] if len(row) > 1 else row[0]
                elif 'KR' in str(row[0]).upper():
                    row_data = row + [''] * (5 - len(row))
                    
                    kr_number = row[0].strip()
                    if 'KR' in kr_number.upper():
                        kr_number = kr_number.upper().replace('KR', '').strip()
                    
                    data.append({
                        'Objetivo': current_objective,
                        'KR': kr_number,
                        'Descrição': row[1],
                        'Valor Inicial': row[2] if len(row) > 2 else '0',
                        'Valor Atual': row[3] if len(row) > 3 else '0',
                        'Meta': row[4] if len(row) > 4 else '0'
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
    st.header(f"OKRs - Time {selected_team}")
    
    for objetivo in df['Objetivo'].unique():
        if objetivo is not None:
            # Cabeçalho do Objetivo
            st.markdown(f"""
                <div class="objective-header">
                    <h2 style="color: {CORES['light']}; margin: 0;">{objetivo}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            # Filtrar KRs do objetivo atual
            krs_obj = df[df['Objetivo'] == objetivo]
            
            # Criar grupos de KRs (3 por linha)
            for i in range(0, len(krs_obj), 3):
                cols = st.columns(3)
                krs_grupo = krs_obj.iloc[i:i+3]
                
                for idx, (_, kr) in enumerate(krs_grupo.iterrows()):
                    with cols[idx]:
                        try:
                            # Processamento dos valores
                            valor_atual = kr['Valor Atual'].replace('%', '').replace('R$', '').replace('.', '').replace(',', '.') if kr['Valor Atual'] else '0'
                            meta = kr['Meta'].replace('%', '').replace('R$', '').replace('.', '').replace(',', '.') if kr['Meta'] else '0'
                            
                            # Limpar e converter valores
                            valor_atual = float(valor_atual) if valor_atual else 0
                            meta = float(meta) if meta else 0
                            
                            # Calcular progresso
                            progresso = (valor_atual / meta * 100) if meta != 0 else 0
                            progresso = min(progresso, 100)
                            
                            # Determinar formato
                            is_percentage = '%' in str(kr['Meta'])
                            is_monetary = 'R$' in str(kr['Meta'])
                            
                            # Formatar valores para exibição
                            if is_percentage:
                                valor_display = f"{valor_atual:.1f}%"
                                meta_display = f"{meta:.1f}%"
                            elif is_monetary:
                                valor_display = f"R$ {valor_atual:,.2f}"
                                meta_display = f"R$ {meta:,.2f}"
                            else:
                                valor_display = f"{valor_atual:,.0f}"
                                meta_display = f"{meta:,.0f}"
                            
                            # Determinar cor do status baseado nas cores da marca
                            if progresso >= 100:
                                status_color = CORES['secondary']  # Verde água
                                status_icon = "●"
                            elif progresso >= 70:
                                status_color = CORES['primary']    # Azul
                                status_icon = "●"
                            else:
                                status_color = CORES['dark']      # Azul escuro
                                status_icon = "●"
                            
                            # Card do KR com as cores da marca
                            st.markdown(f"""
                                <div class="metric-card">
                                    <div class="kr-title">KR {kr['KR']} <span style="color: {status_color}">{status_icon}</span></div>
                                    <p class="description-text">{kr['Descrição']}</p>
                                    <div class="metric-value" style="color: {CORES['secondary']}">{valor_display}</div>
                                    <div class="metric-target">Meta: {meta_display}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Barra de progresso
                            st.progress(progresso/100)
                            st.markdown(f"""
                                <div class="progress-label">
                                    Progresso: {progresso:.1f}%
                                </div>
                                """, unsafe_allow_html=True)
                            
                        except Exception as e:
                            st.error(f"Erro ao processar KR {kr['KR']}: {str(e)}")

    # Gráfico de visão geral
    st.markdown(f"""
        <div class="objective-header">
            <h2 style="color: {CORES['light']}; margin: 0;">Visão Geral do Progresso</h2>
        </div>
        """, unsafe_allow_html=True)
    
    try:
        fig = go.Figure()
        
        for _, kr in df.iterrows():
            try:
                valor_atual = float(kr['Valor Atual'].replace('%', '').replace('R$', '').replace('.', '').replace(',', '.') if kr['Valor Atual'] else '0')
                meta = float(kr['Meta'].replace('%', '').replace('R$', '').replace('.', '').replace(',', '.') if kr['Meta'] else '0')
                progresso = (valor_atual / meta * 100) if meta != 0 else 0
                progresso = min(progresso, 100)
                
                # Cor baseada no progresso usando as cores da marca
                if progresso >= 100:
                    cor = CORES['secondary']  # Verde água
                elif progresso >= 70:
                    cor = CORES['primary']    # Azul
                else:
                    cor = CORES['dark']       # Azul escuro
                
                fig.add_trace(go.Bar(
                    name=f"KR {kr['KR']}",
                    x=[f"{kr['Descrição'][:30]}..."],
                    y=[progresso],
                    text=f"{progresso:.1f}%",
                    textposition='auto',
                    marker_color=cor
                ))
            except:
                continue
        
        fig.update_layout(
            title=f"Progresso dos KRs - {selected_team}",
            yaxis_title="Progresso (%)",
            yaxis_range=[0, 100],
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=CORES['light']),
            margin=dict(t=40, l=40, r=40, b=40)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar gráfico: {str(e)}")

# Rodapé
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: {CORES['light']};">
        Dashboard OKRs GROU • Atualizado automaticamente
    </div>
    """, unsafe_allow_html=True)
