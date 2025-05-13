from flask import Flask, render_template, request, redirect, url_for, flash, abort # Импортируем abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import pytz

# Создание экземпляра приложения Flask
app = Flask(__name__)

# --- Конфигурация приложения ---
# Настройка URI базы данных SQLAlchemy (используем SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dope_music.db'
# Отключение отслеживания изменений объектов SQLAlchemy (рекомендуется для производительности)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Установка секретного ключа для безопасности сессий и flash-сообщений.
# Получаем из переменной окружения или используем заглушку (ОЧЕНЬ ВАЖНО ЗАМЕНИТЬ НА НАДЕЖНЫЙ КЛЮЧ!)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'ВАШ_ОЧЕНЬ_НАДЕЖНЫЙ_И_СЛУЧАЙНЫЙ_СЕКРЕТНЫЙ_КЛЮЧ' # <-- Замените это!

# --- Конфигурация для загрузки файлов ---
# Папка, куда будут сохраняться загруженные изображения. Находится внутри папки 'static'.
UPLOAD_FOLDER = 'static/post_images'
# Разрешенные расширения файлов изображений
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Добавление папки загрузки в конфигурацию приложения
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Проверка и создание папки для загрузки при запуске приложения, если ее нет
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Инициализация расширения SQLAlchemy, связывая его с приложением Flask
db = SQLAlchemy(app)

# Инициализация расширения Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
# Установка имени функции маршрута для страницы входа (Flask-Login будет перенаправлять сюда неавторизованных пользователей)
login_manager.login_view = 'login'
# Сообщение, которое будет показано при перенаправлении на страницу входа
login_manager.login_message = 'Для доступа к этой странице необходимо авторизоваться.'
# Категория сообщения (используется Bootstrap для стилизации alert)
login_manager.login_message_category = 'info'


# --- Вспомогательная функция для проверки расширения файла ---
def allowed_file(filename):
    # Проверяет, есть ли точка в имени файла и является ли часть после последней точки
    # одним из разрешенных расширений (в нижнем регистре).
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Модель пользователя ---
# Определяет структуру таблицы 'user' в базе данных. Наследуется от UserMixin для интеграции с Flask-Login.
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # Первичный ключ, автоинкремент
    username = db.Column(db.String(100), unique=True, nullable=False) # Имя пользователя, уникальное, обязательное
    password_hash = db.Column(db.String(200), nullable=False) # Хеш пароля, обязательное

    # Метод для хеширования и установки пароля
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Метод для проверки введенного пароля с хешем из БД
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Метод для удобного представления объекта пользователя (для отладки)
    def __repr__(self):
        return f'<User {self.username}>'

# --- Модель поста ---
# Определяет структуру таблицы 'post' в базе данных.
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Первичный ключ, автоинкремент
    title = db.Column(db.String(100), nullable=False) # Заголовок поста, обязательное
    text = db.Column(db.Text, nullable=False) # Текст поста, обязательное (тип Text для длинного текста)
    # Поле для хранения имени файла изображения. Может быть NULL, так как изображение необязательно.
    image_filename = db.Column(db.String(100), nullable=True)
    # Поле для даты и времени создания поста. Устанавливается автоматически при создании записи. Храним в UTC.
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # Опционально: user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Опционально: author = db.relationship('User', backref=db.backref('posts', lazy=True))


    # Метод для удобного представления объекта поста (для отладки)
    def __repr__(self):
        return f'<Post {self.title}>'


# --- Функция загрузки пользователя для Flask-Login ---
# Эта функция необходима Flask-Login для загрузки пользователя из сессии по его ID.
@login_manager.user_loader
def load_user(user_id):
    # Возвращает объект пользователя или None, если пользователь не найден.
    return User.query.get(int(user_id))


