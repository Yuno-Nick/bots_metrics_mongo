// Category 1: Agent Cost Breakdown
db.conversations.aggregate([
  { $group: {
      _id: "$agent_name",
      total_cost: { $sum: "$total_cost" },
      conversations: { $sum: 1 },
      avg_cost: { $avg: "$total_cost" }
  }},
  { $sort: { total_cost: -1 } }
])
