"""
Reference only — minimal FastAPI + Mangum pattern for Lambda HTTP API v2.
Production app: ``app.main`` (CMD ["app.main.handler"]).
"""

from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok"}


handler = Mangum(app)
