import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import pymorphy2
from requests.exceptions import HTTPError
import os
import json
import shutil
import re

morph = pymorphy2.MorphAnalyzer()

url = "https://habr.com/ru/all/"
domain = urlparse(url).netloc

headers = {
    "Accept": 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    "User-Agent": 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.119 YaBrowser/22.3.0.2434 Yowser/2.5 Safari/537.36'
}


def src_download(url, name_dir='data_2', name_file='src.html'):  # скачиваем исходный код
    """
    Принимает параметр (url - ссылка на сайт),
    Параметр name_dir='' - название создаваемой директории
    Параметр name_file='' - название создаваемого файла
    Задача функции: создать директорию с именем name_dir и загрузить туда код страницы в формате <str>(c библиотекой requests)
    """
    try:
        os.mkdir(name_dir)  # создаем директроию
    except:
        return
    req = requests.get(url, headers=headers)
    src = req.text
    with open(f"{name_dir}/{name_file}", "w", encoding="utf-8") as file:
        file.write(src)


def src_take(dir='data_2', name='src.html'):
    """
    Считывает и возвращает файл из указаной директории(dir), под указаным именем (name)
    """
    with open(f"{dir}/{name}", encoding="utf-8") as file:  # получаем код страницы
        srce = file.read()
    return srce


link_dict = {}
page_dict = {}
page_index_dict = {}


def all_links(soup):  # все ссылки с текстом
    """
    Принимает объект BeautifulSoup (soup)
    Вытаскивает все ссылки на дочерние страницы из SOUPа и возвращает их список
    """
    get_pattern = r'(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-&?=%.]+'
    p = re.findall(get_pattern, str(soup))  # (pattern, string)
    link_lst = []
    for x in p:
        if 'https://' in x and domain in x and not (x in link_lst) and not ('png' in x or 'assets' in x):
            link_lst.append(str(x))
    return link_lst


def for_page_parsing(link_lst, name_dir='data_2'):  ### функция парсинга дочерних страниц
    """
    Принимает параметр link_lst(список ссылок на страницы) и параметр name_dir(название директории)
    Собирает со страниц текстовую информацию
    Очищает с помощью функции clean_text
    Индексирует и ранжирует каждую страницу
    Записывает полученную информацию(в формате json) в директории - name_dir
    """
    count = 0
    for link in link_lst:
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
        search_key_word(clean_text(textt), link, name_dir=name_dir)


count_page = 0  # номер страницы и кол-во файлов


def search_key_word(text, link, name_dir=''):  ### ранжирование + индексирование ###
    global count_page
    count_words = 0  # номер слова
    page_index_dict = {}
    lst_items = []
    if text != None:
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
        with open(f'{name_dir}/page{count_page}_index_dict.json', 'w', encoding='utf-8') as file:
            json.dump(page_index_dict, file, indent=4, ensure_ascii=False)


def clean_text(text):  ### очищаем текст от предлогов, междометий, союзов, частиц и не нужных символов###
    """
    Принимает параметр text(текст)
    Фильтрует текст
    Возвращает отфильтрованный текст в виде списка(где каждое слово элемент этого списка)
    """
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


def home_page_text(soup, url=url, name_dir='data_2'):  # текст с главной страницы
    """
    Принимает объект BeautifulSoup (soup)
    Ссылку на страницу - url
    Название директории - name_dir
    Собирает со страницы(soup) текстовую информацию
    Очищает с помощью функции clean_text
    Индексирует и ранжирует страницу через функцию search_key_word
    Записывает полученную информацию(в формате json) в директории - name_dir
    """
    for item in soup:
        text = item.text
        if len(text) > 1:
            search_key_word(clean_text(text), url, name_dir=name_dir)


###Поисковая система###


regexp_word = '/([a-zа-я0-9]+)/ui'
regexp_entity = '/&([a-zA-Z0-9]+);/'


