from fastapi import FastAPI

app = FastAPI(title="Ledger Web Application")

@app.get("/")
def home():
    return{"Ledger Web Running"}


