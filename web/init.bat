@echo off 

title ejecucion de la web de lanzamiento de correos 

echo iniciando los elementos dentro del .bat

.\.env\Scripts\activate

fastapi run .\main.py --port 8006