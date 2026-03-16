include .env
export

# ─── MongoDB Connection ──────────────────────────────────────────────
MONGO_USER     ?= microservices
MONGO_PASSWORD ?= u1jnWLnaUN53O1r8couy9fW5
MONGO_HOST     ?= ai-agents-reader.internal-infra.y.uno
MONGO_PORT     ?= 27017
MONGO_DB       ?= analytics
MONGO_AUTH     := $(MONGO_USER):$(MONGO_PASSWORD)@$(MONGO_HOST):$(MONGO_PORT)
MONGO_PARAMS   := $(MONGO_DB)?authSource=admin&retryWrites=false

# Full URI
MONGO_URI      ?= mongodb://$(MONGO_AUTH)/$(MONGO_PARAMS)

# TLS options for AWS DocumentDB
TLS_CA_FILE    := certs/global-bundle.pem
TLS_OPTS       := --tls --tlsCAFile $(TLS_CA_FILE) --tlsAllowInvalidHostnames

MONGOSH := mongosh "$(MONGO_URI)" $(TLS_OPTS)

# ─── SSM Tunnel ──────────────────────────────────────────────────────
AWS_PROFILE    ?= 931412643807_AIBOT-TeamAI
AWS_REGION     ?= us-west-2
EC2_INSTANCE   ?= i-016a5c47547e43db3
DOCDB_HOST     ?= ai-agents-reader.internal-infra.y.uno
DOCDB_PORT     ?= 27017
LOCAL_PORT     ?= 27018
QUERIES := metric_queries

# ─── Tunnel ───────────────────────────────────────────────────────────
.PHONY: tunnel
tunnel: ## Start SSM tunnel to DocumentDB (run in separate terminal)
	AWS_PROFILE=$(AWS_PROFILE) aws ssm start-session \
		--target $(EC2_INSTANCE) \
		--region $(AWS_REGION) \
		--document-name AWS-StartPortForwardingSessionToRemoteHost \
		--parameters '{"host":["$(DOCDB_HOST)"],"portNumber":["$(DOCDB_PORT)"],"localPortNumber":["$(LOCAL_PORT)"]}'

# ─── Shell ────────────────────────────────────────────────────────────
.PHONY: metrics-shell
metrics-shell: ## Open interactive mongosh connected to analytics DB
	$(MONGOSH)

.PHONY: ping
ping: ## Test MongoDB connectivity
	$(MONGOSH) --eval 'db.runCommand({ ping: 1 })'

.PHONY: collections
collections: ## List all collections
	$(MONGOSH) --eval 'db.getCollectionNames()'

.PHONY: count
count: ## Count total conversations
	$(MONGOSH) --eval 'db.conversations.countDocuments({})'

.PHONY: sample
sample: ## Show 3 sample conversation documents
	$(MONGOSH) --eval 'db.conversations.find().limit(3).toArray()'

# ─── Category 1: Agent Activity ──────────────────────────────────────
.PHONY: agent-conversations
agent-conversations: ## Conversations per agent (total + 7d + 30d)
	$(MONGOSH) --file $(QUERIES)/agent-conversations.js

.PHONY: agent-timeseries
agent-timeseries: ## Conversations per agent per day (30d)
	$(MONGOSH) --file $(QUERIES)/agent-timeseries.js

.PHONY: agent-response-time
agent-response-time: ## Agent response time distribution
	$(MONGOSH) --file $(QUERIES)/agent-response-time.js

.PHONY: agent-cost
agent-cost: ## Agent cost breakdown
	$(MONGOSH) --file $(QUERIES)/agent-cost.js

# ─── Category 2: Channel Activity ────────────────────────────────────
.PHONY: channel-conversations
channel-conversations: ## Conversations per channel (total + 7d + 30d)
	$(MONGOSH) --file $(QUERIES)/channel-conversations.js

.PHONY: channel-agents
channel-agents: ## Agents active per channel
	$(MONGOSH) --file $(QUERIES)/channel-agents.js

.PHONY: channel-heatmap
channel-heatmap: ## Channel activity heatmap (day-of-week x hour)
	$(MONGOSH) --file $(QUERIES)/channel-heatmap.js

.PHONY: channel-messages
channel-messages: ## Most active channels by message volume
	$(MONGOSH) --file $(QUERIES)/channel-messages.js

