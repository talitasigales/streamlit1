import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
import time

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

# Funções de autenticação
def is_valid_grou_email(email):
    """Verifica se o email é do domínio grougp.com.br"""
    pattern = r'^[a-zA-Z0-9._%+-]+@grougp\.com\.br$'
    return bool(re.match(pattern, email))

def get_user_team(email):
    """Extrai o time do usuário baseado no email"""
    team = email.split('@')[0].title()
    if team in TIMES:
        return team
    return None

def log_update(team, kr, old_value, new_value, user_email):
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()
        
        log_range = 'Log!A:G'
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        body = {
            'values': [[
                timestamp,
                user_email,
                team,
                kr,
                old_value,
                new_value,
                'Atualização via Dashboard'
            ]]
        }
        
        service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=log_range,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
            
    except Exception as e:
        st.error(f"Erro ao registrar log: {str(e)}")

def update_sheet_value(team, kr, new_value, user_email):
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()
        
        result = sheet.values().get(
            spreadsheetId=SHEET_ID,
            range=f"{team}!A1:E50"
        ).execute()
        
        values = result.get('values', [])
        row_index = None
        old_value = None
        
        for i, row in enumerate(values):
            if kr in row[0]:
                row_index = i + 1
                old_value = row[3] if len(row) > 3 else '0'
                break
        
        if row_index:
            range_name = f"{team}!D{row_index}"
            body = {
                'values': [[new_value]]
            }
            
            service.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            log_update(team, kr, old_value, new_value, user_email)
            
    except Exception as e:
        raise Exception(f"Erro ao atualizar planilha: {str(e)}")

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

# Estilos CSS
st.markdown(f"""
    <style>
    .main {{
        background-color: {CORES['background']};
        padding: 0;
    }}
    
    .block-container {{
        padding-top: 0;
        padding-bottom: 0;
        margin: 0;
    }}
    
    .dashboard-title-container {{
        background-color: #8149f2;
        padding: 20px;
        border-radius: 10px;
        margin: 0 0 40px 0;
        text-align: center;
    }}
    
    .dashboard-title {{
        color: {CORES['white']};
        font-size: 31px !important;
        font-weight: bold;
        margin: 0;
    }}
    
    .login-container {{
        max-width: 400px;
        margin: 40px auto;
        padding: 30px;
        background-color: {CORES['card']};
        border-radius: 10px;
        border: 1px solid {CORES['accent']};
    }}
    
    .login-container h3 {{
        color: {CORES['accent']};
        text-align: center;
        margin-bottom: 20px;
    }}
    
    .stTextInput > div > div > input {{
        background-color: {CORES['background']};
        color: {CORES['white']};
        border: 1px solid {CORES['accent']};
    }}
    
    .team-title {{
        color: {CORES['accent']};
        font-size: 24px !important;
        font-weight: bold;
        margin: 20px 0 10px 0;
        padding: 10px 0;
    }}
    
    .objective-title {{
        color: {CORES['accent']};
        font-size: 20px !important;
        font-weight: bold;
        margin: 30px 0 16.5px 0;
        padding: 10px 0;
    }}
    
    .metric-card {{
        background-color: transparent;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid {CORES['accent']};
    }}
    
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
    
    .stButton button {{
        background-color: {CORES['accent']} !important;
        color: {CORES['white']} !important;
        border: none !important;
        width: 100%;
    }}
    
    div[data-testid="stMarkdownContainer"] > p {{
        color: {CORES['white']};
        margin: 0;
    }}
    </style>
    """, unsafe_allow_html=True)

# Configurações do Google Sheets
SHEET_ID = '1w8ciieZ_r3nYkYROZ0RpubATJZ6NWdDOmDZQMUV4Mac'
TIMES = ['Marketing', 'Comercial', 'Trainers', 'SDR', 'ADM', 'CS']

# Estado da sessão para autenticação
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_team = None

# Interface de Login ou Dashboard
if not st.session_state.authenticated:
    st.markdown("""
        <div class="dashboard-title-container">
            <p class="dashboard-title">📊 Dashboard OKRs GROU 2025</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown("<h3>Login com E-mail Corporativo</h3>", unsafe_allow_html=True)
    
    email = st.text_input("E-mail (@grougp.com.br)")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if is_valid_grou_email(email):
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.session_state.user_team = get_user_team(email)
            st.rerun()
        else:
            st.error("Por favor, use seu e-mail corporativo @grougp.com.br")
    
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # Interface do Dashboard
    st.markdown("""
        <div class="dashboard-title-container">
            <p class="dashboard-title">📊 Dashboard OKRs GROU 2025</p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar
    st.sidebar.markdown(f"### Usuário: {st.session_state.user_email}")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.user_team = None
        st.rerun()

    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

    # Seletor de Time
    selected_team = st.sidebar.selectbox("Selecione o Time para Visualizar", TIMES)

    # Carregar e exibir dados
    df = load_data(selected_team)

    if df is not None:
        st.markdown(f'<p class="team-title">OKRs - Time {selected_team}</p>', unsafe_allow_html=True)
        
        for idx, objetivo in enumerate(df['Objetivo'].unique(), 1):
            if objetivo is not None:
                st.markdown(f'<p class="objective-title">Objetivo {idx}: {objetivo}</p>', unsafe_allow_html=True)
                
                krs_obj = df[df['Objetivo'] == objetivo]
                
                for i in range(0, len(krs_obj), 3):
                    cols = st.columns(3)
                    krs_grupo = krs_obj.iloc[i:i+3]
                    
                    for idx, (_, kr) in enumerate(krs_grupo.iterrows()):
                        with cols[idx]:
                            try:
                                valor_atual = kr['Valor Atual'].replace('%', '').replace('R$', '').replace('.', '').replace(',', '.') if kr['Valor Atual'] else '0'
                                meta = kr['Meta'].replace('%', '').replace('R$', '').replace('.', '').replace(',', '.') if kr['Meta'] else '0'
                                
                                valor_atual = float(valor_atual) if valor_atual else 0
                                meta = float(meta) if meta else 0
                                
                                progresso = (valor_atual / meta * 100) if meta != 0 else 0
                                progresso = min(progresso, 100)
                                valor_restante = meta - valor_atual if meta > valor_atual else 0
                                
                                is_percentage = '%' in str(kr['Meta'])
                                is_monetary = 'R$' in str(kr['Meta'])
                                
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
                                    progress_color = '#8149f2'  # Roxo
                                elif progresso >= 61:
                                    progress_color = '#FFD700'  # Amarelo
                                else:
                                    progress_color = '#FF0000'  # Vermelho

# Card do KR com HTML corrigido
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
