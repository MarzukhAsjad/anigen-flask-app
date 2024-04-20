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
        nFrames = 200
        # count = 0
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
            if line.startswith('Append frame '):
                # TODO: Modify the progress calculation because right now it is just dummy calculation
                iFrame = int(line.removeprefix('Append frame '))
                percent_progress = int((iFrame * 100) / nFrames)
                threading.Thread(target=send_notification, args=('P',percent_progress)).start()
                if iFrame == nFrames:
                    threading.Thread(target=send_notification, args=('R',1)).start()

            elif line.startswith('Blender ') and 'quit' not in line:
                threading.Thread(target=send_notification, args=('R',0)).start()
                
            elif line.startswith('FBX export starting...'):
                threading.Thread(target=send_notification, args=('E',0)).start()            

            elif line.startswith('Export complete!'):
                threading.Thread(target=send_notification, args=('E',1)).start()    
            
            # Write the output to the log file
            log.write(line)

        process.stdout.close()
        process.wait()

    return Response(stream_output(), mimetype='text/event-stream')

def send_notification(code,status):
    # Define the URL of the endpoint
    url = 'http://localhost:5000/notification'

    # Define the JSON payload
    # JSON payload should contain the code and the status message
    # Code 'R' is for 'Rendering', and status '0' is the 'Rendering started', '1' is for 'Rendering completed', and '-1' is for 'Rendering failed'
    # Code 'P' is for 'Rendering Processing', and status 'd' is for 'Rendering Processing at d %'
    # Code 'E' is for 'Exporting', and status '0' is for 'Exporting started', '1' is for 'Exporting completed' and '-1' is for 'Exporting failed'

    # This payload takes code and status as arguments directly
    payload_cs = {
        'code': code,
        'status': status
    }

    payload = payload_cs

    # Send the POST request with the JSON payload
    response = requests.post(url, json=payload)
    # Check the response status code
    if response.status_code == 200:
        # print('Notification sent successfully')
        pass
    else:
        print('Failed to send notification')

