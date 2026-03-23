import json
from langchain_core.tools import tool
from tools.mock_db import RESTAURANTS, PLATFORM_CONFIG, fuzzy_match_restaurant, fuzzy_match_item

# ─────────────────────────────────────────────
#  In-memory cart for this session
# ─────────────────────────────────────────────

_cart: dict = {"restaurant": None, "items": []}

CONFIG = PLATFORM_CONFIG["zomato"]


@tool
def zomato_search_restaurants(query: str) -> str:
    """
    Search for restaurants on Zomato that serve the requested food.
    Returns a list of matching restaurants with their cuisine and rating.
    Use this before getting a menu or adding to cart.
    """
    results = []
    query_lower = query.lower()

    for key, restaurant in RESTAURANTS.items():
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
        return json.dumps({"error": f"No restaurants found for '{query}' on Zomato"})

    return json.dumps({"platform": "zomato", "results": results})


@tool
def zomato_get_menu(restaurant_name: str) -> str:
    """
    Get the full menu with prices for a restaurant on Zomato.
    Zomato prices are slightly higher than Swiggy but delivery fee is lower.
    Call zomato_search_restaurants first to confirm the restaurant exists.
    """
    restaurant = fuzzy_match_restaurant(restaurant_name)

    if not restaurant:
        return json.dumps({"error": f"Restaurant '{restaurant_name}' not found on Zomato"})

    # Zomato applies a 1.05x price factor
    menu_with_prices = {
        name: {
            "item_id": data["id"],
            "price": round(data["price"] * CONFIG["price_factor"])
        }
        for name, data in restaurant["menu"].items()
    }

    return json.dumps({
        "platform": "zomato",
        "restaurant": restaurant["name"],
        "menu": menu_with_prices,
    })


@tool
def zomato_add_to_cart(restaurant_name: str, item_name: str, quantity: int) -> str:
    """
    Add a menu item to the Zomato cart.
    Provide the restaurant name, item name, and quantity.
    Only items from one restaurant can be in the cart at a time.
    """
    global _cart

    restaurant = fuzzy_match_restaurant(restaurant_name)
    if not restaurant:
        return json.dumps({"error": f"Restaurant '{restaurant_name}' not found on Zomato"})

    if _cart["restaurant"] and _cart["restaurant"] != restaurant["name"]:
        return json.dumps({"error": "Cart already has items from a different restaurant. Clear cart first."})

    match = fuzzy_match_item(restaurant["menu"], item_name)
    if not match:
        return json.dumps({"error": f"Item '{item_name}' not found in {restaurant['name']} menu on Zomato"})

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
        "platform": "zomato",
        "message": f"Added {quantity}x {item_key.title()} to cart",
        "cart_item_count": len(_cart["items"]),
    })


@tool
def zomato_get_cart() -> str:
    """
    Get the current Zomato cart with a full bill breakdown.
    Returns subtotal, delivery fee, taxes, and total amount.
    Call this after adding all items to confirm the order value.
    """
    if not _cart["items"]:
        return json.dumps({"error": "Zomato cart is empty"})

    subtotal = sum(item["total_price"] for item in _cart["items"])
    taxes    = round(subtotal * CONFIG["tax_rate"])
    total    = subtotal + CONFIG["delivery_fee"] + taxes

    return json.dumps({
        "platform": "zomato",
        "restaurant": _cart["restaurant"],
        "items": _cart["items"],
        "bill": {
            "subtotal":     subtotal,
            "delivery_fee": CONFIG["delivery_fee"],
            "taxes":        taxes,
            "total":        total,
        },
        "estimated_time": "30-35 mins",
    })


# All Zomato tools in one list — imported by the search node
ZOMATO_TOOLS = [
    zomato_search_restaurants,
    zomato_get_menu,
    zomato_add_to_cart,
    zomato_get_cart,
]
