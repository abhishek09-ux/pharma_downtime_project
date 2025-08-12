# main.py
from fastapi import FastAPI
from app.core.database import Base, engine
from app.routes import downtime_routes

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pharma Downtime Project", version="1.0")

# Include routes
app.include_router(downtime_routes.router)

if __name__ == "__main__":
    print("main.py executed. To run the FastAPI server, use: uvicorn main:app --reload")
    print("Swagger docs available at http://127.0.0.1:8000/docs")

@app.get("/")
def root():
    return {"message": "Welcome to the Pharma Downtime API!"}