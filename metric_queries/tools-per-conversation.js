// Category 6: Tool Calls per Conversation by Agent
db.conversations.aggregate([
  { $group: {
      _id: "$agent_name",
      avg_tool_calls: { $avg: "$total_tool_calls" },
      max_tool_calls: { $max: "$total_tool_calls" },
      conversations: { $sum: 1 }
  }},
  { $sort: { avg_tool_calls: -1 } }
])
