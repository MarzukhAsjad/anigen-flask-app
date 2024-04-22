import subprocess
from flask import Flask, Response
from flask_sse import sse
from flask import request, jsonify
import config as Config
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.register_blueprint(sse, url_prefix='/stream')

@app.route('/')
def home():
    # Reset the config file    
    return 'This is the AniGEN Flask app to execute anigen-blender-utils. Use /exec to execute the command.'

# This method will receive a json which will contain names of motions
@app.route('/motions', methods=['POST'])
def motions_receive():
    data = request.json
    # Store motions in the config file
    Config.MOTIONS = data['motions']
    write_config_file()
    return '', 200

# This method will receive a json which will contain the information about the blender character
@app.route('/character', methods=['POST'])
def character_receive():
    # Extract the character name from the json
    data = request.json
    character = data['character']
    # Store character information in the config file's BLEND_PATH
    blend_path = r'C:\Users\User\Desktop\FYP\blender-utils\{}.blend'.format(character)
    Config.BLEND_PATH = blend_path
    write_config_file()
    return '', 200

# The notification receiver
@app.route('/notification', methods=['GET'])
def notification():
    # Extract the code and status from the config file
    # Return the code and status as a json response
    payload_cs = jsonify({'code': Config.CODE, 'status': Config.STATUS})
    payload_cs.headers.add('Access-Control-Allow-Origin', 'http://localhost')
    return payload_cs, 200

@app.route('/test')
def test():
    write_config_file()
    return "config_data has been modified successfully"

@app.route('/exec')
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
                # Reset the config file
                reset_config_file()
            
            # Write the output to the log file
            log.write(line)

        process.stdout.close()
        process.wait()
    
    return Response(stream_output(), mimetype='text/event-stream')

def write_config_file():
    config_data = '''# Configuration for main.py
BLEND_PATH = r'{blend_path}'
IMPORT_PATH = r'{import_path}'
RENDER_PATH = r'{render_path}'
MOTIONS = {motions}
TOTAL_FRAMES = {total_frames}
# Status and code for the notification receiver
CODE = '{code}'
STATUS = {status}'''.format(
        blend_path=Config.BLEND_PATH,
        import_path=Config.IMPORT_PATH,
        render_path=Config.RENDER_PATH,
        motions=Config.MOTIONS,
        total_frames=Config.TOTAL_FRAMES,
        status=Config.STATUS,
        code=Config.CODE
        )

    # TODO: Remove these 2 lines
    print(config_data)

    # Rewrite the configuration to the config.py file
    file_path = 'config.py'    
    with open(file_path, 'w') as f:
        f.write(config_data)

def reset_config_file():
    config_data = '''# Configuration for main.py
BLEND_PATH = r'{blend_path}'
IMPORT_PATH = r'{import_path}'
RENDER_PATH = r'{render_path}'
MOTIONS = []
TOTAL_FRAMES = 200
# Status and code for the notification receiver
CODE = 'N'
STATUS = -1'''.format(
        blend_path=Config.BLEND_PATH,
        import_path=Config.IMPORT_PATH,
        render_path=Config.RENDER_PATH
        )

    # Rewrite the configuration to the config.py file
    file_path = 'config.py'    
    with open(file_path, 'w') as f:
        f.write(config_data)
