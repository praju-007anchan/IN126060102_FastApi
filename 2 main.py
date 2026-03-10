from fastapi import FastAPI
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional
from typing import List
app = FastAPI()

# Products List
products = [
    {"id": 1, "name": "Laptop", "price": 55000, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Wireless Mouse", "price": 799, "category": "Electronics", "in_stock": True},
    {"id": 3, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": False},

    # Task 1 – Added Products
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False}
]

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)


class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem] = Field(..., min_items=1)

orders = []
@app.post("/orders")
def place_order(product_id: int, quantity: int):

    order_id = len(orders) + 1

    new_order = {
        "order_id": order_id,
        "product_id": product_id,
        "quantity": quantity,
        "status": "pending"
    }

    orders.append(new_order)

    return {
        "message": "Order placed successfully",
        "order": new_order
    }


feedback = []
class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

# -------------------------------------------------------
# Task 1 - Show All Products
# -------------------------------------------------------
@app.get("/products")
def get_products():
    return {
        "products": products,
        "total": len(products)
    }


# -------------------------------------------------------
# Task 2 - Filter by Category
# -------------------------------------------------------
@app.get("/products/category/{category_name}")
def get_by_category(category_name: str):
    result = [p for p in products if p["category"] == category_name]

    if not result:
        return {"error": "No products found in this category"}

    return {
        "category": category_name,
        "products": result,
        "total": len(result)
    }


# -------------------------------------------------------
# Task 3 - Show Only In Stock Products
# -------------------------------------------------------
@app.get("/products/instock")
def get_instock():
    available = [p for p in products if p["in_stock"] == True]

    return {
        "in_stock_products": available,
        "count": len(available)
    }


# -------------------------------------------------------
# Task 4 - Store Summary
# -------------------------------------------------------
@app.get("/store/summary")
def store_summary():

    in_stock_count = len([p for p in products if p["in_stock"]])
    out_stock_count = len(products) - in_stock_count
    categories = list(set([p["category"] for p in products]))

    return {
        "store_name": "My E-commerce Store",
        "total_products": len(products),
        "in_stock": in_stock_count,
        "out_of_stock": out_stock_count,
        "categories": categories
    }


# -------------------------------------------------------
# Task 5 - Search Products
# -------------------------------------------------------
@app.get("/products/search/{keyword}")
def search_products(keyword: str):

    results = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]

    if not results:
        return {"message": "No products matched your search"}

    return {
        "keyword": keyword,
        "results": results,
        "total_matches": len(results)
    }

# -------------------------------------------------------
# Task 6 - Filter Products by Price Range
# -------------------------------------------------------
@app.get("/products/filter")
def filter_products(
    min_price: int = Query(None, description="Minimum price"),
    max_price: int = Query(None, description="Maximum price"),
    category: str = Query(None, description="Category")
):

    result = products

    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]

    if max_price:
        result = [p for p in result if p["price"] <= max_price]

    if min_price:
        result = [p for p in result if p["price"] >= min_price]

    return {
        "filtered_products": result,
        "count": len(result)
    }

# -------------------------------------------------------
# Task 7 - Get Product Price Only
# -------------------------------------------------------
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):

    for product in products:
        if product["id"] == product_id:
            return {
                "name": product["name"],
                "price": product["price"]
            }

    return {"error": "Product not found"}

# -------------------------------------------------------
# Task 8 - Submit Customer Feedback
# -------------------------------------------------------

@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):

    feedback.append(data.dict())

    return {
        "message": "Feedback submitted successfully",
        "feedback": data.dict(),
        "total_feedback": len(feedback)
    }

# -------------------------------------------------------
# Task 9 - Product Summary Dashboard
# -------------------------------------------------------
@app.get("/products/summary")
def product_summary():

    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]

    expensive = max(products, key=lambda p: p["price"])
    cheapest = min(products, key=lambda p: p["price"])

    categories = list(set(p["category"] for p in products))

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive": {
            "name": expensive["name"],
            "price": expensive["price"]
        },
        "cheapest": {
            "name": cheapest["name"],
            "price": cheapest["price"]
        },
        "categories": categories
    }

# -------------------------------------------------------
# Task 10 - Place Bulk Order
# -------------------------------------------------------
@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:

        product = next((p for p in products if p["id"] == item.product_id), None)

        if not product:
            failed.append({
                "product_id": item.product_id,
                "reason": "Product not found"
            })

        elif not product["in_stock"]:
            failed.append({
                "product_id": item.product_id,
                "reason": f"{product['name']} is out of stock"
            })

        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal

            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal
            })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }

# -------------------------------------------------------
# Bonus - Get Order by ID
# -------------------------------------------------------
@app.get("/orders/{order_id}")
def get_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}

    return {"error": "Order not found"}

# -------------------------------------------------------
# Bonus - Confirm Order
# -------------------------------------------------------
@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:

            order["status"] = "confirmed"

            return {
                "message": "Order confirmed",
                "order": order
            }

    return {"error": "Order not found"}    

# -------------------------------------------------------
# Bonus - Best Deal & Premium Pick
# -------------------------------------------------------
@app.get("/products/deals")
def get_deals():

    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])

    return {
        "best_deal": cheapest,
        "premium_pick": expensive
    }
