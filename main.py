import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable


def get_sj_vacancies(language):
    sj_page = 1
    sj_pages = 10
    sj_vacancies_from_all_pages = []
    while sj_page < sj_pages:
        url = "https://api.superjob.ru/2.0/vacancies/"
        secret_key = os.getenv("SECRET_KEY")
        headers = {
            "X-Api-App-Id": secret_key
        }
        payload = {
            "town": "4",
            "keywords": "Программист {}".format(language),
            "catalogues": "Разработка, программирование",
            "page": sj_page
        }
        response = requests.get(url, headers=headers, params=payload)
        response.raise_for_status()
        sj_vacancies_amount = response.json()["total"]
        sj_vacancies = response.json()["objects"]
        sj_vacancies_from_all_pages.append(sj_vacancies)

        sj_page += 1

    return sj_vacancies_amount, sj_vacancies_from_all_pages, sj_pages


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

        vacancies_amount = response.json()["found"]
        vacancies = response.json()["items"]
        vacancies_from_all_pages.append(vacancies)

        page += 1

    return vacancies_amount, vacancies_from_all_pages, pages


def predict_rub_salary_for_SuperJob(vacancies):
    sj_salaries = []
    for vacancy in vacancies:
        if vacancy["payment_from"] == 0.0 and vacancy["payment_to"] != 0.0:
            sj_salaries.append(vacancy["payment_to"] * 0.8)
        elif vacancy["payment_to"] == 0.0 and vacancy["payment_from"] != 0.0:
            sj_salaries.append(vacancy["payment_from"] * 1.2)
        elif vacancy["payment_from"] and vacancy["payment_to"]:
            sj_salaries.append(
                (vacancy["payment_from"] + vacancy["payment_to"]) / 2)
        elif vacancy["payment_from"] == 0.0 and vacancy["payment_to"] == 0.0:
            continue

    sum = 0
    for salary_item in sj_salaries:
        sum += salary_item

    sj_average_salary = int(sum / len(sj_salaries))
    return sj_average_salary, sj_salaries


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

    sum = 0
    for salary_item in salaries:
        sum += salary_item

    average_salary = int(sum / len(salaries))
    return average_salary, salaries


def make_table_for_SJ_vacancies(languages, sj_data):
    title = "SuperJob"
    TABLE_DATA = []
    TABLE_DATA.append(['Language', 'Vacancies found',
                       'Average salary', 'Vacancies processed'])
    for language in languages:
        TABLE_DATA.append(
            [language, sj_data[language]["sj_vacancies_found"],
             sj_data[language]["sj_average_salary"],
             sj_data[language]["sj_vacancies_processed"]])

    table_instance = AsciiTable(TABLE_DATA, title)
    table_instance.justify_columns[3] = 'right'
    print(table_instance.table)
    print()


def make_table_for_HH_vacancies(languages, hh_data):
    title = "HeadHunter"
    TABLE_DATA = []
    TABLE_DATA.append(['Language', 'Vacancies found',
                       'Average salary', 'Vacancies processed'])
    for language in languages:
        TABLE_DATA.append([language, hh_data[language]["hh_vacancies_found"],
                           hh_data[language]["hh_average_salary"],
                           hh_data[language]["hh_vacancies_processed"]])

    table_instance = AsciiTable(TABLE_DATA, title)
    table_instance.justify_columns[3] = 'right'
    print(table_instance.table)
    print()


def get_sj_dict(languages):
    sj_data = {}

    for language in languages:
        try:
            sj_vacancies_amount, sj_vacancies_from_all_pages, sj_pages = get_sj_vacancies(
                language)
        except requests.exceptions.HTTPError:
            print('Warning! Error in request for SuperJob.ru!')
        sj_vacancies_processed = 0
        sj_average_salary_counter = 0
        for sj_vacancies_from_one_page in sj_vacancies_from_all_pages:
            try:
                sj_average_salary, sj_salaries = predict_rub_salary_for_SuperJob(
                    sj_vacancies_from_one_page)
            except ZeroDivisionError:
                continue
            sj_vacancies_processed += len(sj_salaries)
            sj_average_salary_counter += sj_average_salary

        sj_average_salary_from_all_pages = int(
            sj_average_salary_counter / sj_pages)
        sj_vacancies_amount_and_salaries = {
            "sj_vacancies_found": sj_vacancies_amount,
            "sj_average_salary": sj_average_salary_from_all_pages,
            "sj_vacancies_processed": sj_vacancies_processed,
        }
        sj_data[language] = sj_vacancies_amount_and_salaries

    return sj_data


def get_hh_dict(languages):
    hh_data = {}

    for language in languages:
        try:
            vacancies_amount, vacancies_from_all_pages, pages = get_hh_vacancies(
                language)
        except requests.exceptions.HTTPError:
            print('Warning! Error in request for HeadHunter.ru!')
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

        hh_data[language] = hh_vacancies_amount_and_salaries

    return hh_data


def main():
    load_dotenv()
    languages = ['python', 'javascript', 'java', 'ruby', 'php',
                 'c++', 'go', 'c', 'scala', 'swift']

    sj_data = get_sj_dict(languages)
    hh_data = get_hh_dict(languages)
    make_table_for_SJ_vacancies(languages, sj_data)
    make_table_for_HH_vacancies(languages, hh_data)


if __name__ == __name__:
    main()
