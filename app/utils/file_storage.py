from fastapi import HTTPException
import requests
import os

from app.core import settings

UPLOAD_DIR = 'media'


def save_file_from_url(url: str, filename: str) -> str:
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)
    url = url.replace('&amp;', '&')
    response = requests.get(url, stream=True)
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code,
                            detail=f'Ошибка при загрузке изображения:{response.text}\nURL:{url}')
    with open(file_path, "wb") as out_file:
        out_file.write(response.content)
    return f'https://api.cehcom.kz/{file_path}'
