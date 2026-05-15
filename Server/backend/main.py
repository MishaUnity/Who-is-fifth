from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from afisha import router as afisha_router

app = FastAPI()

app.include_router(afisha_router)

app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

@app.get("/")
def index():
    return FileResponse("../frontend/main.html")
