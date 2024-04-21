import subprocess
import threading
from flask import Flask, Response
from flask_sse import sse
from flask import request
import config as Config
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.register_blueprint(sse, url_prefix='/stream')

@app.route('/')
def home():
    print(Config.BLEND_PATH)
    print(Config.IMPORT_PATH)
    print(Config.RENDER_PATH)
    print(Config.MOTIONS)
    return 'This is the AniGEN Flask app to execute anigen-blender-utils. Use /exec to execute the command.'

# This method will receive a json which will contain names of motions
@app.route('/motions', methods=['POST'])
def motions_receive():
    data = request.json
    # TODO: Store motions in the config file
    Config.MOTIONS = data['motions']
    return '', 200

# This method will receive a json which will contain the information about the blender character
@app.route('/character', methods=['POST'])
def character_receive():
    # Extract the character name from the json
    data = request.json
    character = data['character']
    # Store character information in the config file
    blend_path = r'C:\Users\User\Desktop\FYP\blender-utils\{}.blend'.format(character)
    Config.BLEND_PATH = blend_path
    return '', 200

# The notification receiver
@app.route('/notification', methods=['GET'])
def notification_receive():
    # Check if the process is finished
    # Return the code and status as a json response
    payload_cs = {
        'code': Config.CODE,
        'status': Config.STATUS
    }
    return payload_cs, 200

@app.route('/test')
def test():
    write_config_file(Config.BLEND_PATH, Config.IMPORT_PATH, Config.RENDER_PATH, Config.MOTIONS, Config.TOTAL_FRAMES)
    return "config_data has been modified successfully"

@app.route('/exec')
def exec():
    # Execute the execute_command in a thread
    threading.Thread(target=execute_command).start
    return "", 200

def execute_command():
    # Create a file to store the log
    log = open('log.txt', 'w')

    # The command to be executed
    command = r'blender {} --background --python main.py'.format(Config.BLEND_PATH)
    # Function to stream the output of the command back to the client
    def stream_output():
        nFrames = Config.TOTAL_FRAMES
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

            # Process the output to get the necessary information

            # Render start
            if line.startswith('Blender ') and 'quit' not in line:
                Config.CODE = 'R'
                Config.STATUS = 0
            
            elif line.startswith('Append frame '):
                iFrame = int(line.removeprefix('Append frame '))
                percent_progress = int((iFrame * 100) / nFrames)
                # Render progress
                Config.CODE = 'P'
                Config.STATUS = percent_progress
                if iFrame == nFrames:
                    # Render complete
                    Config.CODE = 'R'
                    Config.STATUS = 1
                    # Export start
                    Config.CODE = 'E'
                    Config.STATUS = 0

            # Export complete
            elif line.startswith('Export complete!'):
                Config.CODE = 'E'
                Config.STATUS = 1 
            
            # Write the output to the log file
            log.write(line)

        process.stdout.close()
        process.wait()

    return Response(stream_output(), mimetype='text/event-stream')

def write_config_file(blend_path, import_path, render_path, motions, total_frames, status, code):
    config_data = '''# Configuration for main.py
BLEND_PATH = r'{blend_path}'
IMPORT_PATH = r'{import_path}'
RENDER_PATH = r'{render_path}'
MOTIONS = {motions}
TOTAL_FRAMES = {total_frames}
# Status and code for the notification receiver
STATUS = {status}
CODE = {code}'''.format(
        blend_path=blend_path,
        import_path=import_path,
        render_path=render_path,
        motions=motions,
        total_frames=total_frames,
        status=status,
        code=code
        )

    # TODO: Remove these 2 lines
    print(config_data)

    # Rewrite the configuration to the config.py file
    file_path = 'config.py'    
    with open(file_path, 'w') as f:
        f.write(config_data)