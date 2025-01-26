# Created by modifying the original work of https://github.com/josepg

import config, re, ssl, sys
import requests
from termcolor import cprint
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

cprint("Benvinguts a l'script de tasques d'aules. Versió 1.3. (twitter: @josep_g)", 'green', 'on_grey')

session = requests.Session()
session.mount('https://', SSLAdapter())
session.cookies = requests.cookies.RequestsCookieJar()

login_url = "https://aules.edu.gva.es/moodle/login/index.php"
response = session.get(login_url)

login_data = {
    'username': input("Introduce tu nombre de usuario: "),
    'password': input("Introduce tu contraseña: "),
    'loginbtn': 'Login'
}

response = session.post(login_url, data=login_data)
returnPage = response.text

if 'loginerrormessage' in returnPage:
    cprint("Error iniciant la sessió en aules", 'red', 'on_white')
    sys.exit()

totalTasks = 0

pattern = re.compile(r'(https\:\/\/aules[0-9]?.edu.gva.es\/moodle\/course\/view.php\?id=[0-9]+)">(.*)</a>')
for courseURL, courseName in re.findall(pattern, returnPage):
    result = courseURL.split("id=")
    if int(result[1]) not in config.cursosExclosos:
        cprint(courseName, 'grey', 'on_cyan')
        course_page_url = courseURL.split('moodle')[0] + 'moodle/mod/assign/index.php?id=' + result[1]
        url = session.get(course_page_url)
        returnPage = url.text
        pattern2 = re.compile(r'(https\:\/\/aules[0-9]?.edu.gva.es\/moodle\/mod\/assign\/view.php\?id=[0-9]+)">(.*)</a>')
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