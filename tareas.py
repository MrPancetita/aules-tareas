# Created by modifying the original idea of https://github.com/josepg

import config, re, ssl, sys
import requests
from termcolor import cprint
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import getpass;
from bs4 import BeautifulSoup


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
    cprint("Error iniciant la sessió en aules", 'red', 'on_white')
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
courses_data = response.json()

# Print the courses data
print(courses_data)

pattern = re.compile(r'(https\:\/\/aules.edu.gva.es\/eso03\/course\/view.php\?id=[0-9]+)">(.*)</a>')
print(re.findall(pattern, returnPage))

for courseURL, courseName in re.findall(pattern, returnPage):
    result = courseURL.split("id=")
    print(result)
    if int(result[1]) not in config.cursosExclosos:
        cprint(courseName, 'grey', 'on_cyan')
        course_page_url = courseURL.split('eso03')[0] + 'eso03/mod/assign/index.php?id=' + result[1]
        url = session.get(course_page_url)
        returnPage = url.text
        pattern2 = re.compile(r'(https\:\/\/aules[0-9]?.edu.gva.es\/eso03\/mod\/assign\/view.php\?id=[0-9]+)">(.*)</a>')
        for tascaURL, tascaName in re.findall(pattern2, returnPage):
            url = session.get(tascaURL)
            returnPage3 = url.text
            pattern3 = re.compile(r'(?:Necessiten qualificació|Pendientes por calificar|Needs grading)</td>\n<td [a-zA-Z=" 1]+>([0-9]+)</td>')
            m = re.search(pattern3, returnPage3)
            if m:
                myQnt = m.group(1)
                if int(myQnt) > 0:
                    totalTasks += int(myQnt)
                    print(" └>" + tascaName + ": " + m.group(1) + ' ' + tascaURL + '&action=grader' )
cprint("Total de tasques per corregir: " + str(totalTasks), 'grey', 'on_green')