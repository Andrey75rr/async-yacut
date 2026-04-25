from flask import render_template, redirect, url_for, flash, request

from . import app, db
from .forms import URLShortenerForm, FileUploadForm
from .models import URLMap
from .utils import generate_unique_short_id, is_short_id_taken
from .yandex_disk import upload_files_to_yadisk, get_fresh_download_link


@app.route('/', methods=['GET', 'POST'])
def index_view():
    """Главная страница — создание коротких ссылок."""
    form = URLShortenerForm()
    short_url = None

    if form.validate_on_submit():
        original_link = form.original_link.data
        custom_id = (
            form.custom_id.data.strip() if form.custom_id.data else None
        )

        if custom_id:
            if is_short_id_taken(custom_id):
                flash(
                    'Предложенный вариант короткой ссылки уже существует.',
                    'danger'
                )
                return render_template(
                    'urlmap.html', form=form, short_url=short_url
                )
            short_id = custom_id
        else:
            short_id = generate_unique_short_id()

        url_map = URLMap(original=original_link, short=short_id)
        db.session.add(url_map)
        db.session.commit()
        short_url = url_for(
            'redirect_to_url', short_id=short_id, _external=True
        )

    return render_template('urlmap.html', form=form, short_url=short_url)


@app.route('/files', methods=['GET', 'POST'])
def add_file_map():
    """Страница загрузки файлов на Яндекс Диск."""
    form = FileUploadForm()
    uploaded_files = []

    if request.method == 'POST':
        files = [
            f for f in request.files.getlist('files') if f and f.filename
        ]

        if not files:
            flash('Выберите хотя бы один файл.', 'warning')
        else:
            results = upload_files_to_yadisk(files)

            for result in results:
                if result['success']:
                    short_id = generate_unique_short_id()
                    url_map = URLMap(
                        original=result['disk_path'],
                        short=short_id,
                        disk_path=result['disk_path']
                    )
                    db.session.add(url_map)
                    uploaded_files.append({
                        'name': result['file_name'],
                        'short_url': url_for(
                            'redirect_to_url',
                            short_id=short_id,
                            _external=True
                        )
                    })
                else:
                    flash(
                        f'Ошибка загрузки «{result["file_name"]}»: '
                        f'{result.get("error")}',
                        'danger'
                    )

            if uploaded_files:
                db.session.commit()

    return render_template(
        'add_file_map.html', form=form, uploaded_files=uploaded_files
    )


@app.route('/<string:short_id>')
def redirect_to_url(short_id):
    """Редирект по короткой ссылке."""
    url_map = URLMap.query.filter_by(short=short_id).first_or_404()

    if url_map.disk_path:
        download_url = get_fresh_download_link(url_map.disk_path)
        if not download_url:
            flash('Не удалось получить ссылку на файл.', 'danger')
            return redirect(url_for('add_file_map'))
        return redirect(download_url)

    return redirect(url_map.original)
