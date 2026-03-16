// Category 4: Busiest Hour-of-Day
db.conversations.aggregate([
  { $group: {
      _id: { $hour: "$created_at" },
      conversations: { $sum: 1 }
  }},
  { $sort: { conversations: -1 } }
])
