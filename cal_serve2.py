import os, psycopg2, uuid, save_events, time, random, json
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template, jsonify
from datetime import date

#from werkzeug.utils import secure_filename
GENERAL_FOLDER = r"C:\Users\corbi\Desktop\GitHub\rpi-cal"
UPLOAD_FOLDER = os.path.join(GENERAL_FOLDER,"images")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'heif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 3 * 1000 * 1000
app.secret_key = b'a&Kue*uqMypYxE^V@7I3m9IaLh3j@$S%nDh#H'

loading_messages_list = open(os.path.join(GENERAL_FOLDER,"loading.txt")).read().split("\n")
random.shuffle(loading_messages_list)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = psycopg2.connect(database="defaultdb", user="avnadmin", password=open("avn.txt").read(), host="rpi-all-events-cal-rpi-calendar.l.aivencloud.com", port=20044)
    return conn


@app.route('/edit')
def edit():
    if request.method == 'POST':
        
        return render_template("edit.html")
    return render_template("edit.html")

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    search_date = None
    search_performed = False

    if request.method == 'POST':
        search_performed = True
        if 'today' in request.form:
            search_date = date.today().strftime('%Y-%m-%d')
        else:
            search_date = request.form['search_date']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM events WHERE DATE(event_start) = %s", (search_date,))
        results = cur.fetchall()
        cur.close()
        conn.close()
        #print(results)

    return render_template('date_search.html', results=[[r if r != None else "Unknown" for r in result] for result in results], search_date=search_date, search_performed=search_performed)

@app.route('/get_details/<int:id>')
def get_details(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events WHERE event_id = %s", (id,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        output = {
            'id': result[0],
            'start': result[1],
            'end': result[2],
            'name': result[3],
            'description': result[4],
            'club_name': result[5],
            'cost': result[9],
            'location': result[10],
            'more_info': result[11],
            'public': result[12],
            'image_id': result[16],
        }
        for o in output.keys():
            output[o] = (output[o] if output[o] != None else "Unknown")
        return jsonify(output)
    else:
        return jsonify({'error': 'Record not found'}), 404


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
            event_info = save_events.save_events(json_content, submitted_by="Corbin", image_id=filename)
            #flash("Saved events!")
            return render_template("scanned.html",image_path =url_for('download_file', name=filename),table="\n".join(["<tr>"+'\n'.join([f'<td>{data}</td>' for data in row])+"</tr>" for row in event_info[0]]))
    return render_template("upload.html", error=None, loading_messages = json.dumps(loading_messages_list[:20]),loading_message_speed="3000")
    '''
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