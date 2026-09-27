import uuid
import streamlit as st

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from graph import app


st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide",
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "running" not in st.session_state:
    st.session_state.running = False

if "waiting_for_approval" not in st.session_state:
    st.session_state.waiting_for_approval = False

if "result" not in st.session_state:
    st.session_state.result = None

if "interrupt_data" not in st.session_state:
    st.session_state.interrupt_data = None


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("✈️ AI Travel Planner")

st.markdown(
    """
    Plan your trip using a multi-agent AI system.

    **Agents:** Flight → Hotel → Weather → Budget → Itinerary
    """
)

st.divider()


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.header("⚙️ Trip Planner")

    st.write("**Agent Pipeline**")

    agents = [
        "🧑‍✈️ Flight Agent",
        "🏨 Hotel Agent",
        "🌤️ Weather Agent",
        "💰 Budget Agent",
        "🗺️ Itinerary Agent",
        "👤 Human Approval",
        "✨ Final Response",
    ]

    for agent in agents:
        st.write(agent)

    st.divider()

    st.caption(
        "Each request is processed by the LangGraph "
        "multi-agent workflow."
    )

    if st.button("🔄 New Trip"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.running = False
        st.session_state.waiting_for_approval = False
        st.session_state.result = None
        st.session_state.interrupt_data = None
        st.rerun()


# --------------------------------------------------
# USER INPUT
# --------------------------------------------------

query = st.text_area(
    "Where would you like to travel?",
    placeholder=(
        "Example: Plan a 6-day trip to Bali from "
        "Bhubaneswar with a budget of ₹80,000."
    ),
    height=120,
)


# --------------------------------------------------
# START TRIP
# --------------------------------------------------

if st.button(
    "🚀 Plan My Trip",
    type="primary",
    use_container_width=True,
):

    if not query.strip():
        st.warning("Please enter a travel request.")
        st.stop()

    st.session_state.running = True

    config = {
        "configurable": {
            "thread_id": st.session_state.thread_id
        }
    }

    initial_state = {
        "user_query": query,
        "messages": [
            HumanMessage(content=query)
        ],
        "llm_calls": 0,
    }

    with st.spinner("🤖 AI agents are planning your trip..."):

        try:

            result = app.invoke(
                initial_state,
                config=config,
            )

            # Check whether LangGraph paused
            # for human approval.
            state_snapshot = app.get_state(config)

            interrupts = state_snapshot.interrupts

            if interrupts:

                interrupt_value = interrupts[0].value

                st.session_state.interrupt_data = interrupt_value
                st.session_state.waiting_for_approval = True

            else:

                st.session_state.result = result
                st.session_state.waiting_for_approval = False

        except Exception as e:

            st.error(f"Something went wrong: {e}")

    st.session_state.running = False
    st.rerun()


# --------------------------------------------------
# HUMAN APPROVAL
# --------------------------------------------------

if st.session_state.waiting_for_approval:

    data = st.session_state.interrupt_data

    st.divider()

    st.subheader("👤 Human Approval Required")

    st.info(
        data.get(
            "question",
            "Do you approve this itinerary?"
        )
    )

    st.markdown("### 🗺️ Draft Itinerary")

    st.markdown(
        data.get(
            "draft_itinerary",
            "No itinerary available."
        )
    )

    st.divider()

    feedback = st.text_area(
        "Feedback",
        placeholder=(
            "Optional: Tell the AI what should be "
            "changed before finalizing the trip."
        ),
        height=100,
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "✅ Approve",
            type="primary",
            use_container_width=True,
        ):

            config = {
                "configurable": {
                    "thread_id": st.session_state.thread_id
                }
            }

            with st.spinner(
                "✨ Creating your final travel plan..."
            ):

                result = app.invoke(
                    Command(
                        resume={
                            "approved": True,
                            "feedback": feedback,
                        }
                    ),
                    config=config,
                )

            st.session_state.result = result
            st.session_state.waiting_for_approval = False
            st.session_state.interrupt_data = None

            st.rerun()

    with col2:

        if st.button(
            "❌ Reject",
            use_container_width=True,
        ):

            config = {
                "configurable": {
                    "thread_id": st.session_state.thread_id
                }
            }

            with st.spinner(
                "🔄 Updating the travel plan..."
            ):

                result = app.invoke(
                    Command(
                        resume={
                            "approved": False,
                            "feedback": feedback,
                        }
                    ),
                    config=config,
                )

            st.session_state.result = result
            st.session_state.waiting_for_approval = False
            st.session_state.interrupt_data = None

            st.rerun()


# --------------------------------------------------
# FINAL RESULT
# --------------------------------------------------

if st.session_state.result:

    result = st.session_state.result

    st.divider()

    st.subheader("✨ Your Final Travel Plan")

    final_response = result.get(
        "final_response"
    )

    if final_response:

        st.markdown(final_response)

    else:

        st.warning(
            "The workflow completed but "
            "no final response was returned."
        )


# --------------------------------------------------
# DEBUG / AGENT INFORMATION
# --------------------------------------------------

if st.session_state.result:

    with st.expander("🔍 Agent Execution Details"):

        result = st.session_state.result

        st.write(
            "Selected Agents:",
            result.get("selected_agents", [])
        )

        st.write(
            "Trip Constraints:",
            result.get("trip_constraints", {})
        )

        st.write(
            "Supervisor Reasoning:",
            result.get("supervisor_reasoning", "")
        )

        st.write(
            "LLM Calls:",
            result.get("llm_calls", 0)
        )