from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from passlib.context import CryptContext

import os 
import pandas as pd 

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
static_path = os.path.join(os.path.dirname(__file__), 'app\\static\\')
app.mount('/static', StaticFiles(directory=static_path), 'static')


@app.get("/")
async def root():
    return {"message": "index"}

# parte del post del log para la introduccion del user y pass comparative de "usuario" y la pass 
@app.post("/login", response_class=HTMLResponse) 
async def login(request: Request, username: str = Form(...), password: str = Form(...)):

    is_correct = pwd_context.verify(password, '$2b$12$mOtYDqf7qrplJtc4NIWDxOQao8IZoT8RCJb1v28.8OHPbwjTnEjlS')
    if username =='usuario' and is_correct == True : 
        return templates.TemplateResponse("index.html", {"request": request})
    else :
        return templates.TemplateResponse("login.html", {"request": request, "false_password": True})


@app.post("/lanzamiento_correos")
async def root(request: Request, Fichero_Customers : UploadFile = None, Fichero_solicitudes_de_alta : UploadFile = None):
    
    if Fichero_Customers.content_type == "text/csv":
        elemento_1_csv = await Fichero_Customers.read()  
        customers_csv_format = elemento_1_csv.decode("UTF-16 LE")
        
        print(customers_csv_format.replace('\n', '').replace('\t', '').replace('\r', '').replace('\r\n', ''))

        customers_csv_format = customers_csv_format.replace('\n', '').replace('\t', '').replace('\r', '').replace('\r\n', '')

        customers = pd.DataFrame(customers_csv_format)
        # verificar como solucionar el fallo del decode 
        # elemento_2_csv = await Fichero_solicitudes_de_alta.read(size=32)
        # motivos_csv_format = elemento_2_csv.decode("UTF-16 LE")
        
        # customers = pd.read_csv(customers_csv_format, sep=';')
        # motivos = pd.read_csv(motivos_csv_format, sep=';')
    
        print(customers)
        # print(motivos)
    
    # print(Fichero_solicitudes_de_alta)
    
    # datos_contratos =  pd.read_csv(Fichero_Customers)
    # datos_motivos = pd.read_csv(Fichero_solicitudes_de_alta)
    
    
    # print(datos_contratos)
    # print(datos_motivos)
        
        
    return {
            "tipo1": rf"{Fichero_Customers.content_type}" , 
            "tipo2": rf"{Fichero_solicitudes_de_alta.content_type}"
           }