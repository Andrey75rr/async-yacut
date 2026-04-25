import asyncio
import os

import aiohttp
from dotenv import load_dotenv

load_dotenv()

API_BASE = 'https://cloud-api.yandex.net/v1/disk/resources'
DISK_TOKEN = os.environ.get('DISK_TOKEN')
AUTH_HEADERS = {'Authorization': f'OAuth {DISK_TOKEN}'}
UPLOAD_DIR = 'Приложения/yacut'


async def get_upload_link(session, file_name):
    """Получает ссылку для загрузки файла на Яндекс Диск."""
    params = {
        'path': f'{UPLOAD_DIR}/{file_name}',
        'overwrite': 'true'
    }
    async with session.get(
        f'{API_BASE}/upload', headers=AUTH_HEADERS, params=params
    ) as response:
        if response.status == 200:
            data = await response.json()
            return data.get('href')
        text = await response.text()
        print(f'[YaDisk] upload link error {response.status}: {text}')
    return None


async def get_download_link_async(session, disk_path):
    """Получает ссылку для скачивания файла с Яндекс Диска."""
    params = {'path': disk_path}
    async with session.get(
        f'{API_BASE}/download', headers=AUTH_HEADERS, params=params
    ) as response:
        if response.status == 200:
            data = await response.json()
            return data.get('href')
        text = await response.text()
        print(f'[YaDisk] download link error {response.status}: {text}')
    return None


async def upload_file(session, file):
    """Загружает файл на Яндекс Диск и возвращает путь к нему."""
    try:
        upload_url = await get_upload_link(session, file.filename)
        if not upload_url:
            return {
                'success': False,
                'file_name': file.filename,
                'error': 'Не удалось получить ссылку для загрузки'
            }

        file_content = file.read()
        async with session.put(upload_url, data=file_content) as response:
            if response.status == 201:
                disk_path = f'{UPLOAD_DIR}/{file.filename}'
                download_url = await get_download_link_async(
                    session, disk_path
                )
                return {
                    'success': True,
                    'file_name': file.filename,
                    'disk_path': disk_path,
                    'download_url': download_url
                }
            text = await response.text()
            print(f'[YaDisk] upload error {response.status}: {text}')
            return {
                'success': False,
                'file_name': file.filename,
                'error': f'Ошибка загрузки: {response.status}'
            }
    except Exception as e:
        return {
            'success': False,
            'file_name': file.filename,
            'error': str(e)
        }


def upload_files_to_yadisk(files):
    """Синхронная обёртка для асинхронной загрузки нескольких файлов."""
    if not DISK_TOKEN:
        return [
            {
                'success': False,
                'file_name': f.filename,
                'error': 'Токен Яндекс Диска не настроен'
            }
            for f in files
        ]

    async def upload_all():
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[upload_file(session, f) for f in files]
            )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(upload_all())
    finally:
        loop.close()


def get_fresh_download_link(disk_path):
    """Синхронно получает свежую ссылку для скачивания файла."""
    async def _get():
        async with aiohttp.ClientSession() as session:
            return await get_download_link_async(session, disk_path)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_get())
    finally:
        loop.close()
