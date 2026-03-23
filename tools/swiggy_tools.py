import json
from langchain_core.tools import tool
from tools.mock_db import RESTAURANTS, PLATFORM_CONFIG, fuzzy_match_restaurant, fuzzy_match_item

# ─────────────────────────────────────────────
#  In-memory cart for this session
#
#  A module-level dict acts as a simple cart store.
#  It holds the restaurant name and list of added items.
# ─────────────────────────────────────────────

_cart: dict = {"restaurant": None, "items": []}

CONFIG = PLATFORM_CONFIG["swiggy"]


# ─────────────────────────────────────────────
#  TOOL 1 — swiggy_search_restaurants
#
#  The LLM calls this first to find which
#  restaurants serve the requested food.
#
#  Best practice: tool docstring = tool description
#  for the LLM. Keep it clear and specific.
# ─────────────────────────────────────────────

@tool
def swiggy_search_restaurants(query: str) -> str:
    """
    Search for restaurants on Swiggy that serve the requested food.
    Returns a list of matching restaurants with their cuisine and rating.
    Use this before getting a menu or adding to cart.
    """
    results = []
    query_lower = query.lower()

    for key, restaurant in RESTAURANTS.items():
        # match if query appears in restaurant name or cuisine
        if (query_lower in key
                or query_lower in restaurant["cuisine"].lower()
                or any(query_lower in item for item in restaurant["menu"])):
            results.append({
                "restaurant_id": restaurant["id"],
                "name": restaurant["name"],
                "cuisine": restaurant["cuisine"],
                "rating": restaurant["rating"],
            })

    if not results:
        return json.dumps({"error": f"No restaurants found for '{query}' on Swiggy"})

    return json.dumps({"platform": "swiggy", "results": results})


# ─────────────────────────────────────────────
#  TOOL 2 — swiggy_get_menu
#
#  Returns the full menu of a restaurant with
#  Swiggy-specific prices (base price × 1.0).
# ─────────────────────────────────────────────

@tool
def swiggy_get_menu(restaurant_name: str) -> str:
    """
    Get the full menu with prices for a restaurant on Swiggy.
    Call swiggy_search_restaurants first to confirm the restaurant exists.
    """
    restaurant = fuzzy_match_restaurant(restaurant_name)

    if not restaurant:
        return json.dumps({"error": f"Restaurant '{restaurant_name}' not found on Swiggy"})

    # Apply Swiggy price factor to each item
    menu_with_prices = {
        name: {
            "item_id": data["id"],
            "price": round(data["price"] * CONFIG["price_factor"])
        }
        for name, data in restaurant["menu"].items()
    }

    return json.dumps({
        "platform": "swiggy",
        "restaurant": restaurant["name"],
        "menu": menu_with_prices,
    })


# ─────────────────────────────────────────────
#  TOOL 3 — swiggy_add_to_cart
#
#  Adds one item to the in-memory cart.
#  Only one restaurant per cart (realistic constraint).
# ─────────────────────────────────────────────

@tool
def swiggy_add_to_cart(restaurant_name: str, item_name: str, quantity: int) -> str:
    """
    Add a menu item to the Swiggy cart.
    Provide the restaurant name, item name, and quantity.
    Only items from one restaurant can be in the cart at a time.
    """
    global _cart

    restaurant = fuzzy_match_restaurant(restaurant_name)
    if not restaurant:
        return json.dumps({"error": f"Restaurant '{restaurant_name}' not found on Swiggy"})

    # Enforce single-restaurant cart
    if _cart["restaurant"] and _cart["restaurant"] != restaurant["name"]:
        return json.dumps({"error": "Cart already has items from a different restaurant. Clear cart first."})

    match = fuzzy_match_item(restaurant["menu"], item_name)
    if not match:
        return json.dumps({"error": f"Item '{item_name}' not found in {restaurant['name']} menu on Swiggy"})

    item_key, item_data = match
    price = round(item_data["price"] * CONFIG["price_factor"])

    _cart["restaurant"] = restaurant["name"]
    _cart["items"].append({
        "name": item_key.title(),
        "item_id": item_data["id"],
        "quantity": quantity,
        "unit_price": price,
        "total_price": price * quantity,
    })

    return json.dumps({
        "platform": "swiggy",
        "message": f"Added {quantity}x {item_key.title()} to cart",
        "cart_item_count": len(_cart["items"]),
    })


# ─────────────────────────────────────────────
#  TOOL 4 — swiggy_get_cart
#
#  Returns the full cart with itemized bill:
#  subtotal + delivery fee + taxes = total.
# ─────────────────────────────────────────────

@tool
def swiggy_get_cart() -> str:
    """
    Get the current Swiggy cart with a full bill breakdown.
    Returns subtotal, delivery fee, taxes, and total amount.
    Call this after adding all items to confirm the order value.
    """
    if not _cart["items"]:
        return json.dumps({"error": "Swiggy cart is empty"})

    subtotal = sum(item["total_price"] for item in _cart["items"])
    taxes    = round(subtotal * CONFIG["tax_rate"])
    total    = subtotal + CONFIG["delivery_fee"] + taxes

    return json.dumps({
        "platform": "swiggy",
        "restaurant": _cart["restaurant"],
        "items": _cart["items"],
        "bill": {
            "subtotal":     subtotal,
            "delivery_fee": CONFIG["delivery_fee"],
            "taxes":        taxes,
            "total":        total,
        },
        "estimated_time": "35-40 mins",
    })


# All Swiggy tools in one list — imported by the search node
SWIGGY_TOOLS = [
    swiggy_search_restaurants,
    swiggy_get_menu,
    swiggy_add_to_cart,
    swiggy_get_cart,
]
