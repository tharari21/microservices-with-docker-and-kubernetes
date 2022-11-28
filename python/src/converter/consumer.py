import pika, sys, os, time
from pymongo import MongoClient
import gridfs
from convert import to_mp3

def main():
    client = MongoClient("host.minikube.internal", 27017)
    db_videos = client.videos # videos datanase
    db_mp3s = client.mp3s

    # gridfs
    fs_videos = gridfs.GridFS(db_videos) 
    fs_mp3s = gridfs.GridFS(db_mp3s)
    
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq") # rabbitmq is our service name and it will resolve to the host IP address of our service
    )
    channel = connection.channel()

    def callback(channel, method, properties, body):
        'called when message is taken off queue'
        err = to_mp3.start(body,fs_videos, fs_mp3s,channel)
        if err:
            # delivery tag is how rabbitmq knows which message you want to acknowledged failed
            channel.basic_nack(delivery_tag=method.delivery_tag) # Send a negative acknowledgement back to queue - the message therefore won't be removed from queue because we want to keep them on queue so they can be reprocessed if failed
        else:
            channel.basic_nack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get('VIDEO_QUEUE'), # name of queue - put in env variable in case it changes
        on_message_callback=callback
    )
    print("Waiting for messages. To exit press CTRL+C")

    channel.start_consuming()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # main will run until we click ctrl+c
        print("Interrupted")
        # Gracefully shut down service
        try:
            
            sys.exit()
        except SystemExit:
            os.exit(0)