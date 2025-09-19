from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'legal-neuro-secret-key-2024'
app.config['DATA_FILE'] = 'data/legal_words.json'

def load_data():
    """Загрузка данных из файла"""
    os.makedirs('data', exist_ok=True)
    if os.path.exists(app.config['DATA_FILE']):
        try:
            with open(app.config['DATA_FILE'], 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return get_default_data()
    else:
        data = get_default_data()
        save_data(data)
        return data

def save_data(data):
    """Сохранение данных в файл"""
    with open(app.config['DATA_FILE'], 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_default_data():
    """Базовый набор юридических слов"""
    return {
        "Гражданское право": {
            "contract": "договор",
            "obligation": "обязательство",
            "property": "собственность",
            "liability": "ответственность"
        },
        "Уголовное право": {
            "crime": "преступление",
            "penalty": "наказание",
            "evidence": "доказательство",
            "suspect": "подозреваемый"
        },
        "Международное право": {
            "treaty": "договор",
            "sovereignty": "суверенитет",
            "diplomacy": "дипломатия",
            "sanction": "санкция"
        }
    }

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/encyclopedia')
def encyclopedia():
    """Энциклопедия слов"""
    data = load_data()
    return render_template('encyclopedia.html', data=data)

@app.route('/testing')
def testing():
    """Страница выбора категории для тестирования"""
    data = load_data()
    return render_template('testing.html', categories=list(data.keys()))

@app.route('/test/<category>')
def test(category):
    """Страница тестирования"""
    data = load_data()
    if category not in data:
        return redirect(url_for('testing'))
    
    words = list(data[category].items())
    if not words:
        return redirect(url_for('testing'))
    
    # Сохраняем слова для теста в сессии
    session['test_words'] = words
    session['current_index'] = 0
    session['score'] = 0
    session['category'] = category
    
    return render_template('test.html', 
                         category=category, 
                         total=len(words),
                         current=1)

@app.route('/check_answer', methods=['POST'])
def check_answer():
    """Проверка ответа"""
    data = load_data()
    user_answer = request.json.get('answer', '').strip().lower()
    
    words = session.get('test_words', [])
    current_index = session.get('current_index', 0)
    
    if current_index >= len(words):
        return jsonify({'finished': True})
    
    current_word, correct_translation = words[current_index]
    is_correct = user_answer == correct_translation.lower()
    
    if is_correct:
        session['score'] = session.get('score', 0) + 1
    
    session['current_index'] = current_index + 1
    
    return jsonify({
        'correct': is_correct,
        'correct_answer': correct_translation,
        'finished': session['current_index'] >= len(words)
    })

@app.route('/results')
def results():
    """Страница результатов"""
    score = session.get('score', 0)
    total = len(session.get('test_words', []))
    category = session.get('category', '')
    
    return render_template('results.html', 
                         score=score, 
                         total=total, 
                         category=category,
                         percentage=round(score/total*100, 1) if total > 0 else 0)

@app.route('/add_word', methods=['GET', 'POST'])
def add_word():
    """Добавление нового слова"""
    data = load_data()
    
    if request.method == 'POST':
        english = request.form.get('english', '').strip().lower()
        russian = request.form.get('russian', '').strip()
        category = request.form.get('category', '').strip()
        new_category = request.form.get('new_category', '').strip()
        
        if not english or not russian:
            return render_template('add_word.html', 
                                 categories=list(data.keys()),
                                 error="Все поля обязательны для заполнения")
        
        # Определяем категорию
        final_category = new_category if new_category else category
        
        if not final_category:
            return render_template('add_word.html',
                                 categories=list(data.keys()),
                                 error="Необходимо выбрать или создать категорию")
        
        # Добавляем категорию если её нет
        if final_category not in data:
            data[final_category] = {}
        
        # Добавляем слово
        data[final_category][english] = russian
        save_data(data)
        
        return render_template('add_word.html',
                             categories=list(data.keys()),
                             success=f"Слово '{english}' добавлено в категорию '{final_category}'")
    
    return render_template('add_word.html', categories=list(data.keys()))

@app.route('/edit_words')
def edit_words():
    """Редактирование слов"""
    data = load_data()
    return render_template('edit_words.html', data=data)

@app.route('/api/words', methods=['GET', 'POST', 'DELETE'])
def api_words():
    """API для работы со словами"""
    data = load_data()
    
    if request.method == 'GET':
        return jsonify(data)
    
    elif request.method == 'POST':
        # Добавление или обновление слова
        english = request.json.get('english')
        russian = request.json.get('russian')
        category = request.json.get('category')
        
        if category not in data:
            data[category] = {}
        
        data[category][english] = russian
        save_data(data)
        
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        # Удаление слова или категории
        category = request.json.get('category')
        english = request.json.get('english')
        
        if english:  # Удаление слова
            if category in data and english in data[category]:
                del data[category][english]
                # Если категория пуста, удаляем её
                if not data[category]:
                    del data[category]
        else:  # Удаление категории
            if category in data:
                del data[category]
        
        save_data(data)
        return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
