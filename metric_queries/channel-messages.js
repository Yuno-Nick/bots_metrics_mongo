// Category 2: Most Active Channels by Message Volume
db.conversations.aggregate([
  { $project: {
      channel_name: 1,
      message_count: { $size: "$messages" },
      total_cost: 1
  }},
  { $group: {
      _id: "$channel_name",
      conversations: { $sum: 1 },
      total_messages: { $sum: "$message_count" },
      total_cost: { $sum: "$total_cost" }
  }},
  { $sort: { total_messages: -1 } }
])
