// Category 3: User x Agent Matrix
db.conversations.aggregate([
  { $group: {
      _id: { user: "$requester_name", agent: "$agent_name" },
      conversations: { $sum: 1 },
      cost: { $sum: "$total_cost" }
  }},
  { $sort: { "_id.user": 1, conversations: -1 } }
])
