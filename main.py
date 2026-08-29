from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
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
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "insha_secure_token_123")

SYSTEM_PROMPT = """
You are the smart AI sales assistant for 'Insha Bangles & Purses', located in Dubagga, Lucknow.
Shop highlights:
- Handcrafted bridal velvet choodas, Kundan bangles, designer clutches, party potlis, and comfortable underclothes.
- Standard bangle sizes: 2.4, 2.6, 2.8.
- Retail and wholesale rates available (with MOQ).
- Offline shop in Dubagga, Lucknow (open daily 10 AM - 10 PM).
Help customers with stock, size selection, pricing, and bulk wholesale inquiries politely in English or Hindi.
"""

catalog_db = [
    {
        "id": "1",
        "title": "Royal Velvet Bridal Chooda Set",
        "description": "Handcrafted traditional bridal chooda with intricate stone work & velvet finish.",
        "category_name": "Bridal",
        "retail_price": 1250,
        "wholesale_price": 650,
        "min_wholesale_qty": 6,
        "image_urls": ["https://images.unsplash.com/photo-1611591475152-4735eac870c2"],
        "stock_count": 50
    },
    {
        "id": "2",
        "title": "Maharani Kundan Dulhan Bangles",
        "description": "Heavy Kundan and pearl studded bangle set for grand weddings.",
        "category_name": "Bridal",
        "retail_price": 1450,
        "wholesale_price": 780,
        "min_wholesale_qty": 6,
        "image_urls": ["https://images.unsplash.com/photo-1535632066927-ab7c9ab60908"],
        "stock_count": 40
    },
    {
        "id": "3",
        "title": "Velvet Festive Bangle Set (Pack of 24)",
        "description": "Rich multicolor festive velvet bangles with gold zari edging.",
        "category_name": "Festive",
        "retail_price": 450,
        "wholesale_price": 220,
        "min_wholesale_qty": 12,
        "image_urls": ["https://images.unsplash.com/photo-1600003014755-ba31aa59c4b6"],
        "stock_count": 100
    },
    {
        "id": "4",
        "title": "Zari Embroidered Party Clutch",
        "description": "Premium golden zari stone clutch with detachable metal chain strap.",
        "category_name": "Purses & Clutches",
        "retail_price": 890,
        "wholesale_price": 480,
        "min_wholesale_qty": 10,
        "image_urls": ["https://images.unsplash.com/photo-1566150905458-1bf1fc113f0d"],
        "stock_count": 30
    },
    {
        "id": "5",
        "title": "Trending Matte Silk Everyday Bangles",
        "description": "Smooth textured durable daily wear bangles in 12 festive shades.",
        "category_name": "Best Seller",
        "retail_price": 350,
        "wholesale_price": 180,
        "min_wholesale_qty": 20,
        "image_urls": ["https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f"],
        "stock_count": 150
    },
    {
        "id": "6",
        "title": "Premium Cotton Everyday Innerwear Set",
        "description": "Soft stretch breathable cotton innerwear essentials for all-day comfort.",
        "category_name": "Underclothes",
        "retail_price": 399,
        "wholesale_price": 190,
        "min_wholesale_qty": 15,
        "image_urls": ["https://images.unsplash.com/photo-1583743814966-8936f5b7be1a"],
        "stock_count": 80
    }
]

class ProductCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    category_name: str
    image_urls: List[str] = []
    retail_price: float
    wholesale_price: Optional[float] = None
    min_wholesale_qty: Optional[int] = 10
    stock_count: Optional[int] = 100

class ChatRequest(BaseModel):
    message: str

def generate_ai_reply(prompt_text: str) -> str:
    if not GEMINI_API_KEY:
        return "Namaste! Welcome to Insha Bangles & Purses Lucknow. How may we assist you with sizes, collections, or wholesale orders today?"
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(f"{SYSTEM_PROMPT}\n\nCustomer Inquiry: {prompt_text}\nAssistant Response:")
        return response.text.strip()
    except Exception:
        return "Namaste! Welcome to Insha Bangles & Purses Lucknow. Please let us know your requirements, and our team will get back to you shortly."

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

@app.post("/chat")
def chat_with_assistant(req: ChatRequest):
    return {"reply": generate_ai_reply(req.message)}

# Automated WhatsApp Cloud API Webhook Handler
@app.get("/webhook")
def verify_webhook(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@app.post("/webhook")
async def handle_whatsapp_incoming(request: Request):
    data = await request.json()
    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            msg = messages[0]
            from_number = msg.get("from")
            text_body = msg.get("text", {}).get("body", "")

            if text_body and WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID:
                ai_answer = generate_ai_reply(text_body)
                url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
                headers = {
                    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "to": from_number,
                    "type": "text",
                    "text": {"body": ai_answer}
                }
                requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"Webhook processing error: {e}")

    return {"status": "success"}
