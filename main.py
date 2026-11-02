"""Temporary testing ground: build a sample owner and print today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner("Jordan", available_minutes=90)

    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", 30, "high", time="07:30"))
    mochi.add_task(Task("Breakfast", 10, "high", time="08:00"))
    mochi.add_task(Task("Grooming", 45, "low", time="16:00", frequency="weekly"))
    luna.add_task(Task("Medication", 5, "high", time="09:00"))
    luna.add_task(Task("Play session", 20, "medium", time="18:00"))

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    print("=" * 52)
    print(f"  Today's Schedule for {owner.name}")
    print("=" * 52)
    print(f"  {'Time':<7}{'Task':<16}{'Pet':<9}{'Min':>4}  Priority")
    print("  " + "-" * 48)
    for task in sorted(plan, key=lambda t: t.time or "99:99"):
        print(
            f"  {task.time or '--:--':<7}{task.description:<16}"
            f"{task.pet_name:<9}{task.duration_minutes:>4}  {task.priority}"
        )
    print("  " + "-" * 48)
    used = sum(t.duration_minutes for t in plan)
    print(f"  {used} of {owner.available_minutes} minutes scheduled")
    print()
    print(scheduler.explain_plan())


if __name__ == "__main__":
    main()
