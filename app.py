"""PawPal+ Streamlit UI. All scheduling logic lives in pawpal_system.py; this file only
collects input, calls those classes, and displays the results."""

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

# Colored labels so priorities are easy to scan in the tables.
PRIORITY_LABELS = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.markdown(
    "Plan your pets' care for the day. Add your pets and their tasks, and PawPal+ picks "
    "the most important tasks that fit in your time, puts them in order, and warns you "
    "about anything scheduled at the same time."
)

st.divider()

st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    available_minutes = st.number_input(
        "Minutes available for pet care today", min_value=1, max_value=1440, value=60
    )

# Streamlit reruns this script on every interaction, so keep one Owner in
# session_state and only create it the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, available_minutes=int(available_minutes))
owner = st.session_state.owner
owner.name = owner_name
owner.available_minutes = int(available_minutes)
# The Scheduler holds no data of its own between runs (it reads everything from the
# Owner), so it's fine to create a fresh one on every rerun.
scheduler = Scheduler(owner)

st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        name = pet_name.strip()
        if not name:
            st.error("Enter a pet name.")
        elif any(p.name == name for p in owner.pets):
            st.error(f"You already have a pet named {name}.")
        else:
            owner.add_pet(Pet(name=name, species=species))
            st.success(f"Added {name}.")

if owner.pets:
    st.dataframe(
        [
            {
                "Pet": p.name,
                "Species": p.species,
                "Pending tasks": len(scheduler.filter_tasks(pet_name=p.name, completed=False)),
            }
            for p in owner.pets
        ],
        hide_index=True,
        width="stretch",
    )
else:
    st.info("No pets yet. Add one above.")

