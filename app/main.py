from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return{"Ledger Web Running"}