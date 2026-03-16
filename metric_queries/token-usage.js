// Category 5: Token Usage Breakdown (Input vs Output vs Cache)
db.conversations.aggregate([
  { $unwind: "$messages" },
  { $match: { "messages.role": "assistant" } },
  { $group: {
      _id: "$agent_name",
      total_tokens_in: { $sum: "$messages.tokens_in" },
      total_tokens_out: { $sum: "$messages.tokens_out" },
      total_cache_read: { $sum: "$messages.cache_read" },
      total_cache_write: { $sum: "$messages.cache_write" },
      messages: { $sum: 1 }
  }},
  { $project: {
      _id: 1,
      total_tokens_in: 1,
      total_tokens_out: 1,
      total_cache_read: 1,
      total_cache_write: 1,
      messages: 1,
      cache_hit_ratio: {
        $cond: [
          { $eq: [{ $add: ["$total_cache_read", "$total_cache_write"] }, 0] },
          0,
          { $divide: ["$total_cache_read", { $add: ["$total_cache_read", "$total_cache_write"] }] }
        ]
      }
  }},
  { $sort: { total_tokens_out: -1 } }
])
