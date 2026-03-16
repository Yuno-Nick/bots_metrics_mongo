"""MongoDB query functions for the AI Agent Analytics dashboard."""

import os
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Optional

import pandas as pd
import streamlit as st
from pymongo import MongoClient

from config import AGENTS, CACHE_TTL, MONGO_DB, MONGO_URI, TLS_CA_FILE


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    """Return a singleton MongoClient with TLS configured for DocumentDB."""
    kwargs: dict = {
        "tls": True,
        "tlsCAFile": TLS_CA_FILE,
        "tlsAllowInvalidHostnames": True,
    }
    if not os.path.exists(TLS_CA_FILE):
        # Local dev without TLS
        kwargs = {}
    return MongoClient(MONGO_URI, **kwargs)


def get_collection():
    """Return the conversations collection."""
    return get_client()[MONGO_DB]["conversations"]


def _agent_filter(agent: Optional[str]) -> dict:
    """Build a $match filter for the given agent selection.

    agent: "Tommy", "Partnerships", or None / "All Agents" for no filter.
    """
    if agent and agent in AGENTS:
        return {"agent_name": AGENTS[agent]}
    return {}


def _days_ago(n: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=n)


# ── 1. Conversation Counts (KPI cards) ──────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_conversation_counts(agent: Optional[str] = None) -> dict:
    """Total, 30-day, 7-day conversation counts and failure count."""
    col = get_collection()
    base = _agent_filter(agent)

    total = col.count_documents(base)
    last_30d = col.count_documents({**base, "created_at": {"$gte": _days_ago(30)}})
    last_7d = col.count_documents({**base, "created_at": {"$gte": _days_ago(7)}})

    # Failures: conversations with zero assistant messages
    pipeline = [
        {"$match": base} if base else {"$match": {}},
        {"$project": {
            "assistant_count": {
                "$size": {"$filter": {
                    "input": "$messages",
                    "cond": {"$eq": ["$$this.role", "assistant"]},
                }}
            }
        }},
        {"$match": {"assistant_count": 0}},
        {"$count": "failures"},
    ]
    result = list(col.aggregate(pipeline))
    failures = result[0]["failures"] if result else 0

    return {
        "total": total,
        "last_30d": last_30d,
        "last_7d": last_7d,
        "failures": failures,
    }


# ── 2. Daily Conversations (trend line chart) ───────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_daily_conversations(agent: Optional[str] = None) -> pd.DataFrame:
    """Daily conversation counts per agent over last 30 days."""
    col = get_collection()
    match = {"created_at": {"$gte": _days_ago(30)}}
    match.update(_agent_filter(agent))

    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "agent": "$agent_name",
            },
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id.date": 1}},
    ]
    rows = list(col.aggregate(pipeline))
    if not rows:
        return pd.DataFrame(columns=["date", "agent", "count"])
    df = pd.DataFrame([
        {"date": r["_id"]["date"], "agent": r["_id"]["agent"], "count": r["count"]}
        for r in rows
    ])
    df["date"] = pd.to_datetime(df["date"])
    return df


# ── 3. User Breakdown (table + bar chart) ───────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_user_breakdown(agent: Optional[str] = None) -> pd.DataFrame:
    """Conversations per user in last 30 days with message & cost totals."""
    col = get_collection()
    match = {"created_at": {"$gte": _days_ago(30)}}
    match.update(_agent_filter(agent))

    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": {"id": "$requester_id", "name": "$requester_name"},
            "conversations": {"$sum": 1},
            "total_messages": {"$sum": {"$size": "$messages"}},
            "total_cost": {"$sum": "$total_cost"},
        }},
        {"$sort": {"conversations": -1}},
    ]
    rows = list(col.aggregate(pipeline))
    if not rows:
        return pd.DataFrame(columns=["user", "conversations", "total_messages", "total_cost"])
    return pd.DataFrame([
        {
            "user": r["_id"].get("name") or r["_id"].get("id", "unknown"),
            "conversations": r["conversations"],
            "total_messages": r["total_messages"],
            "total_cost": round(r.get("total_cost", 0) or 0, 4),
        }
        for r in rows
    ])


