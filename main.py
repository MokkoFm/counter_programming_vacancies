import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable
import logging


def get_sj_vacancies(secret_key, language):
    page = 1
    pages = 10
    vacancies_from_all_pages = []
    while page < pages:
        url = "https://api.superjob.ru/2.0/vacancies/"
        headers = {
            "X-Api-App-Id": secret_key,
        }
        payload = {
            "town": "4",
            "keywords": "Программист {}".format(language),
            "catalogues": "Разработка, программирование",
            "page": page
        }
        response = requests.get(url, headers=headers, params=payload)
        response.raise_for_status()
        vacancies = response.json()
        vacancies_amount = vacancies["total"]
        vacancies_items = vacancies["objects"]
        vacancies_from_all_pages.append(vacancies_items)

        page += 1

    return vacancies_amount, vacancies_from_all_pages, pages


def get_hh_vacancies(language):
    page = 0
    pages = 40
    vacancies_from_all_pages = []
    while page < pages:
        url = "https://api.hh.ru/vacancies"
        headers = {"User-Agent": "curl"}
        payload = {
            "text": "Программист {}".format(language),
            "area": "1",
            "search_period": "30",
            "page": page
        }
        response = requests.get(url, headers=headers, params=payload)
        response.raise_for_status()
        vacancies = response.json()
        vacancies_amount = vacancies["found"]
        vacancies_items = vacancies["items"]
        vacancies_from_all_pages.append(vacancies_items)

        page += 1

    return vacancies_amount, vacancies_from_all_pages, pages


def predict_salary(salaries, salary_from, salary_to):
    if salary_from is None or salary_from == 0.0:
        salaries.append(salary_to * 0.8)
    elif salary_to == 0.0 or salary_to is None:
        salaries.append(salary_from * 1.2)
    elif salary_from and salary_to:
        salaries.append((salary_from + salary_to) / 2)


def predict_rub_salary_for_SuperJob(vacancies):
    salaries = []
    for vacancy in vacancies:
        salary_from = vacancy["payment_from"]
        salary_to = vacancy["payment_to"]

        if salary_from == 0.0 and salary_to == 0.0:
            continue
        else:
            predict_salary(salaries, salary_from, salary_to)

    average_salary = int(sum(salaries) / len(salaries))
    return average_salary, salaries


def predict_rub_salary_for_HeadHunter(vacancies):
    salaries = []
    for vacancy in vacancies:
        salary = vacancy['salary']

        if salary is None:
            continue

        if salary['currency'] == 'RUR':
            salary_from = salary['from']
            salary_to = salary['to']
            predict_salary(salaries, salary_from, salary_to)

    average_salary = int(sum(salaries) / len(salaries))
    return average_salary, salaries


def print_table(table, title):
    table_vacancies = AsciiTable(table, title)
    table_vacancies.justify_columns[3] = 'right'
    print(table_vacancies.table)
    print()


def append_vacancies_data_to_table(summary, languages, title):
    table = []
    table.append(['Language', 'Vacancies found',
                  'Average salary', 'Vacancies processed'])
    for language in languages:
        table.append(
            [language, summary[language]["vacancies_found"],
             summary[language]["average_salary"],
             summary[language]["vacancies_processed"]])

    print_table(table, title)


def get_sj_summary(secret_key, languages):
    superjob_summary = {}

    for language in languages:
        try:
            vacancies_amount, vacancies_from_all_pages, pages = get_sj_vacancies(
                secret_key, language)
        except requests.exceptions.HTTPError:
            logging.error('Error in request for SuperJob.ru!')
            continue
        vacancies_processed = 0
        average_salary_counter = 0
        for vacancies_from_one_page in vacancies_from_all_pages:
            try:
                average_salary, salaries = predict_rub_salary_for_SuperJob(
                    vacancies_from_one_page)
            except ZeroDivisionError:
                continue
            vacancies_processed += len(salaries)
            average_salary_counter += average_salary

        average_salary_from_all_pages = int(
            average_salary_counter / pages)
        sj_vacancies_amount_and_salaries = {
            "vacancies_found": vacancies_amount,
            "average_salary": average_salary_from_all_pages,
            "vacancies_processed": vacancies_processed,
        }
        superjob_summary[language] = sj_vacancies_amount_and_salaries

    return superjob_summary


def get_hh_summary(languages):
    headhunter_summary = {}

    for language in languages:
        try:
            vacancies_amount, vacancies_from_all_pages, pages = get_hh_vacancies(
                language)
        except requests.exceptions.HTTPError:
            logging.error('Error in request for HeadHunter.ru!')
            continue
        vacancies_processed = 0
        average_salary_counter = 0
        for vacancies_from_one_page in vacancies_from_all_pages:
            try:
                average_salary, salaries = predict_rub_salary_for_HeadHunter(
                    vacancies_from_one_page)
            except ZeroDivisionError:
                continue
            vacancies_processed += len(salaries)
            average_salary_counter += average_salary

        average_salary_from_all_pages = int(average_salary_counter / pages)
        hh_vacancies_amount_and_salaries = {
            "vacancies_found": vacancies_amount,
            "average_salary": average_salary_from_all_pages,
            "vacancies_processed": vacancies_processed,
        }

        headhunter_summary[language] = hh_vacancies_amount_and_salaries

    return headhunter_summary


def main():
    load_dotenv()
    secret_key = os.getenv("SECRET_KEY")
    languages = ['python', 'javascript', 'java', 'ruby', 'php',
                 'c++', 'go', 'c', 'scala', 'swift']

    superjob_summary = get_sj_summary(secret_key, languages)
    headhunter_summary = get_hh_summary(languages)
    append_vacancies_data_to_table(superjob_summary, languages, "SuperJob")
    append_vacancies_data_to_table(headhunter_summary, languages, "HeadHunter")


if __name__ == __name__:
    main()
