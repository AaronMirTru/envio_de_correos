from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from datetime import datetime

from dotenv import load_dotenv

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import smtplib
import pandas as pd 
import os 

app = FastAPI()


templates = Jinja2Templates(directory="app/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
static_path = os.path.join(os.path.dirname(__file__), 'app\\static\\')
app.mount('/static', StaticFiles(directory=static_path), 'static')

# Correo_copias = 'Canales@alumbraenergia.es, comercial@isofase.es' # testing
# Correo_copias = 'Canales@alumbraenergia.es, F.nieto@alumbraenergia.es ' # end

Correo_copias = 'aaron.mir@alumbraenergia.es; aaron.mir@donvatio.es;'

# brian@donvatio.es
@app.get("/", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# parte del post del log para la introduccion del user y pass comparative de "usuario" y la pass 
@app.post("/login", response_class=HTMLResponse) 
async def login(request: Request, username: str = Form(...), password: str = Form(...)):

    is_correct = pwd_context.verify(password, '$2b$12$mOtYDqf7qrplJtc4NIWDxOQao8IZoT8RCJb1v28.8OHPbwjTnEjlS')
    if username =='usuario' and is_correct == True : 
        return templates.TemplateResponse("index.html", {"request": request})
    else :
        return templates.TemplateResponse("login.html", {"request": request, "false_password": True})


@app.post("/lanzamiento_correos", response_class=HTMLResponse)
async def root(request: Request):
        
    # Cargar las variables del archivo .env
    load_dotenv()

    # Configuración del servidor SMTP
    smtp_server = 'smtp.ionos.es'
    smtp_port = 587
    email_sender = os.getenv('email_sender')
    email_password = os.getenv('email_password')

    formato = "%Y-%m-%d"

    estilos = """
        <style>
            .table-container {
                width: 100%;
                height: 200px;
                overflow-y: auto;
                border: 1px solid #ccc;
            }

            table {
                width: 100%;
                border-collapse: collapse;
            }

            table, th, td {
                border: 1px solid black;
            }

            th, td {
                padding: 8px;
                text-align: left;a
            }

            th {
                background-color: #f2f2f2;
            }
        </style>
        """

    # primero se tiene que extraer la informacion de los datos del csv
    datos_contratos = pd.read_csv(r"\\192.168.1.57\datos_nemon\dashb_entity_customers.csv", delimiter=';')

    tabla_html_rechazos = ''
    tabla_html_bajas = ''


    bajas = datos_contratos.loc[datos_contratos['atr_status_desc'].str.contains("Baja", regex=False, case=False) & 1]
    rechazos = datos_contratos[datos_contratos['atr_status_desc'] == 'Rechazado']
    
    # fichero que tiene que venir por entrada del usuario 
    datos_motivos = pd.read_csv(r"\\192.168.1.57\datos_nemon\dashb_entity_switching.csv", delimiter=';', encoding='UTF-8')

    datos_motivos = datos_motivos.dropna(subset=['Rechazo'])

    bajas = pd.merge(bajas, datos_motivos, how='left', left_on='__cups__', right_on='cups')
        
    email_csv = pd.read_csv(r'.\\data\\intern_data\\mails y canales.csv', sep=';')
    
    email_csv = email_csv.dropna(subset=["CANAL"])
    

    # iterar por cada uno de los resultados recogiendo la informacion
    x = 0
    tabla_de_bajas = pd.DataFrame(
            columns=[
                        'titular', 
                        'contacto', 
                        'cups', 
                        'consumo_sips', 
                        'canal', 
                        'agente', 
                        'fecha_activacion', 
                        'fecha_de_baja', 
                        'dias', 
                        'motivo'
                    ]
            )

    for index, row in bajas.iterrows():
        if row['atr_activation_expected_date'] != '0000-00-00':
            fecha_activacion = datetime.strptime(row['atr_activation_expected_date'], formato)
        else :
            fecha_activacion = '0000-00-00'

        if row['atr_ending_date'] != '0000-00-00':
            fecha_de_baja = datetime.strptime(row['atr_ending_date'], formato)
        else :
            fecha_de_baja = '0000-00-00'

        # Restar las dos fechas
        if row['atr_ending_date'] == '0000-00-00' or row['atr_activation_expected_date'] == '0000-00-00':
            diferencia = 0
        else :
            diferencia = fecha_de_baja - fecha_activacion
            diferencia = diferencia.days
            
        
        tabla_de_bajas.loc[x,'titular'] = row['customerName']
        tabla_de_bajas.loc[x,'contacto'] = row['tariff_name']
        tabla_de_bajas.loc[x,'cups'] = row['__cups__']
        tabla_de_bajas.loc[x,'consumo_sips'] = row['annual_consumption']
        tabla_de_bajas.loc[x,'canal'] = row['agent_number']
        tabla_de_bajas.loc[x,'agente'] = row['agent_name']
        tabla_de_bajas.loc[x,'fecha_activacion'] = fecha_activacion
        tabla_de_bajas.loc[x,'fecha_de_baja'] = fecha_activacion
        tabla_de_bajas.loc[x,'dias'] = diferencia
        tabla_de_bajas.loc[x,'motivo'] = row['Rechazo']

        x = x + 1

    tabla_de_rechazos = pd.DataFrame(
        columns=[
                'titular', 
                'contrato', 
                'cups', 
                'proceso', 
                'canal', 
                'motivo'
            ]
        )

    x = 0

    for index, row in rechazos.iterrows():

        tabla_de_rechazos.loc[x,'titular'] = row['customerName']
        tabla_de_rechazos.loc[x,'contrato'] = row['tariff_name']
        tabla_de_rechazos.loc[x,'cups'] = row['__cups__']
        tabla_de_rechazos.loc[x,'proceso'] = 'None'
        tabla_de_rechazos.loc[x,'canal'] = row['agent_number']
        tabla_de_rechazos.loc[x,'motivo'] = 'None'

        x = x + 1

    #  extraccion de los datos de extraccion de bajas y rechazos cuando coexistan 
    agrupdado_bajas_canal_agente = tabla_de_bajas.groupby(['canal', 'agente'])


    for (canal, agente), baja in agrupdado_bajas_canal_agente:
        
        email1 = email_csv.loc[email_csv["CANAL"] == canal]["MAIL 1"].values
        email2 = email_csv.loc[email_csv["CANAL"] == canal]["MAIL 2"].values
        
        if len(email1): 
            email1 = str(email1[0])
            if email1 == 'nan':
                email1 = ''

        if len(email2):
            email2 = str(email2[0])
            if email2 == 'nan': 
                email2 = ''
        
        listado_correos = email1 + ";" + email2
        
        rechazo = pd.DataFrame(tabla_de_rechazos.loc[(tabla_de_rechazos['canal'] == canal) & (tabla_de_rechazos['cups'].isin(baja['cups']))])

        # en el caso de que el elemento se este enviando con la relacion, solamente se tiene que reenviar con la condicion de que los elementos sean los mismos 
        #  entonces de la condicion anterior, se tiene que establecer
        
        if not rechazo.empty:
            # genera los datos de las tablas html 
            tabla_html_bajas = baja.to_html(index=False)
            tabla_html_rechazos = rechazo.to_html(index=False)
            
            mensaje_html = rf"""
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <meta charset="UTF-8">a
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>correo bajas y rechazos </title>
                            {estilos}
                        </head>
                        <body>
                        
                            <p>correos a los que se envia</p>
                            <p>{listado_correos}</p>
                            
                            <p>Buenas tardes,</p>
                            <p>adjunto las bajas recibidas:</p>

                            <div class="table-container">
                                {tabla_html_bajas}
                            </div>

                            <p>Para poder realizar las recuperaciones hay dos opcioens que detallo a continuación</p>

                                <p>- Desestimar el contrato que ha firmado en la otra comercializadora.</p>
                                <p>- Que el cliente firme el anexo de reposición que adjunto. En caso de firmar la plantilla, se tendrá que enviar por correo a canales@alumbraenergia.es correctamente cumplimentada y firmada por el cliente.</p>

                            <p>Tenemos de plazo 14 días para realizar las recuperaciones desde el día en el que se han dado de baja.</p>

                            <p>Rechazos:</p>

                            <div class="table-container">
                                {tabla_html_rechazos}
                            </div>

                            <p>Un saludo.</p>
                            
                            <a href="https://alumbraenergia.es/">
                            <img src="cid:mi_imagen" alt="IMAGEN_ALUMBRA_CARMEN">
                            </a>
                        </body>
                        </html>                         
                            """
            
            #  en el caso de que el rechazo exista, lo elimina de las condiciones necesarias 
            tabla_de_rechazos = tabla_de_rechazos.loc[~(tabla_de_rechazos['cups'].isin(rechazo['cups']))]
            
            #  en el caso de que la baja tambien exista tambien la elimina para no crear dupliacdos dentro de la condicion de envio 
            tabla_de_bajas = tabla_de_bajas.loc[~(tabla_de_bajas['canal'] == canal)]

            
            # sustitucion por envio de correo 
            with open(rf"data/intern_data/bajas_y_rechazos/{str(canal).replace(' ', '_')}_bajas_y_rechazos.html", "w", encoding="utf-8") as file:
                file.write(mensaje_html)
                # Datos del correo
                # email_recipient = listado_correos
                email_recipient = Correo_copias + 'aaron.mir@alumbraenerga.onmicrosoft.com' 
                # email_recipient = listado_correos
                subject = 'envio bajas y rechazos'
                body = mensaje_html

                # Crear el mensaje
                message = MIMEMultipart()
                
                 # generacion de los datos para poder asignar una imagen 
                with open("./img/footer.png", 'rb') as img_file:
                    img = MIMEImage(img_file.read())
                    img.add_header('Content-ID', '<mi_imagen>')  # Debe coincidir con el cid en el HTML
                    message.attach(img)
                
                
                message['From'] = email_sender
                message['To'] = email_recipient
                message['Subject'] = subject
                message['CC'] = Correo_copias

                # Adjuntar el cuerpo del correo
                message.attach(MIMEText(body, 'html'))

                # Conexión al servidor SMTP y envío
                try:
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()  # Seguridad TLS
                    server.login(email_sender, email_password)
                    text = message.as_string()
                    server.sendmail(email_sender, email_recipient, text)
                    server.quit()
                    print('Correo enviado exitosamente.')
                except Exception as e:
                    print(f'Error al enviar correo: {e}')




    agrupdado_bajas_2_canal_agente = tabla_de_bajas.groupby(['canal', 'agente'])
    for (canal, agente), bajas in agrupdado_bajas_canal_agente:
        email1 = email_csv.loc[email_csv["CANAL"] == canal]["MAIL 1"].values
        email2 = email_csv.loc[email_csv["CANAL"] == canal]["MAIL 2"].values
            
        if len(email1): 
            email1 = str(email1[0])
            if email1 == 'nan':
                email1 = ''

        if len(email2):
            email2 = str(email2[0])
            if email2 == 'nan': 
                email2 = ''
        
        listado_correos = email1 + ";" + email2

        # recogida de los correos a los que se envia 

        # generacion de los elementos que se meten dentro del html que se envia 
        tabla_html_bajas = bajas.to_html(index=False)
        
        
        mensaje_html = rf"""
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>correo bajas y rechazos </title>
                            {estilos}
                        </head>
                        <body>

                            <p>correos a los que se envia</p>
                            <p>{listado_correos}</p>
                            
                            <p>Buenas tardes,</p>
                            <p>adjunto las bajas recibidas:</p>

                            <div class="table_container">
                                {tabla_html_bajas}       
                            </div>

                            <p>Para poder realizar las recuperaciones hay dos opcioens que detallo a continuación</p>

                                <p>- Desestimar el contrato que ha firmado en la otra comercializadora.</p>
                                <p>- Que el cliente firme el anexo de reposición que adjunto. En caso de firmar la plantilla, se tendrá que enviar por correo a canales@alumbraenergia.es correctamente cumplimentada y firmada por el cliente.</p>

                            <p>Tenemos de plazo 14 días para realizar las recuperaciones desde el día en el que se han dado de baja.</p>

                            <p>Un saludo.</p>
                            <a href="https://alumbraenergia.es/">
                            <img src="cid:mi_imagen" alt="IMAGEN_ALUMBRA_CARMEN">
                            </a>
                        </body>
                        </html>
        """
        
        # en esta zona se preparan los html que tendran el mensaje que se envia por correo 
        with open(rf"data/intern_data/bajas/{str(canal).replace(' ', '_')}_bajas.html", "w", encoding="utf-8") as file:
                file.write(mensaje_html)
                # Datos del correo
                # email_recipient = Correo_copias + 'aaron.mir@alumbraenerga.onmicrosoft.com' 
                # # email_recipient = listado_correos
                # subject = 'envio bajas'
                # body = mensaje_html

                # # Crear el mensaje
                # message = MIMEMultipart()
                
                # # generacion de los datos para poder asignar una imagen 
                # with open("./img/footer.png", 'rb') as img_file:
                #     img = MIMEImage(img_file.read())
                #     img.add_header('Content-ID', '<mi_imagen>')  # Debe coincidir con el cid en el HTML
                #     message.attach(img)

                # message['From'] = email_sender
                # message['To'] = email_recipient
                # message['Subject'] = subject
                # message['Cc'] = Correo_copias
                

                # # Adjuntar el cuerpo del correo
                # message.attach(MIMEText(body, 'html'))

                # # Conexión al servidor SMTP y envío
                # try:
                #     server = smtplib.SMTP(smtp_server, smtp_port)
                #     server.starttls()  # Seguridad TLS
                #     server.login(email_sender, email_password)
                #     text = message.as_string()
                #     server.sendmail(email_sender, email_recipient, text)
                #     server.quit()
                #     print('Correo enviado exitosamente.')
                # except Exception as e:
                #     print(f'Error al enviar correo: {e}')
        


    agrupdado_rechazos_2_canal_agente = tabla_de_rechazos.groupby(['canal'])

    for canal, rechazos in agrupdado_rechazos_2_canal_agente:
        email1 = email_csv.loc[email_csv["CANAL"] == canal]["MAIL 1"].values
        email2 = email_csv.loc[email_csv["CANAL"] == canal]["MAIL 2"].values
            
        if len(email1): 
            email1 = str(email1[0])
            if email1 == 'nan':
                email1 = ''

        if len(email2):
            email2 = str(email2[0])
            if email2 == 'nan': 
                email2 = ''

        listado_correos = email1 + ";" + email2
        
        # print(listado_correos)

        # generacion dfel listado de los rechazos  
        tabla_html_rechazos = rechazos.to_html(index=False)

        # generacion del mensaje 
        
        mensaje_html = rf"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>correo bajas y rechazos </title>
                    {estilos}
                </head>
                <body>
                
                    <p>correos a los que se envia</p>
                    <p>{listado_correos}</p>
                            
                    <p>Buenas tardes,</p>
                    <p>Para poder realizar las recuperaciones hay dos opcioens que detallo a continuación</p>

                        <p>- Desestimar el contrato que ha firmado en la otra comercializadora.</p>
                        <p>- Que el cliente firme el anexo de reposición que adjunto. En caso de firmar la plantilla, se tendrá que enviar por correo a canales@alumbraenergia.es correctamente cumplimentada y firmada por el cliente.</p>

                    <p>Tenemos de plazo 14 días para realizar las recuperaciones desde el día en el que se han dado de baja.</p>

                    <p>Rechazos:</p>

                    <div class="table-container">
                    {tabla_html_rechazos}
                    </div>

                    <p>Un saludo.</p>
            
                    <a href="https://alumbraenergia.es/">
                    <img src="cid:mi_imagen" alt="IMAGEN_ALUMBRA_CARMEN">
                    </a>
                </body>
                </html>
        """

        # eliminacion de la parte del inicio y final de la info
        canal = str(canal).replace("('", '').replace("',)", '').replace(' ', '_')

        # envio de correos viene en esta zona 
        with open(rf"data/intern_data/rechazos/{str(canal).replace(' ', '_')}_rechazos.html", "w", encoding="utf-8") as file:
                file.write(mensaje_html)
                # # Datos del correo
                # email_recipient = Correo_copias + 'aaron.mir@alumbraenerga.onmicrosoft.com' 
                # # email_recipient = listado_correos
                # subject = 'envio rechazos'
                # body = mensaje_html

                # # Crear el mensaje
                # message = MIMEMultipart()
                
                # #  generacion de los datos para poder asignar una imagen 
                # with open("./img/footer.png", 'rb') as img_file:
                #     img = MIMEImage(img_file.read())
                #     img.add_header('Content-ID', '<mi_imagen>')  # Debe coincidir con el cid en el HTML
                #     message.attach(img)
                    
                # message['From'] = email_sender
                # message['To'] = email_recipient
                # message['Subject'] = subject
                # message['Cc'] = Correo_copias
                

                # # Adjuntar el cuerpo del correo
                # message.attach(MIMEText(body, 'html'))

                # # Conexión al servidor SMTP y envío
                # try:
                #     server = smtplib.SMTP(smtp_server, smtp_port)
                #     server.starttls()  # Seguridad TLS
                #     server.login(email_sender, email_password)
                #     text = message.as_string()
                #     server.sendmail(email_sender, email_recipient, text)
                #     server.quit()
                #     print('Correo enviado exitosamente.')
                # except Exception as e:
                #     print(f'Error al enviar correo: {e}')
            
    return templates.TemplateResponse("index.html", {"request": request, "results": True})