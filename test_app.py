import unittest
from app import app, db, user, Product

class TestApp(unittest.TestCase):


    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQlALchemy_DATABSE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        db.create_all()


    def tearDown(self):
        db.session.remove()
        db.drop_all

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome', response.data)

    def test_products_page(self):
        response = self.app.get('/products')
        self.assertEqual(response.staus_code, 200)
        self.assertIn(b'Products', response.data)

if __name__ == '__main__':
    unittest.main()
    

