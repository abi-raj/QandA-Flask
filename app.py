from flask import Flask, render_template, g, request, session, redirect
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def get_current_user():
    user_result = None
    if 'user' in session:
        user = session['user']
        db = get_db()
        user_cur = db.execute('select * from users where name=?', [user])
        user_result = user_cur.fetchone()

    return user_result


@app.route('/')
def index():
    user = get_current_user()
    db = get_db()
    q_cur = db.execute('select questions.id,questions.question,askers.name as a_name,experts.name as e_name from questions join users as askers  on askers.id=questions.asked_by_id join users as experts on experts.id=questions.expert_id where questions.answer is not null')
    q_res = q_cur.fetchall()
    return render_template('home.html', user=user, questions=q_res)


@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()
    if request.method == 'POST':
        db = get_db()
        hashed = generate_password_hash(
            request.form['password'], method='sha256')
        print(hashed)
        db.execute('insert into users (name,password,expert,admin) values (?,?,?,?)', [
                   request.form['name'], hashed, '0', '0'])
        db.commit()

        session['user'] = request.form['name']
        return redirect('/')

    return render_template('register.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    user = get_current_user()
    if request.method == 'POST':
        db = get_db()
        name = request.form['name']
        password = request.form['password']
        user_cursor = db.execute(
            'select id,name,password from users where name = ?', [name])
        user_result = user_cursor.fetchone()
        if user_result is None:
            return render_template('login.html', error='User not found')
        if check_password_hash(user_result['password'], password):
            print(user_result['name'])
            session['user'] = user_result['name']
            return redirect('/')
        else:
            return render_template('login.html', error='Incorrect password')

    return render_template('login.html', user=user)


@app.route('/question/<question_id>')
def question(question_id):
    user = get_current_user()
    db = get_db()
    q_cur = db.execute(
        'select questions.question,questions.answer,askers.name as a_name,experts.name as e_name from questions join users as askers  on askers.id=questions.asked_by_id join users as experts on experts.id=questions.expert_id where questions.id = ?', [question_id])
    q_res = q_cur.fetchone()
    return render_template('question.html', user=user, question=q_res)


@app.route('/answer/<question_id>', methods=['GET', 'POST'])
def answer(question_id):
    user = get_current_user()
    if user is None:
        return redirect('/login')
    db = get_db()
    if request.method == 'POST':
        print(question_id)
        db.execute('update questions set answer=? where id=?',
                   [request.form['answer'], question_id])
        db.commit()
        return redirect('/')
    question_cur = db.execute(
        'select id,question from questions where id =?', [question_id])
    question_result = question_cur.fetchone()
    return render_template('answer.html', user=user, question=question_result)


@app.route('/ask', methods=['GET', 'POST'])
def ask():
    user = get_current_user()
    if user is None:
        return redirect('/login')
    db = get_db()
    if request.method == 'POST':
        db.execute('insert into questions(question,asked_by_id,expert_id) values(?,?,?)', [
                   request.form['question'], user['id'], request.form['expert']])
        db.commit()
        return redirect('/')

    exp_cur = db.execute('select id,name from users where expert=1')
    expert_result = exp_cur.fetchall()
    return render_template('ask.html', user=user, experts=expert_result)


@app.route('/unanswered')
def unanswered():
    user = get_current_user()
    if user is None:
        return redirect('/login')
    if user['expert'] == 0:
        return redirect('/')
    db = get_db()
    unanswered_cur = db.execute(
        'select * from questions join users on users.id =questions.asked_by_id where questions.answer is null and questions.expert_id=?', [user['id']])
    unanswered_result = unanswered_cur.fetchall()
    print(unanswered_result)
    return render_template('unanswered.html', user=user, questions=unanswered_result)


@app.route('/promote/<user_id>')
def promote(user_id):
    user = get_current_user()
    if user is None:
        return redirect('/login')
    if user['admin'] == 0:
        return redirect('/')
    db = get_db()
    db.execute('update users set expert=1 where id=?', [user_id])
    db.commit()
    return redirect('/')


@app.route('/users')
def users():
    user = get_current_user()
    if user is None:
        return redirect('/login')
    if user['admin'] == 0:
        return redirect('/')
    db = get_db()
    users_cur = db.execute('select id,name,expert,admin from users')
    users_result = users_cur.fetchall()
    return render_template('users.html', user=user, users=users_result)


@app.route('/logout')
def logout():

    session.pop('user', None)
    return redirect('/')


@app.route('/ipl')
def ipl():
    return render_template('ipl.html')

if __name__ == '__main__':
    app.run(debug=True)
