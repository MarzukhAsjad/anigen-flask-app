import subprocess
from flask import Flask, Response
from flask_sse import sse
from flask import request, jsonify
from flask_cors import CORS
import importlib.util

# Import the config file
spec = importlib.util.spec_from_file_location('config', 'anigen-blender-utils/config.py')
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
Config = config_module

app = Flask(__name__)
CORS(app)
app.register_blueprint(sse, url_prefix='/stream')

@app.route('/')
def home():
    # Reset the config file    
    return 'AniGEN flask app is running!'

# This method will receive a json which will contain names of motions
@app.route('/config/motions', methods=['POST'])
def motions_receive():
    data = request.json
    # Store motions in the config file
    Config.MOTIONS = data['motions']
    # Append the last motion to the Config.MOTIONS 4 times and smooth it to 'idle'
    Config.MOTIONS = Config.MOTIONS + [Config.MOTIONS[-1]] * 4 + ['idle']
    write_config_file()
    return '', 200

# This method will receive a json which will contain the information about the blender character
@app.route('/config/character', methods=['POST'])
def character_receive():
    # Extract the character name from the json
    data = request.json
    character = data['character']
    # Store character information in the config file's BLEND_PATH
    blend_path = r'C:\Users\User\Desktop\FYP\flask-app\{}.blend'.format(character)
    Config.BLEND_PATH = blend_path
    write_config_file()
    return '', 200

# This method will receive a json which will contain the information about the total frames
@app.route('/config/frames', methods=['POST'])
def frames_receive():
    # Extract the total frames from the json
    data = request.json
    total_frames = data['total_frames']
    # Store total frames in the config file
    Config.TOTAL_FRAMES = total_frames
    write_config_file()
    return '', 200

# This method will receive a json which will contain the information about the import path
@app.route('/config/import', methods=['POST'])
def import_receive():
    # Extract the import path from the json
    data = request.json
    import_path = data['import_path']
    # Store import path in the config file
    Config.IMPORT_PATH = import_path
    write_config_file()
    return '', 200

# This method will receive a json which will contain the information about the render path
@app.route('/config/render', methods=['POST'])
def render_receive():
    # Extract the render path from the json
    data = request.json
    render_path = data['render_path']
    # Store render path in the config file
    Config.RENDER_PATH = render_path
    write_config_file()
    return '', 200

# This method will reset the config file
@app.route('/config/reset', methods=['POST'])
def reset_config():
    reset_config_file()
    return '', 200

# The notification receiver
@app.route('/notification', methods=['GET'])
def notification():
    # Extract the code and status from the config file
    # Return the code and status as a json response
    payload_cs = jsonify({'code': Config.CODE, 'status': Config.STATUS})
    payload_cs.headers['Access-Control-Allow-Origin'] = '*'
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
    command = r'blender {} --background --python anigen-blender-utils\main.py'.format(Config.BLEND_PATH)
    # Function to stream the output of the command back to the client
    def stream_output():
        nFrames = Config.TOTAL_FRAMES
        # Execute the command by creating a subprocess and reading the output
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
            # Process the output to get the necessary information
            yield line.rstrip() + '\n'
            # Render start
            if line.startswith('Blender ') and 'quit' not in line:
                Config.CODE = 'R'
                Config.STATUS = 0
            # Frame progress
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
                    # # Export start
                    # Config.CODE = 'E'
                    # Config.STATUS = 0

            # # Export complete
            # elif line.startswith('Export complete!'):
            #     Config.CODE = 'E'
            #     Config.STATUS = 1 
            #     # Reset the config file
            #     reset_config_file()
            
            # Write the output to the log file
            log.write(line)
        # Close the log file and the process
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
# Status and code for external notification receiver
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
    file_path = 'anigen-blender-utils\config.py'    
    with open(file_path, 'w') as f:
        f.write(config_data)

def reset_config_file():
    config_data = '''# Configuration for main.py
BLEND_PATH = r'path/to/blend/file.blend'
IMPORT_PATH = r'path/to/directory/containing/motion/files'
RENDER_PATH = r'path/to/render/output/directory'
MOTIONS = []
TOTAL_FRAMES = 200
# Status and code for external notification receiver
CODE = 'N'
STATUS = -1'''

    # Rewrite the configuration to the config.py file
    file_path = 'anigen-blender-utils\config.py'    
    with open(file_path, 'w') as f:
        f.write(config_data)
