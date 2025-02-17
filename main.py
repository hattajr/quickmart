from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import PRODUCTS_TABLE, get_local_db, download_master_table, is_table_exists, log_search
from sqlalchemy.orm import Session
from sqlalchemy import text
from dataclasses import dataclass



if not is_table_exists():
    print("LOCAL SQLITE not found")
    print("Downloading...")
    download_master_table()
    print("success download master DB")


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
    print(len(search_txt))
    if request.headers.get('HX-Request'):
        if len(search_txt) > 0:
            q = text(f"""
                SELECT name, price, unit,  barcode 
                FROM {PRODUCTS_TABLE} 
                WHERE barcode LIKE '%' || :search_txt || '%'
                    OR name LIKE '%' || :search_txt || '%' 
                    OR search_term LIKE '%' || :search_txt || '%'
            """)
            p = {"search_txt": search_txt}
            result = db.execute(q, p).fetchall()

            # Search log
            if result:
                is_found = True
            else:
                is_found = False

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

            log_search(search_txt,  is_found)
            return templates.TemplateResponse(request=request, name="search_results.html", context={"items": items})
            
