import subprocess, os, requests
from flask import Flask, Response
from flask_sse import sse
from flask import request, jsonify
from flask_cors import CORS
import importlib.util
import time
import logging
import base64
import json  # Import the json module
from pydub import AudioSegment  # Import the AudioSegment class from the pydub module

# Import the config file
spec = importlib.util.spec_from_file_location('config', 'anigen-blender-utils/config.py')
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
Config = config_module
# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(levelname)s: %(message)s')
UPLOAD_FOLDER = os.getcwd()

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
    blend_path = data['character']
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

# This method will delete the rendered file and reset the config file
@app.route('/config/reset', methods=['POST'])
def reset_config():
    delete_rendered_animation()
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

# This method will return the log file
@app.route('/log')
def log():
    with open('log.txt', 'r') as f:
        return f.read()

@app.route('/exec')
def execute_command():
    # Create a file to store the log
    log = open('log.txt', 'w')

    # The command to be executed
    command = r'xvfb-run -a blender {} --background --python anigen-blender-utils/main.py'.format(Config.BLEND_PATH)
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

# This method will use theta video api to upload the video
@app.route('/upload_video', methods=['POST'])
def upload_video():
    # Extract the video file from the request
    data = request.json
    video_path = data['video_path']
    # Step 1: Create a pre-signed URL to Upload a Video
    url = 'https://api.thetavideoapi.com/upload'
    headers = {
        'x-tva-sa-id': os.environ.get('THETA_VIDEO_API_ID'),
        'x-tva-sa-secret': os.environ.get('THETA_VIDEO_API_SECRET')
    }
    response = requests.post(url, headers=headers)
    response_data = response.json()

    # Extract relevant information from the response
    upload_info = response_data['body']['uploads'][0]
    presigned_url = upload_info['presigned_url']
    upload_id = upload_info['id']
    
    # Step 2: Extract video_path from the request body and read the video data
    if request.is_json:
        request_data = request.get_json()
        video_path = request_data.get('video_path')
        
        if video_path and os.path.isfile(video_path):  # Check if the file exists
            with open(video_path, 'rb') as video_file:
                video_data = video_file.read()
                
            # Encode the binary data in Base64
            encoded_video_data = None
            try:
                encoded_video_data = base64.b64encode(video_data).decode('utf-8')
            except Exception as e:
                logging.error(f"Failed to encode video data: {e}")
            
            # Upload the video using the presigned URL
            response = requests.put(presigned_url, headers={'Content-Type': 'application/octet-stream'}, data=video_data)
            
            if response.status_code == 200:
                # Step 3: Transcode the video using the initial upload ID
                transcode_url = 'https://api.thetavideoapi.com/video'
                transcode_data = {
                    "source_upload_id": upload_id,
                    "playback_policy": "public",
                    "nft_collection": "0x5d0004fe2e0ec6d002678c7fa01026cabde9e793",
                    "metadata": {
                        "key": "value"
                    }
                }                
                try:
                    transcode_response = requests.post(transcode_url, headers={**headers, 'Content-Type': 'application/json'}, json=transcode_data)
                    
                    if transcode_response.status_code == 200:
                        while True:
                            try:
                                # Step 4: Check the status of the transcoding process
                                video_id = transcode_response.json()["body"]["videos"][0]["id"]
                                status_url = 'https://api.thetavideoapi.com/video/{}'.format(video_id)
                                status_response = requests.get(status_url, headers=headers)
                                
                                # Check if the response is valid JSON
                                try:
                                    status_data = status_response.json()
                                except ValueError as e:
                                    logging.error(f"Failed to parse status response as JSON: {e}")
                                    return jsonify({"error": "Failed to parse status response as JSON"}), 500
                                
                                # Check if 'body' and 'videos' keys exist
                                if 'body' in status_data and 'videos' in status_data['body']:
                                    try:
                                        status = status_data["body"]["videos"][0]["state"]
                                        if status == 'success':
                                            # Step 5: Get the video URL
                                            video_url = status_data["body"]["videos"][0]["playback_uri"]
                                            return jsonify({"video_url": video_url, "encoded_video_data": encoded_video_data}), 200
                                        else:
                                            time.sleep(1)
                                    except Exception as e:
                                        logging.error(f"No videos found in status response: {e}")
                                        return jsonify({"error": "No videos found in status response"}), 500
                                else:
                                    logging.error(f"Invalid response structure: {status_data}")
                                    return jsonify({"error": "Invalid response structure", "response": status_data}), 500
                            except KeyError as e:
                                logging.error(f"KeyError: {e}")
                                return jsonify({"error": "KeyError in processing response", "exception": str(e)}), 500
                            except Exception as e:
                                logging.error(f"Unexpected error: {e}")
                                return jsonify({"error": "An unexpected error occurred", "exception": str(e)}), 500
                    else:
                        return jsonify({"error": "Failed to transcode video", "status_code": transcode_response.status_code}), transcode_response.status_code
                except Exception as e:
                    logging.error(f"Request Error: {e}")
                    return jsonify({"error": "An error occurred while making the transcode request", "exception": str(e)}), 500
            else:
                return jsonify({"error": "Failed to upload video", "status_code": response.status_code}), response.status_code
        else:
            return jsonify({"error": "Invalid video file path"}), 400
    else:
        return jsonify({"error": "Invalid request format. Please send JSON."}), 400

# This method will receive a POST request of formdata and save the audio file for use
@app.route('/generate', methods=['POST'])
def generate():
    # Check if the post request has the file part or sample part
    if 'file' not in request.files and 'file_from_react' not in request.files:
        return jsonify({"error": "No file or sample part"}), 400

    analysis_result = request.form.get('analysisResult')
    if not analysis_result:
        return jsonify({"error": "No analysis result provided"}), 400

    try:
        analysis_data = json.loads(analysis_result)
        print(f"Analysis Result: {analysis_data}")
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid analysis result format"}), 400

    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if file:
            filename = file.filename
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            print(f"File saved to {file_path}")

            # Perform any required operations with the file and analysis data
            # ...

            return jsonify({"message": "File and analysis data received successfully"}), 200

    elif 'file_from_react' in request.files:
        file = request.files['file_from_react']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if file:
            filename = file.filename
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            print(f"Sample file saved to {file_path}")

            # Perform any required operations with the file and analysis data
            # ...

            return jsonify({"message": "Sample and analysis data received successfully"}), 200

    return jsonify({"error": "File upload or sample selection failed"}), 500

# This method will delete the rendered animation
def delete_rendered_animation():
    filename = f"/home/mizookie/Renders/rendered_animation0001-{str(Config.TOTAL_FRAMES).zfill(4)}.mp4"
    if os.path.exists(filename):
        os.remove(filename)
        print(f"{filename} has been deleted.")
    else:
        print(f"{filename} does not exist.")

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
    file_path = 'anigen-blender-utils/config.py'    
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
    file_path = 'anigen-blender-utils/config.py'    
    with open(file_path, 'w') as f:
        f.write(config_data)
