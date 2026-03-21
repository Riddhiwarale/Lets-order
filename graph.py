from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import OrderState
from nodes.gather_intent import gather_intent


# ─────────────────────────────────────────────
#  Routing function — conditional edge
#
#  After gather_intent runs, LangGraph calls
#  this function to decide which node to go to next.
#
#  It returns a string key that maps to a node name
#  (or END) in add_conditional_edges() below.
# ─────────────────────────────────────────────

def route_after_intent(state: OrderState) -> str:
    has_food    = bool(state.get("food_query"))
    has_address = bool(state.get("delivery_address"))

    if has_food and has_address:
        # We have everything we need — ready to search both platforms
        # For now this goes to END, we'll connect search nodes later
        return "ready_to_search"

    # Still missing info — end this turn and wait for next user message
    return "need_more_info"


# ─────────────────────────────────────────────
#  build_graph — assembles the full graph
#
#  StateGraph takes our OrderState so every node
#  knows the shape of the state it receives.
# ─────────────────────────────────────────────

def build_graph():
    builder = StateGraph(OrderState)

    # ── Register nodes ───────────────────────
    # First argument = name used in edges
    # Second argument = the function to call
    builder.add_node("gather_intent", gather_intent)

    # ── Edges ────────────────────────────────
    # START is a built-in LangGraph constant for the entry point
    builder.add_edge(START, "gather_intent")

    # Conditional edge: after gather_intent, call route_after_intent()
    # and use its return value to pick the next node.
    builder.add_conditional_edges(
        "gather_intent",         # from this node
        route_after_intent,      # call this function to decide
        {
            "ready_to_search": END,   # will become → search node later
            "need_more_info":  END,   # end this turn, wait for user input
        }
    )

    # ── Checkpointer (memory) ────────────────
    # MemorySaver stores the full state after each turn.
    # This is what lets the conversation continue across multiple
    # graph.invoke() calls — the state is never lost between turns.
    checkpointer = MemorySaver()

    return builder.compile(checkpointer=checkpointer)


# Build once, import everywhere
graph = build_graph()
