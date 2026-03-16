// Category 4: Average Conversation Length by Agent
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
