// Category 3: Conversations per User (Last 30 Days)
db.conversations.aggregate([
  { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
  { $group: {
      _id: { id: "$requester_id", name: "$requester_name" },
      conversations: { $sum: 1 },
      total_messages: { $sum: { $size: "$messages" } },
      total_cost: { $sum: "$total_cost" }
  }},
  { $sort: { conversations: -1 } }
])
