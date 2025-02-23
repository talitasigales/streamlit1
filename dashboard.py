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
    
    /* Título principal do dashboard */
    .dashboard-title {{
        color: {CORES['accent']};
        font-size: 31px !important;
        font-weight: bold;
        margin-bottom: 40px;
        padding: 20px 0;
        text-align: center;
    }}
    
    /* Título do time */
    .team-title {{
        color: {CORES['accent']};
        font-size: 24px !important;
        font-weight: bold;
        margin: 20px 0 10px 0;
        padding: 10px 0;
    }}
    
    /* Título dos objetivos */
    .objective-title {{
        color: {CORES['accent']};
        font-size: 20px !important;
        font-weight: bold;
        margin: 30px 0 16.5px 0;
        padding: 10px 0;
    }}
    
    /* Cards de KR */
    .metric-card {{
        background-color: transparent;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid {CORES['accent']};
    }}
    
    /* Título e descrição das KRs */
    .kr-title {{
        color: {CORES['accent']};
        font-size: 18px !important;
        font-weight: bold;
        margin-bottom: 15px;
    }}
    
    .kr-description {{
        color: {CORES['white']};
        font-size: 18px !important;
        margin: 10px 0;
    }}
    
    /* Valores e métricas */
    .metric-value {{
        color: {CORES['accent']};
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
    
    /* Botões e seletores */
    .stSelectbox [data-baseweb="select"] {{
        background-color: {CORES['card']};
    }}
    
    .stButton button {{
        background-color: {CORES['accent']} !important;
        color: {CORES['white']} !important;
        border: none !important;
        width: 100%;
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
st.markdown('<p class="dashboard-title">📊 Dashboard OKRs GROU 2025</p>', unsafe_allow_html=True)

# Controles no sidebar
if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()
selected_team = st.sidebar.selectbox("Selecione o Time", TIMES)

# Carregar dados do time selecionado
df = load_data(selected_team)
if df is not None:
    st.markdown(f'<p class="team-title">OKRs - Time {selected_team}</p>', unsafe_allow_html=True)
    
    for idx, objetivo in enumerate(df['Objetivo'].unique(), 1):
        if objetivo is not None:
            # Início da seção do objetivo
            st.markdown('<div class="objective-section">', unsafe_allow_html=True)
            
            # Título do Objetivo com número
            st.markdown(f'<p class="objective-title">Objetivo {idx}: {objetivo}</p>', unsafe_allow_html=True)
            
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

                            # Determinar cor da barra de progresso
                            if progresso >= 91:
                                progress_color = '#39FF14'  # Verde neon
                            elif progresso >= 81:
                                progress_color = '#e5e4e7'  # Cinza claro (ajustado)
                            elif progresso >= 61:
                                progress_color = '#FFD700'  # Amarelo
                            else:
                                progress_color = '#FF0000'  # Vermelho
                            
                            # Card do KR
                            st.markdown(f"""
                                <div class="metric-card">
                                    <div class="kr-title">KR {kr['KR']}</div>
                                    <p class="kr-description">{kr['Descrição']}</p>
                                    <div class="metric-value">{valor_display}</div>
                                    <div class="metric-target">Meta: {meta_display}</div>
                                    <div style="margin: 15px 0;">
                                        <div style="height: 6px; background-color: rgba(229,228,231,0.2); border-radius: 3px;">
                                            <div style="width: {progresso}%; height: 100%; background-color: {progress_color}; border-radius: 3px; transition: all 0.3s ease;"></div>
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
            
            # Fim da seção do objetivo
            st.markdown('</div>', unsafe_allow_html=True)

    # Visão Geral do Progresso
    st.markdown('<p class="objective-title">Visão Geral do Progresso</p>', unsafe_allow_html=True)

    try:
        # Calcular média de progresso por objetivo
        progress_by_objective = {}
        for objetivo in df['Objetivo'].unique():
            krs_obj = df[df['Objetivo'] == objetivo]
            objetivo_progress = []
            
            for _, kr in krs_obj.iterrows():
                try:
                    valor_atual = float(kr['Valor Atual'].replace('%', '').replace('R$', '').replace('.', '').replace(',', '.') if kr['Valor Atual'] else '0')
                    meta = float(kr['Meta'].replace('%', '').replace('R$', '').replace('.', '').replace(',', '.') if kr['Meta'] else '0')
                    progresso = (valor_atual / meta * 100) if meta != 0 else 0
                    objetivo_progress.append(min(progresso, 100))
                except:
                    continue
            
            if objetivo_progress:
                progress_by_objective[objetivo] = sum(objetivo_progress) / len(objetivo_progress)
        
        # Calcular progresso geral do time
        team_progress = sum(progress_by_objective.values()) / len(progress_by_objective) if progress_by_objective else 0
        
        # Layout com duas colunas para velocímetro e progresso por objetivo
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Criar velocímetro sem background
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = team_progress,
                number = {'suffix': "%", 'font': {'size': 40, 'color': CORES['white']}},
                title = {'text': "Progresso Geral do Time", 'font': {'size': 20, 'color': CORES['accent']}},
                gauge = {
                    'axis': {'range': [0, 100], 'tickcolor': CORES['white']},
                    'bar': {'color': 
                        '#39FF14' if team_progress >= 91 else
                        '#e5e4e7' if team_progress >= 81 else
                        '#FFD700' if team_progress >= 61 else
                        '#FF0000'
                    },
                    'bgcolor': 'rgba(0,0,0,0)',
                    'borderwidth': 0,
                    'steps': [
                        {'range': [0, 60], 'color': 'rgba(255, 0, 0, 0.2)'},
                        {'range': [61, 80], 'color': 'rgba(255, 215, 0, 0.2)'},
                        {'range': [81, 90], 'color': 'rgba(229, 228, 231, 0.2)'},
                        {'range': [91, 100], 'color': 'rgba(57, 255, 20, 0.2)'}
                    ]
                }
            ))
            
            fig.update_layout(
                paper_bgcolor = 'rgba(0,0,0,0)',
                plot_bgcolor = 'rgba(0,0,0,0)',
                font = {'color': CORES['white']},
                height = 300,
                margin = dict(t=60, b=0),
                showlegend = False
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            st.markdown("""
                <h3 style="color: #5abebe; font-size: 18px; margin-bottom: 20px;">
                    Progresso por Objetivo
                </h3>
            """, unsafe_allow_html=True)
            
            for objetivo, progresso in progress_by_objective.items():
                st.markdown(f"""
                    <div style="padding: 15px; background-color: transparent; border: 1px solid {CORES['accent']}; border-radius: 8px; margin: 10px 0;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span style="color: {CORES['white']};">{objetivo}</span>
                            <span style="color: {CORES['accent']};">{progresso:.1f}%</span>
                        </div>
                        <div style="height: 6px; background-color: rgba(229,228,231,0.2); border-radius: 3px;">
                            <div style="width: {progresso}%; height: 100%; background-color: {
                                '#39FF14' if progresso >= 91 else
                                '#8149f2' if progresso >= 81 else
                                '#FFD700' if progresso >= 61 else
                                '#FF0000'
                            }; border-radius: 3px;"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro ao gerar visualização de progresso: {str(e)}")

# Rodapé
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: {CORES['white']};">
        Dashboard OKRs GROU • Atualizado automaticamente
    </div>
    """, unsafe_allow_html=True)
