import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="FIFA 2026 Predictions", layout="wide", initial_sidebar_state="expanded")

# ============================================================================
# LOAD DATA
# ============================================================================
@st.cache_data
def load_data():
    try:
        group_fixtures = pd.read_csv("dataset/group_fixtures.csv")
        knockout_slots = pd.read_csv("dataset/knockout_slots.csv")
        predictions = pd.read_csv("result/predict_matches.csv")
        fifa_rankings = pd.read_csv("result/fifa_rankings.csv")
        group_stage_predictions = pd.read_csv("result/group_stage_predictions.csv")
        return {
            "group_fixtures": group_fixtures,
            "knockout_slots": knockout_slots,
            "predictions": predictions,
            "fifa_rankings": fifa_rankings,
            "group_stage_predictions": group_stage_predictions
        }
    except FileNotFoundError as e:
        st.error(f"Error loading data: {e}")
        return None

data = load_data()

if data is None:
    st.stop()

group_fixtures = data["group_fixtures"]
knockout_slots = data["knockout_slots"]
predictions = data["predictions"]
fifa_rankings = data["fifa_rankings"]
group_stage_predictions = data["group_stage_predictions"]

# ============================================================================
# SIDEBAR - NAVIGATION
# ============================================================================
st.sidebar.title("🏆 FIFA World Cup 2026")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "⚽ Group Stage", "🏅 Knockouts", "📈 Analysis", "🏆 Final Standings"]
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .prediction-box {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    .match-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================
if page == "📊 Dashboard":
    st.title("🏆 FIFA World Cup 2026 Prediction Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Matches", 104, "72 Group + 32 Knockout")
    with col2:
        st.metric("Teams", 48, "12 Groups")
    with col3:
        st.metric("Top Ranked", "Brazil", fifa_rankings.iloc[0]['Points'])
    with col4:
        st.metric("Predictions", len(predictions), "Complete")

    st.markdown("---")

    # Top predictions by probability
    st.subheader("🔥 Most Certain Predictions")
    predictions_copy = predictions.copy()
    predictions_copy['max_prob'] = predictions_copy[['home_win', 'away_win', 'draw']].max(axis=1)
    top_predictions = predictions_copy.nlargest(5, 'max_prob')[['home_team', 'away_team', 'Group', 'home_win', 'away_win', 'draw', 'Probable team win']]

    cols = st.columns(5)
    for idx, (_, row) in enumerate(top_predictions.iterrows()):
        with cols[idx]:
            st.markdown(f"""
            <div class='match-card'>
                <b>{row['home_team']}</b> vs <b>{row['away_team']}</b><br>
                Group {row['Group']}<br>
                <span style='color: green; font-weight: bold;'>{row['Probable team win']} to win</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Group standings overview
    st.subheader("📋 Group Standings Overview")
    group_standings = group_stage_predictions.groupby('group')[['pts']].sum().reset_index()
    group_standings.columns = ['Group', 'Total Points Awarded']

    fig = px.bar(
        group_standings,
        x='Group',
        y='Total Points Awarded',
        title='Total Points by Group',
        color='Total Points Awarded',
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE: GROUP STAGE
# ============================================================================
elif page == "⚽ Group Stage":
    st.title("⚽ Group Stage Predictions")

    # Group selector
    groups = sorted(group_fixtures['group'].unique())
    selected_group = st.selectbox("Select Group", groups)

    # Filter data for selected group
    group_data = predictions[predictions['Group'] == selected_group].copy()
    group_fixtures_filtered = group_fixtures[group_fixtures['group'] == selected_group]

    st.markdown(f"### Group {selected_group}")

    # Show matches in group
    for idx, (_, match) in enumerate(group_data.iterrows()):
        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])

        with col1:
            st.write(f"**{match['home_team']}**")
        with col2:
            st.write("vs")
        with col3:
            st.write(f"**{match['away_team']}**")
        with col4:
            win_prob = f"{match['Probable team win']}"
            st.write(f"*{win_prob} to win*")

        # Prediction details
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.write(f"🏠 Home: {match['home_win']:.1f}%")
        with col2:
            st.write(f"⚖️ Draw: {match['draw']:.1f}%")
        with col3:
            st.write(f"🏃 Away: {match['away_win']:.1f}%")
        with col4:
            st.write(f"⚽ Avg Goals: {match['expected_total_goals']}")
        with col5:
            st.write(f"Top: {match['top_scorelines'][0][0]}")

        st.markdown("---")

    # Group table
    st.subheader(f"Group {selected_group} Table")
    group_table = group_stage_predictions[group_stage_predictions['group'] == selected_group].sort_values('pts', ascending=False)
    group_table_display = group_table[['team', 'W', 'D', 'L', 'pts']].copy()
    group_table_display.columns = ['Team', 'Wins', 'Draws', 'Losses', 'Points']
    st.dataframe(group_table_display, hide_index=True, use_container_width=True)

# ============================================================================
# PAGE: KNOCKOUTS
# ============================================================================
elif page == "🏅 Knockouts":
    st.title("🏅 Knockout Stage")

    # Round selector
    knockout_rounds = sorted(knockout_slots['round'].unique(), key=lambda x: ['Round of 32', 'Round of 16', 'Quarter-final', 'Semi-final', 'Third-place playoff', 'Final'].index(x))
    selected_round = st.selectbox("Select Round", knockout_rounds)

    round_data = knockout_slots[knockout_slots['round'] == selected_round]

    st.markdown(f"### {selected_round}")
    st.write(f"Score Multiplier: **{round_data.iloc[0]['multiplier']}x**")
    st.markdown("---")

    for _, match in round_data.iterrows():
        match_id = int(match['match_id'])
        slot_home = match['slot_home']
        slot_away = match['slot_away']
        venue = match['venue']

        st.markdown(f"""
        <div class='match-card'>
            <b>Match {match_id}</b> | {venue}<br>
            <i style='color: gray;'>{slot_home} vs {slot_away}</i>
        </div>
        """, unsafe_allow_html=True)

    st.info("✅ Knockout matches will show confirmed teams once group stage results are known.")

# ============================================================================
# PAGE: ANALYSIS
# ============================================================================
elif page == "📈 Analysis":
    st.title("📈 Prediction Analysis")

    # Win probability distribution
    st.subheader("Win Probability Distribution")

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Box(y=predictions['home_win'], name='Home Win %'))
        fig.add_trace(go.Box(y=predictions['away_win'], name='Away Win %'))
        fig.add_trace(go.Box(y=predictions['draw'], name='Draw %'))
        fig.update_layout(title="Win Probability Distribution by Match", height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=predictions['home_win'], name='Home Win', opacity=0.7))
        fig.add_trace(go.Histogram(x=predictions['away_win'], name='Away Win', opacity=0.7))
        fig.update_layout(title="Home vs Away Win Rate Distribution", barmode='overlay', height=400)
        st.plotly_chart(fig, use_container_width=True)

    # Expected goals analysis
    st.subheader("Expected Goals Analysis")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.histogram(
            predictions,
            x='expected_total_goals',
            nbins=20,
            title='Distribution of Expected Total Goals',
            labels={'expected_total_goals': 'Expected Goals'}
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        avg_goals_by_group = predictions.groupby('Group')['expected_total_goals'].mean().reset_index()
        fig = px.bar(
            avg_goals_by_group,
            x='Group',
            y='expected_total_goals',
            title='Average Expected Goals by Group',
            labels={'expected_total_goals': 'Avg Goals'}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Top predictions by confidence
    st.subheader("Top Predictions by Confidence")
    predictions_sorted = predictions.copy()
    predictions_sorted['max_prob'] = predictions_sorted[['home_win', 'away_win', 'draw']].max(axis=1)
    top_confident = predictions_sorted.nlargest(10, 'max_prob')[['home_team', 'away_team', 'Group', 'home_win', 'away_win', 'draw', 'Probable team win', 'expected_total_goals']]

    display_df = top_confident.copy()
    display_df.columns = ['Home', 'Away', 'Group', 'Home %', 'Away %', 'Draw %', 'Predicted Winner', 'Exp. Goals']
    st.dataframe(display_df, hide_index=True, use_container_width=True)

# ============================================================================
# PAGE: FINAL STANDINGS
# ============================================================================
elif page == "🏆 Final Standings":
    st.title("🏆 Predicted Final Group Standings")

    # Group selector
    groups = sorted(group_stage_predictions['group'].unique())

    cols = st.columns(3)
    col_idx = 0

    for group in groups:
        with cols[col_idx % 3]:
            st.subheader(f"Group {group}")
            group_table = group_stage_predictions[group_stage_predictions['group'] == group].sort_values('pts', ascending=False)
            group_table_display = group_table[['team', 'W', 'D', 'L', 'pts']].copy()
            group_table_display.columns = ['Team', 'W', 'D', 'L', 'Pts']
            st.dataframe(group_table_display, hide_index=True, use_container_width=True)

        col_idx += 1

    # Summary statistics
    st.markdown("---")
    st.subheader("📊 Qualification Summary")

    qualified_teams = group_stage_predictions[group_stage_predictions.index < 2].groupby('group')['team'].apply(list).reset_index()
    qualified_teams.columns = ['Group', 'Qualified Teams']

    for _, row in qualified_teams.iterrows():
        st.write(f"**Group {row['Group']}:** {' & '.join(row['Qualified Teams'])}")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
    📊 FIFA World Cup 2026 Predictions | Built with Streamlit
    <br>Based on ELO Ratings and Poisson Distribution Model
</div>
""", unsafe_allow_html=True)
