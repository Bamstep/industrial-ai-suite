import uvicorn

if __name__ == "__main__":
    print("[INFO] Starting Predictive Maintenance Edge Ingestion Node...")
    print("[INFO] Web Console: http://127.0.0.1:8000")
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)
