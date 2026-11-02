"""Temporary testing ground: build a sample owner and print today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task


def print_tasks(title: str, tasks: list[Task]) -> None:
    """Print a titled table of tasks."""
    if title:
        print(title)
    print(f"  {'Time':<7}{'Task':<16}{'Pet':<9}{'Min':>4}  {'Priority':<9}Due")
    print("  " + "-" * 56)
    for task in tasks:
        print(
            f"  {task.time or '--:--':<7}{task.description:<16}{task.pet_name:<9}"
            f"{task.duration_minutes:>4}  {task.priority:<9}{task.due_date}"
        )
    print()


def main() -> None:
    owner = Owner("Jordan", available_minutes=90)

    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added out of time order on purpose, to show sort_by_time.
    luna.add_task(Task("Play session", 20, "medium", time="18:00"))
    mochi.add_task(Task("Breakfast", 10, "high", time="08:00"))
    mochi.add_task(Task("Morning walk", 30, "high", time="07:30"))
    mochi.add_task(Task("Grooming", 45, "low", time="16:00", frequency="weekly"))
    luna.add_task(Task("Medication", 5, "high", time="07:45"))  # overlaps the walk

    scheduler = Scheduler(owner)
    all_tasks = owner.get_all_tasks()
    print_tasks("All tasks in the order they were added:", all_tasks)
    print_tasks("All tasks sorted by time:", scheduler.sort_by_time(all_tasks))

    plan = scheduler.generate_plan()

    print("=" * 58)
    print(f"  Today's Schedule for {owner.name}")
    print("=" * 58)
    print_tasks("", scheduler.sort_by_time(plan))
    print(scheduler.explain_plan())
    print()

    print_tasks("Luna's tasks only:", scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Luna")))

    walk = next(t for t in mochi.tasks if t.description == "Morning walk")
    next_walk = scheduler.mark_task_complete(walk)
    print(f"Completed Morning walk; next one is due {next_walk.due_date}.")
    print_tasks(
        "Pending tasks after completing the walk:",
        scheduler.sort_by_time(scheduler.filter_tasks(completed=False)),
    )
    print_tasks("Completed tasks:", scheduler.filter_tasks(completed=True))


if __name__ == "__main__":
    main()
