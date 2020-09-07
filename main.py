import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable
import logging


def get_sj_vacancies(secret_key, language):
    page = 1
    pages = 2
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
        vacancies_amount = response.json()["total"]
        vacancies = response.json()["objects"]
        vacancies_from_all_pages.append(vacancies)

        page += 1

    return vacancies_amount, vacancies_from_all_pages, pages


def get_hh_vacancies(language):
    page = 0
    pages = 1
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

        vacancies_amount = response.json()["found"]
        vacancies = response.json()["items"]
        vacancies_from_all_pages.append(vacancies)

        page += 1

    return vacancies_amount, vacancies_from_all_pages, pages


def predict_rub_salary_for_SuperJob(vacancies):
    salaries = []
    for vacancy in vacancies:
        if vacancy["payment_from"] == 0.0 and vacancy["payment_to"] != 0.0:
            salaries.append(vacancy["payment_to"] * 0.8)
        elif vacancy["payment_to"] == 0.0 and vacancy["payment_from"] != 0.0:
            salaries.append(vacancy["payment_from"] * 1.2)
        elif vacancy["payment_from"] and vacancy["payment_to"]:
            salaries.append(
                (vacancy["payment_from"] + vacancy["payment_to"]) / 2)
        elif vacancy["payment_from"] == 0.0 and vacancy["payment_to"] == 0.0:
            continue

    average_salary = int(sum(salaries) / len(salaries))
    return average_salary, salaries


def predict_rub_salary_for_HeadHunter(vacancies):
    salaries = []
    for vacancy in vacancies:
        salary = vacancy['salary']

        if salary is None:
            continue

        if salary['currency'] == 'RUR':
            if salary['from'] is None:
                salaries.append(salary['to'] * 0.8)
            elif salary['to'] is None:
                salaries.append(salary['from'] * 1.2)
            elif salary['from'] and salary['to']:
                salaries.append((salary['from'] + salary['to']) / 2)

    average_salary = int(sum(salaries) / len(salaries))
    return average_salary, salaries


def print_table_for_SJ_vacancies(languages, superjob_summary):
    title = "SuperJob"
    table_data = []
    table_data.append(['Language', 'Vacancies found',
                       'Average salary', 'Vacancies processed'])
    for language in languages:
        table_data.append(
            [language, superjob_summary[language]["sj_vacancies_found"],
             superjob_summary[language]["sj_average_salary"],
             superjob_summary[language]["sj_vacancies_processed"]])

    table_instance = AsciiTable(table_data, title)
    table_instance.justify_columns[3] = 'right'
    print(table_instance.table)
    print()


def print_table_for_HH_vacancies(languages, headhunter_summary):
    title = "HeadHunter"
    table_data = []
    table_data.append(['Language', 'Vacancies found',
                       'Average salary', 'Vacancies processed'])
    for language in languages:
        table_data.append([language, headhunter_summary[language]["hh_vacancies_found"],
                           headhunter_summary[language]["hh_average_salary"],
                           headhunter_summary[language]["hh_vacancies_processed"]])

    table_instance = AsciiTable(table_data, title)
    table_instance.justify_columns[3] = 'right'
    print(table_instance.table)
    print()


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
            "sj_vacancies_found": vacancies_amount,
            "sj_average_salary": average_salary_from_all_pages,
            "sj_vacancies_processed": vacancies_processed,
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
            "hh_vacancies_found": vacancies_amount,
            "hh_average_salary": average_salary_from_all_pages,
            "hh_vacancies_processed": vacancies_processed,
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
    print_table_for_SJ_vacancies(languages, superjob_summary)
    print_table_for_HH_vacancies(languages, headhunter_summary)


if __name__ == __name__:
    main()
