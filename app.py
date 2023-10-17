import os
import secrets
import sqlite3

import openpyxl as openpyxl
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'C:\\Users\\Pavel\PycharmProjects\\flaskProject1\\upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
bootstrap = Bootstrap(app)


@app.route('/register')
def registration():
    return render_template('register.html', )


@app.route('/')
def home():
    return render_template('login.html')


@app.route('/code', methods=['GET'])
def get_code():
    role = request.args.get('role')
    name = request.args.get('name')
    password = request.args.get('password')
    company = request.args.get('company')

    if role == 'HR' or role == 'admin':
        return render_template('code.html', role=role, name=name, password=password, company=company)
    else:
        return redirect(url_for('register'))


@app.route('/submit-code', methods=['POST'])
def submit_code():
    role = request.form['role']
    code = request.form['code']

    if role == 'HR' and code != '888':
        return 'Invalid code'
    elif role == 'admin' and code != '777':
        return 'Invalid code'

    name = request.args.get('name')
    password = request.args.get('password')
    company = request.args.get('company')

    print(name, password, role, company)
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''INSERT INTO users (name, password, role, company)
                     VALUES (?, ?, ?, ?)''', (name, password, role, company))
    conn.commit()
    conn.close()
    return render_template('login.html', message="Регистрация прошла успешно, выполните вход: ")


@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    password = request.form['password']
    role = request.form['role']
    company = request.form['company']
    if role == 'HR' or role == 'admin':
        return redirect(url_for('get_code', role=role, name=name, password=password, company=company))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''INSERT INTO users (name, password, role, company)
                 VALUES (?, ?, ?, ?)''', (name, password, role, company))
    conn.commit()
    conn.close()

    return render_template('login.html', message="Регистрация прошла успешно, выполните вход: ")


@app.route('/dashboard')
def dashboard():
    role = session.get('user_role')
    if role == 'HR':
        return redirect(url_for('users_hr'))
    elif role == 'Работник':
        return render_template('dashboard.html')
    elif role == 'admin':
        return render_template('admin_panel.html')
    else:
        return redirect(url_for('home'))


