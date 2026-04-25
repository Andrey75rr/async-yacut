import asyncio
import logging
from http import HTTPStatus

import aiohttp
from dotenv import load_dotenv

from settings import Config

load_dotenv()

logger = logging.getLogger(__name__)

DISK_TOKEN = Config.DISK_TOKEN
AUTH_HEADERS = Config.YADISK_AUTH_HEADERS
API_BASE = Config.YADISK_API_BASE
UPLOAD_DIR = Config.YADISK_UPLOAD_DIR


async def get_upload_link(session, file_name):
    """Получает ссылку для загрузки файла на Яндекс Диск."""
    params = {
        'path': f'{UPLOAD_DIR}/{file_name}',
        'overwrite': 'true'
    }
    async with session.get(
        f'{API_BASE}/upload', headers=AUTH_HEADERS, params=params
    ) as response:
        if response.status == HTTPStatus.OK:
            data = await response.json()
            return data.get('href')
        text = await response.text()
        logger.error(
            'YaDisk upload link error %s: %s', response.status, text
        )
    return None


async def get_download_link_async(session, disk_path):
    """Получает ссылку для скачивания файла с Яндекс Диска."""
    params = {'path': disk_path}
    async with session.get(
        f'{API_BASE}/download', headers=AUTH_HEADERS, params=params
    ) as response:
        if response.status == HTTPStatus.OK:
            data = await response.json()
            return data.get('href')
        text = await response.text()
        logger.error(
            'YaDisk download link error %s: %s', response.status, text
        )
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
            if response.status == HTTPStatus.CREATED:
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
            logger.error(
                'YaDisk upload error %s: %s', response.status, text
            )
            return {
                'success': False,
                'file_name': file.filename,
                'error': f'Ошибка загрузки: {response.status}'
            }
    except Exception as e:
        logger.exception(
            'YaDisk upload exception for %s: %s', file.filename, e
        )
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
