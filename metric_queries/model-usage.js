// Category 7: Model Usage Distribution
db.conversations.aggregate([
  { $unwind: "$messages" },
  { $match: { "messages.role": "assistant", "messages.model": { $exists: true } } },
  { $group: {
      _id: { agent: "$agent_name", model: "$messages.model" },
      count: { $sum: 1 },
      total_cost: { $sum: "$messages.cost" }
  }},
  { $sort: { "_id.agent": 1, count: -1 } }
])
