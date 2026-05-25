# Director AI (DAI) - Complete Implementation

A production-ready TypeScript implementation of Director AI, a multi-agent orchestrator running on Anthropic Claude Opus 4.7.

## Overview

Director AI (DAI) is an intelligent orchestrator that manages a virtual company of specialized AI workers. It receives requests, analyzes them, and routes tasks to the appropriate workers based on their skills and availability.

## Architecture

```
DAI (Director AI)
├── Company Model (Divisions → Departments → Workers)
├── Routing Engine (Analyzes & routes requests)
├── Task Engine (Manages task graph & dependencies)
├── Memory Layer (Project, Company, Director memory)
└── Output (Canonical JSON responses)
```

## Components

### 1. DAI System Prompt (`src/daiSystemPrompt.ts`)
Complete system prompt containing:
- Company structure (divisions, departments, workers)
- Worker registry with specializations
- Routing engine logic
- Task management system
- Memory model
- Director loop (10-step process)
- JSON output format

### 2. DAI Agent (`src/daiAgent.ts`)
Main orchestrator class:
- Maintains in-memory state
- Implements Director Loop:
  - RECEIVE → CLASSIFY → LOAD CONTEXT → UPDATE STATE → PLAN → ROUTE → DISPATCH → COMPILE → REPORT → PERSIST
- Manages task graph and worker load
- Returns canonical JSON responses

### 3. Memory Layer (`src/memory.ts`)
Persistent storage system:
- **Project Memory**: Active projects, goals, decisions
- **Company Memory**: Worker status, task graph, resource utilization
- **Director Memory**: Conversation history, routing patterns, user preferences
- JSON file-based storage in `./memory/` directory

### 4. Anthropic Client (`src/daiClient.ts`)
API integration:
- Connects to Claude Opus 4.7
- Uses `process.env.ANTHROPIC_API_KEY`
- Supports streaming responses

### 5. CLI Interface (`src/cli.ts`)
Interactive command-line interface:
- Read user input
- Send to DAI
- Display formatted JSON responses
- Commands: `/exit`, `/state`, `/help`

### 6. Server Endpoint (`src/server.ts`)
HTTP REST API:
- `POST /dai` - Send requests to DAI
- `GET /health` - Health check
- `GET /state` - Current DAI state
- `GET /memory/project` - Project memory
- `GET /memory/company` - Company memory
- `GET /memory/director` - Director memory

### 7. Discord Bot (`src/discordBot.ts`)
Discord integration:
- Responds to @mentions and DMs
- Forwards messages to DAI
- Formats responses for Discord
- Real-time updates

## Installation

### Prerequisites
- Node.js >= 18.0.0
- npm or yarn
- Anthropic API key

### Setup

1. **Install dependencies:**
```bash
npm install
```

2. **Set environment variables:**
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export DISCORD_BOT_TOKEN="your-discord-bot-token"  # Optional, for Discord bot
export PORT=3000  # Optional, defaults to 3000
```

Or create a `.env` file:
```
ANTHROPIC_API_KEY=your-key-here
DISCORD_BOT_TOKEN=your-token-here
PORT=3000
```

3. **Build the project:**
```bash
npm run build
```

## Usage

### CLI Interface
```bash
npm run cli
```

Interactive session:
```
DAI> Build a user authentication API
[DAI will analyze, route to workers, and return JSON response]

DAI> /state
[Shows current system state]

DAI> /exit
```

### HTTP Server
```bash
npm run dev
# or
npm start
```

Make requests:
```bash
curl -X POST http://localhost:3000/dai \
  -H "Content-Type: application/json" \
  -d '{"input": "Create a REST API for user management"}'
