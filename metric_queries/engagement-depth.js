// Category 7: Average Messages per Conversation (Engagement Depth)
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
