from datetime import timedelta
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from flasgger import Swagger
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, get_current_user
)
from werkzeug.security import check_password_hash, generate_password_hash
from redis import Redis

app = Flask(__name__)

# Logging Config
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
# Log a message
app.logger.info('Welcome to the app')

# DB Config
db_name = "SampleDotCom"
swagger = Swagger(app)
app.config["MONGO_URI"] = f"mongodb://mongo:27017/{db_name}"
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
mongo = PyMongo(app)
db = mongo.db
app_redis = Redis(host='redis', port=6379)

# JWT Config
app.config['JWT_SECRET_KEY'] = 'replace-your-secret-key'
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30)
jwt = JWTManager(app)

def authenticate_user():
    current_user = get_jwt_identity()
    access_token = app_redis.get(current_user)
    if not access_token:
        return jsonify({"message": "Invalid access token"}), 401


@app.route("/")
def index():
    """
    Root endpoint
    ---
    responses:
      200:
        description: Returns Welcome to sample.com
        example:
          'Welcome to sample.com'
    """
    return jsonify(
        message="Welcome to sample.com"
    )


@app.route('/api/v1/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if not username or not password:
        return jsonify({"message": "Missing username or password"}), 401

    # Check if the username exists in Redis
    user = app_redis.hgetall(username)

    if not user:
        return jsonify({"message": "User not found"}), 401

    # Check if the password is correct
    if not check_password_hash(user[b'password'].decode('utf-8'), password):
        return jsonify({"message": "Invalid password"}), 401

    # Create a JWT token and store it in Redis
    # access_token = 'abc'
    access_token = create_access_token(identity=username)
    app_redis.setex(username, 3600, access_token)
    return jsonify({"access_token": access_token}), 200


@app.route('/api/v1/register', methods=['POST'])
def register():
    """
    Register new user
    ---
    tags:
      - users
    parameters:
      - in: body
        name: body
        description: JSON payload containing user data
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              description: The user's username
              required: true
            password:
              type: string
              description: The user's password
              required: true
            role:
              type: string
              description: The user's role
              required: false
    responses:
      200:
        description: A dictionary with message
        schema:
          type: object
          properties:
            message:
              type: string
        examples:
          message: User registered successfully
    """
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    role = request.json.get('role', 'user')
    if not username or not password:
        return jsonify({"message": "Missing username or password"}), 401

    # Check if the username already exists in Redis
    if app_redis.hgetall(username):
        return jsonify({"msg": "Username already exists"}), 400

    # Generate a hash for the password and Store the user in Redis
    password_hash = generate_password_hash(password)
    app_redis.hset(username, 'password', password_hash)
    app_redis.hset(username, 'role', role)

    return jsonify({"message": "User registered successfully"}), 201


@app.route("/api/v1/users")
@jwt_required()
def get_all_users():
    """
    Get all users
    ---
    tags:
      - users
    responses:
      200:
        description: A dictionary containing all users
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: Id of the user
                  name:
                    type: string
                    description: Name of user
                  role:
                    type: string
                    description: Role of user
    """
    authenticate_user()
    users = db.users.find()
    data = []
    for user in users:
        item = {
            "id": str(user["_id"]),
            "name": user["Name"],
            "role": user["Role"]
        }
        data.append(item)
    return jsonify(
        data=data
    )


@app.route("/api/v1/users", methods=["POST"])
@jwt_required()
def create_user():
    """
    Create new user
    ---
    tags:
      - users
    parameters:
      - in: body
        name: body
        description: JSON payload containing user data
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: The user's name
              required: true
            role:
              type: string
              description: The user's role
              required: true
    responses:
      200:
        description: A dictionary with message
        schema:
          type: object
          properties:
            message:
              type: string
        examples:
          message: User created successfully!
    """
    authenticate_user()
    data = request.get_json(force=True)
    db.users.insert_one({"Name": data["name"], "Role": data["role"]})
    return jsonify(
        message="User created successfully!"
    )


@app.route("/api/v1/users/<id>", methods=["DELETE"])
@jwt_required()
def delete_user(id):
    """
    Delete user
    ---
    tags:
      - users
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: A dictionary with message
        schema:
          type: object
          properties:
            message:
              type: string
        examples:
          message: 'User with id: 644e3b181cb820830df11fb5 deleted successfully!'
    """
    authenticate_user()
    response = db.users.delete_one({"_id": ObjectId(id)})
    if response.deleted_count:
        message = f"User with id: {id} deleted successfully!"
    else:
        message = f"No User found with id {id}"
    return jsonify(
        message=message
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
