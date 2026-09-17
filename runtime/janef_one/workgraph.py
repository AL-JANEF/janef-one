from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Callable, Iterable


class WorkGraphError(ValueError):
    pass


class NodeStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(slots=True)
class WorkNode:
    id: str
    action: str
    depends_on: tuple[str, ...] = ()
    requires_verification: bool = True
    max_attempts: int = 1
    metadata: dict[str, object] = field(default_factory=dict)
    status: NodeStatus = NodeStatus.PENDING
    attempts: int = 0
    output: object | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.id or not self.action:
            raise WorkGraphError("node id and action are required")
        if self.max_attempts < 1:
            raise WorkGraphError("max_attempts must be >= 1")
        if self.id in self.depends_on:
            raise WorkGraphError(f"node {self.id!r} cannot depend on itself")

    def reset(self) -> None:
        self.status = NodeStatus.PENDING
        self.attempts = 0
        self.output = None
        self.error = None


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    succeeded: tuple[str, ...]
    failed: tuple[str, ...]
    blocked: tuple[str, ...]
    attempts: int

    @property
    def ok(self) -> bool:
        return not self.failed and not self.blocked


class WorkGraph:
    """Dependency graph with verification gates, retries, resume, and safe parallel waves."""

    def __init__(self, nodes: Iterable[WorkNode]) -> None:
        node_list = list(nodes)
        self.nodes = {node.id: node for node in node_list}
        if not self.nodes:
            raise WorkGraphError("workgraph requires at least one node")
        if len(self.nodes) != len(node_list):
            raise WorkGraphError("duplicate node IDs")
        self.validate()

    def validate(self) -> None:
        for node in self.nodes.values():
            for dep in node.depends_on:
                if dep not in self.nodes:
                    raise WorkGraphError(f"node {node.id!r} depends on unknown node {dep!r}")
                if dep == node.id:
                    raise WorkGraphError(f"node {node.id!r} cannot depend on itself")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            if node_id in visiting:
                raise WorkGraphError("dependency cycle detected")
            visiting.add(node_id)
            for dep in self.nodes[node_id].depends_on:
                visit(dep)
            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in self.nodes:
            visit(node_id)

    def topological_order(self) -> list[str]:
        indegree = {node_id: 0 for node_id in self.nodes}
        children: dict[str, list[str]] = {node_id: [] for node_id in self.nodes}
        for node in self.nodes.values():
            for dep in node.depends_on:
                indegree[node.id] += 1
                children[dep].append(node.id)
        queue = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
        result: list[str] = []
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            for child in sorted(children[node_id]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
                    queue.sort()
        if len(result) != len(self.nodes):
            raise WorkGraphError("dependency cycle detected")
        return result

    def reset(self, *, include_succeeded: bool = True) -> None:
        for node in self.nodes.values():
            if include_succeeded or node.status != NodeStatus.SUCCEEDED:
                node.reset()

    def _run_node(
        self,
        node: WorkNode,
        handler: Callable[[WorkNode], object],
        verifier: Callable[[WorkNode, object], bool] | None,
        retry_delay: float,
    ) -> None:
        node.status = NodeStatus.READY
        while node.attempts < node.max_attempts:
            node.attempts += 1
            node.status = NodeStatus.RUNNING
            try:
                output = handler(node)
                if node.requires_verification:
                    if verifier is None:
                        raise RuntimeError("verification required but no verifier was supplied")
                    if not verifier(node, output):
                        raise RuntimeError("verification gate rejected output")
                node.output = output
                node.status = NodeStatus.SUCCEEDED
                node.error = None
                return
            except Exception as exc:  # deliberate execution boundary
                node.error = f"{type(exc).__name__}: {exc}"
                node.status = NodeStatus.FAILED
                if node.attempts < node.max_attempts and retry_delay:
                    time.sleep(retry_delay)

    def _mark_blocked(self) -> None:
        changed = True
        while changed:
            changed = False
            for node in self.nodes.values():
                if node.status not in {NodeStatus.PENDING, NodeStatus.READY}:
                    continue
                bad = [
                    dep
                    for dep in node.depends_on
                    if self.nodes[dep].status in {NodeStatus.FAILED, NodeStatus.BLOCKED}
                ]
                if bad:
                    node.status = NodeStatus.BLOCKED
                    node.error = f"blocked by dependencies: {', '.join(sorted(bad))}"
                    changed = True

    def _report(self) -> ExecutionReport:
        order = self.topological_order()
        return ExecutionReport(
            succeeded=tuple(node_id for node_id in order if self.nodes[node_id].status == NodeStatus.SUCCEEDED),
            failed=tuple(node_id for node_id in order if self.nodes[node_id].status == NodeStatus.FAILED),
            blocked=tuple(node_id for node_id in order if self.nodes[node_id].status == NodeStatus.BLOCKED),
            attempts=sum(node.attempts for node in self.nodes.values()),
        )

    def execute(
        self,
        handlers: dict[str, Callable[[WorkNode], object]],
        verifier: Callable[[WorkNode, object], bool] | None = None,
        *,
        retry_delay: float = 0.0,
        resume: bool = True,
    ) -> ExecutionReport:
        if retry_delay < 0:
            raise ValueError("retry_delay must be >= 0")
        if not resume:
            self.reset()
        for node_id in self.topological_order():
            node = self.nodes[node_id]
            if resume and node.status == NodeStatus.SUCCEEDED:
                continue
            failed_deps = [dep for dep in node.depends_on if self.nodes[dep].status != NodeStatus.SUCCEEDED]
            if failed_deps:
                node.status = NodeStatus.BLOCKED
                node.error = f"blocked by dependencies: {', '.join(sorted(failed_deps))}"
                continue
            handler = handlers.get(node.action)
            if handler is None:
                node.status = NodeStatus.FAILED
                node.error = f"no handler for action {node.action!r}"
                continue
            self._run_node(node, handler, verifier, retry_delay)
        self._mark_blocked()
        return self._report()

    def execute_parallel(
        self,
        handlers: dict[str, Callable[[WorkNode], object]],
        verifier: Callable[[WorkNode, object], bool] | None = None,
        *,
        max_workers: int = 4,
        retry_delay: float = 0.0,
        resume: bool = True,
    ) -> ExecutionReport:
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        if retry_delay < 0:
            raise ValueError("retry_delay must be >= 0")
        if not resume:
            self.reset()

        while True:
            self._mark_blocked()
            pending = [node for node in self.nodes.values() if node.status == NodeStatus.PENDING]
            if not pending:
                break
            ready = sorted(
                (
                    node
                    for node in pending
                    if all(self.nodes[dep].status == NodeStatus.SUCCEEDED for dep in node.depends_on)
                ),
                key=lambda n: n.id,
            )
            if not ready:
                # Validation rules out dependency cycles, so remaining nodes can
                # only be blocked by a non-success dependency.
                self._mark_blocked()
                break

            runnable: list[tuple[WorkNode, Callable[[WorkNode], object]]] = []
            for node in ready:
                handler = handlers.get(node.action)
                if handler is None:
                    node.status = NodeStatus.FAILED
                    node.error = f"no handler for action {node.action!r}"
                else:
                    runnable.append((node, handler))
            if not runnable:
                continue

            with ThreadPoolExecutor(max_workers=min(max_workers, len(runnable))) as pool:
                futures = {
                    pool.submit(self._run_node, node, handler, verifier, retry_delay): node.id
                    for node, handler in runnable
                }
                for future in as_completed(futures):
                    # _run_node catches task failures; this catches executor-level
                    # faults so they cannot vanish silently.
                    exc = future.exception()
                    if exc is not None:
                        node = self.nodes[futures[future]]
                        node.status = NodeStatus.FAILED
                        node.error = f"executor failure: {type(exc).__name__}: {exc}"
        self._mark_blocked()
        return self._report()

    def to_dict(self) -> dict[str, object]:
        return {
            "nodes": [
                {
                    **asdict(self.nodes[node_id]),
                    "status": self.nodes[node_id].status.value,
                }
                for node_id in self.topological_order()
            ]
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "WorkGraph":
        raw_nodes = payload.get("nodes")
        if not isinstance(raw_nodes, list):
            raise WorkGraphError("payload.nodes must be a list")
        nodes: list[WorkNode] = []
        for raw in raw_nodes:
            if not isinstance(raw, dict):
                raise WorkGraphError("node payload must be an object")
            item = dict(raw)
            item["depends_on"] = tuple(item.get("depends_on", ()))
            item["status"] = NodeStatus(item.get("status", NodeStatus.PENDING.value))
            nodes.append(WorkNode(**item))
        return cls(nodes)