# ─── Category 3: User Activity ───────────────────────────────────────
.PHONY: user-conversations
user-conversations: ## Conversations per user (30d)
	$(MONGOSH) --file $(QUERIES)/user-conversations.js

.PHONY: user-cost
user-cost: ## Top users by cost generated
	$(MONGOSH) --file $(QUERIES)/user-cost.js

.PHONY: user-agent-matrix
user-agent-matrix: ## User x Agent matrix
	$(MONGOSH) --file $(QUERIES)/user-agent-matrix.js

.PHONY: user-channel-matrix
user-channel-matrix: ## User x Channel matrix
	$(MONGOSH) --file $(QUERIES)/user-channel-matrix.js

# ─── Category 4: Cross-Dimensional ───────────────────────────────────
.PHONY: agent-channel-matrix
agent-channel-matrix: ## Agent x Channel matrix
	$(MONGOSH) --file $(QUERIES)/agent-channel-matrix.js

.PHONY: full-breakdown
full-breakdown: ## Channel x Agent x User breakdown
	$(MONGOSH) --file $(QUERIES)/full-breakdown.js

.PHONY: busiest-day
busiest-day: ## Busiest day of week
	$(MONGOSH) --file $(QUERIES)/busiest-day.js

.PHONY: busiest-hour
busiest-hour: ## Busiest hour of day
	$(MONGOSH) --file $(QUERIES)/busiest-hour.js

.PHONY: avg-conversation-length
avg-conversation-length: ## Average conversation length by agent
	$(MONGOSH) --file $(QUERIES)/avg-conversation-length.js

# ─── Category 5: Cost Analytics ──────────────────────────────────────
.PHONY: cost-per-day
cost-per-day: ## Total cost per day (30d)
	$(MONGOSH) --file $(QUERIES)/cost-per-day.js

.PHONY: cost-per-agent-day
cost-per-agent-day: ## Cost per agent per day (30d)
	$(MONGOSH) --file $(QUERIES)/cost-per-agent-day.js

.PHONY: avg-cost-per-conversation
avg-cost-per-conversation: ## Average cost per conversation by agent
	$(MONGOSH) --file $(QUERIES)/avg-cost-per-conversation.js

.PHONY: token-usage
token-usage: ## Token usage breakdown (input/output/cache)
	$(MONGOSH) --file $(QUERIES)/token-usage.js

# ─── Category 6: Tool Usage ──────────────────────────────────────────
.PHONY: top-tools
top-tools: ## Most used tools across all agents
	$(MONGOSH) --file $(QUERIES)/top-tools.js

.PHONY: tools-per-agent
tools-per-agent: ## Tool calls per agent
	$(MONGOSH) --file $(QUERIES)/tools-per-agent.js

.PHONY: avg-tools-per-message
avg-tools-per-message: ## Average tool calls per message by agent
	$(MONGOSH) --file $(QUERIES)/avg-tools-per-message.js

.PHONY: tools-per-conversation
tools-per-conversation: ## Tool calls per conversation by agent
	$(MONGOSH) --file $(QUERIES)/tools-per-conversation.js

# ─── Category 7: Operational Health ──────────────────────────────────
.PHONY: daily-trend
daily-trend: ## Conversations per day trend (30d)
	$(MONGOSH) --file $(QUERIES)/daily-trend.js

.PHONY: weekly-users
weekly-users: ## Active users per week
	$(MONGOSH) --file $(QUERIES)/weekly-users.js

.PHONY: engagement-depth
engagement-depth: ## Average messages per conversation (engagement)
	$(MONGOSH) --file $(QUERIES)/engagement-depth.js

.PHONY: failures
failures: ## Conversations with zero assistant replies
	$(MONGOSH) --file $(QUERIES)/failures.js

.PHONY: model-usage
model-usage: ## Model usage distribution
	$(MONGOSH) --file $(QUERIES)/model-usage.js

# ─── Dashboard ──────────────────────────────────────────────────────────
.PHONY: venv
venv: ## Create Python venv and install deps
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

.PHONY: dashboard
dashboard: ## Launch Streamlit dashboard
	.venv/bin/streamlit run dashboard/app.py

# ─── Utilities ────────────────────────────────────────────────────────
.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
