import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):

  #helper function for paginating questions
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_question = questions[start:end]

  return current_question

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app)
  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):

      # set access control
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
      return response
  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def get_categories():

    # query all categories
    selection = Category.query.order_by(Category.id).all()
    selection_dict = {}

    # add categories to a dict
    for category in selection:
      selection_dict[category.id] = category.type

    # if no categories abort
    if len(selection_dict) == 0:
      abort(404)

    # otherwise return successful response
    return jsonify({
      'success': True,
      'categories': selection_dict
    })

  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions')
  def get_questions():

    # query all questions and paginate
    questions = Question.query.all()
    current_questions = paginate_questions(request, questions)
    total_questions = len(Question.query.all())

    #if no questions found abort
    if len(current_questions) == 0:
        abort(404)

    # return successful response
    return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': total_questions
    })
  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      #search question by id
      question = Question.query.filter(Question.id==question_id).one_or_none()

      #if question not found abort
      if question is None:
        abort(404)
      
      # delete question
      question.delete()

      # return successful response
      return jsonify({
        'success': True,
        'deleted': question_id,
      })

    #abort if can't delete question
    except:
        abort(422)
  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def create_question():

      # load the response body
      body = request.get_json()

      if not body:
        abort(400)

      # load data from the body
      new_question = body.get('question')
      new_answer = body.get('answer')
      new_category = body.get('category')
      new_difficulty = body.get('difficulty')

      # make sure all fields have data, if not then abort
      if ((new_question is None) or (new_answer is None) or (new_difficulty is None) or (new_category is None)):
        abort(422)

      try:
          #create and then insert the question into db
          question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
          question.insert()

          # query all questions & paginate them 
          selection = Question.query.order_by(Question.id).all()
          current_questions = paginate_questions(request, selection)

          # return successful response
          return jsonify({
            'success': True,
            'created_question': question.question,
            'created_id': question.id,
            'questions': current_questions,
            'total_questions': len(Question.query.all())
          })

      except:
        abort(422)


  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions/search', methods=['POST'])
  def search_questions():
    # load response body
    body = request.get_json()

    if (body.get('search_term')):
      search_term = body.get('search_term', None)
      
      # query db based on search term
      selection = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()
      total_questions = len(Question.query.all())
      
      #abort if nothing found
      if len(selection) == 0:
        abort(404)

      #return successful result
      return jsonify({
        'success': True,
        'questions': paginate_questions(request, selection),
        'total_questions': total_questions,
      })

  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_questions_by_category(category_id):

    try:
        #query questions by category id
        questions = Question.query.filter(Question.category == category_id).all()

        #return successful results
        return jsonify({
          'success': True,
          'questions': paginate_questions(request, questions),
          'total_questions': len(questions),
          'current_category': category_id
        })
    
    #abort if none found
    except:
      abort(404)


  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def get_quiz_questions():

    try:
      #load response body
      body = request.get_json()

      # load data from body
      quiz_category = body.get('quiz_category')
      cat_id = quiz_category['id']
      previous_questions = body.get('previous_questions', None)

      if not ('quiz_category' in body and 'previous_questions' in body):
        abort(400, 'Required keys missing from body')

      #if no category given, load all questions
      if cat_id == 0:
          questions = Question.query.filter(Question.id.notin_(previous_questions)).all()

      #else load questions for given category
      else:
          questions = Question.query.filter(Question.id.notin_(previous_questions), Question.category == cat_id).all()
      
      # chose a random question from questions above
      if questions != None:
        random_question = random.choice(questions)

      #return successful response
      return jsonify({
        'success': True,
        'question': random_question.format()
      })

    except:
      abort(422)

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
      return jsonify({
          'success': False,
          'error': 404,
          'message': 'resource not found'
      }), 404

  @app.errorhandler(422)
  def unprocessible(error):
      return jsonify({
          'success': False,
          'error': 422,
          'message': 'unprocessible'
      }), 422

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
          'success': False,
          'error': 400,
          'message': 'bad request'
      }), 400

  @app.errorhandler(405)
  def not_found(error):
      return jsonify({
          'success': False,
          'error': 404,
          'message': 'method not allowed'
      }), 405
  
  return app

    