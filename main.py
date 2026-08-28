import os
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai
from google.genai import types

load_dotenv()

# Supabase Client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(title="Store Multilingual E-Commerce & AI Assistant")

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Serve Frontend App ---
@app.get("/")
def serve_store_app():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"status": "online", "message": "Store Backend Ready"}

# --- Data Models ---
class ProductCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category_name: str
    image_urls: List[str] = []
    retail_price: float
    wholesale_price: Optional[float] = None
    min_wholesale_qty: int = 1
    stock_count: int = 0

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[dict] = []
    preferred_language: Optional[str] = "English"

# --- Endpoints ---

@app.get("/manifest.json")
def get_manifest():
    return FileResponse("manifest.json", media_type="application/json")
@app.get("/products")
def get_products():
    response = supabase.table("products").select("*, categories(name)").eq("is_active", True).execute()
    return {"products": response.data}

@app.post("/products")
def create_product(product: ProductCreate):
    cat_res = supabase.table("categories").select("id").eq("name", product.category_name).execute()
    if not cat_res.data:
        raise HTTPException(status_code=400, detail="Category not found")
    
    category_id = cat_res.data[0]["id"]
    
    data = {
        "title": product.title,
        "description": product.description,
        "category_id": category_id,
        "image_urls": product.image_urls,
        "retail_price": product.retail_price,
        "wholesale_price": product.wholesale_price,
        "min_wholesale_qty": product.min_wholesale_qty,
        "stock_count": product.stock_count
    }
    
    insert_res = supabase.table("products").insert(data).execute()
    return {"status": "success", "data": insert_res.data}

def fetch_catalog_items():
    response = supabase.table("products").select("title, description, retail_price, wholesale_price, min_wholesale_qty, stock_count").eq("is_active", True).execute()
    return json.dumps(response.data)

@app.post("/chat")
def chat_with_assistant(req: ChatRequest):
    try:
        catalog_data = fetch_catalog_items()

        system_instruction = f"""
        You are a polite, helpful, and expert multilingual shopping assistant for Insha Bangles and Purses (Retail & Wholesale).
        
        CRITICAL RULES:
        1. NATIVE POLYGLOT: Detect the user's language and respond naturally in that exact same language (English, Hindi, Hinglish, Arabic, Spanish, Bengali, Urdu, etc.).
        2. RETAIL VS. WHOLESALE:
           - For single-item buyers: quote retail prices clearly.
           - For bulk/wholesale buyers: quote wholesale rates and explain the minimum order quantity (MOQ).
        3. ACCURACY: Base recommendations exclusively on available catalog items:
        {catalog_data}
        4. Keep your replies crisp, helpful, and visually scannable.
        """

        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=req.message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
            ),
        )

        return {
            "reply": response.text,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
