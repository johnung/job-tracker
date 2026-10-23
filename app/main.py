from fastapi import FastAPI

app = FastAPI(title="Job Tracker")


@app.get("/health")
def health():
    return {"status": "ok"}
