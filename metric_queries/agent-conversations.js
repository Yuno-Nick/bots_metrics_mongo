// Category 1: Conversations per Agent (Total + Last 7/30 Days)
db.conversations.aggregate([
  { $facet: {
      total: [
        { $group: { _id: "$agent_name", count: { $sum: 1 } } }
      ],
      last_7d: [
        { $match: { created_at: { $gte: new Date(Date.now() - 7*86400000) } } },
        { $group: { _id: "$agent_name", count: { $sum: 1 } } }
      ],
      last_30d: [
        { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
        { $group: { _id: "$agent_name", count: { $sum: 1 } } }
      ]
  }}
])
