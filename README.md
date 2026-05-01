# Memoria

An organic, graph-based memory system for LLM agents. Memoria stores knowledge as an interconnected graph of concepts that decay, reinforce, and get pruned over time — mimicking how human memory naturally works.

## How It Works

Memoria manages a **directed graph** where each node is a concept or fact, and edges represent relationships between them. The system applies:

- **Activation scoring** — every node has a score that decays exponentially over time
- **Reinforcement** — accessing a node boosts its score; well-connected nodes get a connection bonus
- **Gardening** — a background process archives orphaned nodes that fall below a threshold, keeping the active graph lean
- **LLM-powered extraction** — pass a conversation to an LLM and it extracts new concepts as nodes with edges to existing knowledge

The graph is persisted as [DOT files](https://graphviz.org/doc/info/lang.html), organized by day (active) and month (archived).

## Architecture

Built with the [Polylith](https://davidvujic.github.io/python-polylith-docs/) architecture using loose bricks:

| Brick | Type | Description |
|---|---|---|
| `memoria.graph` | Component | Core `MemoryGraph`, `Node`, `Edge`, and DOT serialization |
| `memoria.storage` | Component | File-based persistence (daily + archived DOT files) |
| `memoria.scoring` | Component | Activation scoring with configurable decay and reinforcement |
| `memoria.gardener` | Component | Automatic pruning and archiving of low-scoring orphan nodes |
| `memoria.extractor` | Component | LLM-driven concept extraction from text |
| `memoria.retrieval` | Component | Token-overlap retrieval with activation-weighted ranking |
| `memoria.memory_api` | Base | High-level `MemoryAPI` facade combining all components |

## Installation

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/<your-username>/ai-memory.git
cd ai-memory
uv sync
```

For the optional APScheduler-based gardener scheduler:

```bash
uv sync --extra scheduler
```

## Quick Start

```python
from memoria.memory_api import MemoryAPI

# Without LLM — manual memory management
api = MemoryAPI(storage_path="./my_memory")

# Store concepts
api.store(id="python", content="Python is a high-level programming language", label="Python")
api.store(id="fastapi", content="FastAPI is a Python web framework", label="FastAPI", connects_to=["python"])

# Retrieve relevant memories
results = api.retrieve("What is Python?", top_k=5)

# Connect existing nodes
api.connect("fastapi", "python")

# Visualize the graph (returns DOT format)
dot_string = api.export_dot()

# List all nodes
print(api.list_nodes())
```

### With LLM Extraction

```python
def my_llm(prompt: str) -> str:
    # Call your LLM provider here
    ...

api = MemoryAPI(storage_path="./my_memory", llm_callable=my_llm)

# Extract concepts from conversation text
result = api.extract("The user mentioned they prefer PostgreSQL over MySQL for new projects.")
print(result)  # ExtractionResult(nodes=1, edges=0)
```

### Automated Gardening

```python
# Start background pruning (runs every hour by default)
api.start_scheduler(interval_seconds=3600)

# Run gardening manually
stats = api.garden()
print(stats)  # {"active_nodes": 42, "active_edges": 18, "daily_files": 5, "archived_files": 1}

# Stop the scheduler
api.stop_scheduler()
```

## Scoring Configuration

Scoring behavior is fully configurable via `ScoringConfig`:

```python
from memoria.scoring.config import ScoringConfig

config = ScoringConfig(
    decay_rate=0.05,            # Exponential decay rate per day
    archive_threshold=0.1,      # Score below which orphaned nodes are archived
    reinforcement_boost=0.2,    # Score boost when a node is accessed
    connection_bonus_factor=0.05,  # Bonus from well-connected neighbors
    max_score=1.0,
    min_score=0.0,
)

api = MemoryAPI(storage_path="./my_memory", scoring_config=config)
```

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Lint
uv run ruff check .
```

## Project Structure

```
ai-memory/
├── bases/
│   └── memoria/memory_api/    # Public API facade
├── components/
│   └── memoria/
│       ├── extractor/         # LLM concept extraction
│       ├── gardener/          # Pruning & archiving
│       ├── graph/             # Graph model & DOT serialization
│       ├── retrieval/         # Memory retrieval
│       ├── scoring/           # Activation scoring
│       └── storage/           # File-based persistence
├── tests/                     # Test suite
├── pyproject.toml
└── workspace.toml             # Polylith workspace config
```

## License

MIT