# ── 4. Cost Summary (KPI cards) ─────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_cost_summary(agent: Optional[str] = None) -> dict:
    """Total cost, avg cost per conversation, conversation count."""
    col = get_collection()
    base = _agent_filter(agent)

    pipeline = [
        {"$match": base} if base else {"$match": {}},
        {"$group": {
            "_id": None,
            "total_cost": {"$sum": "$total_cost"},
            "avg_cost": {"$avg": "$total_cost"},
            "conversations": {"$sum": 1},
        }},
    ]
    rows = list(col.aggregate(pipeline))
    if not rows:
        return {"total_cost": 0, "avg_cost": 0, "conversations": 0}
    r = rows[0]
    return {
        "total_cost": round(r.get("total_cost", 0) or 0, 4),
        "avg_cost": round(r.get("avg_cost", 0) or 0, 4),
        "conversations": r.get("conversations", 0),
    }


# ── 5. Daily Costs (cost trend chart) ───────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_daily_costs(agent: Optional[str] = None) -> pd.DataFrame:
    """Daily cost trend over last 30 days."""
    col = get_collection()
    match = {"created_at": {"$gte": _days_ago(30)}}
    match.update(_agent_filter(agent))

    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "agent": "$agent_name",
            },
            "total_cost": {"$sum": "$total_cost"},
            "conversations": {"$sum": 1},
        }},
        {"$sort": {"_id.date": 1}},
    ]
    rows = list(col.aggregate(pipeline))
    if not rows:
        return pd.DataFrame(columns=["date", "agent", "total_cost", "conversations"])
    df = pd.DataFrame([
        {
            "date": r["_id"]["date"],
            "agent": r["_id"]["agent"],
            "total_cost": round(r.get("total_cost", 0) or 0, 4),
            "conversations": r["conversations"],
        }
        for r in rows
    ])
    df["date"] = pd.to_datetime(df["date"])
    return df


# ── 6. Token Usage (stacked bar) ────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_token_usage(agent: Optional[str] = None) -> pd.DataFrame:
    """Token breakdown by agent: input, output, cache read/write."""
    col = get_collection()
    base = _agent_filter(agent)

    pipeline = [
        {"$match": base} if base else {"$match": {}},
        {"$unwind": "$messages"},
        {"$match": {"messages.role": "assistant"}},
        {"$group": {
            "_id": "$agent_name",
            "tokens_in": {"$sum": "$messages.tokens_in"},
            "tokens_out": {"$sum": "$messages.tokens_out"},
            "cache_read": {"$sum": "$messages.cache_read"},
            "cache_write": {"$sum": "$messages.cache_write"},
            "messages": {"$sum": 1},
        }},
        {"$sort": {"tokens_out": -1}},
    ]
    rows = list(col.aggregate(pipeline))
    if not rows:
        return pd.DataFrame(columns=["agent", "tokens_in", "tokens_out", "cache_read", "cache_write"])
    return pd.DataFrame([
        {
            "agent": r["_id"],
            "tokens_in": r.get("tokens_in", 0) or 0,
            "tokens_out": r.get("tokens_out", 0) or 0,
            "cache_read": r.get("cache_read", 0) or 0,
            "cache_write": r.get("cache_write", 0) or 0,
        }
        for r in rows
    ])


