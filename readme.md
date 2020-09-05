# Programming vacancies from HeadHunter and SuperJob

The project uses data from [HeadHunter.ru](https://hh.ru/) and [SuperJob.ru](https://www.superjob.ru/). 
You can get average salaries for python, javascript, java, ruby, php, c++, go, c, scala and swift languages.

### How to install

The script needs an API key from [api.superjob.ru](https://api.superjob.ru/). You need to register an application to get the token. 
You can get a data from HeadHunter without token.

After cloning the repository create a `.env` file in the project's folder and put the token to it:

```SECRET_KEY=your_token```

Python3 should be already installed. Then use pip to install dependencies:

```pip install -r requirements.txt```

Then run `python main.py` in the project's folder. You'll see the results in the console as tables.

### Project Goals

The code is written for educational purposes on online-course for web-developers [dvmn.org](https://dvmn.org/).