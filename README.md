# QuickMart
A super-fast yet simple inventory item search engine built with **FastAPI** and **HTMX**.  
[Live Demo](https://ikmimart.onrender.com/)  

## Features  
- 🔍 **Instant Search** – Fast inventory search with minimal latency.  
- 📜 **Search History Logging** – Keeps track of previous searches for analytics or user convenience.  

## Tech Stack  
- **Backend**: FastAPI (Python) – High-performance async web framework  
- **Frontend**: HTMX – Enhances interactivity without full-page reloads  
- **Database**: SQLite / PostgreSQL (configurable) – Stores inventory and search history  
- **Deployment**: Hosted on Render

## Installation & Setup  
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port <PORT>
```


### Enviroment
```bash
DB_PATH = 
PRODUCTS_TABLE = 
MASTERDB_USER = 
MASTERDB_PASSWORD = 
MASTERDB_HOST = 
MASTERDB_PORT = 
MASTERDB_NAME = 
```