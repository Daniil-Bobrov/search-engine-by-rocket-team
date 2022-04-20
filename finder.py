import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import pymorphy2
from requests.exceptions import HTTPError
import os
import json
import shutil

morph = pymorphy2.MorphAnalyzer()

url = "https://tlgrm.ru/docs"
# url = "https://kivy.org/doc/stable/"
domain = urlparse(url).netloc

headers = {
    "Accept": '*/*',
    "User-Agent": 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.119 YaBrowser/22.3.0.2434 Yowser/2.5 Safari/537.36'
}


def src_download(url):  # скачиваем исходный код
    try:
        os.mkdir('data_2')  # создаем директроию
    except:
        shutil.rmtree('data_2', ignore_errors=False, onerror=None)
        os.mkdir('data_2')  # создаем директроию
    req = requests.get(url, headers=headers)
    src = req.text
    with open("data_2/src.html", "w", encoding="utf-8") as file:
        file.write(src)


# src_download(url)
def src_take():
    with open("data_2/src.html", encoding="utf-8") as file:  # получаем код страницы
        srce = file.read()
    return srce


link_dict = {}
page_dict = {}
page_index_dict = {}


def all_links(soup):  # все ссылки с текстом
    for item in soup.find(class_="article"):
        if item != '\n' and item != ' ' and not (item.get('id')):
            li = item.find_all('li')
            for i in li:
                c = i.find_all('a')
                for j in c:
                    link = j.get('href')
                    txt = j.text
                    link_dict[txt] = "https://tlgrm.ru" + link

    return link_dict


def for_page_parsing(link_dict):  ### функция парсинга дочерних страниц
    count = 0
    for key, link in link_dict.items():
        if count > 13:
            break
        ### содержание страницы ###
        page_dict[f'{count}ссылка'] = link  # сылка на дочернюю страницу
        # текст дочерней страницы
        try:
            req = requests.get(link, headers=headers)
        except HTTPError:
            continue
        src = req.text
        soup = BeautifulSoup(src, 'lxml')
        for item in soup:
            if len(item) > 1:
                textt = item.text
        textt.replace(' ', '')
        textt.replace('\n', '')
        count += 1
        search_key_word(clean_text(textt), link)


count_page = 0  # номер страницы и кол-во файлов


def search_key_word(text, link):  ### ранжирование + индексирование ###
    global count_page
    count_words = 0  # номер слова
    page_index_dict = {}
    lst_items = []
    for item in text:  # оценка веса слова в зависимости от части речи
        if not (item.lower() in lst_items):  # проверка на повторение слова
            p = morph.parse(item)[0]
            if p.tag.POS == 'NOUN' or p.tag.POS == 'VERB' or p.tag.POS == 'INFN':
                weight = 5
            elif p.tag.POS == 'ADJF' or p.tag.POS == 'ADJS' or p.tag.POS == 'ADVB':
                weight = 3
            else:
                weight = 1

            count_word = text.count(item)  # количество повторений слова в тексте
            normal_form = morph.parse(item)[0].normal_form  # начальная форма
            rang = weight * count_word  # коэфицент значимости
            page_index_dict[f"word{count_words}"] = {
                "source": item.lower(),  # само слово
                "range": rang,  # коэфицент значимости
                "count": count_word,  # кол-во повторений
                "weight": weight,  # вес
                "basic": normal_form,  # начальная форма
                "link": link,  # ссылка
                "range_all": 1
            }
            count_words += 1
            lst_items.append(item.lower())
    count_page += 1
    print('Индексируем...')
    with open(f'data_2/page{count_page}_index_dict.json', 'w', encoding='utf-8') as file:
        json.dump(page_index_dict, file, indent=4, ensure_ascii=False)


def clean_text(text):  ### очищаем текст от предлогов, междометий, союзов, частиц и не нужных символов###
    text = str(text).split(' ')
    for item in text:
        result = ''
        count = 0
        for j in item:
            if j != '\n' and not (j in '(){}[]:;.,'):
                result += j
                count = 0
            else:
                if count == 0:
                    result += ' '

        text[text.index(item)] = result
    clean_text = []
    for item in text:
        p = morph.parse(item)[0]
        if p.tag.POS != 'PREP' and p.tag.POS != 'CONJ' and p.tag.POS != 'PRCL' and p.tag.POS != 'INTJ':
            clean_text.append(item)
    for i in range(len(clean_text)):
        clean_text[i] = clean_text[i].strip('\n')
    clean_text = list(filter(lambda x: x != "", clean_text))
    if len(text) > 1:
        return clean_text


