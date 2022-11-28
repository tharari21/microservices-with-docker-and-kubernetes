import os, gridfs, pika, json # gridfs to store large files in mongodb, pika to interface with our RabbitMQ queue
from flask import Flask, request
# mongodb to store our files
from flask_pymongo import PyMongo

# we will create these
from auth import validate 
from auth_svc import access
from storage import util

server = Flask(__name__)
# host.minikube.internal gives us access to localhost within our local kubernetes cluster and this uri is a mongodb uri that's the endpoint to interact with mongodb
server.config["MONGO_URI"] = "mongodb://host.minikube.internal:27017/videos"

# PyMongo wraps our flask server which allows us to interface with mongodb. Manages mongodb connections for your flask app
# Abstracts the handling of mongodb in flask app
mongo = PyMongo(server)

# Wrap our mongodb which enables us to use mongodb
fs = gridfs.GridFS(mongo.db)
'''
Were using mongodb to store our files. Files being both the MP3 files and our video files. If we go to MongoDB limits and thresholds documentation, you'll see that a BSON (Binary JSON)
document size has a max of 16MB. Handling files over 16MB in memory for mongo will slow down performance so they say to use gridFS to store larger file sizes. GridFS shards the files to make it possible to use such large files
It divides files into parts or chunks and stores each chunk as a separate document. GridFS uses 2 collections (tables) to store files. One collection stores the chunks and the other stores the metadata. The metadata
contains the necessary information to reassemble the chunks to create or reform the original file. 
'''

# configure rabbitmq connection - rabbitmq string refers to the rabbitmq host or service we will make later
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq")) # makes connection to rabbitMQ synchroneously
channel = connection.channel()

@server.route('/login', methods=["POST"])
def login():
    token, err = access.login(request)
    if not err:
        return token
    else:
        return err
@server.route('/upload', methods=["POST"])
def upload():
    access, err = validate.token(request)
    # access is a string of the payload of the logged in user so convert it to json
    if err:
        return err
    access = json.loads(access)

    if access["admin"]:
        # Get files sent by request
        print(request.files)
        print(len(request.files))
        if len(request.files) > 1 or len(request.files) < 1:
            return "exactly one file required", 400
        
        for _, f in request.files.items():
            # This function will return error if something goes wrong and None if there's no error
            err = util.upload(f, fs, channel, access)
            if err:
                return err
            return "success!", 200
    else:
        return "Not authorized", 401

@server.route('/download', methods=["GET"])
def download():
    pass

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)