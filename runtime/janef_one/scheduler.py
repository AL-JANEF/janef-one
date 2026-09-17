from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class AgentTask:
    id: str
    depends_on: tuple[str, ...] = ()
    parallel_benefit: int = 50
    risk: int = 0
    estimated_cost: int = 1
    capability: str = "general"

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("task id is required")
        for name, value in (("parallel_benefit", self.parallel_benefit), ("risk", self.risk)):
            if not 0 <= value <= 100:
                raise ValueError(f"{name} must be between 0 and 100")
        if self.estimated_cost < 1:
            raise ValueError("estimated_cost must be >= 1")


@dataclass(frozen=True, slots=True)
class Schedule:
    waves: tuple[tuple[str, ...], ...]
    mode: str
    total_cost: int
    deferred: tuple[str, ...] = ()


class MultiAgentScheduler:
    """Plan independent execution waves without spawning agents itself.

    High-risk tasks are serialized. Optional cost budgets fail closed by
    deferring work rather than silently overspending the declared budget.
    """

    def plan(
        self,
        tasks: Iterable[AgentTask],
        *,
        parallel_threshold: int = 60,
        max_parallel: int = 4,
        max_total_cost: int | None = None,
        high_risk_threshold: int = 70,
    ) -> Schedule:
        if not 0 <= parallel_threshold <= 100:
            raise ValueError("parallel_threshold must be between 0 and 100")
        if not 1 <= max_parallel <= 64:
            raise ValueError("max_parallel must be between 1 and 64")
        if not 0 <= high_risk_threshold <= 100:
            raise ValueError("high_risk_threshold must be between 0 and 100")
        if max_total_cost is not None and max_total_cost < 0:
            raise ValueError("max_total_cost must be >= 0")

        task_list = list(tasks)
        task_map = {task.id: task for task in task_list}
        if len(task_map) != len(task_list):
            raise ValueError("duplicate task IDs")
        if not task_map:
            return Schedule((), "none", 0, ())
        ids = set(task_map)
        for task in task_map.values():
            unknown = set(task.depends_on) - ids
            if unknown:
                raise ValueError(f"task {task.id!r} has unknown dependencies: {sorted(unknown)}")
            if task.id in task.depends_on:
                raise ValueError(f"task {task.id!r} cannot depend on itself")

        remaining = set(task_map)
        completed: set[str] = set()
        deferred: set[str] = set()
        waves: list[tuple[str, ...]] = []
        spent = 0
        while remaining:
            ready = sorted(tid for tid in remaining if set(task_map[tid].depends_on) <= completed)
            if not ready:
                # If remaining tasks depend on deferred work, they are deferred too.
                newly_deferred = {
                    tid for tid in remaining if set(task_map[tid].depends_on) & deferred
                }
                if newly_deferred:
                    deferred.update(newly_deferred)
                    remaining.difference_update(newly_deferred)
                    continue
                raise ValueError("dependency cycle detected")

            affordable = [
                tid for tid in ready
                if max_total_cost is None or spent + task_map[tid].estimated_cost <= max_total_cost
            ]
            for tid in set(ready) - set(affordable):
                deferred.add(tid)
                remaining.remove(tid)
            if not affordable:
                continue

            safe_parallel = [
                tid
                for tid in affordable
                if task_map[tid].parallel_benefit >= parallel_threshold
                and task_map[tid].risk < high_risk_threshold
            ]
            if len(safe_parallel) >= 2:
                wave_candidates = safe_parallel[:max_parallel]
                if max_total_cost is not None:
                    wave: list[str] = []
                    running_cost = spent
                    for tid in wave_candidates:
                        cost = task_map[tid].estimated_cost
                        if running_cost + cost <= max_total_cost:
                            wave.append(tid)
                            running_cost += cost
                    chosen = tuple(wave)
                else:
                    chosen = tuple(wave_candidates)
            else:
                # Risky or low-benefit tasks run one at a time.
                chosen = (affordable[0],)

            if not chosen:
                # Budget cannot fit any ready task.
                deferred.update(affordable)
                remaining.difference_update(affordable)
                continue
            waves.append(chosen)
            cost = sum(task_map[tid].estimated_cost for tid in chosen)
            spent += cost
            remaining.difference_update(chosen)
            completed.update(chosen)

        mode = "parallel" if any(len(wave) > 1 for wave in waves) else ("serial" if waves else "none")
        return Schedule(tuple(waves), mode, spent, tuple(sorted(deferred)))
