from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import PRODUCTS_TABLE, get_local_db, download_master_table, is_table_exists
from sqlalchemy.orm import Session
from sqlalchemy import text
from dataclasses import dataclass
import base64


if not is_table_exists():
    print("LOCAL SQLITE not found")
    print("Downloading...")
    download_master_table()
    print("success download master DB")


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# Register the filter with the Jinja2 environment
def b64encode(data: bytes) -> str:
    # Custom filter for Base64 encoding
    return base64.b64encode(data).decode("utf-8")

templates.env.filters['b64encode'] = b64encode

@dataclass
class Item:
    barcode:str
    name: str
    price: int
    unit: str | None
    image_url: str | None = None
    image_format = ".png"
    _image_base_url =  "https://ynmesjxztocrzaoxktaa.supabase.co/storage/v1/object/public/image_test/output_images/"

    def __post_init__(self):
        self.image_url = self._image_base_url+self.barcode+self.image_format


@app.get("/download_master_db", response_class=HTMLResponse)
async def download_master_db(request: Request):
    print("Downloading...")
    download_master_table()
    print("success download master DB")
    return

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    return templates.TemplateResponse(request=request, name="settings.html")

@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, search_txt:str, db:Session=Depends(get_local_db)):
    print(1, search_txt)
    if request.headers.get('HX-Request'):
        print(2, search_txt)
        if len(search_txt) > 0:
            print(3, search_txt)
            q = text(f"SELECT name, price, unit,  barcode FROM {PRODUCTS_TABLE} WHERE name LIKE '%' || :search_txt || '%' OR barcode LIKE '%' || :search_txt || '%'")
            p = {"search_txt": search_txt}
            result = db.execute(q, p)
            items = [
                Item(
                    name=row[0],
                    price=int(row[1]), 
                    unit=row[2],
                    barcode=row[3],
                ) for row in result
                ]
            for item in items:
                if item.unit is None:
                    item.unit = "pcs"
            return templates.TemplateResponse(request=request, name="search_results.html", context={"items": items})
            