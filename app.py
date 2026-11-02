import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")
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

st.markdown("### Pets")
with st.form("add_pet", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
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
    st.table([{"Pet": p.name, "Species": p.species, "Tasks": len(p.tasks)} for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
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

    scheduler = Scheduler(owner)

    pending = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
    if pending:
        with st.form("complete_task"):
            labels = [f"{t.pet_name}: {t.description} (due {t.due_date})" for t in pending]
            choice = st.selectbox("Mark a task complete", range(len(pending)), format_func=labels.__getitem__)
            if st.form_submit_button("Mark complete"):
                task = pending[choice]
                next_task = scheduler.mark_task_complete(task)
                if next_task is None:
                    st.success(f"Completed {task.description}.")
                else:
                    st.success(f"Completed {task.description}; next one is due {next_task.due_date}.")

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
        st.table(
            [
                {
                    "Time": t.time or "-",
                    "Pet": t.pet_name,
                    "Task": t.description,
                    "Minutes": t.duration_minutes,
                    "Priority": t.priority,
                    "Frequency": t.frequency,
                    "Due": str(t.due_date),
                    "Done": "yes" if t.completed else "no",
                }
                for t in tasks
            ]
        )
    else:
        st.info("No tasks match. Add one above or change the filters.")

st.divider()

st.subheader("Build Schedule")
st.caption("Picks the highest-priority tasks due today that fit in your available time.")

if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()
    for warning in scheduler.conflicts:
        st.warning(warning)
    if plan:
        st.table(
            [
                {
                    "Time": t.time or "-",
                    "Task": t.description,
                    "Pet": t.pet_name,
                    "Minutes": t.duration_minutes,
                    "Priority": t.priority,
                }
                for t in scheduler.sort_by_time(plan)
            ]
        )
    st.text(scheduler.explain_plan())