```

Response:
```json
{
  "director_summary": "I've analyzed your request...",
  "request_analysis": {
    "type": "feature_request",
    "complexity": "moderate",
    "required_skills": ["backend", "api_design", "database"]
  },
  "routing_decision": {
    "strategy": "parallel",
    "assignments": [
      {
        "worker_id": "worker_001",
        "worker_name": "Backend Engineer",
        "task_description": "Design and implement REST API endpoints",
        "priority": "high",
        "estimated_duration": "3 hours"
      }
    ]
  },
  "task_updates": [...],
  "project_status": {
    "active_tasks": 1,
    "completed_tasks": 0,
    "blocked_tasks": 0
  },
  "next_steps": [...],
  "director_notes": "..."
}
```

### Discord Bot
```bash
npm run discord
```

In Discord:
```
@DirectorAI Please implement a login feature
[Bot responds with routing decisions and task assignments]
```

## API Endpoints

### POST /dai
Process a request through DAI.

**Request:**
```json
{
  "input": "Your request here"
}
```

**Response:** Full DAI JSON response (see above)

### GET /health
Health check endpoint.

### GET /state
Get current DAI state (workers, tasks, queues).

### GET /memory/project
Get project memory.

### GET /memory/company
Get company memory (workers, tasks).

### GET /memory/director
Get director memory (conversation history).

## Worker Registry

DAI manages 9 specialized workers:

1. **worker_001** - Backend Engineer (APIs, databases)
2. **worker_002** - Frontend Engineer (React, UI/UX)
3. **worker_003** - DevOps Engineer (CI/CD, deployment)
4. **worker_004** - Data Analyst (data processing, insights)
5. **worker_005** - Technical Writer (docs, guides)
6. **worker_006** - QA Engineer (testing, security)
7. **worker_007** - Project Manager (planning, coordination)
8. **worker_008** - Support Specialist (troubleshooting)
9. **worker_009** - Integration Engineer (APIs, webhooks)

Each worker has:
- Unique ID
- Specialization
- Status (available/busy/offline)
- Current load
- Max capacity

## Memory Structure

### ./memory/project_memory.json
```json
{
  "active_projects": {
    "project_id": {
      "name": "Project Name",
      "status": "active",
      "tasks": ["task_1", "task_2"],
      "priority": "high"
    }
  }
}
```

### ./memory/company_memory.json
```json
{
  "worker_status": {
    "worker_001": {
      "status": "available",
      "current_tasks": [],
      "load": 0,
      "max_capacity": 5
    }
  },
  "task_graph": {
    "task_id": {
      "status": "in_progress",
      "assigned_to": "worker_001",
      "dependencies": []
    }
  }
}
```

### ./memory/director_memory.json
```json
{
  "conversation_history": [],
  "routing_patterns": [],
  "user_preferences": {}
}
```

## Director Loop

DAI executes this 10-step loop for every request:

1. **RECEIVE** - Parse user input, extract intent
2. **CLASSIFY** - Determine request type, assess complexity
3. **LOAD CONTEXT** - Load all memory layers, check worker status
4. **UPDATE STATE** - Sync worker loads, task statuses
5. **PLAN** - Break down into tasks, determine dependencies
6. **ROUTE** - Match tasks to workers, check capacity
7. **DISPATCH** - Generate handoffs, send to workers
8. **COMPILE** - Aggregate results, check blockers
9. **REPORT** - Generate user-facing summary
10. **PERSIST** - Save to memory, update state

## Request Types

DAI handles:
- `feature_request` - Build something new
- `bug_fix` - Fix broken functionality
- `question` - Answer queries
- `analysis` - Analyze data/code
- `documentation` - Write/update docs
- `integration` - Connect external services
- `support` - Help with issues

## Complexity Levels

- **simple** - Single worker, < 1 hour
- **moderate** - 2-3 workers, few hours
- **complex** - Multiple workers, coordination needed

## Development

### Project Structure
```
src/
├── daiSystemPrompt.ts    # Full system prompt
├── daiAgent.ts           # Main orchestrator class
├── memory.ts             # Memory layer
├── daiClient.ts          # Anthropic API client
├── cli.ts                # CLI interface
├── server.ts             # HTTP server
└── discordBot.ts         # Discord bot

memory/                   # JSON storage (auto-created)
├── project_memory.json
├── company_memory.json
└── director_memory.json

dist/                     # Compiled JavaScript (auto-generated)
```

### Scripts
- `npm run build` - Compile TypeScript
- `npm run dev` - Run server in dev mode
- `npm start` - Run compiled server
- `npm run cli` - Interactive CLI
- `npm run discord` - Start Discord bot
- `npm run clean` - Remove dist folder

## Configuration

All configuration via environment variables:

- `ANTHROPIC_API_KEY` - **Required** - Anthropic API key
- `DISCORD_BOT_TOKEN` - Optional - Discord bot token
- `PORT` - Optional - Server port (default: 3000)

## Model

DAI runs on **Claude Opus 4.7**, the most advanced model from Anthropic.

## Output Format

DAI **always** returns valid JSON:
- No markdown wrappers
- No text outside JSON
- Parseable by `JSON.parse()`

## Error Handling

- Invalid API key → Error message
- Worker capacity exceeded → Tasks queued
- Parse errors → Fallback response
- Network errors → Logged and returned

## Production Considerations

1. **Rate Limiting**: Implement rate limiting on endpoints
2. **Authentication**: Add auth to protect endpoints
3. **Logging**: Enhanced logging for production
4. **Monitoring**: Monitor worker loads and task completion
5. **Scaling**: Consider distributed task queue
6. **Database**: Move from JSON files to database for scale

## Examples

### Feature Request
```bash
curl -X POST http://localhost:3000/dai \
  -H "Content-Type: application/json" \
  -d '{"input": "Build a REST API for product catalog with CRUD operations"}'
```

DAI routes to Backend Engineer, plans tasks, updates state.

### Bug Fix
```bash
curl -X POST http://localhost:3000/dai \
  -H "Content-Type: application/json" \
  -d '{"input": "Fix memory leak in user session handling"}'
```

DAI routes to Backend Engineer and QA Engineer, coordinates fix and testing.

### Documentation
```bash
curl -X POST http://localhost:3000/dai \
  -H "Content-Type: application/json" \
  -d '{"input": "Write API documentation for the authentication endpoints"}'
```

DAI routes to Technical Writer.

## License

MIT

## Support

For issues or questions, review the code and system prompt. All logic is self-contained and production-ready.
