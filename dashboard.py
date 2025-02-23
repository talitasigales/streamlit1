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

def sync_sheet_updates():
    """Sincroniza atualizações feitas diretamente na planilha"""
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()
        
        # Para cada time
        for team in TIMES:
            # Ler dados da aba do time
            result = sheet.values().get(
                spreadsheetId=SHEET_ID,
                range=f"{team}!A1:E50"
            ).execute()
            
            values = result.get('values', [])
            if not values:
                continue
                
            # Processar cada linha
            for i, row in enumerate(values):
                if len(row) > 3 and 'KR' in str(row[0]).upper():
                    kr_id = row[0]
                    valor_atual = row[3]
                    
                    # Atualizar nas outras abas se necessário
                    for other_team in TIMES:
                        if other_team != team:
                            # Verificar se o KR existe na outra aba
                            other_result = sheet.values().get(
                                spreadsheetId=SHEET_ID,
                                range=f"{other_team}!A1:E50"
                            ).execute()
                            
                            other_values = other_result.get('values', [])
                            if not other_values:
                                continue
                            
                            # Procurar o mesmo KR
                            for j, other_row in enumerate(other_values):
                                if len(other_row) > 0 and kr_id == other_row[0]:
                                    # Atualizar valor
                                    sheet.values().update(
                                        spreadsheetId=SHEET_ID,
                                        range=f"{other_team}!D{j+1}",
                                        valueInputOption='USER_ENTERED',
                                        body={'values': [[valor_atual]]}
                                    ).execute()
                                    
                                    # Registrar no log
                                    log_update(
                                        team=other_team,
                                        kr=kr_id,
                                        old_value=other_row[3] if len(other_row) > 3 else '0',
                                        new_value=valor_atual,
                                        user_email='sync_system@grougp.com.br'
                                    )
                                    break
        
        return True
    except Exception as e:
        st.error(f"Erro na sincronização: {str(e)}")
        return False

# Estilos CSS
st.markdown(f"""
    <style>
    .main {{
        background-color: {CORES['background']};
    }}
    
    .dashboard-title-container {{
        background-color: #8149f2;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 40px;
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
        margin: 0 auto;
        padding: 20px;
        background-color: {CORES['card']};
        border-radius: 10px;
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
    </style>
    """, unsafe_allow_html=True)

# Configurações do Google Sheets
SHEET_ID = '1w8ciieZ_r3nYkYROZ0RpubATJZ6NWdDOmDZQMUV4Mac'
TIMES = ['Marketing', 'Comercial', 'Trainers', 'SDR', 'ADM', 'CS']

# Estado da sessão para autenticação e atualização
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_team = None
    st.session_state.last_update = time.time()

# Interface de Login ou Dashboard
if not st.session_state.authenticated:
    st.markdown("""
        <div class="dashboard-title-container">
            <p class="dashboard-title">📊 Dashboard OKRs GROU 2025</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown("### Login com E-mail Corporativo")
    
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
    # Verificar necessidade de atualização automática
    current_time = time.time()
    if current_time - st.session_state.last_update > 300:  # 5 minutos
        with st.spinner('Sincronizando dados...'):
            sync_sheet_updates()
            st.session_state.last_update = current_time

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
        with st.spinner('Sincronizando dados...'):
            sync_sheet_updates()
            st.cache_data.clear()
            st.rerun()

    # Interface de edição para o time do usuário
    user_team = st.session_state.user_team
    if user_team:
        st.sidebar.markdown("### Atualizar Valores")
        df_edit = load_data(user_team)
        
        if df_edit is not None:
            for _, row in df_edit.iterrows():
                st.sidebar.markdown(f"**{row['Descrição']}**")
                novo_valor = st.sidebar.text_input(
                    f"Valor Atual para KR {row['KR']}",
                    value=row['Valor Atual'],
                    key=f"input_{row['KR']}"
                )
                
                if st.sidebar.button(f"Atualizar KR {row['KR']}"):
                    try:
                        update_sheet_value(user_team, row['KR'], novo_valor, st.session_state.user_email)
                        sync_sheet_updates()  # Sincroniza após atualização
                        st.sidebar.success("Valor atualizado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.sidebar.error(f"Erro ao atualizar: {str(e)}")

    # Seletor de Time
    selected_team = st.sidebar.selectbox("Selecione o Time para Visualizar", TIMES)

    # Carregar e exibir dados
    df = load_data(selected_team)

    if df is not None:
        st.markdown(f'<p class="team-title">OKRs - Time {selected_team}</p>', unsafe_html=True)
        
        for idx, objetivo in enumerate(df['Objetivo'].unique(), 1):
            if objetivo is not None:
                st.markdown('<div class="objective-section">', unsafe_html=True)
                st.markdown(f'<p class="objective-title">Objetivo {idx}: {objetivo}</p>', unsafe_html=True)
                
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

                                if progresso >= 91:
                                    progress_color = '#39FF14'
                                elif progresso >= 81:
                                    progress_color = '#8149f2'
                                elif progresso >= 61:
                                    progress_color = '#FFD700'
                                else:
                                    progress_color = '#FF0000'
                                
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
                                    """, unsafe_html=True)
                                
                            except Exception as e:
                                st.error(f"Erro ao processar KR {kr['KR']}: {str(e)}")
                
                st.markdown('</div>', unsafe_html=True)

        # Visão Geral do Progresso e gráficos continuam iguais...
        # (O resto do código permanece o mesmo)

# Rodapé
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; color: {CORES['white']};">
        Dashboard OKRs GROU • Atualizado automaticamente
    </div>
    """, unsafe_html=True)
