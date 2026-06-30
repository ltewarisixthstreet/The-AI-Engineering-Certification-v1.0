import secrets

from mcp.server.auth.middleware.auth_context import get_access_token

from .server import mcp, oauth_provider

ORIGIN_ZIP = "10001"

_USPS_RATES: dict[str, dict] = {
    "USPS Ground Advantage": {
        "base": [4.50, 5.10, 5.50, 6.00, 6.75, 7.50, 8.25, 9.00],
        "per_oz_over_16": 0.18,
        "delivery_days": (2, 5),
    },
    "Priority Mail": {
        "base": [8.50, 9.00, 9.75, 10.50, 11.75, 13.25, 15.00, 17.25],
        "per_oz_over_16": 0.30,
        "delivery_days": (1, 3),
    },
    "Priority Mail Express": {
        "base": [28.75, 30.45, 32.95, 37.90, 42.10, 46.20, 50.35, 54.75],
        "per_oz_over_16": 0.50,
        "delivery_days": (1, 2),
    },
}


def _usps_zone(origin_zip: str, dest_zip: str) -> int:
    """Estimate USPS zone (1-8) from the numeric distance between ZIP prefixes."""
    try:
        diff = abs(int(origin_zip[:3]) - int(dest_zip[:3]))
    except ValueError:
        return 4
    if diff == 0:
        return 1
    elif diff <= 20:
        return 2
    elif diff <= 60:
        return 3
    elif diff <= 120:
        return 4
    elif diff <= 200:
        return 5
    elif diff <= 400:
        return 6
    elif diff <= 600:
        return 7
    else:
        return 8


async def _get_username() -> str:
    token = get_access_token()
    if token is None:
        raise ValueError("Not authenticated")
    username = await oauth_provider.get_username_for_token(token.token)
    if username is None:
        raise ValueError("User not found for token")
    return username


@mcp.tool()
async def list_products(category: str | None = None) -> list[dict]:
    """Browse the cat shop catalog. Returns each product's id, name, description, price, category,
    weight_oz, length_in, width_in, and height_in. Use the returned product id with
    estimate_shipping to get accurate shipping costs based on real weight and dimensions.
    Optionally filter by category: toys, beds, food, or furniture."""
    db = await oauth_provider._get_db()
    if category:
        cursor = await db.execute(
            "SELECT id, name, description, price, category, weight_oz, length_in, width_in, height_in FROM products WHERE category = ?",
            (category,),
        )
    else:
        cursor = await db.execute(
            "SELECT id, name, description, price, category, weight_oz, length_in, width_in, height_in FROM products"
        )
    rows = await cursor.fetchall()
    return [
        {
            "id": r[0], "name": r[1], "description": r[2], "price": r[3], "category": r[4],
            "weight_oz": r[5], "length_in": r[6], "width_in": r[7], "height_in": r[8],
        }
        for r in rows
    ]


