// Category 4: Busiest Day-of-Week
db.conversations.aggregate([
  { $group: {
      _id: { $dayOfWeek: "$created_at" },
      conversations: { $sum: 1 },
      total_cost: { $sum: "$total_cost" }
  }},
  { $sort: { conversations: -1 } }
])
// 1=Sunday, 2=Monday, ..., 7=Saturday
