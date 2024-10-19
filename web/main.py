from fastapi import FastAPI, Request, UploadFile, File 
import pandas as pd 

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "index"}

@app.post("/lanzamiento_correos")
async def root(request: Request, Fichero_Customers : UploadFile = None, Fichero_solicitudes_de_alta : UploadFile = None):
    
    if Fichero_Customers.content_type == "text/csv" and Fichero_solicitudes_de_alta.content_type == "text/csv":
        elemento_1_csv = await Fichero_Customers.read()  
        customers_csv_format = elemento_1_csv.decode("UTF-16 LE")
        
        # verificar como solucionar el fallo del decode 
        # elemento_2_csv = await Fichero_solicitudes_de_alta.read(size=32)
        # motivos_csv_format = elemento_2_csv.decode("UTF-16 LE")
        
        customers = pd.read_csv(customers_csv_format.replace("\ufeff", ''), sep=';', delimiter='"')
        # motivos = pd.read_csv(motivos_csv_format, sep=';')
    
        # print(customers)
        # print(motivos)
    
    # print(Fichero_solicitudes_de_alta)
    
    # datos_contratos =  pd.read_csv(Fichero_Customers)
    # datos_motivos = pd.read_csv(Fichero_solicitudes_de_alta)
    
    
    # print(datos_contratos)
    # print(datos_motivos)
        
        
    return {"tipo1": rf"{Fichero_Customers.content_type}" , "tipo2": rf"{Fichero_solicitudes_de_alta.content_type}"}