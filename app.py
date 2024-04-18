import subprocess
import threading
from flask import Flask, Response
from flask_sse import sse
import requests
from flask import request

app = Flask(__name__)
app.register_blueprint(sse, url_prefix='/stream')

@app.route('/')
def home():
    return 'This is the AniGEN Flask app to execute anigen-blender-utils. Use /exec to execute the command.'

@app.route('/exec')
def execute_command():
    # Create a file to store the log
    log = open('log.txt', 'w')

    # The command to be executed
    command = r'blender "C:\Users\User\Desktop\FYP\blender-utils\Xbot.blend" --background --python C:\Users\User\Desktop\FYP\blender-utils\main.py'
    # Function to stream the output of the command back to the client
    def stream_output():
        count = 0
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True
        )
        # Read the output line by line 
        for line in iter(process.stdout.readline, ''):
            yield line.rstrip() + '\n'
            # TODO: Process the output to only get the necessary information
            if count % 10 == 0:
                threading.Thread(target=send_notification).start()
            
            # Write the output to the log file
            log.write(line)
            count += 1

        process.stdout.close()
        process.wait()

    return Response(stream_output(), mimetype='text/event-stream')

@app.route('/notification', methods=['POST'])
def receive_notification():
    # Get the JSON payload from the request
    data = request.json

    # Print the data 
    print(data['message'])

    # Send a response
    return 'Notification received'

def send_notification():
    # Define the URL of the endpoint
    url = 'http://localhost:5000/notification'

    # Define the JSON payload
    payload = {
        'message': 'Hello, world!'
    }

    # Send the POST request with the JSON payload
    response = requests.post(url, json=payload)
    # Check the response status code
    if response.status_code == 200:
        # print('Notification sent successfully')
        pass
    else:
        print('Failed to send notification')

