from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os

app = FastAPI(title="Insha Bangles & Purses API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

SYSTEM_PROMPT = """
You are the official smart shopping assistant for 'Insha Bangles & Purses', a bridal and festive boutique located in Dubagga, Lucknow.
1. Greet customers warmly in English or Hindi (Hinglish).
2. Answer questions about traditional bridal choodas, handcrafted velvet bangles, stone clutches, party potlis, and comfortable underclothes.
3. Help with sizing inquiries (bangle standard sizes: 2.4, 2.6, 2.8, etc.), colors (Maroon, Royal Red, Emerald Green, Golden Zari, Pastel Pink), and wholesale lot terms (MOQ).
4. Direct users to tap the green "Check Availability & Colors" button on any item to connect directly with the shop team on WhatsApp (+91 99036 10501).
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

@app.get("/")
def serve_home():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "Insha Bangles & Purses API is Live"}

@app.get("/products")
def get_products():
    return {"products": catalog_db}

@app.post("/products")
def add_product(item: ProductCreate):
    new_product = item.model_dump() if hasattr(item, "model_dump") else item.dict()
    new_product["id"] = str(len(catalog_db) + 1)
    catalog_db.insert(0, new_product)
    return {"success": True, "product": new_product}

@app.post("/chat")
def chat_with_assistant(req: ChatRequest):
    if not GEMINI_API_KEY:
        return {"reply": "Namaste! 🙏 Welcome to Insha Bangles & Purses. Please feel free to check our collections or reach out via WhatsApp at +91 99036 10501 for stock and color availability!"}
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        full_prompt = f"{SYSTEM_PROMPT}\n\nCustomer: {req.message}\nAssistant:"
        response = model.generate_content(full_prompt)
        return {"reply": response.text.strip()}
    except Exception:
        return {"reply": "Namaste! 🙏 For immediate color and size confirmation, please tap 'Check Availability & Colors' on any item to chat directly on WhatsApp."}
