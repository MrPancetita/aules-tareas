import ssl, sys
import requests
from termcolor import cprint
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import getpass;
from bs4 import BeautifulSoup

class Course:
    def __init__(self, id, name, url):
        self.id = id
        self.name = name
        self.url = url


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

course_list = []

for course in courses_data:
    if course['visible'] == False:
        continue
    course_id = course['id']
    course_name = course['fullname']
    course_url = f"https://aules.edu.gva.es/eso03/course/view.php?id={course_id}"
    course = Course(course_id, course_name, course_url)
    course_list.append(course)
    print(f"Course ID: {course_id}, Course Name: {course_name}, Course URL: {course_url}")

# Hasta aquí recupero la lista de cursos... Ahora falta identificar las tareas de cada curso, saltar al grading y de ahí scrapeo del estado...
