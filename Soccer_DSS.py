import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse 
import requests 
import base64 
import os 
import difflib 

# --- KULLANICILARI DARK MODA ZORLAMA (Otomatik Ayar Dosyası) ---
if not os.path.exists(".streamlit/config.toml"):
    os.makedirs(".streamlit", exist_ok=True)
    with open(".streamlit/config.toml", "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"dark\"\n")

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Top 5 Leagues DSS | Elite", page_icon="🌍", layout="wide")

# --- ADVANCED UI/UX CUSTOMIZATION (CYBER DARK THEME + MOBILE RESPONSIVE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .stApp { background: linear-gradient(135deg, #020617 0%, #0F172A 50%, #1E293B 100%); color: #F8FAFC; }
    
    
    /* MOBİL DÜZELTME: Sidebar artık saydam değil, tam katı renk. Arkadaki yazılar birbirine girmez. */
    [data-testid="stSidebar"] { 
        background-color: #020617 !important; 
        border-right: 1px solid #334155; 
        z-index: 999999;
    }
    
    [data-testid="stSidebarCollapsedControl"] {
        background-color: #020617 !important;
        border-radius: 5px;
    }

    .group-header { color: #FFFFFF !important; font-size: 28px !important; font-weight: 800 !important; letter-spacing: 2px; margin-bottom: 0px; text-align: center;}

    /* Glassmorphism Metric Cards */
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
    
    .badge { padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-right: 5px; color: white; display: inline-block; margin-bottom: 5px;}
    .badge-wonder { background: linear-gradient(90deg, #A855F7, #EC4899); }
    .badge-elite { background: linear-gradient(90deg, #EF4444, #F97316); }
    .badge-maestro { background: linear-gradient(90deg, #3B82F6, #06B6D4); }
    .badge-rating { background: linear-gradient(90deg, #F59E0B, #EAB308); color: #000 !important; font-size: 14px !important;} 
    
    img { max-width: 100%; height: auto; }
</style>
""", unsafe_allow_html=True)

# --- YARDIMCI FONKSİYON: LOKAL RESİMLERİ BASE64'E ÇEVİRME ---
def get_local_image_base64(filepath):
    if os.path.exists(filepath):
        with open(filepath, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return None

# --- YENİ EKLENTİ: LİG BAYRAKLARI ---
def get_flag_logo(league_name):
    flag_map = {
        "Premier League": "england.png",
        "La Liga": "spain.png",
        "Serie A": "italy.png",
        "Bundesliga": "germany.png",
        "Ligue 1": "france.png"
    }
    if league_name in flag_map:
        base64_img = get_local_image_base64(f"image/{flag_map[league_name]}")
        if base64_img:
            # Emoji boyutu için width='20', metinle düzgün hizalama için vertical-align eklendi
            return f"<img src='data:image/png;base64,{base64_img}' width='24' style='vertical-align: middle; margin-right: 6px; border-radius: 3px;'>"
    return ""

# --- 1. TAKIM LOGOLARI İÇİN AKILLI LOKAL (KLASÖR) SİSTEMİ ---
TEAM_MANUAL_MAP = {
    "Paris S-G": "paris-saint-germain",
    "Manchester Utd": "manchester-united",
    "Newcastle Utd": "newcastle-united",
    "Bayern Munich": "bayern",
    "Mönchengladbach": "moenchengladbach",
    "Nürnberg": "nuremberg",
    "Milan": "ac-milan"
}

def get_team_logo(team_name):
    available_logos = []
    if os.path.exists("logos"):
        available_logos = [f.replace(".png", "") for f in os.listdir("logos") if f.endswith(".png")]
    
    clean_name = str(team_name).strip()
    target_filename = ""
    
    if clean_name in TEAM_MANUAL_MAP:
        target_filename = TEAM_MANUAL_MAP[clean_name]
    elif available_logos:
        search_str = clean_name.lower().replace(" ", "-")
        if search_str in available_logos:
            target_filename = search_str
        else:
            matches = difflib.get_close_matches(search_str, available_logos, n=1, cutoff=0.4)
            if not matches:
                for logo in available_logos:
                    if search_str in logo or logo in search_str:
                        matches = [logo]
                        break
            if matches:
                target_filename = matches[0]
                
    if target_filename:
        file_path = f"logos/{target_filename}.png"
        if os.path.exists(file_path):
            with open(file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded_string}"
            
    safe_name = urllib.parse.quote(str(team_name))
    return f"https://ui-avatars.com/api/?name={safe_name}&background=1E293B&color=38BDF8&rounded=true&bold=true"


# --- 2. OYUNCU YÜZLERİ İÇİN API SİSTEMİ ---
PLAYER_FACES = {
    "Erling Haaland": "https://resources.premierleague.com/premierleague/photos/players/250x250/p223094.png",
   # Ferdi Kadıoğlu (Hata vermeyen güncel şeffaf PNG linki)
   
    "Ferdi Kadıoğlu" :"https://raw.githubusercontent.com/EvaHertz/Soccer_DSS/refs/heads/main/image/FerdiKadığlu.png",
    "Ferdi Kadioglu": "https://raw.githubusercontent.com/EvaHertz/Soccer_DSS/refs/heads/main/image/FerdiKadığlu.png",
    "Ferdi Kadığlu": "https://raw.githubusercontent.com/EvaHertz/Soccer_DSS/refs/heads/main/image/FerdiKadığlu.png",

   "Aaron Ciammaglichella": "https://raw.githubusercontent.com/EvaHertz/Soccer_DSS/refs/heads/main/image/Aaron%20Ciammaglichella.png",

    "Abde Ezzalzouli" : "https://assets.laliga.com/squad/2025/t185/p500745/2048x2225/p500745_t185_2025_1_001_000.png"
    }

@st.cache_data(show_spinner=False, ttl=86400)
def get_player_face(player_name):
    if player_name in PLAYER_FACES:
        return PLAYER_FACES[player_name]
    try:
        api_url = f"https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p={urllib.parse.quote(player_name)}"
        response = requests.get(api_url, timeout=3)
        data = response.json()
        if data.get('player') is not None:
            player_data = data['player'][0]
            img_url = player_data.get('strCutout') or player_data.get('strRender') or player_data.get('strThumb')
            if img_url:
                return img_url
    except Exception:
        pass 
        
    safe_name = urllib.parse.quote(str(player_name))
    return f"https://ui-avatars.com/api/?name={safe_name}&background=0F172A&color=38BDF8&size=250&rounded=true&bold=true"

# --- 3. DATA COMPONENT & ALGORITHM ---
@st.cache_data
def load_data():
    df = pd.read_csv('players_data-2024_2025.csv')
    
    # Emojiler temizlendi, saf metne çevrildi
    league_map = {
        'eng Premier League': 'Premier League', 
        'es La Liga': 'La Liga',
        'it Serie A': 'Serie A', 
        'de Bundesliga': 'Bundesliga', 
        'fr Ligue 1': 'Ligue 1'
    }
    df = df[df['Comp'].isin(league_map.keys())].copy()
    df['Comp'] = df['Comp'].map(league_map)
    df.dropna(subset=['Player', 'Squad', 'Comp'], inplace=True)
    
    num_cols = df.select_dtypes(include=['number']).columns
    df[num_cols] = df[num_cols].fillna(0)
    str_cols = df.select_dtypes(exclude=['number']).columns
    df[str_cols] = df[str_cols].fillna("")
    return df

df = load_data()

# MEVKİYE ÖZEL 10 ÜZERİNDEN PUANLAMA ALGORİTMASI
def calculate_player_rating(p, df_full):
    league_df = df_full[df_full['Comp'] == p['Comp']]
    pos = str(p.get('Pos', '')).upper()
    
    def get_max(col):
        if col in league_df.columns:
            m = league_df[col].max()
            return m if m > 0 else 1
        return 1

    score = 5.5
    gls, ast, xg, xag = p.get('Gls', 0), p.get('Ast', 0), p.get('xG', 0), p.get('xAG', 0)
    prgc, tklw, cmp, mins = p.get('PrgC', 0), p.get('TklW', 0), p.get('Cmp%', 0), p.get('Min', 0)
    
    if 'FW' in pos:
        score += 2.5 * (gls / get_max('Gls')) + 1.0 * (ast / get_max('Ast')) + 1.0 * (xg / get_max('xG'))
    elif 'MF' in pos:
        score += 1.5 * (ast / get_max('Ast')) + 1.0 * (xag / get_max('xAG')) + 1.0 * (prgc / get_max('PrgC')) + 1.0 * (cmp / get_max('Cmp%'))
    elif 'DF' in pos:
        score += 2.5 * (tklw / get_max('TklW')) + 1.0 * (cmp / get_max('Cmp%')) + 1.0 * (prgc / get_max('PrgC'))
    elif 'GK' in pos:
        saves = p.get('Saves', mins) 
        max_saves = get_max('Saves') if 'Saves' in league_df.columns else get_max('Min')
        score += 3.5 * (saves / max_saves) + 1.0 * (cmp / get_max('Cmp%'))
    else:
        score += 2.0 * (mins / get_max('Min'))
        
    if mins < 300: score -= 1.5
    score = max(4.0, min(score, 9.9))
    
    if gls >= 15: score = max(score, 8.5 + (gls/50))
    if ast >= 10: score = max(score, 8.3 + (ast/30))
    
    return round(score, 1)

# --- SIDEBAR (GROUP 6) ---
sidebar_logo = get_local_image_base64("image/SoccerDSS.png")
if sidebar_logo:
    st.sidebar.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="data:image/png;base64,{sidebar_logo}" style="width: 150px; height: auto; border-radius: 10px;">
        </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown('<p class="group-header">GROUP 6</p>', unsafe_allow_html=True)
with st.sidebar.expander("Team Members", expanded=True):
    st.markdown("""
    • <a href="https://www.linkedin.com/in/ahmet-tar%C4%B1k-orhan/" target="_blank" style="color: #38BDF8; text-decoration: none;">Ahmet Tarık Orhan</a><br><br>
    • <a href="https://www.linkedin.com/in/ali-eren-kurt-0842a7333" target="_blank" style="color: #38BDF8; text-decoration: none;">Ali Eren Kurt</a><br><br>
    • <a href="https://www.linkedin.com/in/mustafa-d%C3%BC%C5%9F%C3%BCnceli-0139a822a/" target="_blank" style="color: #38BDF8; text-decoration: none;">Mustafa Düşünceli</a><br><br>
    • Ahmet Can Vurmaz
    """, unsafe_allow_html=True)

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
    
    app_logo_base64 = get_local_image_base64("image/SoccerDSS.png")
    if app_logo_base64:
        logo_html = f"<img src='data:image/png;base64,{app_logo_base64}' width='60' style='vertical-align: middle; margin-right: 15px;'>"
    else:
        logo_html = "⚽ " 

    if selected_team != "All Teams":
        col_title, col_logo = st.columns([5, 1])
        with col_title:
            st.markdown(f"<h1 style='display: flex; align-items: center; color: #FFFFFF !important; font-weight: 700 !important; margin: 0;'>{logo_html}Intelligence Hub: {selected_team}</h1>", unsafe_allow_html=True)
            st.markdown("Leverage data analytics for squad planning, performance evaluation, and predictive modeling.")
        with col_logo:
            st.markdown(f"<div style='text-align: right; padding-top: 15px;'><img src='{get_team_logo(selected_team)}' width='80' style='border-radius:10px;'></div>", unsafe_allow_html=True)
    else:
        flag_html = get_flag_logo(selected_league) if selected_league != "All Europe (Top 5)" else ""
        st.markdown(f"<h1 style='display: flex; align-items: center; color: #FFFFFF !important; font-weight: 700 !important; margin: 0;'>{logo_html}Intelligence Hub: {flag_html}{selected_league}</h1>", unsafe_allow_html=True)
        st.markdown("Leverage data analytics for squad planning, performance evaluation, and predictive modeling.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Descriptive", "🧪 Diagnostic (What-If)", "🔮 Predictive", "💡 Prescriptive"])
    
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
        st.subheader("🧪 Tactical Scenario Engine (What-If)")
        st.markdown("Simulate the impact of different coaching philosophies and tactical shifts on team output and end-of-season standings.")
        
        tactical_preset = st.selectbox("📋 Apply Tactical Preset:", [
            "Custom (Manual Adjustments)", 
            "⚡ Gegenpressing (High Intensity & Pressing)", 
            "🧠 Tiki-Taka (Possession & Playmaking)", 
            "🏹 Direct Counter-Attack (Vertical & Finishing)"
        ])
        
        v_xg, v_xag, v_tkl, v_cmp = 0, 0, 0, 0
        if "Gegenpressing" in tactical_preset:
            v_xg, v_xag, v_tkl, v_cmp = 5, 10, 35, -5
        elif "Tiki-Taka" in tactical_preset:
            v_xg, v_xag, v_tkl, v_cmp = -5, 25, -10, 20
        elif "Direct" in tactical_preset:
            v_xg, v_xag, v_tkl, v_cmp = 25, 5, 10, -10

        st.markdown("##### ⚙️ Tactical Micro-Adjustments")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            xg_imp = st.slider("Finishing Camp (+% xG)", -25, 50, v_xg)
        with col_s2:
            xag_imp = st.slider("Playmaking Focus (+% xAG)", -25, 50, v_xag)
        with col_s3:
            def_imp = st.slider("Pressing Line (+% TklW)", -25, 50, v_tkl)
        with col_s4:
            cmp_imp = st.slider("Possession Drills (+% Cmp%)", -25, 50, v_cmp)

        curr_xg = filtered_df['xG'].sum()
        curr_xag = filtered_df['xAG'].sum()
        curr_tklw = filtered_df['TklW'].sum()
        curr_cmp = filtered_df['Cmp%'].mean() if len(filtered_df) > 0 else 0

        new_xg = curr_xg * (1 + (xg_imp / 100))
        new_xag = curr_xag * (1 + (xag_imp / 100))
        new_tklw = curr_tklw * (1 + (def_imp / 100))
        new_cmp = min(100.0, curr_cmp * (1 + (cmp_imp / 100)))

        st.markdown("---")
        
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Simulated xG", f"{new_xg:.1f}", delta=f"{new_xg - curr_xg:+.1f}", delta_color="normal")
        sc2.metric("Simulated xAG", f"{new_xag:.1f}", delta=f"{new_xag - curr_xag:+.1f}", delta_color="normal")
        sc3.metric("Simulated Tackles", f"{new_tklw:.0f}", delta=f"{new_tklw - curr_tklw:+.0f}", delta_color="normal")
        sc4.metric("Simulated Pass Acc.", f"{new_cmp:.1f}%", delta=f"{new_cmp - curr_cmp:+.1f}%", delta_color="normal")

        st.markdown("<br>", unsafe_allow_html=True)
        col_chart, col_impact = st.columns([1.5, 1])

        with col_chart:
            def norm_team(val, orig): return 100 * (val/orig) if orig > 0 else 100
            
            radar_cats = ['Attacking (xG)', 'Creativity (xAG)', 'Passing (Cmp%)', 'Defensive (TklW)']
            orig_vals = [100, 100, 100, 100]
            sim_vals = [norm_team(new_xg, curr_xg), norm_team(new_xag, curr_xag), norm_team(new_cmp, curr_cmp), norm_team(new_tklw, curr_tklw)]

            fig_sim_radar = go.Figure()
            fig_sim_radar.add_trace(go.Scatterpolar(r=orig_vals + [orig_vals[0]], theta=radar_cats + [radar_cats[0]], fill='toself', name='Current Baseline (100%)', line_color='#94A3B8'))
            fig_sim_radar.add_trace(go.Scatterpolar(r=sim_vals + [sim_vals[0]], theta=radar_cats + [radar_cats[0]], fill='toself', name='Simulated Strategy', line_color='#38BDF8'))
            
            fig_sim_radar.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", 
                polar=dict(radialaxis=dict(visible=False, range=[0, max(sim_vals)+10])), 
                title="Team Tactical Profile Shift", 
                legend=dict(orientation="h", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_sim_radar, use_container_width=True)

        with col_impact:
            st.subheader("📈 Business & League Impact")
            st.markdown("Based on historical data models, how does this tactical shift affect the end-of-season outcomes?")
            
            gd_shift = (new_xg - curr_xg) + ((new_tklw - curr_tklw) * 0.08) 
            pt_shift = gd_shift * 0.65 
            
            st.info(f"⚽ **Est. Goal Difference:** {gd_shift:+.1f} goals")
            st.success(f"🏆 **Est. League Points:** {pt_shift:+.1f} points")
            
            max_change = max(abs(xg_imp), abs(xag_imp), abs(def_imp), abs(cmp_imp))
            est_cost = max(1.5, (max_change * 0.5))
            st.warning(f"💰 **Financial Implication:** Targeting these metric shifts requires an estimated **€{est_cost:.1f}M** investment in specialized coaching staff or equipment.")

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
        
        **2. Tactical Optimization:** Explore the What-If Engine. Shifting to a Gegenpressing preset provides the highest points-per-euro ROI based on current squad dynamics.
        
        **3. Roster Management:** Review the 'Underperformers' chart. Players showing a severe negative G-xG delta are costing the team points. Consider benching them.
        """)

elif analysis_mode == "👤 Player Insight":
    st.title("👤 Advanced Player Profiling")
    player = st.selectbox("Search & Select Player:", sorted(filtered_df['Player'].unique()))
    p = filtered_df[filtered_df['Player'] == player].iloc[0]
    pos = str(p.get('Pos', '')).upper()
    
    player_rating = calculate_player_rating(p, df)
    
    badges = f'<span class="badge badge-rating">⭐ {player_rating} / 10</span>'
    if p['Age'] <= 21 and p['MP'] >= 5: badges += '<span class="badge badge-wonder">💎 Wonderkid</span>'
    if p['Gls'] >= 8: badges += '<span class="badge badge-elite">🔥 Elite Scorer</span>'
    if p['Ast'] >= 5: badges += '<span class="badge badge-maestro">🎯 Playmaker</span>'

    col_img, col_info = st.columns([1, 4])
    with col_img:
        st.markdown(f"<img src='{get_player_face(player)}' style='width:100%; border-radius:15px; border:2px solid #38BDF8;'>", unsafe_allow_html=True)
        
    with col_info:
        st.markdown(f"<h2>{player} {badges}</h2>", unsafe_allow_html=True)
        flag_html = get_flag_logo(p['Comp'])
        st.markdown(f"**League:** {flag_html}{p['Comp']} &nbsp;|&nbsp; **Squad:** <img src='{get_team_logo(p['Squad'])}' width='24' style='vertical-align:middle; border-radius:4px;'> {p['Squad']}", unsafe_allow_html=True)
        st.markdown(f"**Position:** {p['Pos']} &nbsp;|&nbsp; **Age:** {int(p['Age'])}")
        st.markdown(f"**Appearances:** {int(p['MP'])} *(Starts: {int(p['Starts'])})* &nbsp;|&nbsp; **Minutes Played:** {int(p['Min'])}")
    
    st.markdown("---")
    
    m1, m2, m3, m4 = st.columns(4)
    if 'GK' in pos:
        m1.metric("Saves", int(p.get('Saves', 0)))
        m2.metric("Clean Sheets", int(p.get('CS', 0)))
        m3.metric("Goals Against", int(p.get('GA', 0)))
        m4.metric("Pass Acc. (%)", f"{float(p.get('Cmp%', 0)):.1f}%")
    elif 'DF' in pos:
        m1.metric("Tackles Won", int(p.get('TklW', 0)))
        m2.metric("Pass Acc. (%)", f"{float(p.get('Cmp%', 0)):.1f}%")
        m3.metric("Prog. Carries", int(p.get('PrgC', 0)))
        m4.metric("Cards (Y / R)", f"{int(p.get('CrdY', 0))} / {int(p.get('CrdR', 0))}")
    elif 'MF' in pos:
        m1.metric("Assists", int(p.get('Ast', 0)))
        m2.metric("Exp. Assists (xAG)", float(p.get('xAG', 0)))
        m3.metric("Pass Acc. (%)", f"{float(p.get('Cmp%', 0)):.1f}%")
        m4.metric("Prog. Carries", int(p.get('PrgC', 0)))
    else: # FW
        m1.metric("Total Goals", int(p.get('Gls', 0)))
        m2.metric("Expected Goals (xG)", float(p.get('xG', 0)))
        m3.metric("Total Assists", int(p.get('Ast', 0)))
        m4.metric("Exp. Assists (xAG)", float(p.get('xAG', 0)))
    
    st.markdown("---")
    st.subheader("🕸️ Attribute Radar vs. League Best")
    st.markdown("Visualizes the player's percentile rank compared to the maximum values achieved in their respective league.")
    
    league_max = df[df['Comp'] == p['Comp']]
    def norm(col): 
        if col not in league_max.columns: return 0
        m = league_max[col].max()
        return (p.get(col, 0) / m) * 100 if m > 0 else 0
    
    if 'GK' in pos:
        r_cols = ['Saves', 'CS', 'Cmp%', 'Min']
        r_names = ['Saves', 'Clean Sheets', 'Pass Acc (%)', 'Minutes Played']
        b_cols = ['Saves', 'CS', 'GA', 'Cmp%']
        b_names = ['Saves', 'Clean Sheets', 'Goals Against', 'Pass Acc (%)']
    elif 'DF' in pos:
        r_cols = ['TklW', 'Cmp%', 'PrgC', 'Ast', 'xG']
        r_names = ['Tackles Won', 'Pass Acc (%)', 'Prog. Carries', 'Assists', 'Attacking (xG)']
        b_cols = ['TklW', 'PrgC', 'Ast', 'xG']
        b_names = ['Tackles Won', 'Prog Carries', 'Assists', 'Exp Goals (xG)']
    elif 'MF' in pos:
        r_cols = ['xAG', 'Cmp%', 'PrgC', 'TklW', 'Gls']
        r_names = ['Playmaking (xAG)', 'Pass Acc (%)', 'Prog. Carries', 'Defensive Work', 'Goals']
        b_cols = ['Ast', 'xAG', 'PrgC', 'Gls']
        b_names = ['Assists', 'Exp Assists', 'Prog Carries', 'Goals']
    else: # FW
        r_cols = ['xG', 'Gls', 'xAG', 'Ast', 'PrgC']
        r_names = ['Exp Goals (xG)', 'Actual Goals', 'Playmaking (xAG)', 'Assists', 'Prog. Carries']
        b_cols = ['Gls', 'xG', 'Ast', 'xAG']
        b_names = ['Goals', 'Exp Goals', 'Assists', 'Exp Assists']

    radar_df = pd.DataFrame(dict(
        r=[norm(c) for c in r_cols],
        theta=r_names
    ))
    
    fig = px.line_polar(radar_df, r='r', theta='theta', line_close=True, range_r=[0,100], template="plotly_dark")
    fig.update_traces(fill='toself', fillcolor='rgba(56, 189, 248, 0.3)', line_color='#38BDF8', line_width=2)
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor='#334155'), angularaxis=dict(gridcolor='#334155')), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        comp_data = {'Metric': b_names, 'Value': [p.get(c, 0) for c in b_cols]}
        fig_bar = px.bar(comp_data, x='Metric', y='Value', text='Value', color='Metric')
        fig_bar.update_layout(title_text='Positional Output Breakdown', template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

elif analysis_mode == "⚔️ H2H Compare":
    st.title("⚔️ Head-to-Head Transfer Comparison")
    st.markdown("Compare two players side-by-side to make data-driven recruitment decisions.")
    
    available_players = sorted(filtered_df['Player'].unique())
    cl1, cl2 = st.columns(2)
    
    with cl1:
        p1_name = st.selectbox("Player 1 (Red)", available_players, index=available_players.index("Erling Haaland") if "Erling Haaland" in available_players else 0)
        p1 = filtered_df[filtered_df['Player']==p1_name].iloc[0]
        r1 = calculate_player_rating(p1, df)
        st.markdown(f"<div style='text-align:center;'><img src='{get_player_face(p1_name)}' width='150' style='border-radius:10px; border:2px solid #EF4444;'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; margin-top:10px;'><span class='badge badge-rating' style='margin:0;'>⭐ {r1}</span> <img src='{get_team_logo(p1['Squad'])}' width='20' style='vertical-align:middle; border-radius:3px;'> {p1['Squad']}</div>", unsafe_allow_html=True)
        
    with cl2:
        p2_idx = 1 if len(available_players) > 1 else 0
        p2_name = st.selectbox("Player 2 (Blue)", available_players, index=available_players.index("Mohamed Salah") if "Mohamed Salah" in available_players else p2_idx)
        p2 = filtered_df[filtered_df['Player']==p2_name].iloc[0]
        r2 = calculate_player_rating(p2, df)
        st.markdown(f"<div style='text-align:center;'><img src='{get_player_face(p2_name)}' width='150' style='border-radius:10px; border:2px solid #3B82F6;'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; margin-top:10px;'><span class='badge badge-rating' style='margin:0;'>⭐ {r2}</span> <img src='{get_team_logo(p2['Squad'])}' width='20' style='vertical-align:middle; border-radius:3px;'> {p2['Squad']}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    pos1 = str(p1.get('Pos', '')).upper()
    
    if 'GK' in pos1:
        categories = ['Saves', 'Clean Sheets', 'Pass Acc (%)', 'Minutes']
        cols = ['Saves', 'CS', 'Cmp%', 'Min']
    elif 'DF' in pos1:
        categories = ['Tackles (TklW)', 'Pass Acc (%)', 'Ball Carry (PrgC)', 'Assists', 'Exp Goals (xG)']
        cols = ['TklW', 'Cmp%', 'PrgC', 'Ast', 'xG']
    elif 'MF' in pos1:
        categories = ['Assists', 'Playmaking (xAG)', 'Pass Acc (%)', 'Ball Carry (PrgC)', 'Tackles (TklW)']
        cols = ['Ast', 'xAG', 'Cmp%', 'PrgC', 'TklW']
    else: # FW
        categories = ['Goals', 'Exp Goals (xG)', 'Assists', 'Exp Assists (xAG)', 'Ball Carry (PrgC)']
        cols = ['Gls', 'xG', 'Ast', 'xAG', 'PrgC']
        
    def norm_h2h(val, col): 
        if col not in df.columns: return 0
        max_v = df[col].max()
        return (val / max_v) * 100 if max_v > 0 else 0
        
    p1_vals = [norm_h2h(p1.get(c, 0), c) for c in cols]
    p2_vals = [norm_h2h(p2.get(c, 0), c) for c in cols]

    fig_h2h = go.Figure()
    fig_h2h.add_trace(go.Scatterpolar(r=p1_vals + [p1_vals[0]], theta=categories + [categories[0]], fill='toself', name=p1['Player'], line_color='#EF4444'))
    fig_h2h.add_trace(go.Scatterpolar(r=p2_vals + [p2_vals[0]], theta=categories + [categories[0]], fill='toself', name=p2['Player'], line_color='#3B82F6'))
    
    fig_h2h.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor='#334155'), angularaxis=dict(gridcolor='#334155')), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    
    c_radar, c_stats = st.columns([1.5, 1])
    with c_radar: 
        st.plotly_chart(fig_h2h, use_container_width=True)
    with c_stats:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.metric(f"AI Overall Score", f"{r1} / 10", delta=round(r1 - r2, 1))
        
        if 'GK' in pos1:
            st.metric(f"Saves Comparison", f"{int(p1.get('Saves',0))} vs {int(p2.get('Saves',0))}", delta=int(p1.get('Saves',0) - p2.get('Saves',0)))
            st.metric(f"Clean Sheets Comparison", f"{int(p1.get('CS',0))} vs {int(p2.get('CS',0))}", delta=int(p1.get('CS',0) - p2.get('CS',0)))
        elif 'DF' in pos1:
            st.metric(f"Tackles Won Comparison", f"{int(p1.get('TklW',0))} vs {int(p2.get('TklW',0))}", delta=int(p1.get('TklW',0) - p2.get('TklW',0)))
            st.metric(f"Prog. Carries Comparison", f"{int(p1.get('PrgC',0))} vs {int(p2.get('PrgC',0))}", delta=int(p1.get('PrgC',0) - p2.get('PrgC',0)))
        elif 'MF' in pos1:
            st.metric(f"Assists Comparison", f"{int(p1.get('Ast',0))} vs {int(p2.get('Ast',0))}", delta=int(p1.get('Ast',0) - p2.get('Ast',0)))
            st.metric(f"Playmaking (xAG)", f"{float(p1.get('xAG',0)):.2f} vs {float(p2.get('xAG',0)):.2f}", delta=round(p1.get('xAG',0) - p2.get('xAG',0), 2))
        else: # FW
            st.metric(f"Goals Comparison", f"{int(p1.get('Gls',0))} vs {int(p2.get('Gls',0))}", delta=int(p1.get('Gls',0) - p2.get('Gls',0)))
            st.metric(f"Finishing Potential (xG)", f"{float(p1.get('xG',0)):.2f} vs {float(p2.get('xG',0)):.2f}", delta=round(p1.get('xG',0) - p2.get('xG',0), 2))