# --- Пользовательский фильтр Jinja2 для форматирования даты/времени с учетом часового пояса ---
@app.template_filter('format_datetime_timezone')
def format_datetime_timezone(value, timezone_name='UTC', format='%Y-%m-%d %H:%M'):
    """
    Форматирует объект datetime в указанный часовой пояс и строку.
    Args:
        value (datetime): Объект datetime (предполагается UTC).
        timezone_name (str): Имя целевого часового пояса (например, 'Asia/Yekaterinburg').
        format (str): Строка формата для strftime.
    Returns:
        str: Отформатированная строка даты/времени.
    """
    if value is None:
        return ""

    utc_timezone = pytz.timezone('UTC')
    if value.tzinfo is None:
        utc_dt = utc_timezone.localize(value)
    else:
         utc_dt = value.astimezone(utc_timezone)


    try:
        # Получаем целевой часовой пояс по имени
        target_timezone = pytz.timezone(timezone_name)
        # Преобразуем UTC время в целевой часовой пояс
        target_dt = utc_dt.astimezone(target_timezone)
        # Форматируем дату и время
        return target_dt.strftime(format)
    except pytz.UnknownTimeZoneError:
        # Если указано неверное имя часового пояса, возвращаем исходное UTC время в формате
        return utc_dt.strftime(format)
    except Exception as e:
        # Обработка других возможных ошибок форматирования
        return f"Ошибка форматирования даты: {e}"


# --- Маршруты ---

# Маршрут для главной страницы
@app.route('/index')
@app.route('/')

def index():
    return render_template('index.html')

# Маршрут для страницы "О нас"
@app.route('/about')
def about():
    return render_template('about.html')

# Маршрут для страницы "Услуги"
@app.route('/services')
def services():
    return render_template('services.html')

# Маршрут для страницы "Контакты"
@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

# --- Маршрут для страницы "Медиа" (отображение постов) ---
@app.route('/media')
def media():
    # Получаем все посты из базы данных, сортируя их по дате создания в убывающем порядке (по UTC).
    # Сортировка по UTC корректна, даже если отображаем в другом поясе.
    all_posts = Post.query.order_by(Post.created_at.desc()).all()
    # Передаем список постов в шаблон media.html
    return render_template('media.html', posts=all_posts)

# Маршрут для страницы "Лейбл"
@app.route('/label')
def label():
    return render_template('label.html')


# --- Маршруты для аутентификации ---

# Маршрут для страницы входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Если пользователь уже авторизован, перенаправляем его на страницу медиа.
    if current_user.is_authenticated:
        return redirect(url_for('media'))

    # Обработка отправки формы входа (POST запрос)
    if request.method == 'POST':
        username = request.form.get('username') # Получаем имя пользователя из формы
        password = request.form.get('password') # Получаем пароль из формы

        # Ищем пользователя в базе данных по имени пользователя
        user = User.query.filter_by(username=username).first()

        # Проверяем, найден ли пользователь и совпадает ли пароль
        if user and user.check_password(password):
            login_user(user) # Авторизуем пользователя с помощью Flask-Login
            # Перенаправляем на страницу, которую пользователь пытался посетить до входа,
            # или на страницу медиа по умолчанию.
            next_page = request.args.get('next')
            return redirect(next_page or url_for('media'))
        else:
            # Если логин или пароль неверны, показываем flash-сообщение об ошибке.
            flash('Неверное имя пользователя или пароль.', 'danger')
            # Повторно отображаем шаблон входа, сохраняя введенное имя пользователя.
            return render_template('login.html', username=username)

    # Обработка GET запроса (просто отображение страницы входа)
    return render_template('login.html')


# Маршрут для выхода пользователя
@app.route('/logout')
# Декоратор @login_required требует, чтобы пользователь был авторизован для доступа к этому маршруту.
@login_required
def logout():
    logout_user() # Выходим из системы с помощью Flask-Login
    flash('Вы вышли из системы.', 'info') # Показываем flash-сообщение о выходе
    return redirect(url_for('index')) # Перенаправляем на главную страницу


