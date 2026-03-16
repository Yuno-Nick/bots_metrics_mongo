// Category 4: Channel x Agent x User Breakdown
db.conversations.aggregate([
  { $group: {
      _id: {
        channel: "$channel_name",
        agent: "$agent_name",
        user: "$requester_name"
      },
      conversations: { $sum: 1 }
  }},
  { $sort: { "_id.channel": 1, "_id.agent": 1, conversations: -1 } }
])
