"""Generic directed-graph utilities over DataModelRelationship edges —
shared by the Data Modeler, Architecture Diagram Builder, and Pipeline
Playground validation (spec's "cycle detection, topological ordering"),
since all three are, underneath, just a labeled graph of boxes and arrows
(see DataModel.model_kind's docstring)."""

from __future__ import annotations

from app.models.data_model import DataModelRelationship


def build_adjacency(relationships: list[DataModelRelationship]) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = {}
    for rel in relationships:
        adjacency.setdefault(rel.from_table_id, []).append(rel.to_table_id)
        adjacency.setdefault(rel.to_table_id, [])
    return adjacency


def find_one_cycle(adjacency: dict[str, list[str]]) -> list[str] | None:
    """DFS with white/gray/black coloring; returns one cycle (as a list of
    node ids, in order) if the graph has any, else None. Doesn't enumerate
    every cycle — one concrete example is enough to explain the problem."""
    white, gray, black = 0, 1, 2
    color: dict[str, int] = dict.fromkeys(adjacency, white)
    parent: dict[str, str | None] = {}

    def _dfs(start: str) -> list[str] | None:
        stack = [(start, iter(adjacency.get(start, [])))]
        color[start] = gray
        parent[start] = None
        while stack:
            node, neighbors = stack[-1]
            advanced = False
            for neighbor in neighbors:
                if color.get(neighbor, white) == white:
                    color[neighbor] = gray
                    parent[neighbor] = node
                    stack.append((neighbor, iter(adjacency.get(neighbor, []))))
                    advanced = True
                    break
                if color.get(neighbor) == gray:
                    # Found a back-edge: reconstruct the cycle via parent pointers.
                    cycle = [neighbor, node]
                    cursor = node
                    while parent.get(cursor) is not None and parent[cursor] != neighbor:
                        cursor = parent[cursor]  # type: ignore[assignment]
                        cycle.append(cursor)
                    cycle.append(neighbor)
                    cycle.reverse()
                    return cycle
            if not advanced:
                color[node] = black
                stack.pop()
        return None

    for node in adjacency:
        if color[node] == white:
            result = _dfs(node)
            if result is not None:
                return result
    return None


def topological_order(adjacency: dict[str, list[str]]) -> list[str] | None:
    """Kahn's algorithm. Returns None if the graph has a cycle (no valid order exists)."""
    in_degree: dict[str, int] = dict.fromkeys(adjacency, 0)
    for neighbors in adjacency.values():
        for neighbor in neighbors:
            in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

    queue = [node for node, degree in in_degree.items() if degree == 0]
    order: list[str] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for neighbor in adjacency.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(adjacency):
        return None
    return order
