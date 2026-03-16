// Category 1: Conversations per Agent per Day (Time Series)
db.conversations.aggregate([
  { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
  { $group: {
      _id: {
        date: { $dateToString: { format: "%Y-%m-%d", date: "$created_at" } },
        agent: "$agent_name"
      },
      count: { $sum: 1 }
  }},
  { $sort: { "_id.date": -1, "_id.agent": 1 } }
])
