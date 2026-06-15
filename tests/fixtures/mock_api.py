from fastapi import FastAPI, HTTPException

mock_app = FastAPI()

@mock_app.get("/users")
async def list_users():
    return [{"id": "1", "email": "test@example.com"}]

@mock_app.post("/users", status_code=201)
async def create_user(body: dict):
    return {"id": "2", **body}

@mock_app.get("/users/{id}")
async def get_user(id: str):
    if id == "999":
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": id, "email": "user@example.com"}
