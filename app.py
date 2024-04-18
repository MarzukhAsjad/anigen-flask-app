import subprocess
import threading
from flask import Flask, Response
from flask_sse import sse
import requests
from flask import request
import config as Config

app = Flask(__name__)
app.register_blueprint(sse, url_prefix='/stream')

@app.route('/')
def home():
    print(Config.BLEND_PATH)
    print(Config.IMPORT_PATH)
    print(Config.RENDER_PATH)
    print(Config.MOTIONS)
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
            if (count % 10) == 0:
                # TODO: Modify the progress calculation because right now it is just dummy calculation
                progress = int((count * 100) / 200)
                threading.Thread(target=send_notification, args=(progress,)).start()
            
            # Write the output to the log file
            log.write(line)
            count += 1

        process.stdout.close()
        process.wait()

    return Response(stream_output(), mimetype='text/event-stream')

# THIS IS A DEMO ENDPOINT TO TEST THE NOTIFICATION FUNCTIONALITY
# TODO: Remove this endpoint
@app.route('/notification', methods=['POST'])
def receive_notification():
    # Get the JSON payload from the request
    data = request.json

    # Print the data 
    print(data['code'], data['status'])

    # Send a response
    return 'Notification received'

# Function to send notifications in a separate thread
def send_notification_thread(progress):
    send_notification((progress,))  # Wrap the progress value in a tuple

def send_notification(progress):
    # Define the URL of the endpoint
    url = 'http://localhost:5000/notification'

    # Define the JSON payload
    # JSON payload should contain the code and the status message
    # Code 'R' is for 'Rendering', and status '0' is the 'Rendering started', '1' is for 'Rendering completed', and '-1' is for 'Rendering failed'
    # Code 'P' is for 'Rendering Processing', and status 'd' is for 'Rendering Processing at d %'
    # Code 'E' is for 'Exporting', and status '0' is for 'Exporting started', '1' is for 'Exporting completed' and '-1' is for 'Exporting failed'
    
    # Example payloads
    # This payload is for 'Rendering started'
    payload0 = {
        'code': 'R',
        'status': '0'
    }

    # This payload is for 'Rendering process now at 70%'
    payload1 = {
        'code': 'P',
        'status': progress
    }

    # This payload is for 'Exporting completed'
    payload2 = {
        'code': 'E',
        'status': '1'
    }

    # This payload is for 'Exporting failed'
    payload3 = {
        'code': 'E',
        'status': '-1'
    }

    payload = payload1

    # Send the POST request with the JSON payload
    response = requests.post(url, json=payload)
    # Check the response status code
    if response.status_code == 200:
        # print('Notification sent successfully')
        pass
    else:
        print('Failed to send notification')

