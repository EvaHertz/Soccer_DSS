import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Top 5 Leagues DSS", page_icon="🌍", layout="wide")

# --- ÖZEL CSS (SİYAH-LACİVERT GRADYAN VE MODERN UI) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    /* Global Font and Background */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    .stApp {
        background: linear-gradient(135deg, #020617 0%, #0F172A 50%, #1E293B 100%);
        color: #F8FAFC;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: rgba(2, 6, 23, 0.7);
        border-right: 1px solid #334155;
    }

    /* Group 6 Özel Başlık Tasarımı */
    .group-header {
        color: #FFFFFF !important;
        font-size: 26px !important;
        font-weight: 800 !important;
        letter-spacing: 2px;
        margin-bottom: -10px;
    }

    /* Metrik Kartları (Cam Efekti - Glassmorphism) */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid #38BDF8;
        padding: 20px;
        border-radius: 16px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: #0EA5E9;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 1px solid #334155;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px 8px 0px 0px;
        padding: 12px 20px;
        color: #94A3B8;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(56, 189, 248, 0.1);
        color: #38BDF8;
        border-bottom: 2px solid #38BDF8;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
</style>
""", unsafe_allow_html=True)


# --- 1. DATA COMPONENT ---
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
    
    num_cols = df.select_dtypes(include=['number']).columns
    df[num_cols] = df[num_cols].fillna(0)
    str_cols = df.select_dtypes(exclude=['number']).columns
    df[str_cols] = df[str_cols].fillna("")
    
    return df

df = load_data()

# --- SIDEBAR (USER CONTROLS) ---

# Sol Üst: Group 6 İmzası ve İsimler
st.sidebar.markdown('<p class="group-header">GROUP 6</p>', unsafe_allow_html=True)
with st.sidebar.expander("Team Members", expanded=False):
    st.markdown("""
    * Ahmet Tarık Orhan
    * Ali Eren Kurt
    * Mustafa Düşünceli
    * Ahmet Can Vurmaz
    """)

st.sidebar.markdown("---")
st.sidebar.title("⚙️ DSS Control Panel")
st.sidebar.markdown("Configure your analysis parameters below.")

league_list = ["All Europe (Top 5)"] + sorted(list(df['Comp'].unique()))
selected_league = st.sidebar.selectbox("🌍 Select League", league_list)

if selected_league != "All Europe (Top 5)":
    filtered_df = df[df['Comp'] == selected_league]
else:
    filtered_df = df

team_list = ["All Teams"] + sorted(list(filtered_df['Squad'].unique()))
selected_team = st.sidebar.selectbox("🏟️ Select Squad", team_list)

if selected_team != "All Teams":
    filtered_df = filtered_df[filtered_df['Squad'] == selected_team]

st.sidebar.markdown("---")
analysis_mode = st.sidebar.radio("🔍 View Mode:", ["📊 Team/League Analysis", "👤 Player Profiling"])


# --- MAIN CONTENT AREA ---
if analysis_mode == "📊 Team/League Analysis":
    header_text = selected_team if selected_team != 'All Teams' else selected_league
    st.title(f"⚽ Football Intelligence Hub: {header_text}")
    st.markdown("Leverage data analytics for squad planning, performance evaluation, and predictive modeling.")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Descriptive (What happened?)", 
        "🧪 Diagnostic (Why & What-If?)", 
        "🔮 Predictive (What's next?)", 
        "💡 Prescriptive (Action Plan)"
    ])
    
    # --- TAB 1: DESCRIPTIVE ---
    with tab1:
        st.subheader("Overview Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Players Analyzed", len(filtered_df))
        c2.metric("Total Goals Scored", int(filtered_df['Gls'].sum()))
        c3.metric("Total Assists", int(filtered_df['Ast'].sum()))
        c4.metric("Average Squad Age", round(filtered_df['Age'].mean(), 1))
        
        st.markdown("<br>", unsafe_allow_html=True)
        colA, colB = st.columns(2)
        
        with colA:
            st.subheader("🔥 Top 10 Goalscorers")
            top_scorers = filtered_df.sort_values(by='Gls', ascending=False).head(10)
            fig1 = px.bar(top_scorers, x='Player', y='Gls', text='Gls', color='Gls', color_continuous_scale='Blues')
            fig1.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
            
        with colB:
            st.subheader("🥶 Top 10 Underperformers (G-xG)")
            st.caption("Players with lowest Goals minus Expected Goals (Minimum 300 mins played).")
            worst_finishers = filtered_df[filtered_df['Min'] > 300].sort_values(by='G-xG', ascending=True).head(10)
            fig_worst = px.bar(worst_finishers, x='Player', y='G-xG', text='G-xG', color='G-xG', color_continuous_scale='Reds_r')
            fig_worst.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig_worst, use_container_width=True)

    # --- TAB 2: DIAGNOSTIC / WHAT-IF ---
    with tab2:
        st.subheader("Attacking Efficiency Simulator (What-If)")
        st.info("Hypothesis: If we allocate more budget to offensive coaching and finishing drills, how does it impact our Expected Goals (xG) output?")
        
        current_xg = filtered_df['xG'].sum()
        imp_pct = st.slider(
            "Finishing Improvement Target (%)", 
            min_value=0, max_value=50, value=15, step=5,
            help="Simulates the percentage increase in shot quality and conversion rates."
        )
        new_xg = current_xg * (1 + (imp_pct / 100))
        
        sc1, sc2 = st.columns(2)
        sc1.metric("Current Total xG", f"{current_xg:.2f}")
        sc2.metric("Projected New xG", f"{new_xg:.2f}", delta=f"+{new_xg - current_xg:.2f}")

    # --- TAB 3: PREDICTIVE ---
    with tab3:
        st.subheader("End of Season Forecast (Matchweek 38)")
        st.markdown("Linear projection model based on current Goals per Match Played (MP) ratio.")
        
        top_players = filtered_df.sort_values(by='Gls', ascending=False).head(15)
        predictive_list = []
        for _, row in top_players.iterrows():
            if row['MP'] > 0:
                forecast = (row['Gls'] / row['MP']) * 38
                predictive_list.append({
                    "League": row['Comp'],
                    "Squad": row['Squad'],
                    "Player": row['Player'],
                    "Matches Played": row['MP'],
                    "Current Goals": row['Gls'],
                    "MW38 Forecast": round(forecast)
                })
        pred_df = pd.DataFrame(predictive_list)
        pred_df.index = np.arange(1, len(pred_df) + 1)
        st.dataframe(pred_df, use_container_width=True)
        
        csv = pred_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Forecast Data (CSV)",
            data=csv,
            file_name='forecast_mw38.csv',
            mime='text/csv',
        )

    # --- TAB 4: PRESCRIPTIVE ---
    with tab4:
        st.subheader("💡 System Recommendations & Action Plan")
        st.success("""
        **1. Transfer Strategy (Recruitment):** Data indicates that players under 24 exhibit a higher growth trajectory in xG per 90 mins. Allocate the upcoming transfer budget towards young, high-potential midfielders.
        
        **2. Tactical Optimization:** The What-If scenario proves that a 15% increase in shot quality yields a massive output advantage. Implement specialized finishing camps immediately.
        
        **3. Roster Management:** Review the 'Underperformers' chart. Players showing a severe negative G-xG delta are costing the team points. Consider benching them or applying rigorous individual training plans.
        """)

elif analysis_mode == "👤 Player Profiling":
    st.title("👤 Advanced Player Radar")
    st.markdown("Deep dive into individual player metrics compared to league benchmarks.")
    
    available_players = sorted(filtered_df['Player'].unique())
    target_player = st.selectbox("Search & Select Player:", available_players)
    
    p_data = filtered_df[filtered_df['Player'] == target_player].iloc[0]
    st.markdown("---")
    
    col_img, col_info = st.columns([1, 4])
    with col_img:
        avatar_url = f"https://ui-avatars.com/api/?name={target_player.replace(' ', '+')}&background=0F172A&color=38BDF8&size=200&rounded=true&bold=true"
        st.image(avatar_url, use_container_width=True)
        
    with col_info:
        st.subheader(p_data['Player'])
        st.markdown(f"**League:** {p_data['Comp']} &nbsp;|&nbsp; **Squad:** {p_data['Squad']}")
        st.markdown(f"**Position:** {p_data['Pos']} &nbsp;|&nbsp; **Age:** {int(p_data['Age'])}")
        st.markdown(f"**Appearances:** {int(p_data['MP'])} *(Starts: {int(p_data['Starts'])})*")

    st.markdown("<br>", unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Goals", int(p_data['Gls']))
    m2.metric("Assists", int(p_data['Ast']))
    m3.metric("Expected Goals (xG)", float(p_data['xG']))
    m4.metric("Cards (Y / R)", f"{int(p_data['CrdY'])} / {int(p_data['CrdR'])}")
    
    st.markdown("---")
    
    st.subheader("🕸️ Attribute Radar vs. League Best")
    st.markdown("Visualizes the player's percentile rank compared to the maximum values achieved in their respective league. **Indentations towards the center represent weaknesses.**")
    
    league_df = df[df['Comp'] == p_data['Comp']]
    max_xg = league_df['xG'].max() if league_df['xG'].max() > 0 else 1
    max_xag = league_df['xAG'].max() if league_df['xAG'].max() > 0 else 1
    max_prgc = league_df['PrgC'].max() if league_df['PrgC'].max() > 0 else 1
    max_tklw = league_df['TklW'].max() if league_df['TklW'].max() > 0 else 1
    
    score_xg = (p_data['xG'] / max_xg) * 100
    score_xag = (p_data['xAG'] / max_xag) * 100
    score_cmp = p_data.get('Cmp%', 0)
    score_prgc = (p_data['PrgC'] / max_prgc) * 100
    score_tklw = (p_data['TklW'] / max_tklw) * 100
    
    radar_data = pd.DataFrame(dict(
        Value=[score_xg, score_xag, score_cmp, score_prgc, score_tklw],
        Attribute=['Attacking Threat (xG)', 'Playmaking (xAG)', 'Pass Accuracy (%)', 'Ball Progression', 'Defensive Work']
    ))
    
    fig_radar = px.line_polar(radar_data, r='Value', theta='Attribute', line_close=True, range_r=[0,100], markers=True)
    fig_radar.update_traces(fill='toself', fillcolor='rgba(56, 189, 248, 0.3)', line=dict(color='#38BDF8', width=2))
    fig_radar.update_layout(
        template="plotly_dark", 
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='#334155'),
            angularaxis=dict(gridcolor='#334155')
        )
    )
    
    g1, g2 = st.columns([1, 1])
    with g1:
        st.plotly_chart(fig_radar, use_container_width=True)
        
    with g2:
        comp_data = {
            'Metric': ['Actual Goals', 'Expected Goals (xG)', 'Actual Assists', 'Expected Assists (xAG)'],
            'Value': [p_data['Gls'], p_data['xG'], p_data['Ast'], p_data['xAG']]
        }
        fig_bar = px.bar(comp_data, x='Metric', y='Value', text='Value', color='Metric')
        fig_bar.update_layout(
            title_text='Offensive Output Breakdown',
            template="plotly_dark", 
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)