# --- Маршрут для создания поста (с обработкой загрузки файла) ---
@app.route('/create', methods=['GET', 'POST'])
# Декоратор @login_required требует, чтобы пользователь был авторизован для доступа к этому маршруту.
@login_required
def create():
    # Обработка отправки формы создания поста (POST запрос)
    if request.method == 'POST':
        title = request.form.get('title') # Получаем заголовок из формы
        text = request.form.get('text') # Получаем текст из формы
        image = request.files.get('image') # Получаем загруженный файл изображения из формы

        image_filename = None # Инициализируем имя файла изображения как None

        # Проверяем, был ли файл загружен и имеет ли он имя (т.е. пользователь выбрал файл)
        if image and image.filename:
            # Проверяем, разрешено ли расширение файла
            if allowed_file(image.filename):
                # Генерируем безопасное имя файла, очищая его от потенциально опасных символов.
                original_filename = secure_filename(image.filename)
                # Генерируем уникальное имя файла, чтобы избежать конфликтов при загрузке файлов с одинаковыми именами.
                unique_filename = str(uuid.uuid4()) + '_' + original_filename
                # Формируем полный путь для сохранения файла.
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

                try:
                    image.save(filepath) # Сохраняем файл на сервере
                    image_filename = unique_filename # Сохраняем уникальное имя файла для записи в базу данных.
                except Exception as e:
                    # Если произошла ошибка при сохранении файла, показываем flash-сообщение.
                    flash(f'Ошибка при сохранении файла изображения: {e}', 'danger')
                    # Убеждаемся, что image_filename остается None, если сохранение не удалось.
                    image_filename = None

            else:
                # Если расширение файла не разрешено, показываем flash-сообщение.
                flash('Недопустимый формат файла изображения! Разрешены только PNG, JPG, JPEG, GIF.', 'warning')
                # image_filename остается None, пост будет создан без изображения.
                image_filename = None

        # Простая валидация: проверяем, что заголовок и текст не пустые.
        if not title or not text:
            flash('Заголовок и текст записи не могут быть пустыми!', 'warning')
            # Повторно отображаем шаблон создания поста, сохраняя введенные данные.
            return render_template('create.html', title=title, text=text)


        # Создаем новый объект Post.
        # Поле created_at установится автоматически благодаря default=datetime.utcnow.
        # Поле image_filename будет либо уникальным именем файла, либо None.
        post = Post(title=title, text=text, image_filename=image_filename)
        # Если добавили user_id: post = Post(title=title, text=text, image_filename=image_filename, author=current_user)


        try:
            # Добавляем новый пост в сессию базы данных.
            db.session.add(post)
            # Сохраняем изменения в базе данных.
            db.session.commit()
            # Показываем flash-сообщение об успешном создании поста.
            flash('Запись успешно создана!', 'success')
            # Перенаправляем пользователя на страницу медиа.
            return redirect(url_for('media'))

        except Exception as e:
            # Если произошла ошибка при сохранении в базу данных, откатываем изменения.
            db.session.rollback()
            # Показываем flash-сообщение об ошибке сохранения в БД.
            flash(f'При сохранении записи в базу данных произошла ошибка: {e}', 'danger')
            # Повторно отображаем шаблон создания поста, сохраняя введенные данные.
            return render_template('create.html', title=title, text=text)

    # Обработка GET запроса (просто отображение страницы создания поста)
    # --- ИСПРАВЛЕННЫЙ ОТСТУП ЭТОГО БЛОКА ---
    else:
        return render_template('create.html')