@mcp.tool()
async def get_product(product_id: int) -> dict:
    """Get full details of a single product by its ID, including weight_oz, length_in, width_in,
    and height_in. Pass the returned id to estimate_shipping to calculate accurate USPS shipping
    costs using the product's actual weight and dimensions."""
    db = await oauth_provider._get_db()
    cursor = await db.execute(
        "SELECT id, name, description, price, category, weight_oz, length_in, width_in, height_in FROM products WHERE id = ?",
        (product_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return {"error": "Product not found"}
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "price": row[3],
        "category": row[4],
        "weight_oz": row[5],
        "length_in": row[6],
        "width_in": row[7],
        "height_in": row[8],
    }


@mcp.tool()
async def add_to_cart(product_id: int, quantity: int = 1) -> dict:
    """Add a product to your shopping cart. If already in cart, quantity is increased."""
    username = await _get_username()
    db = await oauth_provider._get_db()

    cursor = await db.execute("SELECT name FROM products WHERE id = ?", (product_id,))
    product = await cursor.fetchone()
    if product is None:
        return {"error": "Product not found"}

    await db.execute(
        """INSERT INTO cart_items (username, product_id, quantity)
           VALUES (?, ?, ?)
           ON CONFLICT(username, product_id)
           DO UPDATE SET quantity = quantity + excluded.quantity""",
        (username, product_id, quantity),
    )
    await db.commit()
    return {"success": True, "message": f"Added {quantity}x {product[0]} to your cart"}


@mcp.tool()
async def view_cart() -> dict:
    """View everything in your shopping cart with quantities and totals."""
    username = await _get_username()
    db = await oauth_provider._get_db()
    cursor = await db.execute(
        """SELECT p.id, p.name, p.price, c.quantity
           FROM cart_items c JOIN products p ON c.product_id = p.id
           WHERE c.username = ?""",
        (username,),
    )
    rows = await cursor.fetchall()
    items = [
        {
            "product_id": r[0],
            "name": r[1],
            "price": r[2],
            "quantity": r[3],
            "subtotal": round(r[2] * r[3], 2),
        }
        for r in rows
    ]
    total = round(sum(i["subtotal"] for i in items), 2)
    return {"items": items, "total": total, "item_count": len(items)}


@mcp.tool()
async def remove_from_cart(product_id: int) -> dict:
    """Remove a product from your shopping cart."""
    username = await _get_username()
    db = await oauth_provider._get_db()
    cursor = await db.execute(
        "DELETE FROM cart_items WHERE username = ? AND product_id = ?",
        (username, product_id),
    )
    await db.commit()
    if cursor.rowcount == 0:
        return {"error": "Item not in cart"}
    return {"success": True, "message": "Item removed from cart"}


@mcp.tool()
async def checkout() -> dict:
    """Complete your purchase. Shows order summary and clears the cart."""
    username = await _get_username()
    db = await oauth_provider._get_db()

    cart = await view_cart()
    if not cart["items"]:
        return {"error": "Your cart is empty"}

    await db.execute("DELETE FROM cart_items WHERE username = ?", (username,))
    await db.commit()

    order_id = secrets.token_hex(8).upper()
    return {
        "order_id": order_id,
        "status": "confirmed",
        "items": cart["items"],
        "total": cart["total"],
        "message": f"Order {order_id} confirmed! Thanks {username}, your cats will love their new goodies!",
    }


@mcp.tool()
async def estimate_shipping(
    destination_zip: str,
    product_id: int | None = None,
    weight_oz: float | None = None,
) -> dict:
    """Estimate USPS shipping cost and delivery time to a destination ZIP code.

    When the user asks about shipping cost for a specific product, always pass product_id
    (the id field from list_products or get_product) so real weight and dimensions are used.
    The billable weight is the greater of actual weight and USPS dimensional weight
    (length x width x height / 166, converted to ounces).

    Returns three USPS service options with cost and estimated delivery time:
    - USPS Ground Advantage (economy, 2-5 business days)
    - Priority Mail (standard, 1-3 business days)
    - Priority Mail Express (fastest, 1-2 business days)

    Args:
        destination_zip: 5-digit US destination ZIP code.
        product_id: Product id from list_products or get_product. Use this for accurate
            shipping based on the product's real weight and box dimensions.
        weight_oz: Manual weight override in ounces. Only use when no product_id is available.
            Defaults to 8 oz if neither product_id nor weight_oz is supplied.
    """
    if not destination_zip.isdigit() or len(destination_zip) != 5:
        return {"error": "destination_zip must be a 5-digit US ZIP code"}

    product_info: dict | None = None
    if product_id is not None:
        db = await oauth_provider._get_db()
        cursor = await db.execute(
            "SELECT id, name, weight_oz, length_in, width_in, height_in FROM products WHERE id = ?",
            (product_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return {"error": f"Product {product_id} not found"}
        product_info = {
            "id": row[0], "name": row[1],
            "weight_oz": row[2], "length_in": row[3], "width_in": row[4], "height_in": row[5],
        }
        actual_weight = product_info["weight_oz"]
        dim_weight_oz = (product_info["length_in"] * product_info["width_in"] * product_info["height_in"]) / 166.0 * 16
        billable_weight = max(actual_weight, dim_weight_oz)
    else:
        billable_weight = weight_oz if weight_oz is not None else 8.0
        dim_weight_oz = None

    if billable_weight <= 0:
        return {"error": "weight_oz must be greater than 0"}

    zone = _usps_zone(ORIGIN_ZIP, destination_zip)
    zone_idx = zone - 1

    options = []
    for service, info in _USPS_RATES.items():
        base_cost = info["base"][zone_idx]
        extra_oz = max(0.0, billable_weight - 16.0)
        total_cost = round(base_cost + extra_oz * info["per_oz_over_16"], 2)
        low, high = info["delivery_days"]
        delivery = f"{low} business day" if low == high else f"{low}\u2013{high} business days"
        options.append({
            "service": service,
            "estimated_cost_usd": total_cost,
            "estimated_delivery": delivery,
        })

    result: dict = {
        "origin_zip": ORIGIN_ZIP,
        "destination_zip": destination_zip,
        "usps_zone": zone,
        "billable_weight_oz": round(billable_weight, 2),
        "shipping_options": options,
    }
    if product_info:
        result["product"] = product_info["name"]
        result["actual_weight_oz"] = product_info["weight_oz"]
        result["dimensions_in"] = {
            "length": product_info["length_in"],
            "width": product_info["width_in"],
            "height": product_info["height_in"],
        }
        result["dimensional_weight_oz"] = round(dim_weight_oz, 2)
    return result


@mcp.tool()
async def estimate_shipping_bulk(
    destination_zip: str,
    items: list[dict],
) -> dict:
    """Estimate USPS shipping costs for multiple products in a single shipment.

    Use this when the user wants shipping costs for a cart or a list of products.
    Each item in the list must have a product_id and optionally a quantity (defaults to 1).
    Returns a per-item breakdown table and combined shipping options for the full order.

    The total billable weight is the sum of each product's actual weight multiplied by quantity.
    USPS zone is determined from the origin ZIP (10001) and destination ZIP.

    Returns three USPS service options with combined cost and estimated delivery time:
    - USPS Ground Advantage (economy, 2-5 business days)
    - Priority Mail (standard, 1-3 business days)
    - Priority Mail Express (fastest, 1-2 business days)

    Args:
        destination_zip: 5-digit US destination ZIP code.
        items: List of objects with keys:
            - product_id (int, required): Product id from list_products or get_product.
            - quantity (int, optional): Number of units. Defaults to 1.

    Example:
        items=[{"product_id": 1, "quantity": 2}, {"product_id": 4, "quantity": 1}]
    """
    if not destination_zip.isdigit() or len(destination_zip) != 5:
        return {"error": "destination_zip must be a 5-digit US ZIP code"}
    if not items:
        return {"error": "items list must not be empty"}

    db = await oauth_provider._get_db()
    rows_table = []
    total_weight_oz = 0.0
    errors = []

    for entry in items:
        product_id = entry.get("product_id")
        quantity = int(entry.get("quantity", 1))
        if product_id is None:
            errors.append(f"Missing product_id in entry: {entry}")
            continue
        cursor = await db.execute(
            "SELECT id, name, price, weight_oz, length_in, width_in, height_in FROM products WHERE id = ?",
            (int(product_id),),
        )
        row = await cursor.fetchone()
        if row is None:
            errors.append(f"Product {product_id} not found")
            continue
        line_weight = row[3] * quantity
        total_weight_oz += line_weight
        rows_table.append({
            "product_id": row[0],
            "name": row[1],
            "unit_price": row[2],
            "quantity": quantity,
            "subtotal": round(row[2] * quantity, 2),
            "weight_oz": row[3],
            "line_weight_oz": round(line_weight, 2),
            "dimensions_in": {"length": row[4], "width": row[5], "height": row[6]},
        })

    if not rows_table:
        return {"error": "No valid products found", "details": errors}

    zone = _usps_zone(ORIGIN_ZIP, destination_zip)
    zone_idx = zone - 1
    order_total = round(sum(r["subtotal"] for r in rows_table), 2)

    shipping_options = []
    for service, info in _USPS_RATES.items():
        base_cost = info["base"][zone_idx]
        extra_oz = max(0.0, total_weight_oz - 16.0)
        total_cost = round(base_cost + extra_oz * info["per_oz_over_16"], 2)
        low, high = info["delivery_days"]
        delivery = f"{low} business day" if low == high else f"{low}\u2013{high} business days"
        shipping_options.append({
            "service": service,
            "estimated_cost_usd": total_cost,
            "estimated_delivery": delivery,
        })

    result: dict = {
        "origin_zip": ORIGIN_ZIP,
        "destination_zip": destination_zip,
        "usps_zone": zone,
        "items": rows_table,
        "order_total_usd": order_total,
        "total_weight_oz": round(total_weight_oz, 2),
        "shipping_options": shipping_options,
    }
    if errors:
        result["warnings"] = errors
    return result
