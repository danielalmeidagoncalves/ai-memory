"""
memoria - AI Memory System: Usage Examples
===========================================

Run with: uv run python development/scratch.py
"""

import json
import tempfile

from memoria.memory_api import MemoryAPI


def mock_llm(prompt: str) -> str:
    """Simulates an LLM response for memory extraction."""
    return json.dumps(
        [
            {
                "content": "Metaclasses are classes that create other classes",
                "label": "Metaclasses",
                "connects_to": ["python_classes"],
            }
        ]
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        mem = MemoryAPI(
            storage_path=tmp,
            llm_callable=mock_llm,
        )

        # --- Manual storage ---
        n1 = mem.store(
            "python_decorators",
            "Decorators wrap functions to modify behavior",
            label="Python Decorators",
        )
        n2 = mem.store(
            "python_functions",
            "Functions are first-class objects in Python",
            label="Functions",
            connects_to=["python_decorators"],
        )
        n3 = mem.store(
            "python_classes",
            "Classes define objects with attributes and methods",
            label="Classes",
            connects_to=["python_functions"],
        )
        print(f"Stored nodes: {n1.id}, {n2.id}, {n3.id}")

        # --- LLM-based extraction ---
        result = mem.extract(
            "The user asked about Python metaclasses and "
            "how they relate to class creation."
        )
        print(f"\nExtracted {len(result.nodes)} new nodes:")
        for node in result.nodes:
            print(f"  - {node.id}: {node.label}")
        for edge in result.edges:
            print(f"  - edge: {edge.source_id} -> {edge.target_id}")

        # --- Retrieve context ---
        context = mem.retrieve("how do decorators work?", top_k=5)
        print(f"\nRetrieved {len(context)} results:")
        for item in context:
            print(f"  [{item['id']}] {item['label']} (score: {item['score']:.4f})")
            for related in item["related"]:
                print(f"    -> [{related['id']}] {related['label']}")

        # --- Export DOT ---
        dot = mem.export_dot()
        print(f"\nDOT representation ({len(dot)} chars):")
        print(dot[:300])

        # --- Gardening ---
        stats = mem.garden()
        print(f"\nGarden stats: {stats}")

        # --- List all nodes ---
        nodes = mem.list_nodes()
        print(f"\nAll active nodes ({len(nodes)}):")
        for n in nodes:
            print(f"  - {n['id']} (score: {n['score']:.4f})")

        # --- Scheduler lifecycle ---
        mem.start_scheduler(interval_seconds=3600)
        print(f"\nScheduler running: {mem.scheduler_running}")
        mem.stop_scheduler()
        print(f"Scheduler running: {mem.scheduler_running}")


if __name__ == "__main__":
    main()
