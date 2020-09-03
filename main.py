import requests


def get_vacancies(language):
    url = "https://api.hh.ru/vacancies"
    headers = {"User-Agent": "curl"}
    payload = {
        "text": "Программист {}".format(language),
        "area": "1",
        "search_period": "30",
    }
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()

    vacancies_amount = response.json()["found"]
    vacancies = response.json()["items"]

    filename = "hh-{}.json".format(language)
    #with open(filename, "wb") as file:
    #    file.write(response.content)

    return vacancies_amount, vacancies


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
    languages = ['python', 'javascript', 'java', 'ruby', 'php',
                 'c++', 'go', 'c', 'scala', 'swift']

    vacancies_amounts = []
    for language in languages:
        vacancies_amount, vacancies = get_vacancies(language)
        vacancies_amounts.append(vacancies_amount)
        average_salary, salaries = predict_rub_salary(vacancies)
        new_dict = {
            "vacancies_found": vacancies_amount,
            "average_salary": average_salary,
            "vacancies_processed": len(salaries),
        }
        language_data = {
            language: new_dict,
        }
        print(language_data)


if __name__==__name__:
    main()