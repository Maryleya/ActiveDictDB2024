import sys
sys.path.append("~/.local/lib/python3.9/site-packages/")
import re
import pymorphy2
from pymorphy2 import MorphAnalyzer
import sqlite3

class Processing():
    def __init__(self, q):
        self.q = q
        self.morph = MorphAnalyzer()
        self.tags = (
            'ГЛАГ', 'МЕЖДОМ', 'НАРЕЧ', 'ПРИЛ',
            'СОЮЗ', 'СУЩ', 'ЧАСТ'
        )
    
    def standardize(self, tag):
        new_tags = {'ГЛАГ': 'VERB', 'МЕЖДОМ': 'INTJ', 'НАРЕЧ': 'ADVB', 'ПРИЛ': 'ADJ', 'СОЮЗ': 'CONJ', 'СУЩ': 'NOUN', 'ЧАСТ': 'PRCL'}
        if tag in new_tags:
            new_tag = new_tags[tag]
            return new_tag
        return tag

    def lemmatization(self, word, tag=None):
        w = self.morph.parse(word)
        l = w[0].normal_form
        if tag:
            tag = self.standardize(tag)
            for ana in w:
                if tag == 'ADJ' or tag == 'PRT':
                    if ana.tag.POS.startswith(tag):
                        l = ana.normal_form
                else:
                    if ana.tag.POS == tag:
                        l = ana.normal_form
        return (l)

    def only_one_word(self, phrase):
        to_search = {'lemma': None, 'pos': None, 'word': None}
        phrase = phrase[0].lower()
        if re.search(r'[a-z]', phrase):
            error = 'Латинские символы не могут использоваться!'
            return error
        else:
            to_search['word'] = phrase
            l = self.lemmatization(phrase)
            to_search['lemma'] = l
        return to_search
    
    def token_and_tag(self, phrase):
        if re.search(r'[a-z]', phrase[0].lower()):
            error = 'Формат введенного запроса неверный!'
            return error
        else:
            to_search = {'lemma': None, 'pos': None, 'word': None}
            w = phrase[0].lower() # слово
            tag = phrase[1].upper() # тег
            if tag not in self.tags:
                error = 'Указан неправильный частеречный тег!'
                return error
            to_search['word'] = w
            l = self.lemmatization(w, tag)
            to_search['lemma'] = l
            to_search['pos'] = tag
            return to_search

    def main_search(self):
        if re.search(r'[^a-zA-Zа-яА-Я +"]', self.q):
            error = 'В запросе присутствуют некорректные символы!'
            return error
        else:
            request = []
            self.q = self.q.split()
            
            if len(self.q) > 1:
                for element in self.q:
                    q1 = element.split('+')
                    result = self.only_one_word(q1)
                    if isinstance(result, dict):
                        request.append(result)                    
                    elif isinstance(result, str):
                        error = result
                        return error
                    else:
                        request = []
                        break
                return request
            else:
                if self.q == []:
                    error = 'К сожалению, ничего не найдено.'
                    return error
                else:
                    q1 = self.q[0].split('+')
                    if len(q1) == len(self.q):    # в запросе только слово или только тег
                        result = self.only_one_word(q1)
                        if isinstance(result, dict):
                            request.append(result)
                        else:
                            error = result
                            return error
                    else:                         # в запросе и токен, и тег
                        result = self.token_and_tag(q1)
                        if isinstance(result, dict):
                            request.append(result)
                        else:
                            error = result
                            return error
                return request

class GetData():
    def __init__(self, q, conn, pos):
        self.q = q
        self.conn = conn
        self.cur = conn.cursor()
        self.pos = pos

    def only_lemma(self, dct):
        query = """
        SELECT lexeme, pos FROM dictionary
        WHERE lexeme_lemmas LIKE ?
        """
        self.cur.execute(query, (str(dct['lemma'] + '%'),))
        result = self.cur.fetchall()
        if not result:
            self.cur.execute(query, (str(dct['word'] + '%'),))
            result = self.cur.fetchall()
        return result

    def only_pos(self, dct):
        query = """
        SELECT lexeme, pos FROM dictionary
        WHERE pos = ?
        """
        result = []
        for i in dct['pos']:
            self.cur.execute(query, (i,))
            result.append(self.cur.fetchall())
        if not result:
            self.cur.execute(query, (str(dct['word'] + '%'),))
            result = self.cur.fetchall()
        return result
    
    def lemma_and_pos(self, dct):
        query = """
        SELECT lexeme, pos FROM dictionary
        WHERE lexeme_lemmas LIKE ? AND pos = ?
        """
        self.cur.execute(query, (str(dct['lemma'] + '%'), dct['pos']))
        result = self.cur.fetchall()
        if not result:
            self.cur.execute(query, (str(dct['word'] + '%'), dct['pos']))
            result = self.cur.fetchall()
        return result

    def get_lemmas(self):
        if self.q[0]['lemma'] and self.q[0]['pos']:
            result = self.lemma_and_pos(self.q[0])
        elif self.q[0]['lemma']:
            result = self.only_lemma(self.q[0])
        elif self.q[0]['pos']:
            result = self.only_pos(self.q[0])
            result = [x for xs in result for x in xs]
        if result:
            links = [obj[0] for obj in result]
            poses = [obj[1] for obj in result]

            return links, poses
        else:
            error = 'Такого слова нет!'
            return error