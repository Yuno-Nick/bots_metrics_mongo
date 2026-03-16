// Category 5: Cost per Agent per Day
db.conversations.aggregate([
  { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
  { $group: {
      _id: {
        date: { $dateToString: { format: "%Y-%m-%d", date: "$created_at" } },
        agent: "$agent_name"
      },
      cost: { $sum: "$total_cost" },
      conversations: { $sum: 1 }
  }},
  { $sort: { "_id.date": 1, "_id.agent": 1 } }
])
