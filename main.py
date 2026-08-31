from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Any
import os
import requests

app = FastAPI(title="Insha Bangles & Purses API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
STORE_URL = os.environ.get("STORE_URL", "https://insha-store.onrender.com")

# TELEGRAM INSTANT NOTIFICATION CONFIG
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Orders Database
orders_db = []

catalog_db = [
    {
        "id": "1",
        "title": "Royal Velvet Bridal Chooda Set",
        "description": "Handcrafted traditional bridal chooda with intricate stone work & velvet finish.",
        "category_name": "Bridal",
        "categories": ["Bridal", "Festive"],
        "original_price": 1600,
        "retail_price": 1250,
        "wholesale_price": 650,
        "min_wholesale_qty": 6,
        "discount_pct": 22,
        "image_urls": ["https://images.unsplash.com/photo-1611591475152-4735eac870c2"],
        "stock_count": 50
    },
    {
        "id": "2",
        "title": "Maharani Kundan Dulhan Bangles",
        "description": "Heavy Kundan and pearl studded bangle set for grand weddings.",
        "category_name": "Bridal",
        "categories": ["Bridal", "Best Seller"],
        "original_price": 1850,
        "retail_price": 1450,
        "wholesale_price": 780,
        "min_wholesale_qty": 6,
        "discount_pct": 21,
        "image_urls": ["https://images.unsplash.com/photo-1535632066927-ab7c9ab60908"],
        "stock_count": 40
    },
    {
        "id": "3",
        "title": "Red Metal Chudi & Velvet Set (Pack of 24)",
        "description": "Rich red daily wear metal chudis with gold shimmer finish.",
        "category_name": "Daily Wear",
        "categories": ["Daily Wear", "Festive"],
        "original_price": 650,
        "retail_price": 450,
        "wholesale_price": 220,
        "min_wholesale_qty": 12,
        "discount_pct": 30,
        "image_urls": ["https://images.unsplash.com/photo-1600003014755-ba31aa59c4b6"],
        "stock_count": 100
    },
    {
        "id": "4",
        "title": "Zari Embroidered Bridal Party Clutch",
        "description": "Premium golden zari stone clutch with detachable metal chain strap.",
        "category_name": "Purses & Clutches",
        "categories": ["Purses & Clutches", "Bridal"],
        "original_price": 1200,
        "retail_price": 890,
        "wholesale_price": 480,
        "min_wholesale_qty": 10,
        "discount_pct": 25,
        "image_urls": ["https://images.unsplash.com/photo-1566150905458-1bf1fc113f0d"],
        "stock_count": 30
    },
    {
        "id": "5",
        "title": "Trending Matte Silk Everyday Bangles",
        "description": "Smooth textured durable daily wear bangles in 12 festive shades.",
        "category_name": "Daily Wear",
        "categories": ["Daily Wear", "Best Seller"],
        "original_price": 500,
        "retail_price": 350,
        "wholesale_price": 180,
        "min_wholesale_qty": 20,
        "discount_pct": 30,
        "image_urls": ["https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f"],
        "stock_count": 150
    },
    {
        "id": "6",
        "title": "Premium Cotton Everyday Innerwear Set",
        "description": "Soft stretch breathable cotton innerwear essentials for all-day comfort.",
        "category_name": "Underclothes",
        "categories": ["Underclothes"],
        "original_price": 599,
        "retail_price": 399,
        "wholesale_price": 190,
        "min_wholesale_qty": 15,
        "discount_pct": 33,
        "image_urls": ["https://images.unsplash.com/photo-1583743814966-8936f5b7be1a"],
        "stock_count": 80
    }
]

class ProductCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    category_name: Optional[str] = ""
    categories: Optional[List[str]] = []
    image_urls: List[str] = []
    original_price: Optional[float] = None
    retail_price: float
    wholesale_price: Optional[float] = None
    min_wholesale_qty: Optional[int] = 10
    discount_pct: Optional[int] = 0
    stock_count: Optional[int] = 100

class OrderCreate(BaseModel):
    order_id: Optional[str] = ""
    customer_name: str
    customer_phone: str
    delivery_address: str
    city_pincode: str
    items: List[Any]
    subtotal: float
    discount: float
    final_total: float
    coupon_code: Optional[str] = ""
    status: Optional[str] = "CONFIRMED"
    timestamp: Optional[str] = ""

def send_instant_telegram_notification(order: dict):
    token = TELEGRAM_BOT_TOKEN
    chat_id = TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return

    items_text = ""
    for item in order.get("items", []):
        title = item.get("title", "Item")
        qty = item.get("qty", 1)
        price = item.get("price", 0)
        order_type = item.get("orderType", "retail").upper()
        items_text += f"• {title} ({order_type}) x{qty} = Rs. {price * qty}\n"

    msg = (
        f"🚨 *NEW ORDER RECEIVED!* 🚨\n\n"
        f"🆔 *Order ID:* `{order.get('order_id')}`\n"
        f"👤 *Customer:* {order.get('customer_name')}\n"
        f"📞 *Phone:* {order.get('customer_phone')}\n"
        f"📍 *Address:* {order.get('delivery_address')}, {order.get('city_pincode')}\n\n"
        f"🛍️ *Items Ordered:*\n{items_text}\n"
        f"💰 *Total Amount:* Rs. {order.get('final_total')}\n"
        f"⏰ *Time:* {order.get('timestamp')}"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=8)
    except Exception as e:
        print(f"Telegram dispatch error: {e}")

@app.get("/")
def serve_home():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"status": "Insha Bangles & Purses API Online"}