@app.route('/users_hr')
def users_hr():
    criteria_list = ['Критерий 3', 'Критерий 4']

    if session.get('user_role') != 'HR':
        return redirect(url_for('home'))


    hr_company = session.get('company')


    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''SELECT name, company, id FROM users WHERE role="Работник" AND company=?''', (hr_company,))
    users = c.fetchall()
    conn.close()



    return render_template('users_hr.html', users=users, criteria_list=criteria_list, hr_company=hr_company)


@app.route('/give_points', methods=['POST'])
def give_points():
    criteria_list = ['Критерий 3', 'Критерий 4']
    user_id = request.form.get('user_id')
    scores = []
    for criteria in criteria_list:
        if criteria == 'Критерий 4':
            try:
                score = 1.33 * (int(request.form.get(f"{user_id}_{criteria}_1")) + int(
                    request.form.get(f"{user_id}_{criteria}_2")))
            except Exception:
                score = -2

        elif criteria == 'Критерий 3':
            score = -2
            for file in request.files.getlist('3'):
                if file:
                    # filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{user_id}_{criteria}_{file.filename}"))
                    score = -1
        else:
            score = int(request.form.get(f"{criteria}"))
        scores.append((criteria, int(score)))
    evaluator_id = session['user_id']
    if scores:
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            for criteria, score in scores:
                c.execute('''DELETE FROM scores WHERE user_id = ? AND criteria = ? AND score = -2''',
                          (user_id, criteria,))
                c.execute('''INSERT INTO scores (user_id, criteria, score, evaluator_id) VALUES (?, ?, ?, ?)''',
                          (user_id, criteria, score, evaluator_id))
            conn.commit()
    return redirect(url_for('users_hr'))


@app.route('/criteria_2_user', methods=['GET', 'POST'])
def criteria_2_user():
    if request.method == 'POST':
        try:
            file_1 = request.files.get('file1')
            file_2 = request.files.get('file2')
            file_1.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{session['user_id']}_Критерий 2_{file_1.filename}"))
            file_2.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{session['user_id']}_Критерий 2_{file_2.filename}"))
            with sqlite3.connect('database.db') as conn:
                c = conn.cursor()
                c.execute('''SELECT 1 FROM scores WHERE user_id = ? AND criteria = ? ''',
                          (session['user_id'], 'Критерий 2'))
                exists = c.fetchone()
                if exists:
                    c.execute('''DELETE FROM scores WHERE user_id = ? AND criteria = ?''',
                              (session['user_id'], 'Критерий 2'))
                c.execute('''INSERT INTO scores (user_id, criteria, score, evaluator_id) VALUES (?, ?, ?, ?)''',
                          (session['user_id'], 'Критерий 2', -1, session['user_id']))
                conn.commit()
            return render_template('criteria_2_user.html', message='Файлы успешно отправлены на проверку')

        except Exception:
            return render_template('criteria_2_user.html', message='Не удалось загрузить файлы')
    else:
        return render_template('criteria_2_user.html')


@app.route('/criteria_5_user', methods=['GET', 'POST'])
def criteria_5_user():
    if request.method == 'POST':
        user_id = session['user_id']
        answered_yes_1 = request.form.get('speaker_event') == 'Да'
        answered_yes_2 = request.form.get('participated_this_year') == 'Да'
        file_1 = request.files.get('certificate_file')
        file_2 = request.files.get('program_file')

        scores = []
        if answered_yes_1 and answered_yes_2:
            if file_1:
                # filename = secure_filename(file_1.filename)
                file_1.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{user_id}_Критерий5_{file_1.filename}"))
                scores.append(('file_1', 5))

            if file_2:
                # filename = secure_filename(file_2.filename)
                file_2.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{user_id}_Критерий5_{file_2.filename}"))
                scores.append(('file_2', 5))

        if len(scores) == 2:
            evaluator_id = session['user_id']
            with sqlite3.connect('database.db') as conn:
                c = conn.cursor()
                c.execute('''SELECT 1 FROM scores WHERE user_id = ? AND criteria = ? ''',
                          (user_id, 'Критерий 5'))
                exists = c.fetchone()
                if exists:
                    c.execute('''DELETE FROM scores WHERE user_id = ? AND criteria = ?''',
                              (user_id, 'Критерий 5'))
                c.execute('''INSERT INTO scores (user_id, criteria, score, evaluator_id) VALUES (?, ?, ?, ?)''',
                          (user_id, 'Критерий 5', 10, evaluator_id))
                conn.commit()

            return render_template('criteria_5_user.html',
                                   message='Спасибо, документы приняты и балл по критерию 5 добавлен.')

    return render_template('criteria_5_user.html')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# @app.route('/users')
# def users():
#     conn = sqlite3.connect('database.db')
#     c = conn.cursor()
#     c.execute('''SELECT name, company FROM users''')
#     users = c.fetchall()
#     conn.close()
#     return render_template('users.html', users=users)
@app.route('/users')
def users():

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT id, name FROM users WHERE role = "Работник"')
    temp = c.fetchall()
    users = []

    for user_id, name in temp:
        row = [user_id]
        for criterion in ['Критерий 1', 'Критерий 2', 'Критерий 3', 'Критерий 4', 'Критерий 5']:
            c.execute('SELECT score FROM scores WHERE user_id=? AND criteria=?', (user_id, criterion))
            score = c.fetchone()
            row.append(score[0] if score is not None and score[0] >= 0 else '-')
        row.append(sum(max(score[0], 0) for score in c.execute('SELECT score FROM scores WHERE user_id=?', (user_id,))))
        users.append(row)
    users.sort(key=lambda x: x[-1], reverse=True)

    conn.close()

    return render_template('users.html', users=users)




@app.route('/points')
def points():
    user_id = session.get('user_id')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''SELECT criteria, score FROM scores WHERE user_id = ?''', (user_id,))
    scores = c.fetchall()
    conn.close()
    return render_template('points.html', scores=scores)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''SELECT * FROM users WHERE name = ? AND password = ?''',
                  (name, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_role'] = user[3]
            session['company'] = user[4]
            # f'Hello {session["user_name"]} from {session["company"]} which is {session["user_role"]}'
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid login details'

    return render_template('login.html')


def find_info_for_everyone(file_path):
    workbook = openpyxl.load_workbook(file_path)
    worksheet = workbook.active

    fio_column = worksheet['A']
    event_column = worksheet['B']
    activation_column = worksheet['C']
    end_column = worksheet['D']
    points_column = worksheet['E']
    status_column = worksheet['F']

    result = []
    for i in range(1, worksheet.max_row):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        str1 = fio_column[i].value
        query = "SELECT * FROM users WHERE name = '{}'".format(str1)
        cursor.execute(query)
        results = cursor.fetchall()
        if len(results) == 0:
            break
        fio = fio_column[i].value
        res_list = list(results[0])
        if len(res_list) > 0:
            id = res_list[0]
        else:
            id = None
        # id = results[0] - > works if table is not shit
        event = event_column[i].value
        points = list(map(str, points_column[i].value.split(' ')))
        percent = points[0]
        # print(points)
        status = status_column[i].value
        result_string = f"{event};{percent};{status}"
        result.append((id, result_string))
        conn.close()
    return result


@app.route('/upload_test', methods=['GET', 'POST'])
def upload_test():
    if request.method == 'POST':
        try:
            criteria_name = request.form.get('criteria_name')
            uploaded_file = request.files.get('file')
            filepath = UPLOAD_FOLDER + f"\\{session['user_id']}_{criteria_name}_{uploaded_file.filename}"
            uploaded_file.save(
                os.path.join(app.config['UPLOAD_FOLDER'],
                             f"{session['user_id']}_{criteria_name}_{uploaded_file.filename}"))
            data_list = find_info_for_everyone(filepath)
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            for data in data_list:
                cur.execute('''INSERT INTO posts (title, content, user_id) VALUES (?, ?, ?)''',
                            (criteria_name, data[1], data[0]))
            conn.commit()
            conn.close()
            return render_template('upload_test.html', message="Файл успешно загружен. ")
        except Exception:
            return render_template('upload_test.html', message="Ошибка при загрузке файла")

    return render_template('upload_test.html')


@app.route("/admin_criteria_1", methods=["GET", "POST"])
def admin_criteria_1():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":

        user_id = request.form["user_id"]
        score = request.form["score"]

        c.execute(
            """
            UPDATE scores
            SET score = score + ?
            WHERE user_id = ? AND criteria = 'Критерий 1'
            """,
            (score, user_id),
        )

        if c.rowcount == 0:
            c.execute(
                """
                INSERT INTO scores (user_id, criteria, score, evaluator_id)
                VALUES (?, 'Критерий 1', ?, ?)
                """,
                (user_id, score, 0),
            )

        c.execute(
            """
            DELETE FROM posts
            WHERE title = 'Критерий 1' AND user_id = ?
            """,
            (user_id,),
        )

        conn.commit()
        conn.close()

    c.execute(
        """
        SELECT user_id, content
        FROM posts
        WHERE title = 'Критерий 1'
        """
    )
    rows = c.fetchall()
    conn.close()

    return render_template("admin_criteria_1.html", posts=rows)


@app.route("/admin_criteria_2")
def admin_criteria_2():
    return render_template("admin_criteria_2.html")




def find_by_criterion(criterion_num):
    dict_ans = dict()
    path = UPLOAD_FOLDER
    files = os.listdir(path)
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            path_to_file = os.path.join(dirpath, filename)
            while (path_to_file.find('\\') != -1):  # разворот /  пути к файлу
                x = path_to_file.find('\\')
                path_to_file = path_to_file[:x] + '/' + path_to_file[x + 1:]
            last_slash = path_to_file.rfind('/')
            name_of_file = path_to_file[last_slash + 1:]
            parced = list(map(str, name_of_file.split('_')))
            # print(parced)
            if (parced[1] == criterion_num):
                if (dict_ans.__contains__(parced[0])):
                    dict_ans[parced[0]].append(path_to_file)
                else:
                    dict_ans[parced[0]] = list()
                    dict_ans[parced[0]].append(path_to_file)
    return dict_ans

@app.route("/admin_criteria_3", methods=["GET", "POST"])
def admin_criteria_3():
    user_files = find_by_criterion("Критерий 3")
    users = []
    files = []
    for user_id, file_list in user_files.items():
        users.append([user_id, file_list])
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        scores = request.form.to_dict()
        total_score = sum(int(score) for score in scores.values()) - int(user_id)
        conn = sqlite3.connect("database.db")
        db = conn.cursor()
        db.execute(
            """
            UPDATE scores
            SET score = score + ?
            WHERE user_id = ? AND criteria = 'Критерий 3'
            """,
            (total_score, user_id),
        )

        if db.rowcount == 0:
            db.execute(
                """
                INSERT INTO scores (user_id, criteria, score, evaluator_id)
                VALUES (?, 'Критерий 3', ?, ?)
                """,
                (user_id, total_score, 0),
            )
        for file_path in user_files[user_id]:
            os.remove(file_path)
        conn.commit()
        conn.close()
    return render_template('admin_criteria_3.html', users=users)
@app.route("/admin_criteria_2_check", methods=["GET", "POST"])
def admin_criteria_2_check():
    user_files = find_by_criterion("Критерий 2")
    users = []
    files = []
    for user_id, file_list in user_files.items():
        users.append([user_id, file_list])
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        scores = request.form.to_dict()
        total_score = sum(int(score) for score in scores.values()) - int(user_id)
        conn = sqlite3.connect("database.db")
        db = conn.cursor()
        db.execute(
            """
            UPDATE scores
            SET score = score + ?
            WHERE user_id = ? AND criteria = 'Критерий 2'
            """,
            (total_score, user_id),
        )

        if db.rowcount == 0:
            db.execute(
                """
                INSERT INTO scores (user_id, criteria, score, evaluator_id)
                VALUES (?, 'Критерий 2', ?, ?)
                """,
                (user_id, total_score, 0),
            )
        for file_path in user_files[user_id]:
            os.remove(file_path)
        conn.commit()
        conn.close()
    return render_template('criteria_2_check.html', users=users)



@app.route("/admin_criteria_2_test", methods=["GET", "POST"])
def admin_criteria_2_test():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":

        user_id = request.form["user_id"]
        score = request.form["score"]

        c.execute(
            """
            UPDATE scores
            SET score = score + ?
            WHERE user_id = ? AND criteria = 'Критерий 2'
            """,
            (score, user_id),
        )

        if c.rowcount == 0:
            c.execute(
                """
                INSERT INTO scores (user_id, criteria, score, evaluator_id)
                VALUES (?, 'Критерий 2', ?, ?)
                """,
                (user_id, score, 0),
            )

        c.execute(
            """
            DELETE FROM posts
            WHERE title = 'Критерий 2' AND user_id = ?
            """,
            (user_id,),
        )

        conn.commit()
        conn.close()

    c.execute(
        """
        SELECT user_id, content
        FROM posts
        WHERE title = 'Критерий 2'
        """
    )
    rows = c.fetchall()
    conn.close()

    return render_template("admin_criteria_2_test.html", posts=rows)


app.secret_key = secrets.token_hex(16)
if __name__ == '__main__':
    app.run(debug=False)
