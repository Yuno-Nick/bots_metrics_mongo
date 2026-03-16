// Category 4: Agent x Channel Matrix
db.conversations.aggregate([
  { $group: {
      _id: { agent: "$agent_name", channel: "$channel_name" },
      conversations: { $sum: 1 },
      cost: { $sum: "$total_cost" }
  }},
  { $sort: { "_id.agent": 1, conversations: -1 } }
])