# --- НОВЫЙ МАРШРУТ ДЛЯ РЕДАКТИРОВАНИЯ ПОСТА ---
# Принимает ID поста в URL
@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required # Только авторизованные пользователи могут редактировать
def edit(post_id):
    # Ищем пост по ID. Если не найден, возвращаем ошибку 404.
    post = Post.query.get_or_404(post_id)

    # Опционально: Добавить проверку, является ли текущий пользователь автором поста, если вы добавили user_id в модель Post
    # if post.user_id != current_user.id:
    #    abort(403) # Запрещено

    if request.method == 'POST':
        # Получаем обновленные данные из формы
        post.title = request.form.get('title')
        post.text = request.form.get('text')
        image = request.files.get('image') # Получаем новый файл изображения

        # Проверяем, был ли установлен чекбокс "Удалить текущее изображение"
        delete_image_checked = request.form.get('delete_image') is not None

        # Если чекбокс установлен И у поста есть текущее изображение
        if delete_image_checked and post.image_filename:
            try:
                # Формируем полный путь к файлу изображения
                old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], post.image_filename)
                # Проверяем, существует ли файл перед удалением
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)  # Удаляем файл с диска
                    flash(f'Старое изображение "{post.image_filename}" удалено.', 'info')
                post.image_filename = None  # Очищаем поле в базе данных

            except Exception as e:
                flash(f'Ошибка при удалении старого файла изображения: {e}', 'danger')
                # Если удаление файла не удалось, image_filename остается прежним в объекте post

        # Обработка нового загруженного изображения (если оно есть)
        if image and image.filename:
            if allowed_file(image.filename):
                original_filename = secure_filename(image.filename)
                unique_filename = str(uuid.uuid4()) + '_' + original_filename
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                try:
                    # Удаляем старое изображение, если оно было
                    if post.image_filename:
                        old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], post.image_filename)
                        if os.path.exists(old_filepath):
                            os.remove(old_filepath)
                    image.save(filepath)  # Сохраняем новый файл
                    post.image_filename = unique_filename  # Обновляем имя файла в посте
                except Exception as e:
                    flash(f'Ошибка при сохранении нового файла изображения: {e}', 'danger')
            else:
                flash('Недопустимый формат файла изображения! Разрешены только PNG, JPG, JPEG, GIF.', 'warning')

        # Простая валидация обновленных данных
        if not post.title or not post.text:
            flash('Заголовок и текст записи не могут быть пустыми!', 'warning')
            # Возвращаем форму редактирования с текущими данными поста и сообщением об ошибке
            return render_template('edit.html', post=post)


        try:
            # Сохраняем изменения в базе данных. SQLAlchemy отслеживает изменения в объекте 'post'.
            db.session.commit()
            flash('Запись успешно обновлена!', 'success')
            # Перенаправляем на страницу медиа после успешного обновления
            return redirect(url_for('media'))

        except Exception as e:
            db.session.rollback() # Откатываем изменения при ошибке
            flash(f'При обновлении записи произошла ошибка: {e}', 'danger')
            # Возвращаем форму редактирования с текущими данными поста и сообщением об ошибке
            return render_template('edit.html', post=post)

    # Обработка GET запроса (отображение формы редактирования)
    # --- ИСПРАВЛЕННЫЙ ОТСТУП ЭТОГО БЛОКА ---
    else:
        # Передаем объект поста в шаблон edit.html для предзаполнения формы
        return render_template('edit.html', post=post)


# --- НОВЫЙ МАРШРУТ ДЛЯ УДАЛЕНИЯ ПОСТА ---
# Принимает ID поста в URL. Принимает только POST запросы для безопасности.
@app.route('/delete/<int:post_id>', methods=['POST'])
@login_required # Только авторизованные пользователи могут удалять
def delete(post_id):
    # Ищем пост по ID. Если не найден, возвращаем ошибку 404.
    post = Post.query.get_or_404(post_id)

    # Опционально: Добавить проверку, является ли текущий пользователь автором поста
    # if post.user_id != current_user.id:
    #    abort(403) # Запрещено

    try:
        # Удаляем связанное изображение с диска, если оно существует
        if post.image_filename:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], post.image_filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                flash(f'Изображение "{post.image_filename}" удалено.', 'info')


        # Удаляем пост из сессии базы данных
        db.session.delete(post)
        # Сохраняем изменения (фиксируем удаление)
        db.session.commit()
        flash('Запись успешно удалена!', 'success')
        # Перенаправляем на страницу медиа после удаления
        return redirect(url_for('media'))

    except Exception as e:
        db.session.rollback() # Откатываем изменения при ошибке
        flash(f'При удалении записи произошла ошибка: {e}', 'danger')
        # При ошибке удаления, возвращаемся на страницу медиа
        return redirect(url_for('media'))


# --- Маршрут для регистрации (опционально) ---
# Этот маршрут закомментирован, так как вы планируете создавать пользователей вручную.
# Если решите добавить регистрацию, раскомментируйте и реализуйте логику.
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     # ... (логика регистрации) ...
#     pass


# --- Запуск приложения ---
if __name__ == '__main__':
    # !!! ВАЖНО: После добавления или изменения полей в моделях (User, Post и др.),
    # необходимо обновить структуру таблиц в базе данных.
    # Если вы не используете Flask-Migrate, самый простой способ для этапа разработки -
    # удалить существующий файл базы данных (dope_music.db)
    # и заново выполнить db.create_all() в Python консоли из активированного виртуального окружения:
    # from app import app, db
    # with app.app_context():
    #     db.create_all() # Создаст или обновит таблицы, включая новые поля
    #     # Не забудьте при необходимости заново создать пользователя(ей) вручную
    #     # после удаления старой базы данных!

    # Запуск Flask-приложения в режиме отладки на порту 5001.
    # debug=True позволяет видеть подробные ошибки в браузере и автоматически перезагружать сервер при изменениях кода.
    # port=5001 указывает, на каком порту запустить сервер.
    app.run(debug=True, port=5001)
