from fastapi import FastAPI

app = FastAPI(title="SAGE Runtime")


@app.get("/")
def root():
    return {"status": "SAGE Runtime online"}
