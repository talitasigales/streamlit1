import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import plotly.express as px
import plotly.graph_objects as go

# Cores da marca
CORES = {
    'background': '#1b1938',  # Background geral
    'accent': '#5abebe',      # Cor de destaque
    'card': '#2a2b66',        # Cor dos cards
    'light': '#e5e4e7',      # Cor clara
    'white': '#ffffff'        # Branco
}

# Configuração da página
st.set_page_config(page_title="Dashboard OKRs - GROU", layout="wide")

# Estilos CSS atualizados
st.markdown(f"""
    <style>
    /* Estilo geral */
    .main {{
        background-color: {CORES['background']};
    }}
    
    /* Título principal */
    .title {{
        color: {CORES['accent']};
        font-size: 2em;
        font-weight: bold;
        margin-bottom: 30px;
    }}
    
    /* Cards de KR */
    .metric-card {{
        background-color: {CORES['card']};
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }}
    
    /* Título dos objetivos */
    .objective-title {{
        color: {CORES['accent']};
        font-size: 1.5em;
        margin: 30px 0 20px 0;
        padding: 0;
    }}
    
    /* Título das KRs */
    .kr-title {{
        color: {CORES['accent']};
        font-size: 1.1em;
        margin-bottom: 15px;
    }}
    
    /* Valores e métricas */
    .metric-value {{
        color: {CORES['white']};
        font-size: 2em;
        font-weight: bold;
        margin: 15px 0;
    }}
    
    .metric-target {{
        color: {CORES['white']};
        font-size: 1em;
        opacity: 0.9;
    }}
    
    .remaining-value {{
        color: {CORES['accent']};
        font-size: 0.9em;
        margin-top: 10px;
    }}
    
    /* Barra de progresso */
    .stProgress > div > div {{
        background-color: {CORES['light']};
    }}
    
    /* Descrição */
    .description-text {{
        color: {CORES['white']};
        font-size: 0.9em;
        opacity: 0.8;
        margin: 10px 0;
    }}
    
    /* Botões e seletores */
    .stSelectbox [data-baseweb="select"] {{
        background-color: {CORES['card']};
    }}
    
    .stButton button {{
        background-color: {CORES['card']};
        color: {CORES['white']};
        border: none;
    }}
    
    /* Sidebar */
    .sidebar .sidebar-content {{
        background-color: {CORES['background']};
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
st.markdown('<p class="title">📊 Dashboard OKRs GROU 2025</p>', unsafe_allow_html=True)

# Botão de atualização
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
    st.markdown(f'<p class="title" style="font-size: 1.5em;">OKRs - Time {selected_team}</p>', unsafe_allow_html=True)
    
    for objetivo in df['Objetivo'].unique():
        if objetivo is not None:
            # Título do Objetivo (sem caixa/contorno)
            st.markdown(f'<p class="objective-title">{objetivo}</p>', unsafe_allow_html=True)
            
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
                            
                            # Calcular progresso e valor restante
                            progresso = (valor_atual / meta * 100) if meta != 0 else 0
                            progresso = min(progresso, 100)
                            
                            # Calcular valor restante
                            valor_restante = meta - valor_atual if meta > valor_atual else 0
                            
                            # Determinar formato
                            is_percentage = '%' in str(kr['Meta'])
                            is_monetary = 'R$' in str(kr['Meta'])
                            
                            # Formatar valores para exibição
                            if is_percentage:
                                valor_display = f"{valor_atual:.1f}%"
                                meta_display = f"{meta:.1f}%"
                                restante_display = f"{valor_restante:.1f}%"
                            elif is_monetary:
                                valor_display = f"R$ {valor_atual:,.2f}"
                                meta_display = f"R$ {meta:,.2f}"
                                restante_display = f"R$ {valor_restante:,.2f}"
                            else:
                                valor_display = f"{valor_atual:,.0f}"
                                meta_display = f"{meta:,.0f}"
                                restante_display = f"{valor_restante:,.0f}"
                            
                            # Card do KR com novo layout
                            st.markdown(f"""
                                <div class="metric-card">
                                    <div class="kr-title">KR {kr['KR']}</div>
                                    <p class="description-text">{kr['Descrição']}</p>
                                    <div class="metric-value">{valor_display}</div>
                                    <div class="metric-target">Meta: {meta_display}</div>
                                    <div style="margin: 15px 0;">
                                        <div style="height: 6px; background-color: rgba(229,228,231,0.2); border-radius: 3px;">
                                            <div style="width: {progresso}%; height: 100%; background-color: {CORES['light']}; border-radius: 3px;"></div>
                                        </div>
                                    </div>
                                    <div class="progress-label" style="display: flex; justify-content: space-between;">
                                        <span>Progresso: {progresso:.1f}%</span>
                                        <span class="remaining-value">Faltam: {restante_display}</span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                        except Exception as e:
                            st.error(f"Erro ao processar KR {kr['KR']}: {str(e)}")

    # Gráfico de visão geral
    st.markdown('<p class="objective-title">Visão Geral do Progresso</p>', unsafe_allow_html=True)
    
    try:
        fig = go.Figure()
        
        for _, kr in df.iterrows():
            try:
                valor_atual = float(kr['Valor Atual'].replace('%', '').replace('R$', '').replace('.', '').replace(',', '.') if kr['Valor Atual'] else '0')
                meta = float(kr['Meta'].replace('%', '').replace('R$', '').replace('.', '').replace(',', '.') if kr['Meta'] else '0')
                progresso = (valor_atual / meta * 100) if meta != 0 else 0
                progresso = min(progresso, 100)
                
                fig.add_trace(go.Bar(
                    name=f"KR {kr['KR']}",
                    x=[f"{kr['Descrição'][:30]}..."],
                    y=[progresso],
                    text=f"{progresso:.1f}%",
                    textposition='auto',
                    marker_color=CORES['accent']
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
            font=dict(color=CORES['white']),
            margin=dict(t=40, l=40, r=40, b=40)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar gráfico: {str(e)}")

# Rodapé
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: {CORES['white']};">
        Dashboard OKRs GROU • Atualizado automaticamente
    </div>
    """, unsafe_allow_html=True)
