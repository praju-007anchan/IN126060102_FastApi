from fastapi import FastAPI, Query, Response, status
from pydantic import BaseModel, Field

app = FastAPI()

# ══ PYDANTIC MODELS ═══════════════════════════════════════════════

class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=100)
    delivery_address: str = Field(..., min_length=10)

class NewProduct(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    in_stock: bool = True

class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)

# ══ DATA ══════════════════════════════════════════════════════════

products = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True},
    {'id': 2, 'name': 'Notebook', 'price': 99, 'category': 'Stationery', 'in_stock': True},
    {'id': 3, 'name': 'USB Hub', 'price': 799, 'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set', 'price': 49, 'category': 'Stationery', 'in_stock': True},
]

orders = []
order_counter = 1
cart = []

# ══ HELPERS ═══════════════════════════════════════════════════════

def find_product(product_id: int):
    for p in products:
        if p['id'] == product_id:
            return p
    return None

def calculate_total(product: dict, quantity: int) -> int:
    return product['price'] * quantity

# ══ BASIC ROUTES ══════════════════════════════════════════════════

@app.get('/')
def home():
    return {'message': 'Welcome to our E-commerce API'}

@app.get('/products')
def get_all_products():
    return {'products': products, 'total': len(products)}

# ══ SEARCH PRODUCTS ═══════════════════════════════════════════════

@app.get('/products/search')
def search_products(keyword: str = Query(...)):
    results = [p for p in products if keyword.lower() in p['name'].lower()]
    if not results:
        return {'message': f'No products found for: {keyword}'}
    return {'keyword': keyword, 'total_found': len(results), 'products': results}

# ══ SORT PRODUCTS ═════════════════════════════════════════════════

@app.get('/products/sort')
def sort_products(sort_by: str = Query('price'), order: str = Query('asc')):
    if sort_by not in ['price', 'name']:
        return {'error': "sort_by must be 'price' or 'name'"}

    sorted_products = sorted(
        products,
        key=lambda p: p[sort_by],
        reverse=(order == 'desc')
    )

    return {'sort_by': sort_by, 'order': order, 'products': sorted_products}

# ══ PAGINATION ════════════════════════════════════════════════════

@app.get('/products/page')
def paginate_products(page: int = Query(1, ge=1), limit: int = Query(2, ge=1)):
    start = (page - 1) * limit
    return {
        'page': page,
        'limit': limit,
        'total': len(products),
        'total_pages': -(-len(products) // limit),
        'products': products[start:start + limit]
    }

# ══ SEARCH ORDERS ═════════════════════════════════════════════════

@app.get('/orders/search')
def search_orders(customer_name: str = Query(...)):
    results = [o for o in orders if customer_name.lower() in o['customer_name'].lower()]
    if not results:
        return {'message': f'No orders found for: {customer_name}'}
    return {'customer_name': customer_name, 'total_found': len(results), 'orders': results}

# ══ SORT BY CATEGORY ══════════════════════════════════════════════

@app.get('/products/sort-by-category')
def sort_by_category():
    result = sorted(products, key=lambda p: (p['category'], p['price']))
    return {'products': result, 'total': len(result)}

# ══ COMBINED (SEARCH + SORT + PAGINATION) ═════════════════════════

@app.get('/products/browse')
def browse_products(
    keyword: str = Query(None),
    sort_by: str = Query('price'),
    order: str = Query('asc'),
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1, le=20),
):
    result = products

    if keyword:
        result = [p for p in result if keyword.lower() in p['name'].lower()]

    if sort_by not in ['price', 'name']:
        return {'error': "sort_by must be 'price' or 'name'"}

    result = sorted(
        result,
        key=lambda p: p[sort_by],
        reverse=(order == 'desc')
    )

    total = len(result)
    start = (page - 1) * limit
    paged = result[start:start + limit]

    return {
        'keyword': keyword,
        'sort_by': sort_by,
        'order': order,
        'page': page,
        'limit': limit,
        'total_found': total,
        'total_pages': -(-total // limit),
        'products': paged,
    }

# ══ PLACE ORDER ═══════════════════════════════════════════════════

@app.post('/orders')
def place_order(order_data: OrderRequest):
    global order_counter

    product = find_product(order_data.product_id)

    if not product:
        return {'error': 'Product not found'}

    if not product['in_stock']:
        return {'error': f"{product['name']} is out of stock"}

    total = calculate_total(product, order_data.quantity)

    order = {
        'order_id': order_counter,
        'customer_name': order_data.customer_name,
        'product': product['name'],
        'quantity': order_data.quantity,
        'delivery_address': order_data.delivery_address,
        'total_price': total,
        'status': 'confirmed',
    }

    orders.append(order)
    order_counter += 1

    return {'message': 'Order placed successfully', 'order': order}

@app.get('/orders')
def get_orders():
    return {'orders': orders, 'total_orders': len(orders)}

# ══ ORDERS PAGINATION ═════════════════════════════════════════════

@app.get('/orders/page')
def get_orders_paged(page: int = Query(1, ge=1), limit: int = Query(3, ge=1, le=20)):
    start = (page - 1) * limit
    return {
        'page': page,
        'limit': limit,
        'total': len(orders),
        'total_pages': -(-len(orders) // limit),
        'orders': orders[start:start + limit],
    }

# ══ GET PRODUCT BY ID (KEEP LAST) ═════════════════════════════════

@app.get('/products/{product_id}')
def get_product(product_id: int):
    product = find_product(product_id)
    if not product:
        return {'error': 'Product not found'}
    return {'product': product}