@app.get("/products")
def get_products():
    return {"products": catalog_db}

@app.post("/products")
def add_product(item: ProductCreate):
    new_product = item.model_dump() if hasattr(item, "model_dump") else item.dict()
    new_product["id"] = str(len(catalog_db) + 1)
    catalog_db.insert(0, new_product)
    return {"success": True, "product": new_product}

@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    global catalog_db
    catalog_db = [p for p in catalog_db if str(p.get("id")) != str(product_id)]
    return {"success": True, "message": f"Product {product_id} deleted"}

@app.get("/orders")
def get_orders():
    return {"orders": orders_db}

@app.post("/orders")
def create_order(order: OrderCreate, background_tasks: BackgroundTasks):
    order_data = order.model_dump() if hasattr(order, "model_dump") else order.dict()
    if not order_data.get("order_id"):
        order_data["order_id"] = f"IB-{len(orders_db) + 1001}"
    orders_db.insert(0, order_data)
    
    # Send instant push notification to Telegram
    background_tasks.add_task(send_instant_telegram_notification, order_data)
    return {"success": True, "order": order_data}

@app.delete("/orders/{order_id}")
def delete_single_order(order_id: str):
    global orders_db
    orders_db = [o for o in orders_db if str(o.get("order_id")) != str(order_id)]
    return {"success": True, "message": f"Order {order_id} deleted"}

@app.delete("/orders")
def clear_all_orders():
    global orders_db
    orders_db = []
    return {"success": True, "message": "All orders cleared"}

@app.api_route("/chat", methods=["GET", "POST"])
async def chat_with_assistant(request: Request):
    msg_text = ""
    try:
        data = await request.json()
        if isinstance(data, dict):
            if "message" in data:
                msg_text = str(data["message"])
            elif "query" in data and isinstance(data["query"], dict):
                msg_text = str(data["query"].get("message", ""))
            elif "text" in data:
                msg_text = str(data["text"])
    except Exception:
        pass

    if not msg_text:
        msg_text = request.query_params.get("message") or request.query_params.get("query") or ""

    default_msg = "Namaste! Welcome to Insha Bangles & Purses Lucknow. How may we assist you?"
    return {"reply": default_msg, "replies": [{"message": default_msg}]}
