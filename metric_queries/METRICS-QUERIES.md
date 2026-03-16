# Analytics Queries

Comprehensive aggregation pipelines for cross-agent analytics dashboards. All queries are `mongosh`-ready — run via `make metrics-shell`.

---

## Category 1: Agent Activity

### Conversations per Agent (Total + Last 7/30 Days)

```js
db.conversations.aggregate([
  { $facet: {
      total: [
        { $group: { _id: "$agent_name", count: { $sum: 1 } } }
      ],
      last_7d: [
        { $match: { created_at: { $gte: new Date(Date.now() - 7*86400000) } } },
        { $group: { _id: "$agent_name", count: { $sum: 1 } } }
      ],
      last_30d: [
        { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
        { $group: { _id: "$agent_name", count: { $sum: 1 } } }
      ]
  }}
])
```

### Conversations per Agent per Day (Time Series)

```js
db.conversations.aggregate([
  { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
  { $group: {
      _id: {
        date: { $dateToString: { format: "%Y-%m-%d", date: "$created_at" } },
        agent: "$agent_name"
      },
      count: { $sum: 1 }
  }},
  { $sort: { "_id.date": -1, "_id.agent": 1 } }
])
```

### Agent Response Time Distribution

Measures time between user message and next assistant message within each conversation.

```js
db.conversations.aggregate([
  { $unwind: { path: "$messages", includeArrayIndex: "idx" } },
  { $match: { "messages.role": "assistant" } },
  { $group: {
      _id: "$agent_name",
      avg_response_ms: { $avg: {
        $subtract: ["$messages.timestamp", "$created_at"]
      }},
      count: { $sum: 1 }
  }},
  { $project: {
      _id: 1,
      avg_response_sec: { $divide: ["$avg_response_ms", 1000] },
      count: 1
  }},
  { $sort: { avg_response_sec: 1 } }
])
```

### Agent Cost Breakdown

```js
db.conversations.aggregate([
  { $group: {
      _id: "$agent_name",
      total_cost: { $sum: "$total_cost" },
      conversations: { $sum: 1 },
      avg_cost: { $avg: "$total_cost" }
  }},
  { $sort: { total_cost: -1 } }
])
```

---

## Category 2: Channel Activity

### Conversations per Channel (Total + Last 7/30 Days)

```js
db.conversations.aggregate([
  { $facet: {
      total: [
        { $group: { _id: "$channel_name", count: { $sum: 1 } } },
        { $sort: { count: -1 } }
      ],
      last_7d: [
        { $match: { created_at: { $gte: new Date(Date.now() - 7*86400000) } } },
        { $group: { _id: "$channel_name", count: { $sum: 1 } } },
        { $sort: { count: -1 } }
      ],
      last_30d: [
        { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
        { $group: { _id: "$channel_name", count: { $sum: 1 } } },
        { $sort: { count: -1 } }
      ]
  }}
])
```

### Agents Active per Channel

```js
db.conversations.aggregate([
  { $group: {
      _id: "$channel_name",
      agents: { $addToSet: "$agent_name" },
      conversations: { $sum: 1 }
  }},
  { $project: {
      _id: 1,
      agents: 1,
      agent_count: { $size: "$agents" },
      conversations: 1
  }},
  { $sort: { conversations: -1 } }
])
```

### Channel Activity Heatmap (Day-of-Week × Hour)

```js
db.conversations.aggregate([
  { $group: {
      _id: {
        dow: { $dayOfWeek: "$created_at" },
        hour: { $hour: "$created_at" }
      },
      count: { $sum: 1 }
  }},
  { $sort: { "_id.dow": 1, "_id.hour": 1 } }
])
// dow: 1=Sunday, 2=Monday, ..., 7=Saturday
```

### Most Active Channels by Message Volume

```js
db.conversations.aggregate([
  { $project: {
      channel_name: 1,
      message_count: { $size: "$messages" },
      total_cost: 1
  }},
  { $group: {
      _id: "$channel_name",
      conversations: { $sum: 1 },
      total_messages: { $sum: "$message_count" },
      total_cost: { $sum: "$total_cost" }
  }},
  { $sort: { total_messages: -1 } }
])
```

---

## Category 3: User Activity

### Conversations per User (Last 30 Days)

```js
db.conversations.aggregate([
  { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
  { $group: {
      _id: { id: "$requester_id", name: "$requester_name" },
      conversations: { $sum: 1 },
      total_messages: { $sum: { $size: "$messages" } },
      total_cost: { $sum: "$total_cost" }
  }},
  { $sort: { conversations: -1 } }
])
```

### Top Users by Cost Generated

```js
db.conversations.aggregate([
  { $group: {
      _id: { id: "$requester_id", name: "$requester_name" },
      total_cost: { $sum: "$total_cost" },
      conversations: { $sum: 1 },
      avg_cost_per_conversation: { $avg: "$total_cost" }
  }},
  { $sort: { total_cost: -1 } }
])
```

