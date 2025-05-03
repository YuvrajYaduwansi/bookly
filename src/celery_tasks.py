from celery import Celery
from src.config import config
from src.mail import create_message,mail
from typing import List
from asgiref.sync import async_to_sync


celery_app=Celery(
    'celery_tasks',
)

celery_app.config_from_object('src.config')

@celery_app.task
def send_email(recipients:List[str],subject:str,body:str):
    message=create_message(
        recipients=recipients,
        subject=subject,
        body=body,
    )
    # old way without background tasks
    # await mail.send_message(message)

    # new way with background tasks
    async_to_sync(mail.send_message)(message)
    print("Email sent successfully")
