// Category 6: Average Tool Calls per Message by Agent
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
