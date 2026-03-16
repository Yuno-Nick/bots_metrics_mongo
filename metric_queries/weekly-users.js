// Category 7: Active Users per Week
db.conversations.aggregate([
  { $match: { created_at: { $gte: new Date(Date.now() - 30*86400000) } } },
  { $group: {
      _id: { $dateToString: { format: "%Y-W%V", date: "$created_at" } },
      unique_users: { $addToSet: "$requester_id" },
      conversations: { $sum: 1 }
  }},
  { $project: {
      _id: 1,
      active_users: { $size: "$unique_users" },
      conversations: 1
  }},
  { $sort: { _id: 1 } }
])