def home_page_text(soup):  # текст с главной страницы
    for item in soup:
        text = item.text
        if len(text) > 1:
            search_key_word(clean_text(text), url)


###Поисковая система###


regexp_word = '/([a-zа-я0-9]+)/ui'
regexp_entity = '/&([a-zA-Z0-9]+);/'


def get_words(content):
    # Фильтрация HTML - тегов  и HTML - сущностей
    content = content.strip()
    content = content.replace(regexp_entity, ' ')

    # Перевод в нижний регистр
    content = content.lower()

    # Замена ё на е
    content = content.replace("ё", "е")
    return content


def lemmatize(content: str):
    lemm_lst = []
    # Получение базовой формы слова
    for item in content.split(' '):
        morph = pymorphy2.MorphAnalyzer()
        p = morph.parse(item)[0].normal_form
        lemm_lst.append(p)
    return lemm_lst


serch_dict = {}


def make_dir():
    os.mkdir('data_search')  # создаем директроию под запросы


def delete_dir():
    shutil.rmtree('data_search', ignore_errors=False, onerror=None)


def search_in_json(lem):
    count_page = len(os.listdir(path="data_2")) - 1  # количество проиндексированных страниц
    # поиск по запросу
    count = 1
    count_of_lem = 1
    for i in range(1, count_page + 1):
        with open(f'data_2/page{count}_index_dict.json', encoding='utf-8') as file:
            index_dict = json.load(file)
            for k, value in index_dict.items():
                for key, item in value.items():
                    for j in range(len(lem)):
                        if lem[j] in value['basic']:
                            serch_dict[f'lem_{count_of_lem}'] = value['basic']
                            serch_dict[f'weight_{count_of_lem}'] = value['weight']
                            serch_dict[f'link{count_of_lem}'] = value['link']  # ссылка для слова
                            serch_dict[f'rang{count_of_lem}'] = value['range']  # ранг слова
                            serch_dict[f'count{count_of_lem}'] = value['count']  # кол-во слов
                            serch_dict['page'] = i
                            serch_dict['range_all'] = value['count'] + value['range'] + value[
                                'weight']  # общий ранг(по  нему будет сортировка страниц)
                            serch_dict['place'] = 0
                            if value['link'] != serch_dict[f'link{count_of_lem}']:
                                count_of_lem += 1
        with open(f'data_search/serch_dict{i}.json', "w", encoding='utf-8') as file:
            json.dump(serch_dict, file, indent=4, ensure_ascii=False)

        count += 1


def sorted_result():
    max_rang_all = 1
    serch_lst = []
    c = len(os.listdir(path="data_search"))  # кол-во найденных запросов
    for i in range(1, c + 1):
        with open(f'data_search/serch_dict{i}.json', encoding='utf-8') as file:
            serch_lst.append(json.load(file))

    def sorted_for_range_all(x):
        return x['range_all']

    sorted(serch_lst, key=sorted_for_range_all)
    result = list()
    for i in range(3):
        if serch_lst[i]['link1'] != 'https://tlgrm.ru/docs/api':
            # print(serch_lst[i]['link1'])  # return
            result.append(serch_lst[i]['link1'])
    return result


def main_2():  # главная функция по поиску запроса
    make_dir()  # создаем дректорию
    search = input('Поиск:')  # ввод в поиск
    lem = lemmatize(get_words(search))  # начальная форма (список)
    search_in_json(lem)
    sorted_result()
    delete_dir()  # удаляем уже использовавшие ссылки по поиску


def find(search):  # главная функция по поиску запроса
    make_dir()  # создаем дректорию
    lem = lemmatize(get_words(search))  # начальная форма (список)
    search_in_json(lem)
    result = sorted_result()
    delete_dir()  # удаляем уже использовавшие ссылки по поиску
    # print("result:", result)
    return result


def main():  # главная функция по индексированию и парсингу страниц
    src_download(url)
    src_take()

    src = src_take()
    soup = BeautifulSoup(src, 'lxml')

    home_page_text(soup)
    for_page_parsing(all_links(soup))
    if __name__ == "__main__":
        print('Индексация заверилась!!!\nВводите: \n')
        main_2()


main()
