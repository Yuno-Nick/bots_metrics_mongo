// Category 3: User x Channel Matrix
db.conversations.aggregate([
  { $group: {
      _id: { user: "$requester_name", channel: "$channel_name" },
      conversations: { $sum: 1 }
  }},
  { $sort: { "_id.user": 1, conversations: -1 } }
])
