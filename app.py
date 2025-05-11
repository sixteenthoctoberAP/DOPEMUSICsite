from flask import Flask, render_template, url_for # Убедитесь, что url_for импортирован

app = Flask(__name__) # Убедитесь, что приложение создано

# Маршрут для главной страницы (уже есть)
@app.route('/')
def index(): # Endpoint: 'index'
    return render_template('index.html')

# *** Вам нужно добавить следующие маршруты: ***

# Маршрут для страницы "Услуги"
@app.route('/services') # Вы можете выбрать любой URL-путь, например, /services
def services(): # Endpoint: 'services' - имя совпадает с тем, что в url_for
    return render_template('services.html') # Замените 'services.html' на имя вашего файла шаблона для услуг

# Маршрут для страницы "О нас"
@app.route('/about') # Например, /about
def about(): # Endpoint: 'about'
    return render_template('about.html') # Шаблон для "О нас"

# Маршрут для страницы "Контакты"
@app.route('/contacts') # Например, /contacts
def contacts(): # Endpoint: 'contacts'
    return render_template('contacts.html') # Шаблон для "Контакты"

# Маршрут для страницы "Медиа"
@app.route('/media') # Например, /media
def media(): # Endpoint: 'media'
    return render_template('media.html') # Шаблон для "Медиа"

@app.route('/create') # Выберите URL-путь для этой страницы
def create(): # Имя этой функции ('create') ДОЛЖНО совпадать с именем в url_for('create')
    return render_template('create.html') # Укажите имя файла шаблона для страницы создания записи

# Маршрут для страницы "Лейбл"
@app.route('/label') # Например, /label
def label(): # Endpoint: 'label'
    return render_template('label.html') # Шаблон для "Лейбл"


# Убедитесь, что ваш app.run() находится в блоке if __name__ == '__main__':
if __name__ == '__main__':
    app.run(debug=True, port=5001) # debug=True полезно во время разработки