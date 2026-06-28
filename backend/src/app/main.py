
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routes import router

def _build_webserver() -> FastAPI:
    load_dotenv()

    app = FastAPI(
        title="Finance Agent Task Runner",
        version="0.1.0",
    )

    app.include_router(router)

    return app

app = _build_webserver()

def main() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()