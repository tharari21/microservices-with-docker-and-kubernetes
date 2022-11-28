import pika, json
def upload(f, fs, channel, access):
    # First upload video file to mongodb database using gridfs
    try:
        # put file in mongodb through gridfs - returns a file id of the file in database
        fid = fs.put(f)
    except Exception as err:
        return "Internal server error", 500

    # Create message for queue
    message ={
        "video_fid": str(fid),
        "mp3_fid": None, # This will be set when the downstream service (service that converts file) completes
        "username": access["username"], # Need to know who requested so we can only allow them to get the file
    }
    # Add message to RabbitMQ queue
    try:
        channel.basic_publish(
            exchange="", # Use default exchange
            routing_key="video", # Name of queue to bound to exchange
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE # Ensures messages are persisted in our queue in the event of a pod crash. Since our pod for our RabbitMQ queue is a stateful pod within the cluster, we need to make sure that messages added to the queue are persisted so when pod fails and resets we still have what was on the queue before
            )
        )

    except:
        # delete file from mongodb because if there's no message on the queue for the file but the file is still in DB, that file will never be processed because our converter service will never get it.
        fs.delete(fid)
        return "internal server error", 500
        