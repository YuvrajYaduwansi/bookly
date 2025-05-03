from fastapi_mail import FastMail,MessageSchema,ConnectionConfig,MessageType
from src.config import config
from pathlib import Path


BASE_DIR=Path(__file__).resolve().parent

mail_config=ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME=config.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(BASE_DIR, "templates")
    )


mail=FastMail(config=mail_config)
    

def create_message(recipients:list[str],subject:str,body:str,subtype:MessageType=MessageType.html):
    message=MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype=subtype
    )
    
    return message
