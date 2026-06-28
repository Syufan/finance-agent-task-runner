import uvicorn
from fastapi import FastAPI

from app.factory import AppFactory


app: FastAPI = AppFactory().create_app()

def main() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
