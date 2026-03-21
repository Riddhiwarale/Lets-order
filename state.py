from typing import Optional
from langgraph.graph import MessagesState


# ─────────────────────────────────────────────
#  OrderState — the single source of truth
#
#  LangGraph passes this state object between
#  every node in the graph. Each node can read
#  from it and write back to it.
#
#  We extend MessagesState so we automatically
#  get the `messages` field — a running list of
#  all Human / AI / Tool messages in the chat.
# ─────────────────────────────────────────────

class OrderState(MessagesState):

    # ── What the user wants ──────────────────
    # Plain text description of food the user wants to order.
    # Example: "2 butter chicken, 1 naan"
    food_query: Optional[str]

    # Name of the restaurant the user prefers.
    # Example: "Behrouz Biryani"
    # Optional — user may not specify a restaurant.
    restaurant_name: Optional[str]

    # Full delivery address provided by the user.
    # Example: "42, MG Road, Bangalore - 560001"
    delivery_address: Optional[str]

    # ── Search results from both platforms ───
    # Raw search results returned by the Swiggy MCP tool.
    # Will be a list of product/restaurant dicts.
    swiggy_results: Optional[list]

    # Raw search results returned by the Zomato MCP tool.
    # Will be a list of product/restaurant dicts.
    zomato_results: Optional[list]

    # ── Cart summaries ────────────────────────
    # After searching, we build a cart on each platform.
    # This stores the cart details (items + total price) from Swiggy.
    # Example: {"items": [...], "total": 450, "delivery_fee": 30}
    swiggy_cart: Optional[dict]

    # Same as above but for Zomato.
    zomato_cart: Optional[dict]

    # ── User's final decision ─────────────────
    # Which platform the user chose to order from.
    # Value will be either "swiggy" or "zomato".
    chosen_platform: Optional[str]

    # Whether the order has been successfully placed.
    # Starts as False, flipped to True after checkout.
    order_placed: Optional[bool]
