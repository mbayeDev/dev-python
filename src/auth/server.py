import os, datetime
import jwt
from flask import Flask, request, jsonify
from flask_mysqldb import MySQL

server = Flask(__name__)
mysql = MySQL(server)

#config
server.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
server.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
server.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')
server.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
server.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT'))

def create_jwt_token(userid, username, secret, authz):

    payload = {
        'sub': str(userid),
        'username': username,
        'exp': datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
        'iat': datetime.datetime.now(tz=datetime.timezone.utc),
        'admin': authz,
    }

    return jwt.encode( payload, secret, algorithm='HS256' )

@server.route('/api/v1/login', methods=['POST'])
def login():
    print(f'auth request: {request}\n')

    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return "Missing credentials username or password", 401

    #check credentials in db
    cur = mysql.connection.cursor()
    res = cur.execute("SELECT id, email, password FROM user WHERE email = %s", (auth.username,))

    print(f'Mysql connexion OK: {res}\n')

    if res > 0:
        user_row = cur.fetchone()
        if user_row is None:
            return "Invalid credentials: unable to fetch user from db", 401

        userid = user_row[0]
        email = user_row[1]
        password = user_row[2]

        print(f'userid: {userid}, email: {email}, password: {password}')

        if str(password).strip() != str(auth.password).strip():
            return f"Invalid Password {password}!={auth.password} !!!", 401
        else:
            return create_jwt_token(userid, email, os.environ.get('JWT_SECRET'), True)
            
    else:
        return "Invalid credentials", 401

@server.route('/api/v1/validate', methods=['POST'])
def validate():
    encoded_jwt = request.headers['Authorization']

    if not encoded_jwt:
        return "Missing authorization header", 401

    encoded_jwt = encoded_jwt.strip().replace('Bearer ', '')

    try:
        decoded_token = jwt.decode(encoded_jwt, os.environ.get('JWT_SECRET'), algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return "Token has expired", 403
    except jwt.InvalidTokenError as err:
        return f"Invalid authorization header {err}", 403

    return decoded_token, 200

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5000, debug=True)