# ── 7. Top Tools (bar chart) ────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_top_tools(agent: Optional[str] = None) -> pd.DataFrame:
    """Most frequently called tools."""
    col = get_collection()
    base = _agent_filter(agent)

    pipeline = [
        {"$match": base} if base else {"$match": {}},
        {"$unwind": "$messages"},
        {"$match": {"messages.role": "assistant", "messages.tool_calls": {"$exists": True, "$ne": []}}},
        {"$unwind": "$messages.tool_calls"},
        {"$group": {
            "_id": "$messages.tool_calls",
            "count": {"$sum": 1},
        }},
        {"$sort": {"count": -1}},
        {"$limit": 15},
    ]
    rows = list(col.aggregate(pipeline))
    if not rows:
        return pd.DataFrame(columns=["tool", "count"])
    return pd.DataFrame([
        {"tool": r["_id"], "count": r["count"]}
        for r in rows
    ])


# ── 8. Tool Stats (KPI) ─────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_tool_stats(agent: Optional[str] = None) -> dict:
    """Average and max tool calls per conversation."""
    col = get_collection()
    base = _agent_filter(agent)

    pipeline = [
        {"$match": base} if base else {"$match": {}},
        {"$group": {
            "_id": None,
            "avg_tool_calls": {"$avg": "$total_tool_calls"},
            "max_tool_calls": {"$max": "$total_tool_calls"},
            "conversations": {"$sum": 1},
        }},
    ]
    rows = list(col.aggregate(pipeline))
    if not rows:
        return {"avg_tool_calls": 0, "max_tool_calls": 0, "conversations": 0}
    r = rows[0]
    return {
        "avg_tool_calls": round(r.get("avg_tool_calls", 0) or 0, 1),
        "max_tool_calls": r.get("max_tool_calls", 0) or 0,
        "conversations": r.get("conversations", 0),
    }


# ── 9. Channel Distribution (donut chart) ───────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_channel_distribution(agent: Optional[str] = None) -> pd.DataFrame:
    """Conversations per channel."""
    col = get_collection()
    base = _agent_filter(agent)

    pipeline = [
        {"$match": base} if base else {"$match": {}},
        {"$group": {
            "_id": "$channel_name",
            "count": {"$sum": 1},
        }},
        {"$sort": {"count": -1}},
    ]
    rows = list(col.aggregate(pipeline))
    if not rows:
        return pd.DataFrame(columns=["channel", "count"])
    return pd.DataFrame([
        {"channel": r["_id"] or "unknown", "count": r["count"]}
        for r in rows
    ])


# ── 10. Failures (expandable table) ─────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_failures(agent: Optional[str] = None) -> pd.DataFrame:
    """Conversations with zero assistant replies."""
    col = get_collection()
    base = _agent_filter(agent)

    pipeline = [
        {"$match": base} if base else {"$match": {}},
        {"$project": {
            "agent_name": 1,
            "channel_name": 1,
            "requester_name": 1,
            "created_at": 1,
            "assistant_count": {
                "$size": {"$filter": {
                    "input": "$messages",
                    "cond": {"$eq": ["$$this.role", "assistant"]},
                }}
            },
        }},
        {"$match": {"assistant_count": 0}},
        {"$sort": {"created_at": -1}},
        {"$limit": 50},
    ]
    rows = list(col.aggregate(pipeline))
    if not rows:
        return pd.DataFrame(columns=["agent", "channel", "user", "created_at"])
    return pd.DataFrame([
        {
            "agent": r.get("agent_name", ""),
            "channel": r.get("channel_name", ""),
            "user": r.get("requester_name", ""),
            "created_at": r.get("created_at"),
        }
        for r in rows
    ])


# ── 11. Model Usage ─────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_model_usage(agent: Optional[str] = None) -> pd.DataFrame:
    """Model distribution by agent with cost breakdown."""
    col = get_collection()
    base = _agent_filter(agent)

    pipeline = [
        {"$match": base} if base else {"$match": {}},
        {"$unwind": "$messages"},
        {"$match": {"messages.role": "assistant", "messages.model": {"$exists": True}}},
        {"$group": {
            "_id": {"agent": "$agent_name", "model": "$messages.model"},
            "count": {"$sum": 1},
            "total_cost": {"$sum": "$messages.cost"},
        }},
        {"$sort": {"count": -1}},
    ]
    rows = list(col.aggregate(pipeline))
    if not rows:
        return pd.DataFrame(columns=["agent", "model", "count", "total_cost"])
    return pd.DataFrame([
        {
            "agent": r["_id"]["agent"],
            "model": r["_id"]["model"],
            "count": r["count"],
            "total_cost": round(r.get("total_cost", 0) or 0, 4),
        }
        for r in rows
    ])


