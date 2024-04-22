# AniGEN-Flask-App
This repository contains a Flask application to run the anigen-blender-utils tool.

## Installation
1. Clone the repository:

```bash
git clone https://github.com/MarzukhAsjad/anigen-flask-app.git
```
2. Navigate to the project directory:

```bash
cd anigen-flask-app
```
3. (Recommended) Create and activate a virtual environment:

```bash
python -m venv venv
```
Activate the venv with the following command
```bash
./venv/Scripts/activate
```
4. Install the dependencies:

```bash
pip install -r requirements.txt
```
5. Run the Flask development server:

```bash
flask run
```
OR
```bash
python -m flask --app .\app.py run
```

The server will start running on http://localhost:5000.

## Usage
Access the Flask app by visiting http://localhost:5000 in your web browser. Run the anigen-blender-utils tool by visiting http://localhost:5000/exec

## Contributing
Contributions are welcome! If you find any issues or have suggestions for improvement, please open an issue or submit a pull request.
