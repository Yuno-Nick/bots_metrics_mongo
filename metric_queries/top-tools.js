// Category 6: Most Used Tools Across All Agents
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