### User × Agent Matrix

```js
db.conversations.aggregate([
  { $group: {
      _id: { user: "$requester_name", agent: "$agent_name" },
      conversations: { $sum: 1 },
      cost: { $sum: "$total_cost" }
  }},
  { $sort: { "_id.user": 1, conversations: -1 } }
])
```

### User × Channel Matrix

```js
db.conversations.aggregate([
  { $group: {
      _id: { user: "$requester_name", channel: "$channel_name" },
      conversations: { $sum: 1 }
  }},
  { $sort: { "_id.user": 1, conversations: -1 } }
])
```

---

## Category 4: Cross-Dimensional

### Agent × Channel Matrix

```js
db.conversations.aggregate([
  { $group: {
      _id: { agent: "$agent_name", channel: "$channel_name" },
      conversations: { $sum: 1 },
      cost: { $sum: "$total_cost" }
  }},
  { $sort: { "_id.agent": 1, conversations: -1 } }
])
```

### Channel × Agent × User Breakdown

```js
db.conversations.aggregate([
  { $group: {
      _id: {
        channel: "$channel_name",
        agent: "$agent_name",
        user: "$requester_name"
      },
      conversations: { $sum: 1 }
  }},
  { $sort: { "_id.channel": 1, "_id.agent": 1, conversations: -1 } }
])
```

### Busiest Day-of-Week

```js
db.conversations.aggregate([
  { $group: {
      _id: { $dayOfWeek: "$created_at" },
      conversations: { $sum: 1 },
      total_cost: { $sum: "$total_cost" }
  }},
  { $sort: { conversations: -1 } }
])
// 1=Sunday, 2=Monday, ..., 7=Saturday
```

### Busiest Hour-of-Day

```js
db.conversations.aggregate([
  { $group: {
      _id: { $hour: "$created_at" },
      conversations: { $sum: 1 }
  }},
  { $sort: { conversations: -1 } }
])
```

### Average Conversation Length by Agent

```js
db.conversations.aggregate([
  { $project: {
      agent_name: 1,
      message_count: { $size: "$messages" }
  }},
  { $group: {
      _id: "$agent_name",
      avg_messages: { $avg: "$message_count" },
      min_messages: { $min: "$message_count" },
      max_messages: { $max: "$message_count" },
      conversations: { $sum: 1 }
  }},
  { $sort: { avg_messages: -1 } }
])
```

---

## Category 5: Cost Analytics

### Total Cost per Day (Time Series)

```js
db.conversations.aggregate([
  { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
  { $group: {
      _id: { $dateToString: { format: "%Y-%m-%d", date: "$created_at" } },
      total_cost: { $sum: "$total_cost" },
      conversations: { $sum: 1 }
  }},
  { $sort: { _id: 1 } }
])
```

### Cost per Agent per Day

```js
db.conversations.aggregate([
  { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
  { $group: {
      _id: {
        date: { $dateToString: { format: "%Y-%m-%d", date: "$created_at" } },
        agent: "$agent_name"
      },
      cost: { $sum: "$total_cost" },
      conversations: { $sum: 1 }
  }},
  { $sort: { "_id.date": 1, "_id.agent": 1 } }
])
```

### Average Cost per Conversation by Agent

```js
db.conversations.aggregate([
  { $group: {
      _id: "$agent_name",
      avg_cost: { $avg: "$total_cost" },
      median_cost: { $median: { input: "$total_cost", method: "approximate" } },
      min_cost: { $min: "$total_cost" },
      max_cost: { $max: "$total_cost" },
      total_cost: { $sum: "$total_cost" },
      conversations: { $sum: 1 }
  }},
  { $sort: { avg_cost: -1 } }
])
```

### Token Usage Breakdown (Input vs Output vs Cache)

```js
db.conversations.aggregate([
  { $unwind: "$messages" },
  { $match: { "messages.role": "assistant" } },
  { $group: {
      _id: "$agent_name",
      total_tokens_in: { $sum: "$messages.tokens_in" },
      total_tokens_out: { $sum: "$messages.tokens_out" },
      total_cache_read: { $sum: "$messages.cache_read" },
      total_cache_write: { $sum: "$messages.cache_write" },
      messages: { $sum: 1 }
  }},
  { $project: {
      _id: 1,
      total_tokens_in: 1,
      total_tokens_out: 1,
      total_cache_read: 1,
      total_cache_write: 1,
      messages: 1,
      cache_hit_ratio: {
        $cond: [
          { $eq: [{ $add: ["$total_cache_read", "$total_cache_write"] }, 0] },
          0,
          { $divide: ["$total_cache_read", { $add: ["$total_cache_read", "$total_cache_write"] }] }
        ]
      }
  }},
  { $sort: { total_tokens_out: -1 } }
])
```

---

