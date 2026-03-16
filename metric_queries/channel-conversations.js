// Category 2: Conversations per Channel (Total + Last 7/30 Days)
db.conversations.aggregate([
  { $facet: {
      total: [
        { $group: { _id: "$channel_name", count: { $sum: 1 } } },
        { $sort: { count: -1 } }
      ],
      last_7d: [
        { $match: { created_at: { $gte: new Date(Date.now() - 7*86400000) } } },
        { $group: { _id: "$channel_name", count: { $sum: 1 } } },
        { $sort: { count: -1 } }
      ],
      last_30d: [
        { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
        { $group: { _id: "$channel_name", count: { $sum: 1 } } },
        { $sort: { count: -1 } }
      ]
  }}
])
