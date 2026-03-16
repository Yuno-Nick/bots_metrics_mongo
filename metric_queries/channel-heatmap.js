// Category 2: Channel Activity Heatmap (Day-of-Week x Hour)
db.conversations.aggregate([
  { $group: {
      _id: {
        dow: { $dayOfWeek: "$created_at" },
        hour: { $hour: "$created_at" }
      },
      count: { $sum: 1 }
  }},
  { $sort: { "_id.dow": 1, "_id.hour": 1 } }
])
// dow: 1=Sunday, 2=Monday, ..., 7=Saturday