## Category 6: Tool Usage

### Most Used Tools Across All Agents

```js
db.conversations.aggregate([
  { $unwind: "$messages" },
  { $match: { "messages.role": "assistant", "messages.tool_calls": { $exists: true, $ne: [] } } },
  { $unwind: "$messages.tool_calls" },
  { $group: {
      _id: "$messages.tool_calls",
      count: { $sum: 1 }
  }},
  { $sort: { count: -1 } }
])
```

### Tool Calls per Agent

```js
db.conversations.aggregate([
  { $unwind: "$messages" },
  { $match: { "messages.role": "assistant", "messages.tool_calls": { $exists: true, $ne: [] } } },
  { $unwind: "$messages.tool_calls" },
  { $group: {
      _id: { agent: "$agent_name", tool: "$messages.tool_calls" },
      count: { $sum: 1 }
  }},
  { $sort: { "_id.agent": 1, count: -1 } }
])
```

### Average Tool Calls per Message by Agent

```js
db.conversations.aggregate([
  { $unwind: "$messages" },
  { $match: { "messages.role": "assistant" } },
  { $group: {
      _id: "$agent_name",
      avg_tool_calls: { $avg: { $size: { $ifNull: ["$messages.tool_calls", []] } } },
      total_messages: { $sum: 1 }
  }},
  { $sort: { avg_tool_calls: -1 } }
])
```

### Tool Calls per Conversation by Agent

```js
db.conversations.aggregate([
  { $group: {
      _id: "$agent_name",
      avg_tool_calls: { $avg: "$total_tool_calls" },
      max_tool_calls: { $max: "$total_tool_calls" },
      conversations: { $sum: 1 }
  }},
  { $sort: { avg_tool_calls: -1 } }
])
```

---

## Category 7: Operational Health

### Conversations per Day Trend

```js
db.conversations.aggregate([
  { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
  { $group: {
      _id: { $dateToString: { format: "%Y-%m-%d", date: "$created_at" } },
      conversations: { $sum: 1 },
      unique_users: { $addToSet: "$requester_id" }
  }},
  { $project: {
      _id: 1,
      conversations: 1,
      unique_users: { $size: "$unique_users" }
  }},
  { $sort: { _id: 1 } }
])
```

### Active Users per Week

```js
db.conversations.aggregate([
  { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
  { $group: {
      _id: { $dateToString: { format: "%Y-W%V", date: "$created_at" } },
      unique_users: { $addToSet: "$requester_id" },
      conversations: { $sum: 1 }
  }},
  { $project: {
      _id: 1,
      active_users: { $size: "$unique_users" },
      conversations: 1
  }},
  { $sort: { _id: 1 } }
])
```

### Average Messages per Conversation (Engagement Depth)

```js
db.conversations.aggregate([
  { $project: {
      agent_name: 1,
      message_count: { $size: "$messages" },
      user_messages: {
        $size: { $filter: { input: "$messages", cond: { $eq: ["$$this.role", "user"] } } }
      },
      assistant_messages: {
        $size: { $filter: { input: "$messages", cond: { $eq: ["$$this.role", "assistant"] } } }
      }
  }},
  { $group: {
      _id: "$agent_name",
      avg_total: { $avg: "$message_count" },
      avg_user: { $avg: "$user_messages" },
      avg_assistant: { $avg: "$assistant_messages" }
  }},
  { $sort: { avg_total: -1 } }
])
```

### Conversations with Zero Assistant Replies (Failures)

```js
db.conversations.aggregate([
  { $project: {
      agent_name: 1,
      channel_name: 1,
      requester_name: 1,
      created_at: 1,
      assistant_count: {
        $size: { $filter: { input: "$messages", cond: { $eq: ["$$this.role", "assistant"] } } }
      }
  }},
  { $match: { assistant_count: 0 } },
  { $sort: { created_at: -1 } }
])
```

### Model Usage Distribution

```js
db.conversations.aggregate([
  { $unwind: "$messages" },
  { $match: { "messages.role": "assistant", "messages.model": { $exists: true } } },
  { $group: {
      _id: { agent: "$agent_name", model: "$messages.model" },
      count: { $sum: 1 },
      total_cost: { $sum: "$messages.cost" }
  }},
  { $sort: { "_id.agent": 1, count: -1 } }
])
```

---

## Quick Reference

| Query | Category | Key Metric |
|-------|----------|------------|
| Conversations per agent | Agent Activity | Volume |
| Agent cost breakdown | Agent Activity | Cost |
| Channel heatmap | Channel Activity | Timing patterns |
| User × agent matrix | User Activity | Cross-usage |
| Cost per day | Cost Analytics | Spend trend |
| Token breakdown | Cost Analytics | Efficiency |
| Most used tools | Tool Usage | Automation |
| Zero-reply conversations | Operational Health | Failures |
| Active users per week | Operational Health | Adoption |
