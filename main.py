import uuid
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from graph import graph

load_dotenv()


def run():
    # ── thread_id ────────────────────────────
    # The checkpointer uses thread_id to store and retrieve
    # state for THIS conversation. Each new run() call gets
    # a fresh uuid = fresh conversation.
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    print("=" * 45)
    print("   Food Ordering Agent")
    print("   Type 'quit' to exit")
    print("=" * 45)

    while True:
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        # ── Invoke the graph ─────────────────
        # We pass only the NEW human message.
        # LangGraph appends it to the existing messages in state
        # (because MessagesState uses a list reducer).
        result = graph.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
        )

        # The last message in state is always the AI's reply
        ai_message = result["messages"][-1]
        print(f"\nAgent: {ai_message.content}")

        # ── Debug: show extracted fields ─────
        # This helps us see what the node pulled out of the conversation.
        # We'll remove this once the full graph is working.
        food       = result.get("food_query")
        restaurant = result.get("restaurant_name")
        address    = result.get("delivery_address")

        if any([food, restaurant, address]):
            print("\n[Extracted so far]")
            if food:       print(f"  Food       : {food}")
            if restaurant: print(f"  Restaurant : {restaurant}")
            if address:    print(f"  Address    : {address}")


if __name__ == "__main__":
    run()