def get_words(content):
    """
    Принимает строку - content
    Фильтрует строку и переводит в нижний регистр
    Возвращает полученную строку
    """
    # Фильтрация HTML - тегов  и HTML - сущностей
    content = content.strip()
    content = content.replace(regexp_entity, ' ')

    # Перевод в нижний регистр
    content = content.lower()

    # Замена ё на е
    content = content.replace("ё", "е")
    return content


def lemmatize(content: str):
    """
    Принимает строку(на русском)
    Переводит все слова в начальную форму
    Возвращает список полученных элементов
    """
    lemm_lst = []
    # Получение базовой формы слова
    for item in content.split(' '):
        morph = pymorphy2.MorphAnalyzer()
        p = morph.parse(item)[0].normal_form
        lemm_lst.append(p)
    return lemm_lst


serch_dict = {}


def make_dir(name_dir_write='data_search'):
    """
    Создает директорию с названием: name_dir_write
    """
    os.mkdir(name_dir_write)  # создаем директроию под запросы


def delete_dir(name_dir="data_search"):
    """
    Создает директорию с названием: name_dir
    """
    shutil.rmtree(name_dir, ignore_errors=False, onerror=None)


def search_in_json(lem, name_dir_of_read='data_2', name_dir_write='data_search'):
    """
    Принимает список начальных форм(lem)
    Принимает название директории(name_dir_of_read) в которой находится словарь образованный функцией: for_page_parsing
    Принимает название директории(созданную в функции: make_dir) в которую записываются(в формате json) результаты сравнения lem и значений словаря(name_dir_or_read)
    """
    count_page = len(os.listdir(path=name_dir_of_read)) - 1  # количество проиндексированных страниц
    # поиск по запросу
    count = 1
    count_of_lem = 1
    for i in range(1, count_page + 1):
        with open(f'{name_dir_of_read}/page{count}_index_dict.json', encoding='utf-8') as file:
            index_dict = json.load(file)
            for k, value in index_dict.items():
                for key, item in value.items():
                    counted = 1
                    for j in range(len(lem)):
                        if lem[j] in value['basic']:
                            serch_dict[f'lem_{count_of_lem}'] = value['basic']
                            serch_dict[f'weight_{count_of_lem}'] = value['weight']
                            serch_dict[f'link{count_of_lem}'] = value['link']  # ссылка для слова
                            serch_dict[f'rang{count_of_lem}'] = value['range']  # ранг слова
                            serch_dict[f'count{count_of_lem}'] = value['count']  # кол-во слов
                            serch_dict['page'] = i
                            serch_dict['range_all'] = counted * value[
                                'range']  # общий ранг(по  нему будет сортировка страниц)
                            if value['link'] != serch_dict[f'link{count_of_lem}']:
                                count_of_lem += 1
                        if lem[j] in value['basic']:
                            serch_dict['range_all'] += 5
        with open(f'{name_dir_write}/serch_dict{i}.json', "w", encoding='utf-8') as file:
            json.dump(serch_dict, file, indent=4, ensure_ascii=False)

        count += 1


def sorted_result(name_dir='data_search', key_sort='range_all', key_get='link1'):
    """
    Принимает название директории с файлами(формата json) записанными в функции search_in_json
    Сортирует словари по ключу: key_sort
    Добовляет по порядку значения ключа: key_get, в список(result)
    Возвращает список result
    """
    serch_lst = []
    c = len(os.listdir(path=name_dir))  # кол-во найденных запросов
    for i in range(1, c + 1):
        with open(f'{name_dir}/serch_dict{i}.json', encoding='utf-8') as file:
            serch_lst.append(json.load(file))

    def sorted_for_range_all(x):
        if x.get(key_sort) == None:
            return 1
        return x.get(key_sort)

    sorted(serch_lst, key=sorted_for_range_all)
    result = list()
    for i in range(len(serch_lst)):
        if serch_lst[i].get(key_get) in result:
            continue
        else:
            if serch_lst[i].get(key_get) != None:
                result.append(serch_lst[i].get(key_get))
    return result


def main_2():  # главная функция по поиску запроса
    make_dir()  # создаем директорию
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
        print('Индексация заверишлась!!!\nВводите: \n')
        main_2()


main()
