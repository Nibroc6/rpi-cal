import os, psycopg2, uuid, save_events, time
from flask import Flask, flash, request, redirect, url_for, send_from_directory
#from werkzeug.utils import secure_filename

UPLOAD_FOLDER = r"C:\Users\corbi\Desktop\GitHub\rpi-cal\images"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'heif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 3 * 1000 * 1000

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/image', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = str(uuid.uuid4())+"."+file.filename.rsplit('.', 1)[1]
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) 
            #flash("Processing image...")
            json_content = save_events.process_image(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #flash("Found the following events: \n"+json_content+"\n\n"+"Saving events...")
            save_events.save_events(json_content, submitted_by="Corbin", image_id=filename)
            #flash("Saved events!")
            return redirect(url_for('download_file', name=filename))
    return '''
    <!doctype html>
    <title>Poster Upload</title>
    <h1>Upload picture of a poster (max 3 MB)</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''
    
@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)
    
app.add_url_rule(
    "/uploads/<name>", endpoint="download_file", build_only=True
)