# ── 12. Engagement Depth ────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_engagement_depth(agent: Optional[str] = None) -> pd.DataFrame:
    """Average messages per conversation with user/assistant split."""
    col = get_collection()
    base = _agent_filter(agent)

    pipeline = [
        {"$match": base} if base else {"$match": {}},
        {"$project": {
            "agent_name": 1,
            "message_count": {"$size": "$messages"},
            "user_messages": {
                "$size": {"$filter": {
                    "input": "$messages",
                    "cond": {"$eq": ["$$this.role", "user"]},
                }}
            },
            "assistant_messages": {
                "$size": {"$filter": {
                    "input": "$messages",
                    "cond": {"$eq": ["$$this.role", "assistant"]},
                }}
            },
        }},
        {"$group": {
            "_id": "$agent_name",
            "avg_total": {"$avg": "$message_count"},
            "avg_user": {"$avg": "$user_messages"},
            "avg_assistant": {"$avg": "$assistant_messages"},
        }},
        {"$sort": {"avg_total": -1}},
    ]
    rows = list(col.aggregate(pipeline))
    if not rows:
        return pd.DataFrame(columns=["agent", "avg_total", "avg_user", "avg_assistant"])
    return pd.DataFrame([
        {
            "agent": r["_id"],
            "avg_total": round(r.get("avg_total", 0) or 0, 1),
            "avg_user": round(r.get("avg_user", 0) or 0, 1),
            "avg_assistant": round(r.get("avg_assistant", 0) or 0, 1),
        }
        for r in rows
    ])


# ── 13. Weekly Users ────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_weekly_users(agent: Optional[str] = None) -> pd.DataFrame:
    """Active users per week over last 30 days."""
    col = get_collection()
    match = {"created_at": {"$gte": _days_ago(30)}}
    match.update(_agent_filter(agent))

    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-W%V", "date": "$created_at"}},
            "unique_users": {"$addToSet": "$requester_id"},
            "conversations": {"$sum": 1},
        }},
        {"$project": {
            "_id": 1,
            "active_users": {"$size": "$unique_users"},
            "conversations": 1,
        }},
        {"$sort": {"_id": 1}},
    ]
    rows = list(col.aggregate(pipeline))
    if not rows:
        return pd.DataFrame(columns=["week", "active_users", "conversations"])
    return pd.DataFrame([
        {
            "week": r["_id"],
            "active_users": r["active_users"],
            "conversations": r["conversations"],
        }
        for r in rows
    ])


# ── 14. Daily Trend (with unique users) ─────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def get_daily_trend(agent: Optional[str] = None) -> pd.DataFrame:
    """Daily conversation trend with unique user count (30d)."""
    col = get_collection()
    match = {"created_at": {"$gte": _days_ago(30)}}
    match.update(_agent_filter(agent))

    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "conversations": {"$sum": 1},
            "unique_users": {"$addToSet": "$requester_id"},
        }},
        {"$project": {
            "_id": 1,
            "conversations": 1,
            "unique_users": {"$size": "$unique_users"},
        }},
        {"$sort": {"_id": 1}},
    ]
    rows = list(col.aggregate(pipeline))
    if not rows:
        return pd.DataFrame(columns=["date", "conversations", "unique_users"])
    df = pd.DataFrame([
        {
            "date": r["_id"],
            "conversations": r["conversations"],
            "unique_users": r["unique_users"],
        }
        for r in rows
    ])
    df["date"] = pd.to_datetime(df["date"])
    return df
