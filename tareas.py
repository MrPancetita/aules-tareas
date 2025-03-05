import ssl, sys
import requests
from termcolor import cprint
from requests.adapters import HTTPAdapter
import getpass
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Course, Task, Submission

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

cprint("Nuevo y definitivo script de tareas de Aules", 'green', 'on_grey')

session = requests.Session()
session.mount('https://', SSLAdapter())
session.cookies = requests.cookies.RequestsCookieJar()

login_url = "https://aules.edu.gva.es/eso03/login/index.php"
response = session.get(login_url)

# Parse the HTML response
soup = BeautifulSoup(response.text, 'html.parser')

# Extract the 'logintoken' property
logintoken = soup.find('input', {'name': 'logintoken'})['value']

# Print the logintoken
print(f'Login Token: {logintoken}')

login_data = {
    'username': input("Introduce tu nombre de usuario: "),
    'password': getpass.getpass("Introduce tu contraseña: "),
    'logintoken': logintoken
}

response = session.post(login_url, data=login_data)
returnPage = response.text

if 'loginerrormessage' in returnPage:
    cprint("Error iniciando la sesión en Aules", 'red', 'on_white')
    print(returnPage)
    sys.exit()

totalTasks = 0

# Parse the HTML response
soup = BeautifulSoup(returnPage, 'html.parser')

# Extract the 'sesskey' property
sesskey = soup.find('input', {'name': 'sesskey'})['value']

# Print the sesskey
print(f'Sesskey: {sesskey}')

# Se deben capturar los cursos de https://aules.edu.gva.es/eso03/lib/ajax/service.php?sesskey=theactualkey&info=core_course_get_enrolled_courses_by_timeline_classification

courses_url = f"https://aules.edu.gva.es/eso03/lib/ajax/service.php?sesskey={sesskey}&info=core_course_get_enrolled_courses_by_timeline_classification"
courses_data_payload = [
    {
        "index": 0,
        "methodname": "core_course_get_enrolled_courses_by_timeline_classification",
        "args": {
            "offset": 0,
            "limit": 0,
            "classification": "all",
            "sort": "fullname",
            "customfieldname": "",
            "customfieldvalue": ""
        }
    }
]

response = session.post(courses_url, json=courses_data_payload)
courses_data = response.json()[0]['data']['courses']

# Setup SQLAlchemy session
engine = create_engine('sqlite:///aules_tareas.db')
Session = sessionmaker(bind=engine)
db_session = Session()

course_list = []

for entry in courses_data:
    if entry['visible'] == False:
        continue
    course_id = entry['id']
    course_name = entry['fullname']
    course_url = f"https://aules.edu.gva.es/eso03/course/view.php?id={course_id}"
    course = Course(course_id, course_name, course_url)
    db_session.add(course)
    course_list.append(course)
    print(course)

def get_tarea_grading(session, task, db_session):
    task_id = task.id
    grading_url = f"https://aules.edu.gva.es/eso03/mod/assign/view.php?id={task_id}&action=grading"
    response = session.get(grading_url)

    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all('tr', class_=lambda x: x and 'user' in x)

    for fila in rows:
        student_name = fila.find('td', class_='c2').text.strip()
        student_email = fila.find('td', class_='c3').text.strip()
        status = fila.find('td', class_='c4').text.strip()
        date = fila.find('td', class_='c7').text.strip()
        files = fila.find('td', class_='c8').text.strip()

        submission = Submission(student_name, student_email, status, date, files)
        submission.task = task
        db_session.add(submission)
        print(f"Prueba to_csv: {submission.to_csv_semicolon()}")

    db_session.commit()

for course in course_list:
    response = session.get(course.url)
    soup = BeautifulSoup(response.text, 'html.parser')
        
    tasks = soup.find_all('div', class_='modtype_assign')
    print(f'Course: {course.name}, Tasks: {len(tasks)}')
    print('*' * 50)
    print(f'Detalle de las tareas del curso {course.name}:')
    for entry in tasks:
        task_name = entry.find('span', class_='instancename').text.strip()
        task_url = entry.find('a')['href']
        task_id = task_url.split('id=')[-1] if 'id=' in task_url else 'N/A'
        task = Task(task_id, task_name, task_url)
        task.course = course
        db_session.add(task)
        print(f'Task Name: {task_name}, Task URL: {task_url}, Task ID: {task_id}')
        print(f'Recuperando entregas de la tarea...')
        get_tarea_grading(session, task, db_session)  
        print('*' * 50)

db_session.commit()
db_session.close()




