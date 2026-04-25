import re
from http import HTTPStatus

from flask import Blueprint, jsonify, request, url_for

from . import db
from .error_handler import InvalidAPIUsage
from .models import URLMap
from .utils import generate_unique_short_id, is_short_id_taken

api_bp = Blueprint('api', __name__)

SHORT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]+$')
MAX_SHORT_ID_LENGTH = 16


@api_bp.route('/id/', methods=['POST'])
def create_short_link():
    """POST /api/id/ — создаёт новую короткую ссылку."""
    data = request.get_json(silent=True)

    if not data:
        raise InvalidAPIUsage('Отсутствует тело запроса')

    original_link = data.get('url')
    if not original_link:
        raise InvalidAPIUsage('"url" является обязательным полем!')

    custom_id = data.get('custom_id')

    if custom_id:
        if len(custom_id) > MAX_SHORT_ID_LENGTH:
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки'
            )
        if not SHORT_ID_PATTERN.match(custom_id):
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки'
            )
        if is_short_id_taken(custom_id):
            raise InvalidAPIUsage(
                'Предложенный вариант короткой ссылки уже существует.'
            )
        short_id = custom_id
    else:
        short_id = generate_unique_short_id()

    url_map = URLMap(original=original_link, short=short_id)
    db.session.add(url_map)
    db.session.commit()

    return jsonify({
        'url': original_link,
        'short_link': url_for(
            'redirect_to_url', short_id=short_id, _external=True
        )
    }), HTTPStatus.CREATED


@api_bp.route('/id/<string:short_id>/', methods=['GET'])
def get_original_link(short_id):
    """GET /api/id/<short_id>/ — возвращает оригинальную ссылку."""
    url_map = URLMap.query.filter_by(short=short_id).first()

    if not url_map:
        raise InvalidAPIUsage(
            'Указанный id не найден', status_code=HTTPStatus.NOT_FOUND
        )

    return jsonify({'url': url_map.original}), HTTPStatus.OK
