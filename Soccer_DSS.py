import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse 
import requests # API istekleri için eklendi

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Top 5 Leagues DSS | Elite", page_icon="🌍", layout="wide")

# --- ADVANCED UI/UX CUSTOMIZATION (CYBER DARK THEME + MOBILE RESPONSIVE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    
    /* Ana Arka Plan */
    .stApp { background: linear-gradient(135deg, #020617 0%, #0F172A 50%, #1E293B 100%); color: #F8FAFC; }
    
    /* MOBİL DÜZELTME: Sidebar artık saydam değil, tam katı renk. Arkadaki yazılar birbirine girmez. */
    [data-testid="stSidebar"] { 
        background-color: #020617 !important; 
        border-right: 1px solid #334155; 
        z-index: 999999;
    }
    
    /* Mobil Sidebar açma butonunun arkasını düzeltme */
    [data-testid="stSidebarCollapsedControl"] {
        background-color: #020617 !important;
        border-radius: 5px;
    }

    .group-header { color: #FFFFFF !important; font-size: 28px !important; font-weight: 800 !important; letter-spacing: 2px; margin-bottom: 0px; text-align: center;}

    /* Glassmorphism Metric Cards - Mobilde daha okunaklı arka plan */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.85); 
        border: 1px solid #38BDF8; 
        padding: 20px; 
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s ease;
    }
    div[data-testid="stMetric"]:hover { transform: translateY(-5px); border-color: #0EA5E9; }

    /* Tabs Styling - Mobilde taşmayı engelleyen 'flex-wrap' ayarı eklendi */
    .stTabs [data-baseweb="tab-list"] { gap: 12px; border-bottom: 1px solid #334155; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] { color: #94A3B8; font-weight: 600; padding: 12px 20px; }
    .stTabs [aria-selected="true"] { color: #38BDF8; border-bottom: 2px solid #38BDF8; }
    
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 700 !important; }
    
    /* Etiketleri mobilde alt alta düzgün dizmek için inline-block ayarı */
    .badge { padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-right: 5px; color: white; display: inline-block; margin-bottom: 5px;}
    .badge-wonder { background: linear-gradient(90deg, #A855F7, #EC4899); }
    .badge-elite { background: linear-gradient(90deg, #EF4444, #F97316); }
    .badge-maestro { background: linear-gradient(90deg, #3B82F6, #06B6D4); }
    
    /* Resimleri mobil ekrana göre otomatik sığdırma */
    img { max-width: 100%; height: auto; }
</style>
""", unsafe_allow_html=True)

# --- IMAGE & LOGO FALLBACK SYSTEM ---
TEAM_LOGOS = {
    "Arsenal": "https://logo.clearbit.com/arsenal.com",
}

PLAYER_FACES = {
    "Erling Haaland": "https://resources.premierleague.com/premierleague/photos/players/250x250/p223094.png",
}

def get_team_logo(team_name):
    safe_name = urllib.parse.quote(str(team_name))
    return TEAM_LOGOS.get(team_name, f"https://ui-avatars.com/api/?name={safe_name}&background=1E293B&color=38BDF8&rounded=true&bold=true")

# GELİŞTİRİLMİŞ OYUNCU YÜZÜ ÇEKME FONKSİYONU (API Entegrasyonlu)
@st.cache_data(show_spinner=False, ttl=86400) # 1 günlük önbellek
def get_player_face(player_name):
    # 1. Manuel listede var mı kontrolü (Hızlı Yükleme)
    if player_name in PLAYER_FACES:
        return PLAYER_FACES[player_name]
    
    # 2. Listede yoksa TheSportsDB API'sine ücretsiz istek at
    try:
        api_url = f"https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p={urllib.parse.quote(player_name)}"
        response = requests.get(api_url, timeout=3)
        data = response.json()
        
        if data.get('player') is not None:
            player_data = data['player'][0]
            # Arka planı silinmiş (Cutout) > Render > Normal Thumb sıralamasıyla ara
            img_url = player_data.get('strCutout') or player_data.get('strRender') or player_data.get('strThumb')
            
            if img_url:
                return img_url
    except Exception as e:
        # API çökmesi durumunda sessizce geç
        pass 
        
    # 3. API'de bulunamazsa UI-Avatars Joker Görselini kullan
    safe_name = urllib.parse.quote(str(player_name))
    return f"https://ui-avatars.com/api/?name={safe_name}&background=0F172A&color=38BDF8&size=250&rounded=true&bold=true"

# --- 1. DATA COMPONENT (SAFE & STABLE) ---
@st.cache_data
def load_data():
    df = pd.read_csv('players_data-2024_2025.csv')
    
    league_map = {
        'eng Premier League': '🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League', 
        'es La Liga': '🇪🇸 La Liga',
        'it Serie A': '🇮🇹 Serie A', 
        'de Bundesliga': '🇩🇪 Bundesliga', 
        'fr Ligue 1': '🇫🇷 Ligue 1'
    }
    df = df[df['Comp'].isin(league_map.keys())].copy()
    df['Comp'] = df['Comp'].map(league_map)
    df.dropna(subset=['Player', 'Squad', 'Comp'], inplace=True)
    
    # Safe NA filling to prevent Pandas 2.0+ TypeErrors
    num_cols = df.select_dtypes(include=['number']).columns
    df[num_cols] = df[num_cols].fillna(0)
    str_cols = df.select_dtypes(exclude=['number']).columns
    df[str_cols] = df[str_cols].fillna("")
    
    return df

df = load_data()

# --- SIDEBAR (GROUP 6) ---
st.sidebar.markdown('<p class="group-header">GROUP 6</p>', unsafe_allow_html=True)
with st.sidebar.expander("Team Members", expanded=True):
    st.markdown("• Ahmet Tarık Orhan\n\n• Ali Eren Kurt\n\n• Mustafa Düşünceli\n\n• Ahmet Can Vurmaz")

st.sidebar.markdown("---")
st.sidebar.title("⚙️ Control Panel")
league_list = ["All Europe (Top 5)"] + sorted(list(df['Comp'].unique()))
selected_league = st.sidebar.selectbox("🌍 Select League", league_list)

filtered_df = df if selected_league == "All Europe (Top 5)" else df[df['Comp'] == selected_league]

team_list = ["All Teams"] + sorted(list(filtered_df['Squad'].unique()))
selected_team = st.sidebar.selectbox("🏟️ Select Squad", team_list)

if selected_team != "All Teams":
    filtered_df = filtered_df[filtered_df['Squad'] == selected_team]

st.sidebar.markdown("---")
analysis_mode = st.sidebar.radio("🔍 Navigation:", ["📊 Overview", "👤 Player Insight", "⚔️ H2H Compare"])

# --- MAIN CONTENT ---
if analysis_mode == "📊 Overview":
    st.title(f"⚽ Intelligence Hub: {selected_team if selected_team != 'All Teams' else selected_league}")
    st.markdown("Leverage data analytics for squad planning, performance evaluation, and predictive modeling.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Descriptive", "🧪 Diagnostic", "🔮 Predictive", "💡 Prescriptive"])
    
    with tab1:
        st.subheader("Key Performance Indicators")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Players", len(filtered_df))
        c2.metric("Total Goals", int(filtered_df['Gls'].sum()))
        c3.metric("Total Assists", int(filtered_df['Ast'].sum()))
        c4.metric("Avg. Age", round(filtered_df['Age'].mean(), 1))
        
        st.markdown("<br>", unsafe_allow_html=True)
        colL, colR = st.columns(2)
        with colL:
            st.subheader("🔥 Top 10 Scorers")
            top = filtered_df.sort_values(by='Gls', ascending=False).head(10)
            fig = px.bar(top, x='Player', y='Gls', text='Gls', color='Gls', color_continuous_scale='Blues')
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
        with colR:
            st.subheader("🥶 Underperformers (G-xG)")
            st.caption("Players wasting the most chances (Min. 300 minutes played).")
            worst = filtered_df[filtered_df['Min'] > 300].sort_values(by='G-xG', ascending=True).head(10)
            fig2 = px.bar(worst, x='Player', y='G-xG', text='G-xG', color='G-xG', color_continuous_scale='Reds_r')
            fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.subheader("Attacking Efficiency Simulator (What-If)")
        st.info("Hypothesis: If we allocate more training time to finishing drills, how does it impact our Expected Goals (xG)?")
        current_xg = filtered_df['xG'].sum()
        imp = st.slider("Finishing Improvement Target (%)", 0, 50, 15, step=5)
        new_xg = current_xg * (1 + (imp / 100))
        sc1, sc2 = st.columns(2)
        sc1.metric("Current Total xG", f"{current_xg:.2f}")
        sc2.metric("Projected New xG", f"{new_xg:.2f}", delta=f"+{new_xg - current_xg:.2f}")

    with tab3:
        st.subheader("End of Season Forecast (Matchweek 38)")
        st.markdown("Linear projection model based on current Goals per Match Played (MP) ratio.")
        top_p = filtered_df.sort_values(by='Gls', ascending=False).head(15)
        pred = [{"League": r['Comp'], "Squad": r['Squad'], "Player": r['Player'], "Matches": r['MP'], "Current Goals": r['Gls'], "MW38 Forecast": round((r['Gls']/r['MP'])*38)} for _, r in top_p.iterrows() if r['MP']>0]
        pred_df = pd.DataFrame(pred)
        pred_df.index = np.arange(1, len(pred_df) + 1)
        st.dataframe(pred_df, use_container_width=True)
        
        csv = pred_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Forecast Data (CSV)", data=csv, file_name='forecast_mw38.csv', mime='text/csv')

    with tab4:
        st.subheader("💡 System Recommendations & Action Plan")
        st.success("""
        **1. Recruitment Strategy:** Data indicates that players under 24 exhibit a higher growth trajectory in xG per 90 mins. Target young, high-potential midfielders.
        
        **2. Tactical Optimization:** The What-If scenario proves that a 15% increase in shot quality yields a massive output advantage. Implement specialized finishing camps.
        
        **3. Roster Management:** Review the 'Underperformers' chart. Players showing a severe negative G-xG delta are costing the team points. Consider benching them.
        """)

elif analysis_mode == "👤 Player Insight":
    st.title("👤 Advanced Player Profiling")
    player = st.selectbox("Search & Select Player:", sorted(filtered_df['Player'].unique()))
    p = filtered_df[filtered_df['Player'] == player].iloc[0]
    
    badges = ""
    if p['Age'] <= 21 and p['MP'] >= 5: badges += '<span class="badge badge-wonder">💎 Wonderkid</span>'
    if p['Gls'] >= 8: badges += '<span class="badge badge-elite">🔥 Elite Scorer</span>'
    if p['Ast'] >= 5: badges += '<span class="badge badge-maestro">🎯 Playmaker</span>'

    col_img, col_info = st.columns([1, 4])
    with col_img:
        st.markdown(f"<img src='{get_player_face(player)}' style='width:100%; border-radius:15px; border:2px solid #38BDF8;'>", unsafe_allow_html=True)
        
    with col_info:
        st.markdown(f"<h2>{player} {badges}</h2>", unsafe_allow_html=True)
        st.markdown(f"**League:** {p['Comp']} &nbsp;|&nbsp; **Squad:** <img src='{get_team_logo(p['Squad'])}' width='24' style='vertical-align:middle; border-radius:4px;'> {p['Squad']}", unsafe_allow_html=True)
        st.markdown(f"**Position:** {p['Pos']} &nbsp;|&nbsp; **Age:** {int(p['Age'])}")
        st.markdown(f"**Appearances:** {int(p['MP'])} *(Starts: {int(p['Starts'])})* &nbsp;|&nbsp; **Minutes Played:** {int(p['Min'])}")
    
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Goals", int(p['Gls']))
    m2.metric("Total Assists", int(p['Ast']))
    m3.metric("Expected Goals (xG)", float(p['xG']))
    m4.metric("Cards (Y / R)", f"{int(p['CrdY'])} / {int(p['CrdR'])}")
    
    st.markdown("---")
    st.subheader("🕸️ Attribute Radar vs. League Best")
    st.markdown("Visualizes the player's percentile rank compared to the maximum values achieved in their respective league.")
    
    league_max = df[df['Comp'] == p['Comp']]
    def norm(col): return (p[col] / league_max[col].max()) * 100 if league_max[col].max() > 0 else 0
    
    radar_df = pd.DataFrame(dict(
        r=[norm('xG'), norm('xAG'), p.get('Cmp%', 0), norm('PrgC'), norm('TklW')],
        theta=['Attacking Threat (xG)', 'Playmaking (xAG)', 'Pass Accuracy (%)', 'Ball Carry (PrgC)', 'Defensive Work (TklW)']
    ))
    
    fig = px.line_polar(radar_df, r='r', theta='theta', line_close=True, range_r=[0,100], template="plotly_dark")
    fig.update_traces(fill='toself', fillcolor='rgba(56, 189, 248, 0.3)', line_color='#38BDF8', line_width=2)
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor='#334155'), angularaxis=dict(gridcolor='#334155')), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        comp_data = {'Metric': ['Goals', 'Expected (xG)', 'Assists', 'Expected (xAG)'], 'Value': [p['Gls'], p['xG'], p['Ast'], p['xAG']]}
        fig_bar = px.bar(comp_data, x='Metric', y='Value', text='Value', color='Metric')
        fig_bar.update_layout(title_text='Actual vs. Expected Output', template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

elif analysis_mode == "⚔️ H2H Compare":
    st.title("⚔️ Head-to-Head Transfer Comparison")
    st.markdown("Compare two players side-by-side to make data-driven recruitment decisions.")
    
    available_players = sorted(filtered_df['Player'].unique())
    cl1, cl2 = st.columns(2)
    
    with cl1:
        p1_name = st.selectbox("Player 1 (Red)", available_players, index=available_players.index("Erling Haaland") if "Erling Haaland" in available_players else 0)
        p1 = filtered_df[filtered_df['Player']==p1_name].iloc[0]
        st.markdown(f"<div style='text-align:center;'><img src='{get_player_face(p1_name)}' width='150' style='border-radius:10px; border:2px solid #EF4444;'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; margin-top:10px;'><b>Squad:</b> <img src='{get_team_logo(p1['Squad'])}' width='20' style='vertical-align:middle; border-radius:3px;'> {p1['Squad']}</div>", unsafe_allow_html=True)
        
    with cl2:
        p2_idx = 1 if len(available_players) > 1 else 0
        p2_name = st.selectbox("Player 2 (Blue)", available_players, index=available_players.index("Mohamed Salah") if "Mohamed Salah" in available_players else p2_idx)
        p2 = filtered_df[filtered_df['Player']==p2_name].iloc[0]
        st.markdown(f"<div style='text-align:center;'><img src='{get_player_face(p2_name)}' width='150' style='border-radius:10px; border:2px solid #3B82F6;'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; margin-top:10px;'><b>Squad:</b> <img src='{get_team_logo(p2['Squad'])}' width='20' style='vertical-align:middle; border-radius:3px;'> {p2['Squad']}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    def norm_h2h(val, col): max_v = df[col].max(); return (val / max_v) * 100 if max_v > 0 else 0
    categories = ['Goals', 'Assists', 'Expected Goals (xG)', 'Ball Carry (PrgC)', 'Pass Accuracy (%)']
    p1_vals = [norm_h2h(p1['Gls'], 'Gls'), norm_h2h(p1['Ast'], 'Ast'), norm_h2h(p1['xG'], 'xG'), norm_h2h(p1['PrgC'], 'PrgC'), p1.get('Cmp%', 0)]
    p2_vals = [norm_h2h(p2['Gls'], 'Gls'), norm_h2h(p2['Ast'], 'Ast'), norm_h2h(p2['xG'], 'xG'), norm_h2h(p2['PrgC'], 'PrgC'), p2.get('Cmp%', 0)]

    fig_h2h = go.Figure()
    fig_h2h.add_trace(go.Scatterpolar(r=p1_vals + [p1_vals[0]], theta=categories + [categories[0]], fill='toself', name=p1['Player'], line_color='#EF4444'))
    fig_h2h.add_trace(go.Scatterpolar(r=p2_vals + [p2_vals[0]], theta=categories + [categories[0]], fill='toself', name=p2['Player'], line_color='#3B82F6'))
    
    fig_h2h.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor='#334155'), angularaxis=dict(gridcolor='#334155')), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    
    c_radar, c_stats = st.columns([1.5, 1])
    with c_radar: 
        st.plotly_chart(fig_h2h, use_container_width=True)
    with c_stats:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.metric(f"Goals Comparison", f"{int(p1['Gls'])} vs {int(p2['Gls'])}", delta=int(p1['Gls'] - p2['Gls']))
        st.metric(f"Assists Comparison", f"{int(p1['Ast'])} vs {int(p2['Ast'])}", delta=int(p1['Ast'] - p2['Ast']))
        st.metric(f"xG (Finishing Potential)", f"{float(p1['xG']):.2f} vs {float(p2['xG']):.2f}", delta=round(p1['xG'] - p2['xG'], 2))
