from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import SubmitField, StringField, URLField
from wtforms.validators import DataRequired, URL, Optional, Length


class URLShortenerForm(FlaskForm):
    original_link = URLField(
        'Длинная ссылка',
        validators=[
            DataRequired(message='Обязательное поле'),
            URL(message='Введите корректный URL')
        ]
    )
    custom_id = StringField(
        'Вариант короткой ссылки',
        validators=[
            Optional(),
            Length(min=1, max=16, message='Длина от 1 до 16 символов')
        ]
    )
    submit = SubmitField('Создать')


class FileUploadForm(FlaskForm):
    files = MultipleFileField(
        'Файлы',
        validators=[
            FileAllowed(
                [
                    'jpg', 'jpeg', 'png', 'gif', 'bmp',
                    'txt', 'py', 'csv', 'pdf', 'doc', 'docx', 'html'
                ],
                message=(
                    'Разрешены: изображения, текстовые файлы, '
                    'CSV, PDF и документы Word'
                )
            )
        ]
    )
    submit = SubmitField('Загрузить')
