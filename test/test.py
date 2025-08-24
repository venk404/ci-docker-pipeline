import unittest
import requests
from dotenv import load_dotenv
import os


load_dotenv()
APP_PORT = os.getenv('APP_PORT', '8000')
HOST = os.getenv('HOST', 'localhost')

url = f"http://{HOST}:{APP_PORT}/"


class TestStudentDetailsAPI(unittest.TestCase):

    student_id = None

    def setUp(self):
        self.url = url
        self.student_data = {
            "name": "Foo",
            "email": "foo@example.com",
            "age": 20,
            "phone": "1234567890"
        }

    def test_post_studentdetails(self):
        response = requests.post(self.url + 'AddStudent',
                                 json=self.student_data)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        TestStudentDetailsAPI.student_id = response_data['student_id']['id']

    def test_getALLstudentdetails(self):
        response = requests.get(self.url + 'GetAllStudents')
        self.assertEqual(response.status_code, 200)

    def test_GetStudenbyid(self):
        if not hasattr(TestStudentDetailsAPI, 'student_id'):
            self.skipTest("No student ID available for test_GetStudent")
        url = f"{self.url}GetStudent?id={TestStudentDetailsAPI.student_id}"
        response = requests.get(url)
        self.assertEqual(response.status_code, 200,
                         f'''Expected status code 200 but got
                         {response.status_code}''')

    def test_Update(self):
        url = f'''{self.url}v2/UpdateStudent?id=
        {TestStudentDetailsAPI.student_id}'''
        update_data = {
            'name': 'Ganesh Gaitonde',
            'email': 'Gopalmat@gmail.com',
            'age': 0,
            'phone': '1234567895'
        }
        response = requests.patch(url, json=update_data)
        self.assertEqual(response.status_code, 200,
                         f'''Expected status code 200 but got
                         {response.status_code}''')

    def test_DeleteStudent(self):
        if not hasattr(TestStudentDetailsAPI, 'student_id'):
            self.skipTest("No student ID available for test_DeleteStudent")
        url = f'''{self.url}v2/DeleteStudent?id=
        {TestStudentDetailsAPI.student_id}'''
        response = requests.delete(url)
        self.assertEqual(response.status_code, 200,
                         f'''Expected status code 200 but got
                         {response.status_code}''')


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(TestStudentDetailsAPI('test_post_studentdetails'))
    suite.addTest(TestStudentDetailsAPI('test_GetStudenbyid'))
    suite.addTest(TestStudentDetailsAPI('test_getALLstudentdetails'))
    suite.addTest(TestStudentDetailsAPI('test_Update'))
    suite.addTest(TestStudentDetailsAPI('test_DeleteStudent'))
    runner = unittest.TextTestRunner()
    runner.run(suite)
