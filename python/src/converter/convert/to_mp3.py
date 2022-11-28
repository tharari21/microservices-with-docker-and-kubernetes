import pika, json, tempfile, os
from bson.objectid import ObjectId
import moviepy.editor # convert videos to mp3

def start(message, fs_videos, fs_mp3s, channel):
    'function called by consumer to get message from queue with videos and mp3 mongo gridFS collections and convert the file'
    message = json.loads(message) # convert message from json string

    # create a temporary file to write contents of file
    tf = tempfile.NamedTemporaryFile() # returns an object with a file-like interface. The file is accessible by name
    # video contents - get the video from gridfs by getting video file id from the message which we encode in the gateway
    # objectId is a mongodb thing. By default, ObjectId() creates a new unique identifier but with an identifier already defined it simply converts it to an ObjectId which is how mongo knows which object you refer to.
    # We can't get the file using the string version of the id so we convert to ObjectId
    out = fs_videos.get(ObjectId(message["video_fid"]))
    # add video content to tempfile
    tf.write(out.read())
    # Extract audio from tf file and make a file with just the audio
    audio = moviepy.editor.VideoFileClip(tf.name).audio
    # tempfile is deleted after you close
    tf.close()

    # Write audio to the file.
    # Gets the dir in our os where tempfiles are being stored and add the filename we want our mp3 to be
    # Reason we use tempfile is because this file is going into the database we don't need to save locally but we need the file to create it that's all
    # Since video_fid is unique from gridfs we'll never get a duplicate file name
    tf_path = tempfile.gettempdir() + f"/{message['video_fid']}.mp3"
    audio.write_audiofile(tf_path)# Write audio to tempfile

    # save file to mongo
    f = open(tf_path, "rb")
    data = f.read()
    # Store mp3 file in gridfs
    fid = fs_mp3s.put(data)
    f.close()
    # audio.write_audiofile created an actual file and we don't want to store that.
    os.remove(tf_path)
    
    # save mp3 id to message to put back on queue
    message["mp3_fid"] = str(fid)

    try:
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("MP3_QUEUE"),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as err:
        fs_mp3s.delete(fid)
        # Where we call this method in consumer.py we check if it returns something. If it does then we know its an error otherwise the message was successfully added to queue
        return "failed to publish message"


    