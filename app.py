from flask import Flask, render_template, flash, session, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from flask_ckeditor import CKEditor
import yaml, os

app = Flask(__name__)
Bootstrap(app)
CKEditor(app)

# DB configuration
db = yaml.safe_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = os.urandom(24)
mysql = MySQL(app)

@app.route('/')
def index():
    cursor = mysql.connection.cursor()
    result_value = cursor.execute('SELECT * FROM blog;')
    if result_value > 0:
        blogs = cursor.fetchall()
        cursor.close()
        return render_template('index.html', blogs=blogs)
    return render_template('index.html', blogs=None)

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/blog/<int:id>')
def blog(id):
    cursor = mysql.connection.cursor()
    result_value = cursor.execute('SELECT * FROM blog WHERE blog_id=%s;', (id,))
    if result_value > 0:
        blog = cursor.fetchone()
        return render_template('blog.html', blog=blog)
    return flash('Block is not found!', 'warning')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_details = request.form
        if user_details['password'] != user_details['confirmPassword']:
            flash('Пароли не совпадают! TRY AGAIN!!!', 'danger')
            return render_template('register.html')
        cursor = mysql.connection.cursor()
        tuple_data = (
            user_details['firstname'],
            user_details['lastname'],
            user_details['username'],
            user_details['email'],
            generate_password_hash(user_details['password'])
        ) # it's my tuple
        cursor.execute('INSERT INTO user(first_name, last_name, username, email, password) VALUES(%s, %s, %s, %s, %s);', tuple_data)
        cursor.connection.commit()
        cursor.close()
        flash('Вы успешно зарегистрировались! Можете залогиниться!!!', 'success')
        return redirect(url_for('login')) # it's my

    return render_template('register.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_details = request.form
        username = user_details['username']
        password = user_details['password']
        cursor = mysql.connection.cursor()
        result_value = cursor.execute("SELECT * FROM user WHERE username=%s;", (username,))
        if result_value > 0:
            user = cursor.fetchone()
            if check_password_hash(user['password'], password):
                session['login'] = True
                session['first_name'] = user['first_name']
                session['last_name'] = user['last_name']
                flash('Welcome ' + session['first_name'] + '! You have been successfully logged in!', 'success')
                cursor.close()
                return redirect(url_for('index'))
            else:
                cursor.close()
                flash('Password is incorrect!', 'danger')
                return redirect(url_for('login'))
        else:
            cursor.close()
            flash('User does not exist!', 'danger')
            return redirect(url_for('login'))


    return render_template('login.html')

@app.route('/write-blog/', methods=['GET', 'POST'])
def write_blog():
    if request.method == 'POST':
        if 'login' in session:
            if session['login']:
                blogpost = request.form
                title = blogpost['title']
                body = blogpost['body']
                if title and body:
                    author = session['first_name'] + ' ' + session['last_name']
                    tuple_blog = (title, author, body)
                    cursor = mysql.connection.cursor()
                    cursor.execute('INSERT INTO blog(title, author, body) VALUES(%s, %s, %s);', tuple_blog)
                    cursor.connection.commit()
                    cursor.close()
                    flash('Your blogpost is successfully posted!', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Вы не заполнили title или body!!!', 'warning')
        else:
            flash('Дебил сперва надо ЗАЛОГИНИТЬСЯ !!!', 'secondary')
    return render_template('write-blog.html')

@app.route('/my-blogs/')
def my_blogs():
    author = session['first_name'] + ' ' + session['last_name']
    cursor = mysql.connection.cursor()
    result_value = cursor.execute('SELECT * FROM blog WHERE author=%s;', (author,))
    if result_value > 0:
        my_blogs = cursor.fetchall()
        cursor.close()
        return render_template('my-blogs.html', blogs=my_blogs)
    else:
        return render_template('my-blogs.html', blogs=None)

@app.route('/edit-blog/<int:id>', methods=['GET', 'POST'])
def edit_blog(id):
    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        title = request.form['title']
        body = request.form['body']
        cursor.execute('UPDATE blog SET title=%s, body=%s WHERE blog_id=%s;', (title, body, id))
        cursor.connection.commit()
        cursor.close()
        flash('Blog is updated successfully!', 'success')
        return redirect(f'/blog/{id}')
    cursor = mysql.connection.cursor()
    result_value = cursor.execute('SELECT * FROM blog WHERE blog_id=%s;', (id,))
    if result_value > 0:
        edit_blog = cursor.fetchone()
        cursor.close()
        blog_form = {}
        blog_form['title'] = edit_blog['title']
        blog_form['body'] = edit_blog['body']
        return render_template('edit-blog.html', blog_form=blog_form)

@app.route('/delete-blog/<int:id>')
def delete_blog(id):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM blog WHERE blog_id=%s;', (id,))
    cursor.connection.commit()
    cursor.close()
    flash('Твой блок успешно удален!', 'success')
    return redirect(url_for('my_blogs'))

@app.route('/logout/')
def logout():
    session.clear()
    flash('Ты вышел из аккаунта:(', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)