// Category 2: Agents Active per Channel
db.conversations.aggregate([
  { $group: {
      _id: "$channel_name",
      agents: { $addToSet: "$agent_name" },
      conversations: { $sum: 1 }
  }},
  { $project: {
      _id: 1,
      agents: 1,
      agent_count: { $size: "$agents" },
      conversations: 1
  }},
  { $sort: { conversations: -1 } }
])
