"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Character, Favorite
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/users', methods=['GET'])
def get_users(user_id=None):
    if user_id:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"msg": "User not found"}), 404
        return jsonify(user.serialize()), 200

    users = User.query.all()
    users = [user.serialize() for user in users]
    return jsonify(users), 200

@app.route('/planets', methods=['GET'])
@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planets(planet_id=None):
    if planet_id:
        planet = Planet.query.get(planet_id)
        if not planet:
            return jsonify({"msg": "Planet not found"}), 404
        return jsonify(planet.serialize()), 200

    planets = Planet.query.all()
    planets = [planet.serialize() for planet in planets]
    return jsonify(planets), 200

@app.route('/people', methods=['GET'])
@app.route('/people/<int:character_id>', methods=['GET'])
def get_characters(character_id=None):
    if character_id:
        character = Character.query.get(character_id)
        if not character:
            return jsonify({"msg": "character not found"}), 404
        return jsonify(character.serialize()), 200

    characters = Character.query.all()
    characters = [character.serialize() for character in characters]
    return jsonify(characters), 200

@app.route('/users/favorites', methods=['GET'])
def get_all_user_favorites():
    favorites = Favorite.query.all()
    favorites = list(map(lambda favorite: favorite.serialize(), favorites))
    return jsonify(favorites), 200

@app.route('/users', methods=['POST'])
def create_user():
    body = request.get_json()
    required_fields = ['email', 'password']
    if not all(field in body for field in required_fields):
        return jsonify({"msg": "Missing required fields"}), 400

    new_user = User(
        email=body.get('email'),
        password=body.get('password'),
        first_name=body.get('first_name'),
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.serialize()), 201

@app.route('/planet', methods=['POST'])
def create_planet():
    body = request.get_json()
    if 'name' not in body:
        return jsonify({"msg": "Missing name field"}), 400
    new_planet = Planet(name=body['name'])
    if 'properties' in body:
        new_planet.properties = body['properties']
    db.session.add(new_planet)
    db.session.commit()
    return jsonify(new_planet.serialize()), 201

@app.route('/people', methods=['POST'])
def create_character():
    body = request.get_json()
    if 'name' not in body:
        return jsonify({"msg": "Missing name field"}), 400
    new_character = Character(name=body['name'])
    if 'properties' in body:
        new_character.properties = body['properties']
    db.session.add(new_character)
    db.session.commit()
    return jsonify(new_character.serialize()), 201

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id=None):
    body = request.get_json()
    
    if 'user_id' not in body:
        return jsonify({"error": "The 'user_id' field is required"}), 400
    try:
        user_id = int(body['user_id'])
    except ValueError:
        return jsonify({"error": "Invalid 'user_id' value"}), 400
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    if planet_id is None:
        if 'planet_id' not in body:
            return jsonify({"error": "The 'planet_id' field is required"}), 400
        try:
            planet_id = int(body['planet_id'])
        except ValueError:
            return jsonify({"error": "Invalid 'planet_id' value"}), 400
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"error": "Planet not found"}), 404
    try:
        new_favorite = Favorite(user=user, planet=planet)
        db.session.add(new_favorite)
        db.session.commit()
        return jsonify(new_favorite.serialize()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to add favorite"}), 500
    
@app.route('/favorite/character/<int:character_id>', methods=['POST'])
def add_favorite_charcter(character_id=None):
    body = request.get_json()
    
    if 'user_id' not in body:
        return jsonify({"error": "The 'user_id' field is required"}), 400
    try:
        user_id = int(body['user_id'])
    except ValueError:
        return jsonify({"error": "Invalid 'user_id' value"}), 400
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    if character_id is None:
        if 'character_id' not in body:
            return jsonify({"error": "The 'character_id' field is required"}), 400
        try:
            character_id = int(body['character_id'])
        except ValueError:
            return jsonify({"error": "Invalid 'character_id' value"}), 400
    character = character.query.get(character_id)
    if character is None:
        return jsonify({"error": "Character not found"}), 404
    try:
        new_favorite = Favorite(user=user, character=character)
        db.session.add(new_favorite)
        db.session.commit()
        return jsonify(new_favorite.serialize()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to add favorite"}), 500
    
@app.route('/planet/<int:id>', methods=['DELETE'])
def delete_planet(id):
    planet = Planet.query.get(id)
    if planet is None:
        return jsonify({'error': 'Planet not found'}), 404
    try:
        db.session.delete(planet)
        db.session.commit()
        return jsonify({'message': 'Planet deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete planet'}), 500

@app.route('/people/<int:id>', methods=['DELETE'])
def delete_character(id):
    character = Character.query.get(id)
    if character is None:
        return jsonify({'error': 'Character not found'}), 404
    try:
        db.session.delete(character)
        db.session.commit()
        return jsonify({'message': 'Character deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete character'}), 500
    
@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet:
        try:
            db.session.delete(planet)
            db.session.commit()
            return jsonify({"message": "Favorite planet deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Failed to delete favorite planet"}), 500
    else:
        return jsonify({"error": "Planet not found"}), 404

@app.route('/favorite/character/<int:character_id>', methods=['DELETE'])
def delete_favorite_character(character_id):
    character = Character.query.get(character_id)
    if character:
        try:
            db.session.delete(character)
            db.session.commit()
            return jsonify({"message": "Favorite character deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Failed to delete favorite character"}), 500
    else:
        return jsonify({"error": "Character not found"}), 404

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
