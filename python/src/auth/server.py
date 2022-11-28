import datetime
import os

import jwt  # JWT for auth, datetime to set expiration date of JWT and os to work with environment variables for MySQL
from flask import Flask, request  # Create server
from flask_mysqldb import MySQL  # To query database

server = Flask(__name__)
mysql = MySQL(server)

# config
server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST") # Get environment variable called MYSQL_HOST
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER") # Get environment variable called MYSQL_USER
server.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD") # Get environment variable called MYSQL_PASSWORD
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB") # Get environment variable called MYSQL_DB
server.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT")) # Get environment variable called MYSQL_PORT




# route
@server.route('/login', methods=["POST"])
def login():
    auth = request.authorization # provides credentials from request's header. The authorization header will container username and password can access via auth.username & auth.password
    if not auth:
        return "missing credentials", 401
    

    # check db for username/password
    # This auth service will have it's own mysql database and we are checking the user credentials against existing users.
    cur = mysql.connection.cursor()
    res = cur.execute("SELECT email, password FROM user WHERE email=%s", (auth.username,))
    # res is array of rows
    if res > 0:
        # user exists
        user_row = cur.fetchone()
        # email,password = user_row
        email = user_row[0]
        password = user_row[1]

        # TODO: this makes no sense - we already know username is equal to email because we queried it
        if auth.username != email or auth.password != password:
            return "invalid credentials", 401
        else:
            return createJWT(auth.username, os.environ.get("JWT_SECRET"), True)
    else:
        return "invalid credentials", 401 

# authz tells us if user is an admin
def createJWT(username, secret, authz): 
    return jwt.encode(
        {"username": username,
        "exp": datetime.datetime.utcnow()+datetime.timedelta(days=1), # expiration
        "iat": datetime.datetime.utcnow(), # issued at
        "admin": authz
        }, # payload
        secret,
        algorithm="HS256" # default but better to be verbose
    )

@server.route('/validate', methods=["POST"])
def validate():
    # Not sure why above used request.authorization and here we use request.headers["Authorization"]
    encoded_jwt = request.headers["Authorization"]
    if not encoded_jwt:
        return "missing credentials", 401
    
    # Comes as bearer <token> so need to split it
    encoded_jwt = encoded_jwt.split(" ")[1]
    print(encoded_jwt)

    try:
        decoded = jwt.decode(encoded_jwt, os.environ.get("JWT_SECRET"), algorithms=["HS256"])
        return decoded, 200
    except Exception as e:
        print(e)
        return "not authorized", 403

if __name__ == "__main__":
    # host basically allows the app to be accessible from anywhere not just our machine
    
    server.run(host="0.0.0.0",port=5000) # The host param allows our app to listen to any IP address on our host. If we didn't set it, the default is localhost which would mean our API wouldnt be available externally
