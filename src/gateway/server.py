import os, gridfs, pika, json, datetime, urllib
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util
from bson.objectid import ObjectId

server = Flask(__name__)

username = urllib.parse.quote_plus(os.environ.get('MONGO_USERNAME'))
password = urllib.parse.quote_plus(os.environ.get('MONGO_PASSWORD'))
mongo_uri = f"mongodb://{username}:{password}@{os.environ.get('MONGO_URI')}"
options="?authSource=admin&retryWrites=true&w=majority"

mongo_video = PyMongo(server, uri=f"{mongo_uri}{os.environ.get('MONGO_DATABASE_VIDEO')}{options}")
mongo_mp3 = PyMongo(server, uri=f"{mongo_uri}{os.environ.get('MONGO_DATABASE_MP3')}{options}")

fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()

def validate_and_decode_token(request):
    print(f'gateway upload request: {request}\n')

    # validation du token jwt
    decoded_token, err = validate.token(request)
    if err:
        return None, ('Token validation failed', 400)

    print(f'decoded token: {decoded_token}\n')
    return json.loads(decoded_token), None

@server.route('/api/v1/login', methods=['POST'])
def login():

    print(f'gateway login request: {request}\n')

    token, err = access.login(request)

    if not err:
        return token
    else:
        return err

@server.route('/api/v1/upload', methods=['POST'])
def upload():

    print(f'validate token from upload request: {request}\n')
    decoded_token, err = validate_and_decode_token
    if err:
        return err

    if decoded_token['admin']:

        if len(request.files) > 1 or len(request.files) < 1:
            return 'exactly 1 file required', 400

        if 'file' not in request.files:
            return "No file part in the request", 400

        f = request.files['file']
        print(f'Start uploading file -------- {datetime.datetime.now()}')
        message, err = util.upload(f, fs_videos, channel, decoded_token)
        if err:
            return err,

        print(f'End uploading file -------- {datetime.datetime.now()}')
        return 'Success upload!', 200

    else:
        return 'Not authorized, only admin should upload videos', 401

@server.route('/api/v1/download', methods=['GET'])
def download():

    print(f'validate token from download request: {request}\n')
    decoded_token, err = validate_and_decode_token
    if err:
        return err

    decoded_token = json.loads(decoded_token)
    if decoded_token['admin']:

        fid_string = request.args.get('fid')
        if not fid_string:
            return None, ('No fid provided, fid is required', 400)

        try:
            out = fs_mp3s.get(ObjectId(fid_string))
            return send_file(out, download_name=f'{fid_string}.mp3', as_attachment=True)

        except ValueError as err:
            print(f'Error downloading file {fid_string}: {err}')
            return None, ('Invalid fid provided, fid is required', 400)

    return None, ('Not authorized', 401)


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=8080, debug=True)


