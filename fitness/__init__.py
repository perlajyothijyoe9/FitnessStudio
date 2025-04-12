from flask import Flask
from flask_pymongo import PyMongo
from flask_wtf import CSRFProtect

csrf = CSRFProtect()

fitness = Flask(__name__)
fitness.config["MONGO_URI"] = "mongodb://localhost:27017/fitness-studio"
fitness.config["WTF_CSRF_ENABLED"] = False
fitness.secret_key = "notokenneeded"
mongo = PyMongo(fitness)
csrf.init_app(fitness)

fitness.jinja_env.globals.update(str=str)


if __name__ == "__main__":
    fitness.run()
