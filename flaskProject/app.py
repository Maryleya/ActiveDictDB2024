# -*- coding: utf-8 -*-
import sqlite3
from this import d
from search import Processing, GetData
from flask import Flask, request, render_template, g, render_template_string, jsonify
from pymorphy2 import MorphAnalyzer
import re

ALPHABET = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ'

con = sqlite3.connect("finalvol1.db", check_same_thread=False)
cur = con.cursor()

app = Flask(__name__, instance_relative_config=True)
morph = MorphAnalyzer()
app.config['TEMPLATES_AUTO_RELOAD'] = True


def remove_stress_marks(input_str):
    # удаляем комбинирующий акутный акцент и пробел после него
    stress_mark = '\u0301 '
    input_str = input_str.replace(stress_mark, '')
    
    return input_str


#стартовая
@app.route('/')
def hello():
    # общая статистика
    sql_query = '''SELECT pos, COUNT(*) as cnt FROM dictionary
                    WHERE pos IN (
                                'ГЛАГ', 'МЕЖДОМ', 'НАРЕЧ', 'ПРИЛ',
                                'СОЮЗ', 'СУЩ', 'ЧАСТ'
                            )
                    GROUP BY pos
                    ORDER BY cnt DESC;'''
    cur.execute(sql_query)
    res_lexemes = cur.fetchall()
    
    to_right_tag = {'ГЛАГ': 'Глагол', 'МЕЖДОМ': 'Междометие', 'НАРЕЧ': 'Наречие', 'ПРИЛ': 'Прилагательное',
                    'СОЮЗ': 'Союз', 'СУЩ': 'Существительное', 'ЧАСТ': 'Частица'}

    final_res_lexemes = []
    for res in res_lexemes:
        new_res = (to_right_tag[res[0]], res[1])
        final_res_lexemes.append(new_res)

    lexemes = [list(x) for x in final_res_lexemes]
    
    # список рандомных слов для начальной страницы
    sql_query = '''SELECT lexeme, pos FROM dictionary
                    WHERE pos IN (
                                'ГЛАГ', 'МЕЖДОМ', 'НАРЕЧ', 'ПРИЛ',
                                'СОЮЗ', 'СУЩ', 'ЧАСТ'
                            )
                    ORDER BY random() 
                    LIMIT 12;'''

    cur.execute(sql_query)
    res_lexemes_pos = cur.fetchall()
    
    lexemes_pos = []
    for i in res_lexemes_pos:
        new_i = remove_stress_marks(i[0]).lower().replace(' ', '_')
        lexemes_pos.append((new_i, i[1]))
    lexemes_pos

    wordlist_interesting = [{'lexeme': x[0],
                             'pos': x[1]} for x in lexemes_pos]

    return render_template('index.html', wordlist_interesting=wordlist_interesting, lexemes=lexemes)

# поиск
@app.route('/search')
def search():
    poses = ['Глагол', 'Междометие', 'Наречие', 'Прилагательное', 'Союз', 'Существительное', 'Частица']
    return render_template('new_search.html', poses=poses)


def process_search(q, pos):
    path_to_db = 'finalvol1.db'
    if q:
        conn = sqlite3.connect(path_to_db)
        my = Processing(q)
        new_qs = my.main_search()
        results = []
        for new_q in new_qs:
            if type(new_q) == str:
                error = new_q
                results = ''
            else:
                data = GetData([new_q], conn, pos)
                res_search = data.get_lemmas() 
                if type(res_search) == str:
                    error = res_search
                    results = ''
                else:
                    results.append(res_search)
                    error = ''
    elif pos:
        results = []
        error = ''
        conn = sqlite3.connect(path_to_db)
        to_search = {'lemma': None, 'pos': []}
        for p in pos:
            to_search['pos'].append(p)
        data = GetData([to_search], conn, pos)
        res_search = data.get_lemmas()
        results.append(res_search)
    else:
        results = ''
        error = ''
    return results, error


# результаты
@app.route('/process', methods=['GET'])
def process():
    q = request.args.get('q')
    q = re.sub(r'[^\w\s]','',q)

    pos = request.args.getlist('pos')

    to_right_tag = {'Глагол': 'ГЛАГ', 'Междометие': 'МЕЖДОМ', 'Наречие': 'НАРЕЧ', 'Прилагательное': 'ПРИЛ',
                    'Союз': 'СОЮЗ', 'Существительное': 'СУЩ', 'Частица': 'ЧАСТ'}

    qs = []
    new_pos = ''
    if pos:        
        if len(pos) == 1 and len(q.split()) == 1:
            q = q + '+' + to_right_tag[pos[0]]
        elif len(pos) == 1 and len(q.split()) != 0:            
            for el in q.split():
                new_el = el + '+' + to_right_tag[pos[0]]             
                qs.append(new_el)
        else:
            new_pos = []
            for i in pos:
                new_i = to_right_tag[i]
                new_pos.append(new_i)

    full_qs = []
    if not qs:
        results, error = process_search(q, new_pos)
    else:        
        for i in qs:
            results, error = process_search(i, new_pos)
            full_qs.append(results)
    
    if full_qs:
        results = []
        for i in full_qs:
            results.extend(i)
    
    if results:
        full_results = []
        for res in results:
            for i in range(len(res[0])):
                new_i = remove_stress_marks(res[0][i]).lower().replace(' ', '_')
                if (new_i, res[1][i]) not in full_results:
                    full_results.append((new_i, res[1][i]))

        results = sorted(full_results, key=lambda x: x[0])

    return render_template('results.html', error=error, results=results)


def get_words(letter):
    sql_query = '''SELECT lexeme, pos FROM dictionary
                    WHERE lexeme LIKE {0}'''.format('"' + letter + '%"')
    cur.execute(sql_query)

    res = [{'lexeme': x[0],
            'pos': x[1]} for x in cur.fetchall()]

    results = []
    for i in res:
        new_i = {'lexeme': remove_stress_marks(i['lexeme']).lower().replace(' ', '_'), 'pos': i['pos']}
        results.append(new_i)
    return results


# словник
@app.route('/dictionary/<start_letter>')
def dictionary(start_letter):

    if start_letter == 'all':
        article_list = get_words('')
    else:
        article_list = get_words(start_letter)

    return render_template('new_dictionary.html',
                           alphabet=ALPHABET,
                           current_letter=start_letter.lower(),
                           article_list=article_list)


# статьи
@app.route('/post/<article_id>')
def post(article_id):
    conn = sqlite3.connect("finalvol1.db", check_same_thread=False)
    cur = conn.cursor()
    conn.create_function("remove_stress", 1, remove_stress_marks)

    article_id = article_id.replace('_', ' ')
    cur.execute("SELECT * FROM dictionary WHERE remove_stress(lexeme) = ?", (article_id.upper(),))
    article = cur.fetchone()

    if article:
        return render_template('post.html',
                               lexeme=article[1],
                               pos=article[3],
                               tags=article[4].split(',') if article[4] else [],
                               new_html=article[7])
    else:
        return "Статья не найдена", 404


# про сайт и словарь
@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(threaded=True)
