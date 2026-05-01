# AGENTS.md

## Project Overview

**memoria** is an organic, graph-based memory system for LLM agents. It stores memories as nodes in a directed graph with activation scoring, periodic decay, and automated archival of forgotten concepts. Persistence is file-based using Graphviz DOT format.

This is a **Python Polylith** monorepo. Code is organized as composable bricks (components and bases) under a shared `memoria` namespace.

## Commands

### Install & Sync
```bash
uv sync --all-extras
```

### Run Tests
```bash
uv run pytest tests/ -v
```

### Lint
```bash
uv run ruff check .
uv run ruff check . --fix       # auto-fix
uv run ruff format .             # format
```

### Run the Usage Example
```bash
uv run python development/scratch.py
```

### Polylith Tooling
```bash
uv run poly info                              # workspace overview
uv run poly create component --name <name>    # add a new component
uv run poly create base --name <name>         # add a new base
```

**Always run lint and tests after making changes.**

## Architecture

### Polylith Structure

```
components/memoria/     # Reusable bricks (business logic)
  graph/                #   Node, Edge, MemoryGraph, DOT serializer
  storage/              #   FileStore (daily/*.dot, archived/*.dot)
  scoring/              #   Scorer with decay + reinforcement
  gardener/             #   Pruning, archival, APScheduler integration
  extractor/            #   LLM-based memory extraction, slug generation
  retrieval/            #   Keyword + activation-scored retrieval

bases/memoria/          # Entry points (public API)
  memory_api/           #   MemoryAPI facade class

development/            # Scratch files, experimentation
projects/               # Deployable artifacts (packaging configs)
tests/                  # All tests (flat layout under tests/components/ and tests/bases/)
```

### Data Flow

```
LLM conversation turn
    -> extractor.extract(text, existing_graph)   [needs llm_callable]
    -> graph.add_node / add_edge
    -> storage.save_active (writes daily/*.dot)
    -> gardener (scheduled) applies scoring decay, archives low-score orphans
    -> retriever.retrieve(query) returns scored subgraph for LLM context
```

### Storage Layout

```
<storage_path>/
  daily/          # Active memories, one .dot file per day (YYYY-MM-DD.dot)
  archived/       # Forgotten memories, one .dot file per month (YYYY-MM.dot)
```

### Key Design Decisions

- **Node IDs**: slug-first (human-readable, derived from content), UUID fallback for ambiguous/short content. Deduplication appends `_2`, `_3`, etc.
- **Edge relations**: always `"connects"` -- the LLM infers relationship type.
- **Orphan archival**: only archived if both orphaned AND below activation threshold.
- **LLM is abstracted**: consumers inject a `Callable[[str], str]`. No LLM SDK dependency.
- **APScheduler is optional**: falls back to `threading.Timer` if not installed.

## Code Conventions

### Style
- Line length: 88 (Black default)
- Linting: `ruff` with rules `E, F, I, N, W`
- No comments unless requested
- Type hints on all function parameters and returns
- Absolute imports: `from memoria.graph.node import Node` (not relative)

### Polylith Rules
- Each brick lives under `components/memoria/<name>/` or `bases/memoria/<name>/`.
- The `__init__.py` defines the brick's public interface (what it exports).
- Components must not import from other components except `graph` (the shared data model).
- Bases compose components together. They are the only place cross-component wiring happens.
- The `core.py` files in each brick are Polylith scaffolding -- leave them empty.

### Imports
```python
# correct
from memoria.graph.node import Node
from memoria.graph.edge import Edge

# wrong
from memoria.node import Node       # not a real module path
from .node import Node               # no relative imports
```

### Testing
- Tests live in `tests/components/` and `tests/bases/` (flat layout).
- Test files: `test_<component_name>.py`.
- Use `pytest` with `tempfile.TemporaryDirectory()` for storage tests.
- Mock the LLM callable as a plain function returning JSON strings.
- No external services, no network, no database required for tests.

## Component Reference

| Component | Key Classes | File | Purpose |
|-----------|------------|------|---------|
| graph | `Node`, `Edge`, `MemoryGraph` | `graph/graph.py`, `graph/node.py`, `graph/edge.py` | In-memory directed graph |
| graph | `serialize`, `deserialize`, `to_graphviz` | `graph/dot_serializer.py` | DOT format I/O |
| storage | `FileStore` | `storage/file_store.py` | File persistence (daily + archived) |
| scoring | `Scorer`, `ScoringConfig` | `scoring/scorer.py`, `scoring/config.py` | Activation scoring with decay |
| gardener | `Gardener`, `MemoryScheduler` | `gardener/gardener.py`, `gardener/scheduler.py` | Pruning + scheduled gardening |
| extractor | `Extractor`, `ExtractionResult` | `extractor/extractor.py` | LLM-based memory extraction |
| extractor | `generate_slug`, `generate_id` | `extractor/slug.py` | Node ID generation |
| retrieval | `Retriever`, `RetrievalResult` | `retrieval/retriever.py` | Scored context retrieval |
| memory_api | `MemoryAPI` | `memory_api/api.py` | Public API facade (the base) |

## Public API (MemoryAPI)

The single entry point consumers use:

```python
from memoria.memory_api import MemoryAPI

mem = MemoryAPI(
    storage_path="./memories",       # defaults to ~/.memoria
    llm_callable=my_llm_function,    # Callable[[str], str], required for extract()
    scoring_config=ScoringConfig(),  # optional tuning
)
```

| Method | What it does |
|--------|-------------|
| `store(id, content, label?, connects_to?)` | Manually add a node with optional edges |
| `extract(conversation_text)` | Extract memories from text via LLM |
| `retrieve(query, top_k=10)` | Get relevant memories as dicts |
| `garden()` | Run pruning, returns stats dict |
| `start_scheduler(interval_seconds=3600)` | Start periodic gardening |
| `stop_scheduler()` | Stop the scheduler |
| `export_dot()` | Get DOT string of active graph |
| `get_node(id)` | Fetch single node |
| `connect(source_id, target_id)` | Add edge between nodes |
| `remove_node(node_id)` | Remove node and its edges |
| `list_nodes()` | All nodes as `{id, label, score}` dicts |
| `get_graph()` | Full active MemoryGraph |

## Dependencies

- **Core**: `graphviz` (DOT parsing/rendering)
- **Optional** (`pip install memoria[scheduler]`): `apscheduler`
- **Dev**: `polylith-cli`, `pytest`, `pytest-cov`, `ruff`

## Common Tasks

### Adding a new component
```bash
uv run poly create component --name my_component
# Then implement in components/memoria/my_component/
# Export from __init__.py
# Wire into MemoryAPI in bases/memoria/memory_api/api.py
```

### Modifying the scoring algorithm
- Edit `components/memoria/scoring/scorer.py` for logic.
- Edit `components/memoria/scoring/config.py` for parameters.
- Run tests: `uv run pytest tests/components/test_scoring.py -v`

### Changing the DOT file format
- Edit `components/memoria/graph/dot_serializer.py`.
- The `serialize()` and `deserialize()` functions must stay in sync.
- Run tests: `uv run pytest tests/components/test_graph.py -v`
- Verify storage roundtrip: `uv run pytest tests/components/test_storage.py -v`

### Changing the extraction prompt
- Edit `components/memoria/extractor/prompts.py`.
- The expected LLM response format is: `[{"content": "...", "label": "...", "connects_to": [...]}]`.
- Run tests: `uv run pytest tests/components/test_extractor.py -v`
