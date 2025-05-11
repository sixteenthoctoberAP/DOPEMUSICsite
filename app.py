from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os # Добавляем импорт os для получения SECRET_KEY

app = Flask(__name__)

# --- Конфигурация приложения ---
# Используем SQLite базу данных, она будет создана в корне проекта
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dope_music.db' # Изменил имя файла БД
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Рекомендуется отключить для производительности
# !!! ОЧЕНЬ ВАЖНО: Установите надежный случайный секретный ключ!
# Можно сгенерировать, например, в Python: import os; os.urandom(24).hex()
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'ВАШ_ОЧЕНЬ_НАДЕЖНЫЙ_И_СЛУЧАЙНЫЙ_СЕКРЕТНЫЙ_КЛЮЧ' # <-- Замените это!

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Указываем имя функции маршрута для входа
login_manager.login_message = 'Для доступа к этой странице необходимо авторизоваться.' # Сообщение при перенаправлении
login_manager.login_message_category = 'info' # Класс для сообщения (для Bootstrap)


# --- Модель пользователя ---
# Описывает структуру таблицы 'user' в базе данных
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # Уникальный ID пользователя
    username = db.Column(db.String(100), unique=True, nullable=False) # Логин пользователя (уникальный, обязательный)
    password_hash = db.Column(db.String(200), nullable=False) # Хеш пароля (обязательный)

    # Метод для установки хешированного пароля
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Метод для проверки пароля
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Метод для удобного отображения объекта пользователя (для отладки)
    def __repr__(self):
        return f'<User {self.username}>'

# --- Модель поста ---
# Описывает структуру таблицы 'post' в базе данных
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Уникальный ID поста
    title = db.Column(db.String(100), nullable=False) # Заголовок поста (обязательный)
    text = db.Column(db.Text, nullable=False) # Текст поста (обязательный, тип Text для длинного текста)
    # Опционально: добавляем связь с пользователем, который создал пост
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # author = db.relationship('User', backref=db.backref('posts', lazy=True)) # Создает атрибут 'author' у поста и 'posts' у пользователя

    # Метод для удобного отображения объекта поста (для отладки)
    def __repr__(self):
        return f'<Post {self.title}>'


# --- Функция загрузки пользователя для Flask-Login ---
# Эта функция вызывается Flask-Login при каждом запросе для получения пользователя по его ID из сессии
@login_manager.user_loader
def load_user(user_id):
    # user_id здесь - это строка, Flask-Login сам передает его как строку
    return User.query.get(int(user_id)) # Ищем пользователя в базе по ID

# --- Ваши существующие маршруты ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

# *** Изменяем маршрут /media, чтобы он получал все посты ***
@app.route('/media')
def media():
    # Получаем все посты из базы данных, отсортированные по ID в обратном порядке (новые сверху)
    all_posts = Post.query.order_by(Post.id.desc()).all()
    # Передаем посты в шаблон media.html под именем 'posts'
    return render_template('media.html', posts=all_posts)

@app.route('/label')
def label():
    return render_template('label.html')


# --- Новые маршруты для аутентификации ---

# Маршрут для страницы входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('media'))

    if request.method == 'POST':
        # Получаем данные из формы входа
        username = request.form.get('username') # Используем .get() для безопасного доступа
        password = request.form.get('password')

        # Ищем пользователя в базе по имени
        user = User.query.filter_by(username=username).first()

        # Проверяем, найден ли пользователь и правильный ли пароль
        if user and user.check_password(password):
            # Если все верно, авторизуем пользователя с помощью Flask-Login
            login_user(user) # Можно добавить remember=True для "запомнить меня"
            # Перенаправляем пользователя на страницу, которую он пытался посетить до входа,
            # или на главную страницу по умолчанию
            next_page = request.args.get('next')
            return redirect(next_page or url_for('media'))
        else:
            # Если имя пользователя или пароль неверны, показываем сообщение
            flash('Неверное имя пользователя или пароль.', 'danger') # 'danger' - класс для стилизации (например, Bootstrap)
            # Возвращаем форму входа, можно передать введенный логин для удобства
            return render_template('login.html', username=username)

    # Если метод запроса GET, просто показываем форму входа
    return render_template('login.html') # Вам нужно создать этот файл шаблона


