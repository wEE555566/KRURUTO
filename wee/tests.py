import unittest
import requests
 

class MyTest(unittest.TestCase):

    def test_openapi(self):
        self.assertEqual(requests.get('http://203.185.67.178/intern/akisame/api/v1/openapi.json').status_code, 200, "Should be 200")

    def test_add(self):
        self.assertEqual(requests.get('http://203.185.67.178/intern/akisame/api/v1/add?num1=5&num2=10').text, "15", "Should be 15")
    
    def test_mul(self):
        self.assertEqual(requests.get('http://203.185.67.178/intern/akisame/api/v1/mul?num1=5&num2=10').text, "50", "Should be 50")
   
if __name__ == '__main__':
    unittest.main()
