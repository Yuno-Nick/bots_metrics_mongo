// Category 5: Average Cost per Conversation by Agent
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
