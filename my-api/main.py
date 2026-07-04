from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="my-api")


class Item(BaseModel):
    name: str
    description: str | None = None


@app.get("/")
async def root():
    return {"message": "Hello from my-api"}


@app.post("/items/")
async def create_item(item: Item):
    return item
