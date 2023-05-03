from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from flasgger import Swagger

db_name = "SampleDotCom"
app = Flask(__name__)
swagger = Swagger(app)
app.config["MONGO_URI"] = f"mongodb://mongo:27017/{db_name}"
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
mongo = PyMongo(app)
db = mongo.db

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

@app.route("/api/v1/users")
def get_all_users():
    """
    Get all users
    ---
    tags:
      - users
    responses:
      200:
        description: A dectionary containing all users
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
        description: A dectionary with message
        schema:
          type: object
          properties:
            message:
              type: string
        examples:
          message: User created successfully!
    """
    data = request.get_json(force=True)
    db.users.insert_one({"Name": data["name"], "Role": data["role"]})
    return jsonify(
        message="User created successfully!"
    )

@app.route("/api/v1/users/<id>", methods=["DELETE"])
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
        description: A dectionary with message
        schema:
          type: object
          properties:
            message:
              type: string
        examples:
          message: 'User with id: 644e3b181cb820830df11fb5 deleted successfully!'
    """
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
