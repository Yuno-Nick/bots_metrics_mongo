// Category 3: Top Users by Cost Generated
db.conversations.aggregate([
  { $group: {
      _id: { id: "$requester_id", name: "$requester_name" },
      total_cost: { $sum: "$total_cost" },
      conversations: { $sum: 1 },
      avg_cost_per_conversation: { $avg: "$total_cost" }
  }},
  { $sort: { total_cost: -1 } }
])
