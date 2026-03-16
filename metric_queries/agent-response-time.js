// Category 1: Agent Response Time Distribution
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
