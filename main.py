import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import date

from database import create_document, get_documents
from schemas import Booking

app = FastAPI(title="Kids Interactive Center API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Kids Interactive Center Backend is running"}

# Public catalog of themed programs with animators (static list for now)
class Program(BaseModel):
    key: str
    title: str
    description: str
    recommended_age: str
    duration_minutes: int
    price: int
    animators: List[str]
    cover: str

PROGRAMS: List[Program] = [
    Program(
        key="pirates_treasure",
        title="Пиратский клад",
        description="Весёлое приключение с поиском сокровищ, морскими конкурсами и квестами.",
        recommended_age="5–9",
        duration_minutes=90,
        price=6900,
        animators=["Капитан Джек", "Юнга Мими"],
        cover="/images/pirates.jpg",
    ),
    Program(
        key="space_odyssey",
        title="Космическая одиссея",
        description="Научное шоу, опыты, планетарные игры и спасение космической станции.",
        recommended_age="7–12",
        duration_minutes=90,
        price=7900,
        animators=["Астронавт Нео", "Робот Пикс"],
        cover="/images/space.jpg",
    ),
    Program(
        key="fairy_unicorns",
        title="Единороги и феи",
        description="Сказочная анимация, блестки, аквагрим и волшебные мастер‑классы.",
        recommended_age="4–8",
        duration_minutes=75,
        price=6500,
        animators=["Фея Лили", "Единорог Стар"],
        cover="/images/unicorns.jpg",
    ),
]

@app.get("/api/programs", response_model=List[Program])
def list_programs():
    return PROGRAMS

@app.post("/api/bookings")
def create_booking(booking: Booking):
    try:
        inserted_id = create_document("booking", booking)
        return {"status": "ok", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bookings")
def get_bookings():
    try:
        docs = get_documents("booking", limit=50)
        # Convert ObjectId and dates to serializable
        for d in docs:
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
            if isinstance(d.get("preferred_date"), date):
                d["preferred_date"] = d["preferred_date"].isoformat()
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
