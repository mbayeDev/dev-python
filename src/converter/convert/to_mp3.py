import pika, json, tempfile, os
from bson.objectid import ObjectId
import moviepy

def start(message, fs_videos, fs_mp3s, channel):
    message = json.loads(message)

    #create empty temp file
    tf = tempfile.NamedTemporaryFile()
    #videos content
    out = fs_videos.get(ObjectId(message['video_fid']))
    #add videos content to empty file
    tf.write(out.read())
    # create audio mp3 from temp video file
    with moviepy.VideoFileClip(tf.name, audio=True).subclipped(0, -5) as clip:
        #write audio to the file
        tf_path=tempfile.gettempdir() + f"/{message['video_fid']}.mp3"
        print(f"Converting {message['video_fid']} to {tf_path}")
        if clip.audio is not None:

            clip.audio.write_audiofile(out.name)
            tf.close()
            print('success audio file written to temporary folder')

            # save the file to mongo mp3s gridfs
            print('Save audio file to mongo db')

            f = open(tf_path, 'rb')
            data = f.read()
            fid = fs_mp3s.put(data)
            f.close()
            os.remove(tf_path)

            message['mp3_fid'] = str(fid)

            #publish message to mp3 queue
            try:
                channel.basic_publish(
                    exchange='',
                    routing_key=os.environ['MP3_QUEUE'],
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                    )
                )
                print('Success audio file save to mongo db')
                return 'Success audio file save to mongo db', None
            except Exception as err:
                fs_mp3s.delete(fid)
                return None, f'Failed to publish mp3 file:\n{err}'

        else:
            return None, 'Video file conversion to audio failed'