import subprocess
from flask import Flask, Response
from flask_sse import sse

app = Flask(__name__)
app.register_blueprint(sse, url_prefix='/stream')

@app.route('/')
def home():
    return 'This is the AniGEN Flask app to execute anigen-blender-utils. Use /exec to execute the command.'

@app.route('/exec')
def execute_command():
    # The command to be executed
    command = r'blender "C:\Users\User\Desktop\FYP\blender-utils\Xbot.blend" --background --python C:\Users\User\Desktop\FYP\blender-utils\main.py'

    # Function to stream the output of the command back to the client
    def stream_output():
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True
        )
        # Read the output line by line 
        # TODO: Process the output to send only the relevant information to another endpoint
        for line in iter(process.stdout.readline, ''):
            yield line.rstrip() + '\n'

        process.stdout.close()
        process.wait()

    return Response(stream_output(), mimetype='text/event-stream')