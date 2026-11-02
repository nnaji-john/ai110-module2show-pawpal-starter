"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str  # "low", "medium", or "high"
    completed: bool = False

    def priority_value(self) -> int:
        """Return a numeric rank for this task's priority (higher = more important)."""
        pass

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove the task with the given title."""
        pass


@dataclass
class Owner:
    """A pet owner, their daily time budget, and their pets."""

    name: str
    available_minutes: int
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        pass


class Scheduler:
    """Builds and explains a daily care plan for an owner."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.plan: list[Task] = []
        self.skipped: list[Task] = []

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered from highest to lowest priority."""
        pass

    def generate_plan(self) -> list[Task]:
        """Choose and order tasks that fit within the owner's available time."""
        pass

    def explain_plan(self) -> str:
        """Describe why each task was scheduled or skipped."""
        pass
