// Category 7: Conversations per Day Trend
db.conversations.aggregate([
  { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
  { $group: {
      _id: { $dateToString: { format: "%Y-%m-%d", date: "$created_at" } },
      conversations: { $sum: 1 },
      unique_users: { $addToSet: "$requester_id" }
  }},
  { $project: {
      _id: 1,
      conversations: 1,
      unique_users: { $size: "$unique_users" }
  }},
  { $sort: { _id: 1 } }
])
