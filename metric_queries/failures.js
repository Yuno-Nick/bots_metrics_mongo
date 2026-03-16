// Category 7: Conversations with Zero Assistant Replies (Failures)
db.conversations.aggregate([
  { $project: {
      agent_name: 1,
      channel_name: 1,
      requester_name: 1,
      created_at: 1,
      assistant_count: {
        $size: { $filter: { input: "$messages", cond: { $eq: ["$$this.role", "assistant"] } } }
      }
  }},
  { $match: { assistant_count: 0 } },
  { $sort: { created_at: -1 } }
])
