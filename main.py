import requests
import os
from dotenv import load_dotenv


def get_sj_vacancies():
    url = "https://api.superjob.ru/2.0/vacancies/"
    secret_key = os.getenv("SECRET_KEY")
    headers = {
        "X-Api-App-Id": secret_key
    }
    payload = {
        "town": "4",
        "keyword": "Программист",
        "catalogues": "Разработка, программирование"
    }
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    filename = "sj.json"
    vacancies = response.json()["objects"]
    for vacancy in vacancies:
        print(vacancy["profession"] + ", " + vacancy["town"]["title"])

    with open(filename, "wb") as file:
        file.write(response.content)


def get_vacancies(language):
    page = 0
    pages = 1
    all_vacancies = []
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
        all_vacancies.append(vacancies)

        page += 1

    filename = "hh-{}.json".format(language)
    with open(filename, "wb") as file:
        file.write(response.content)

    return vacancies_amount, all_vacancies, pages


def predict_rub_salary(vacancies):
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
                salaries.append(salary['from'] + salary['to'] / 2)

    sum = 0
    for salary_item in salaries:
        sum += salary_item

    average_salary = int(sum / len(salaries))
    return average_salary, salaries


def main():
    load_dotenv()
    get_sj_vacancies()
    languages = ['python', 'javascript', 'java', 'ruby', 'php',
                 'c++', 'go', 'c', 'scala', 'swift']

    vacancies_amounts = []
    for language in languages:
        vacancies_amount, all_vacancies, pages = get_vacancies(language)

        vacancies_processed = 0
        average_salary_counter = 0
        for vacancy in all_vacancies:
            vacancies_amounts.append(vacancies_amount)
            try:
                average_salary, salaries = predict_rub_salary(vacancy)
            except ZeroDivisionError:
                continue
            vacancies_processed += len(salaries)
            average_salary_counter += average_salary
        
        average_salary_from_all_pages = int(average_salary_counter / pages)
        vacancies_amount_and_salaries = {
            "vacancies_found": vacancies_amount,
            "average_salary": average_salary_from_all_pages,
            "vacancies_processed": vacancies_processed,
        }
        about_language = {
            language: vacancies_amount_and_salaries,
        }
        print(about_language)


if __name__==__name__:
    main()