from fileinput import filename

import pika, json, os

def upload(f, fs, channel, access):
    # Putting the file into mongodb
    print(f'Putting file in mongo db\n')
    try:
        file_content = f.read()
        fid = fs.put(file_content, filename= f.filename, content_type= f.content_type)
    except Exception as err:
        print(err)
        return None, (f'Internal server error' , 500)

    print(f'File {f.filename} successfully saved in mongo db\n')

    # If upload to mongo success push message to rabbitmq
    message = {
        'video_fid': str(fid),
        'mp3_fid': None,
        'username': access['username'],
    }

    try:
        print(f'publishing message {message} to rabbitmq\n')
        channel.basic_publish(
            exchange='',
            routing_key='video',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )

        return 'Success', 200

    except Exception as err:
        print(err)
        fs.delete(fid)
        return None, (f'Internal server error' , 500)