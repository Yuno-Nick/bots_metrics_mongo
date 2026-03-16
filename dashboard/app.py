"""AI Agent Analytics Dashboard — Streamlit app."""

from datetime import timedelta

import streamlit as st

from dashboard.charts import (
    bar_chart,
    format_cost,
    line_chart,
    pie_chart,
    stacked_bar,
)
from dashboard.db import (
    get_channel_distribution,
    get_conversation_counts,
    get_cost_summary,
    get_daily_conversations,
    get_daily_costs,
    get_daily_trend,
    get_engagement_depth,
    get_failures,
    get_model_usage,
    get_token_usage,
    get_top_tools,
    get_tool_stats,
    get_user_breakdown,
    get_weekly_users,
)

# ── Page config ──────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Agent Analytics",
    page_icon="🤖",
    layout="wide",
)

# ── Sidebar ──────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("AI Agent Analytics")
    st.divider()
    agent = st.radio(
        "Select Agent",
        options=["All Agents", "Tommy", "Partnerships"],
        index=0,
    )
    st.divider()
    st.caption("Auto-refresh: every 1 hour")
    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.rerun()

# Normalize selection
selected = agent if agent != "All Agents" else None


# ── Auto-refresh fragment ────────────────────────────────────────────────

@st.fragment(run_every=timedelta(hours=1))
def _auto_refresh():
    """Clears cache periodically to pull fresh data."""
    pass


_auto_refresh()

# ── 1. KPI Cards ────────────────────────────────────────────────────────

st.header("Overview")

try:
    counts = get_conversation_counts(selected)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Conversations", f"{counts['total']:,}")
    c2.metric("Last 30 Days", f"{counts['last_30d']:,}")
    c3.metric("Last 7 Days", f"{counts['last_7d']:,}")
    c4.metric("Failures", f"{counts['failures']:,}")
except Exception as e:
    st.error(f"Could not load conversation counts: {e}")

# ── 2. Daily Conversation Trend ─────────────────────────────────────────

st.header("Daily Conversation Trend")

try:
    daily_df = get_daily_conversations(selected)
    if not daily_df.empty:
        fig = line_chart(daily_df, x="date", y="count", title="Conversations per Day", color="agent")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No conversation data available.")
except Exception as e:
    st.error(f"Could not load daily conversations: {e}")

# ── 3. User Breakdown ───────────────────────────────────────────────────

st.header("User Breakdown (Last 30 Days)")

try:
    users_df = get_user_breakdown(selected)
    if not users_df.empty:
        col_table, col_chart = st.columns([1, 1])
        with col_table:
            display_df = users_df.copy()
            display_df["total_cost"] = display_df["total_cost"].apply(format_cost)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        with col_chart:
            fig = bar_chart(
                users_df.head(10),
                x="user",
                y="conversations",
                title="Top Users by Conversations",
                horizontal=True,
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No user data available.")
except Exception as e:
    st.error(f"Could not load user breakdown: {e}")

# ── 4. Cost Analytics ───────────────────────────────────────────────────

st.header("Cost Analytics")

try:
    cost = get_cost_summary(selected)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Cost", format_cost(cost["total_cost"]))
    c2.metric("Avg Cost / Conversation", format_cost(cost["avg_cost"]))
    c3.metric("Conversations", f"{cost['conversations']:,}")

    daily_cost_df = get_daily_costs(selected)
    if not daily_cost_df.empty:
        fig = line_chart(
            daily_cost_df,
            x="date",
            y="total_cost",
            title="Daily Cost Trend",
            color="agent",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No cost data available.")
except Exception as e:
    st.error(f"Could not load cost analytics: {e}")

# ── 5. Token Usage ──────────────────────────────────────────────────────

st.header("Token Usage")

try:
    token_df = get_token_usage(selected)
    if not token_df.empty:
        fig = stacked_bar(
            token_df,
            x="agent",
            y_cols=["tokens_in", "tokens_out", "cache_read", "cache_write"],
            title="Token Breakdown by Agent",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No token data available.")
except Exception as e:
    st.error(f"Could not load token usage: {e}")

# ── 6. Tool Usage ───────────────────────────────────────────────────────

st.header("Tool Usage")

try:
    tools_df = get_top_tools(selected)
    if not tools_df.empty:
        fig = bar_chart(
            tools_df,
            x="tool",
            y="count",
            title="Top 15 Tools",
            horizontal=True,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tool usage data available.")
except Exception as e:
    st.error(f"Could not load tool usage: {e}")

# ── 7. Channel Distribution ─────────────────────────────────────────────

st.header("Channel Distribution")

try:
    channel_df = get_channel_distribution(selected)
    if not channel_df.empty:
        fig = pie_chart(channel_df, names="channel", values="count", title="Conversations by Channel")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No channel data available.")
except Exception as e:
    st.error(f"Could not load channel distribution: {e}")

# ── 8. Failures ──────────────────────────────────────────────────────────

with st.expander("Failures (conversations with zero assistant replies)"):
    try:
        fail_df = get_failures(selected)
        if not fail_df.empty:
            st.dataframe(fail_df, use_container_width=True, hide_index=True)
        else:
            st.success("No failures detected.")
    except Exception as e:
        st.error(f"Could not load failures: {e}")
