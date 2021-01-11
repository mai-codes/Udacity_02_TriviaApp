import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        pass

    def test_get_paginated_questions(self):
        # get response and load data
        response = self.client().get('/questions')
        data = json.loads(response.data)

        # check status code and message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

        # check that total_questions and questions return data
        self.assertTrue(len(data['questions']))
        self.assertTrue(data['total_questions'])


    def test_404_request_beyond_valid_page(self):
        # send request with bad page data & load response
        response = self.client().get('/questions?page=100')
        data = json.loads(response.data)

        # check status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_delete_question(self):
        # create a new question to be deleted
        question = Question(question=self.new_question['question'], answer=self.new_question['answer'],
                            category=self.new_question['category'], difficulty=self.new_question['difficulty'])
        question.insert()

        # get id of the new question
        question_id = question.id

        # get number of questions before delete
        questions_before = Question.query.all()

        # delete the question and store response
        response = self.client().delete('/questions/{}'.format(question_id))
        data = json.loads(response.data)

        # get number of questions after delete
        questions_after = Question.query.all()

        # check if the question has been deleted from db
        question = Question.query.filter(Question.id == 1).one_or_none()

        # check status code and return success message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

        # check if question id matches deleted question id
        self.assertEqual(data['deleted'], question_id)

        # check if one less question after delete
        self.assertTrue(len(questions_before) - len(questions_after) == 1)

        # check if question equals None after delete
        self.assertEqual(question, None)

    def test_create_new_question(self):
        # retrieve number of questions before POST request
        questions_before = Question.query.all()

        # create new question & load response data
        response = self.client().post('/questions', json=self.new_question)
        data = json.loads(response.data)

        # retrieve number of questions after POST request
        questions_after = Question.query.all()

        # check if the question has been created
        question = Question.query.filter_by(id=data['created']).one_or_none()

        # check status code and return success message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

        # check if one more question after POST request by subtracting
        self.assertTrue(len(questions_after) - len(questions_before) == 1)

        # check that question is valid and not None
        self.assertIsNotNone(question)

    def test_422_question_creation_fails(self):
        """Tests question creation failure 422"""

        # retrieve number of questions before POST request
        questions_before = Question.query.all()

        # create new question without json data and load response data
        response = self.client().post('/questions', json={})
        data = json.loads(response.data)

        # retrieve number of questions after post
        questions_after = Question.query.all()

        # check status code and load success message
        self.assertEqual(response.status_code, 422)
        self.assertEqual(data['success'], False)

        # check if questions_after and questions_before are equal value
        self.assertTrue(len(questions_after) == len(questions_before))

    def test_search_questions(self):
        # send post request with search term & load response data
        response = self.client().post('/questions', json={'search_term': 'peanut'})
        data = json.loads(response.data)

        # check response status code and success message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

        # check results = 1
        self.assertEqual(len(data['questions']), 1)

        # check id of question in response is correct
        self.assertEqual(data['questions'][0]['id'], 12)

    def test_404_if_search_questions_fails(self):
        # send post request with search term that doesn't exist & load response data
        response = self.client().post('/questions', json={'search_term': 'magicians'})
        data = json.loads(response.data)

        # check response status code and return message 404
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_get_questions_by_category(self):
        # send request with category id 2 for art & load response 
        response = self.client().get('/categories/2/questions')
        data = json.loads(response.data)

        # check response status code and message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

        # check that questions are returned and length isn't 0
        self.assertNotEqual(len(data['questions']), 0)

        # check that current category returned is art
        self.assertEqual(data['current_category'], 'Art')

    def test_400_if_questions_by_category_fails(self):
        # send request with category id 1000 & load data
        response = self.client().get('/categories/1000/questions')
        data = json.loads(response.data)

        # check response status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'bad request')

    def test_play_quiz_game(self):
        # send post request with category and previous questions & load data
        response = self.client().post('/quizzes', json={'previous_questions': [],
            'quiz_category': {'id': '5', 'type': 'Entertainment'}})
        data = json.loads(response.data)

        # check response status code and message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

        # check that a question is returned
        self.assertTrue(data['question'])

        # check that the question returned is in correct category
        self.assertEqual(data['question']['category'], 5)

        # ensure question returned is not on previous question list
        self.assertNotEqual(data['question']['id'], 20)
        self.assertNotEqual(data['question']['id'], 21)

    def test_play_quiz_fails(self):
        # send post request without json data & load response data
        response = self.client().post('/quizzes', json={})
        data = json.loads(response.data)

        # check response status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'bad request')

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()