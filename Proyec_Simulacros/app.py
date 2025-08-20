from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from database import app, db, init_database
from models import User, Question, TestResult, TestAnswer
import bcrypt
import random
from datetime import datetime

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado')
            return redirect(url_for('register'))
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user = User(username=username, email=email, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        
        flash('Registro exitoso. Por favor inicia sesión.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_results = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.completed_at.desc()).limit(5).all()
    return render_template('dashboard.html', results=user_results)

@app.route('/select_test')
@login_required
def select_test():
    return render_template('test_selection.html')

@app.route('/start_test/<test_type>')
@login_required
def start_test(test_type):
    if test_type not in ['ICFES', 'SaberPro']:
        flash('Tipo de prueba no válido')
        return redirect(url_for('select_test'))
    
    questions = Question.query.filter_by(test_type=test_type).all()
    if not questions:
        flash('No hay preguntas disponibles para esta prueba')
        return redirect(url_for('select_test'))
    
    # Mezclar preguntas
    random.shuffle(questions)
    
    session['test_questions'] = [q.id for q in questions]
    session['test_type'] = test_type
    session['test_start_time'] = datetime.utcnow().isoformat()
    session['current_question'] = 0
    session['answers'] = {}
    
    return redirect(url_for('take_test'))

@app.route('/take_test')
@login_required
def take_test():
    if 'test_questions' not in session:
        return redirect(url_for('select_test'))
    
    question_ids = session['test_questions']
    current_index = session.get('current_question', 0)
    
    if current_index >= len(question_ids):
        return redirect(url_for('finish_test'))
    
    question = Question.query.get(question_ids[current_index])
    time_elapsed = (datetime.utcnow() - datetime.fromisoformat(session['test_start_time'])).total_seconds()
    
    return render_template('test.html', 
                         question=question, 
                         question_number=current_index + 1,
                         total_questions=len(question_ids),
                         time_elapsed=int(time_elapsed))

@app.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    if 'test_questions' not in session:
        return jsonify({'error': 'No hay prueba activa'}), 400
    
    question_id = request.form.get('question_id')
    answer = request.form.get('answer')
    
    if not question_id or not answer:
        return jsonify({'error': 'Respuesta inválida'}), 400
    
    session['answers'][question_id] = answer
    session['current_question'] = session.get('current_question', 0) + 1
    
    return jsonify({'success': True})

@app.route('/finish_test')
@login_required
def finish_test():
    if 'test_questions' not in session:
        return redirect(url_for('dashboard'))
    
    question_ids = session['test_questions']
    test_type = session['test_type']
    answers = session['answers']
    
    correct_count = 0
    test_answers = []
    
    for question_id in question_ids:
        question = Question.query.get(question_id)
        user_answer = answers.get(str(question_id), '')
        is_correct = user_answer == question.correct_answer
        
        if is_correct:
            correct_count += 1
        
        test_answer = TestAnswer(
            question_id=question_id,
            user_answer=user_answer,
            is_correct=is_correct
        )
        test_answers.append(test_answer)
    
    time_taken = (datetime.utcnow() - datetime.fromisoformat(session['test_start_time'])).total_seconds()
    score = (correct_count / len(question_ids)) * 100
    
    test_result = TestResult(
        user_id=current_user.id,
        test_type=test_type,
        score=score,
        total_questions=len(question_ids),
        correct_answers=correct_count,
        time_taken=int(time_taken)
    )
    
    db.session.add(test_result)
    db.session.flush()  # Para obtener el ID del test_result
    
    for answer in test_answers:
        answer.test_result_id = test_result.id
        db.session.add(answer)
    
    db.session.commit()
    
    # Limpiar sesión
    session.pop('test_questions', None)
    session.pop('test_type', None)
    session.pop('test_start_time', None)
    session.pop('current_question', None)
    session.pop('answers', None)
    
    return redirect(url_for('view_results', test_id=test_result.id))

@app.route('/results/<int:test_id>')
@login_required
def view_results(test_id):
    result = TestResult.query.get_or_404(test_id)
    
    if result.user_id != current_user.id:
        flash('No tienes permiso para ver estos resultados')
        return redirect(url_for('dashboard'))
    
    answers = TestAnswer.query.filter_by(test_result_id=test_id).all()
    questions_with_answers = []
    
    for answer in answers:
        question = Question.query.get(answer.question_id)
        questions_with_answers.append({
            'question': question,
            'user_answer': answer.user_answer,
            'is_correct': answer.is_correct
        })
    
    return render_template('results.html', result=result, questions=questions_with_answers)

@app.route('/history')
@login_required
def history():
    results = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.completed_at.desc()).all()
    return render_template('history.html', results=results)

if __name__ == '__main__':
    init_database()
    app.run(debug=True)