st.subheader("Tasks")
if not owner.pets:
    st.caption("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        pet_choice = st.selectbox("Pet", [p.name for p in owner.pets])
        description = st.text_input("Task", value="Morning walk")
        col1, col2 = st.columns(2)
        with col1:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            time = st.text_input("Preferred time (HH:MM, optional)")
        with col2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        if st.form_submit_button("Add task"):
            if not description.strip():
                st.error("Enter a task description.")
            else:
                pet = next(p for p in owner.pets if p.name == pet_choice)
                try:
                    task = Task(
                        description=description.strip(),
                        duration_minutes=int(duration),
                        priority=priority,
                        time=time,
                        frequency=frequency,
                    )
                except ValueError as err:
                    st.error(str(err))
                else:
                    pet.add_task(task)
                    st.success(f"Added {task.description} for {pet.name}.")

    # The complete and reschedule forms below only offer pending tasks, in time order.
    pending = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
    if pending:
        with st.form("complete_task"):
            # The selectbox returns a position in `pending` rather than a label, because
            # two tasks can have the same label (same pet, name, and time).
            labels = [
                f"{t.time or 'Any time'} · {t.pet_name}: {t.description} (due {t.due_date})"
                for t in pending
            ]
            choice = st.selectbox(
                "Mark a task complete", range(len(pending)), format_func=labels.__getitem__
            )
            if st.form_submit_button("Mark complete"):
                task = pending[choice]
                # Goes through the Scheduler so a repeating task's next occurrence is
                # added to the right pet.
                next_task = scheduler.mark_task_complete(task)
                if next_task is None:
                    st.success(f"Completed {task.description} for {task.pet_name}.")
                else:
                    st.success(
                        f"Completed {task.description} for {task.pet_name}. "
                        f"The next one is due {next_task.due_date:%A, %B %d}."
                    )

        # Lets the owner fix a time conflict flagged in Today's Schedule.
        with st.form("reschedule_task"):
            choice = st.selectbox(
                "Change a task's time", range(len(pending)), format_func=labels.__getitem__
            )
            new_time = st.text_input("New time (HH:MM, or leave blank for any time)")
            if st.form_submit_button("Change time"):
                task = pending[choice]
                try:
                    task.reschedule(new_time)
                except ValueError as err:
                    st.error(str(err))
                else:
                    st.success(
                        f"Moved {task.pet_name}'s {task.description} to {task.time or 'any time'}."
                    )

    # Task browser: the dropdowns map onto Scheduler.filter_tasks(), where None means "any".
    col1, col2 = st.columns(2)
    with col1:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with col2:
        status_filter = st.selectbox("Show status", ["Pending", "Completed", "All"])
    tasks = scheduler.sort_by_time(
        scheduler.filter_tasks(
            pet_name=None if pet_filter == "All pets" else pet_filter,
            completed={"Pending": False, "Completed": True, "All": None}[status_filter],
        )
    )
    if tasks:
        st.caption(f"Showing {len(tasks)} task(s), sorted by time.")
        st.dataframe(
            [
                {
                    "Time": t.time or "Any time",
                    "Pet": t.pet_name,
                    "Task": t.description,
                    "Minutes": t.duration_minutes,
                    "Priority": PRIORITY_LABELS[t.priority],
                    "Repeats": t.frequency,
                    "Due": t.due_date,
                    "Done": t.completed,
                }
                for t in tasks
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No tasks match. Add one above or change the filters.")

st.divider()

st.subheader("Today's Schedule")
st.caption("Picks the highest-priority tasks due today that fit in your available time.")

if st.button("Generate schedule", type="primary"):
    plan = scheduler.generate_plan()
    conflict_pairs = scheduler.find_conflicts(plan)
    used = sum(t.duration_minutes for t in plan)

    if not plan and not scheduler.skipped:
        st.info("Nothing to schedule today. Add some tasks, or check back when tasks are due.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Tasks planned", len(plan))
        col2.metric("Minutes used", f"{used} / {owner.available_minutes}")
        col3.metric("Time conflicts", len(conflict_pairs))
        # Share of the day's minutes used. The plan never exceeds the budget, but
        # min() keeps the bar valid if the budget is lowered after planning.
        st.progress(min(used / owner.available_minutes, 1.0))

        # Conflicts come first and are grouped in one box, so the owner sees every
        # clash at once with a suggested fix, instead of a stack of separate alerts.
        if conflict_pairs:
            lines = [
                f"- **{a.time}** {a.pet_name}'s {a.description} ({a.duration_minutes} min) "
                f"{'and' if a.time == b.time else 'runs into'} "
                f"**{b.time}** {b.pet_name}'s {b.description}"
                for a, b in conflict_pairs
            ]
            st.warning(
                f"**{len(conflict_pairs)} time conflict(s) in today's plan.** "
                "Both tasks are still in the schedule, so you can decide how to handle them:\n\n"
                + "\n".join(lines)
                + "\n\nTo fix one, use **Change a task's time** above. Or keep both if you "
                "can do them together, or someone else can help."
            )
        elif plan:
            st.success("No time conflicts. Your schedule is ready!")

        if plan:
            # Track clashing tasks by identity: two different tasks can have identical
            # fields, and dataclass tasks can't go in a set directly.
            clashing = {id(t) for pair in conflict_pairs for t in pair}
            st.dataframe(
                [
                    {
                        "": "⚠️" if id(t) in clashing else "✅",
                        "Time": t.time or "Any time",
                        "Pet": t.pet_name,
                        "Task": t.description,
                        "Minutes": t.duration_minutes,
                        "Priority": PRIORITY_LABELS[t.priority],
                    }
                    for t in scheduler.sort_by_time(plan)
                ],
                hide_index=True,
                width="stretch",
            )

        if scheduler.skipped:
            skipped = ", ".join(f"{t.pet_name}'s {t.description} ({t.duration_minutes} min)" for t in scheduler.skipped)
            st.info(
                f"**Didn't fit today:** {skipped}. "
                "Add more available minutes to include them."
            )

        with st.expander("Why this plan?"):
            st.text(scheduler.explain_plan())
