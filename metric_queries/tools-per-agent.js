// Category 6: Tool Calls per Agent
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