# Маршрут для выхода
@app.route('/logout')
@login_required # Этот декоратор требует, чтобы пользователь был авторизован для доступа к этому маршруту
def logout():
    # Выходим из системы с помощью Flask-Login
    logout_user()
    # Показываем сообщение о выходе
    flash('Вы вышли из системы.', 'info') # 'info' - класс для стилизации (например, Bootstrap)
    # Перенаправляем на главную страницу (или страницу входа)
    return redirect(url_for('index'))


# Маршрут для создания поста (ТЕПЕРЬ ЗАЩИЩЕН)
@app.route('/create', methods=['GET', 'POST'])
@login_required # Этот декоратор требует, чтобы пользователь был авторизован для доступа к этому маршруту
def create():
    # Если метод запроса POST (форма отправлена)
    if request.method == 'POST':
        # Получаем данные из формы
        title = request.form.get('title')
        text = request.form.get('text')

        # Простая валидация
        if not title or not text:
            flash('Заголовок и текст записи не могут быть пустыми!', 'warning') # 'warning' - класс для стилизации
            # Возвращаем форму с уже введенными данными
            return render_template('create.html', title=title, text=text)

        # Создаем новый объект Post
        # Если добавили user_id: post = Post(title=title, text=text, author=current_user)
        post = Post(title=title, text=text)

        try:
            # Добавляем пост в сессию базы данных и сохраняем изменения
            db.session.add(post)
            db.session.commit()
            # Показываем сообщение об успехе
            flash('Запись успешно создана!', 'success') # 'success' - класс для стилизации
            # Перенаправляем на страницу, где отображаются посты (например, /media)
            return redirect(url_for('media')) # Использовать 'media', т.к. посты показываются там

        except Exception as e:
            # Если произошла ошибка при сохранении в БД
            db.session.rollback() # Откатываем изменения
            flash(f'При создании записи произошла ошибка: {e}', 'danger') # Показываем сообщение об ошибке
            # Возвращаем форму с введенными данными
            return render_template('create.html', title=title, text=text) # Возвращаем форму с данными

    # Если метод запроса GET (просто открываем страницу)
    else:
        # Показываем пустую форму создания поста
        return render_template('create.html') # Вам нужно создать этот файл шаблона


# --- Маршрут для регистрации (опционально) ---
# Если вы хотите дать пользователям возможность самостоятельно регистрироваться.
# Если нет, вы можете создавать пользователей вручную через Python консоль.
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('index')) # Если пользователь уже вошел, перенаправляем

#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')

#         user = User.query.filter_by(username=username).first() # Проверяем, нет ли пользователя с таким именем

#         if user:
#             flash('Пользователь с таким именем уже существует.', 'warning')
#             return render_template('register.html', username=username)

#         # Создаем нового пользователя
#         new_user = User(username=username)
#         new_user.set_password(password) # Устанавливаем хешированный пароль

#         try:
#             db.session.add(new_user)
#             db.session.commit()
#             flash('Регистрация успешна! Теперь вы можете войти.', 'success')
#             return redirect(url_for('login')) # Перенаправляем на страницу входа
#         except Exception as e:
#             db.session.rollback()
#             flash(f'Произошла ошибка при регистрации: {e}', 'danger')
#             return render_template('register.html', username=username)

#     return render_template('register.html') # Вам нужно создать этот файл шаблона


# --- Запуск приложения ---
if __name__ == '__main__':
    # !!! ВАЖНО: Перед первым запуском приложения или после ЛЮБЫХ изменений в моделях (User, Post и др.)
    # необходимо создать или обновить структуры таблиц в базе данных.
    # Выполните следующие команды в Python консоли (активировав виртуальное окружение .venv):
    # from app import app, db
    # with app.app_context():
    #     db.create_all() # Создаст таблицы User и Post в файле dope_music.db
    #     # После первого создания базы, если вы захотите добавить пользователя вручную:
    #     # admin = User(username='admin') # Создаем объект пользователя
    #     # admin.set_password('ваш_безопасный_пароль') # Устанавливаем пароль (замените 'ваш_безопасный_пароль')
    #     # db.session.add(admin) # Добавляем пользователя в сессию
    #     # db.session.commit() # Сохраняем изменения в базе

    app.run(debug=True, port=5001) # Запускаем приложение в режиме отладки