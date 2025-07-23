import pika, sys, os, urllib
from pymongo import MongoClient
import gridfs
from convert import to_mp3

def main():
    options = "?authSource=admin&retryWrites=true&w=majority"
    username = urllib.parse.quote_plus(os.environ.get('MONGO_USERNAME'))
    password = urllib.parse.quote_plus(os.environ.get('MONGO_PASSWORD'))
    mongo_uri = f"mongodb://{username}:{password}@{os.environ.get('MONGO_URI')}{options}"

    client = MongoClient(mongo_uri)
    db_videos = client.videos
    db_mp3s = client.mp3s

    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    #rabbitmq connection
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq')
    )
    channel = connection.channel()
    channel.queue_declare(queue=os.environ.get('VIDEO_QUEUE'), durable=True, passive=True)

    def callback(ch, method, properties, body):
        message, err = to_mp3.start(body, fs_videos, fs_mp3s, ch)
        if err:
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get('VIDEO_QUEUE'),
        on_message_callback= callback,
    )

    print('Waiting for messages... To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nInterrupted!')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)