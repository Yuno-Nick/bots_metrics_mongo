// Category 5: Total Cost per Day (Time Series)
db.conversations.aggregate([
  { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
  { $group: {
      _id: { $dateToString: { format: "%Y-%m-%d", date: "$created_at" } },
      total_cost: { $sum: "$total_cost" },
      conversations: { $sum: 1 }
  }},
  { $sort: { _id: 1 } }
])
