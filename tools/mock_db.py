# ─────────────────────────────────────────────
#  mock_db.py — shared restaurant + menu data
#
#  Both Swiggy and Zomato tools import from here.
#  Prices are base prices — each platform applies
#  its own modifier on top (see platform config below).
# ─────────────────────────────────────────────

RESTAURANTS = {
    "behrouz biryani": {
        "id": "rest_001",
        "name": "Behrouz Biryani",
        "rating": 4.5,
        "cuisine": "Mughlai",
        "menu": {
            "butter chicken":   {"id": "item_001", "price": 320},
            "chicken biryani":  {"id": "item_002", "price": 299},
            "dal makhani":      {"id": "item_003", "price": 199},
            "paneer tikka":     {"id": "item_004", "price": 249},
        }
    },
    "dominos": {
        "id": "rest_002",
        "name": "Domino's Pizza",
        "rating": 4.2,
        "cuisine": "Pizza",
        "menu": {
            "margherita pizza": {"id": "item_005", "price": 199},
            "pepperoni pizza":  {"id": "item_006", "price": 349},
            "garlic bread":     {"id": "item_007", "price": 99},
        }
    },
    "mcdonalds": {
        "id": "rest_003",
        "name": "McDonald's",
        "rating": 4.1,
        "cuisine": "Fast Food",
        "menu": {
            "mcaloo tikki":  {"id": "item_008", "price": 99},
            "mcchicken":     {"id": "item_009", "price": 149},
            "fries":         {"id": "item_010", "price": 89},
            "mcflurry":      {"id": "item_011", "price": 119},
        }
    },
    "kfc": {
        "id": "rest_004",
        "name": "KFC",
        "rating": 4.0,
        "cuisine": "Fast Food",
        "menu": {
            "chicken bucket":      {"id": "item_012", "price": 599},
            "zinger burger":       {"id": "item_013", "price": 199},
            "hot wings":           {"id": "item_014", "price": 249},
            "coleslaw":            {"id": "item_015", "price": 79},
        }
    },
}

# ─────────────────────────────────────────────
#  Platform config — what makes Swiggy vs Zomato different
#
#  price_factor : Zomato charges 5% more per item
#  delivery_fee : Swiggy charges more for delivery
#  tax_rate     : same for both (5% GST)
# ─────────────────────────────────────────────

PLATFORM_CONFIG = {
    "swiggy": {"price_factor": 1.0,  "delivery_fee": 49, "tax_rate": 0.05},
    "zomato": {"price_factor": 1.05, "delivery_fee": 29, "tax_rate": 0.05},
}


def fuzzy_match_restaurant(query: str) -> dict | None:
    """
    Match a user query to a restaurant in the DB.
    e.g. "Behrouz" or "behrouz biryani" → RESTAURANTS["behrouz biryani"]
    Returns None if no match found.
    """
    query = query.lower().strip()
    for key, restaurant in RESTAURANTS.items():
        if query in key or key in query:
            return restaurant
    return None


def fuzzy_match_item(menu: dict, query: str) -> tuple[str, dict] | None:
    """
    Match a user query to a menu item.
    e.g. "Butter Chicken" → ("butter chicken", {"id": ..., "price": ...})
    Returns None if no match found.
    """
    query = query.lower().strip()
    for item_name, item_data in menu.items():
        if query in item_name or item_name in query:
            return item_name, item_data
    return None
