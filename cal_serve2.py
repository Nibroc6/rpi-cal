import os, psycopg2, uuid, save_events, time, random, json, pillow_heif
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template, jsonify
from datetime import date
from PIL import Image

#from werkzeug.utils import secure_filename
GENERAL_FOLDER = r"C:\Users\corbi\Desktop\GitHub\rpi-cal"
SITE_LOCATION = "http://localhost:5000"

UPLOAD_FOLDER = os.path.join(GENERAL_FOLDER,"images")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'heif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1000 * 1000
app.secret_key = b'a&Kue*uqMypYxE^V@7I3m9IaLh3j@$S%nDh#H'

loading_messages_list = open(os.path.join(GENERAL_FOLDER,"loading.txt")).read().split("\n")
random.shuffle(loading_messages_list)


pillow_heif.register_heif_opener()


#=======================Helper functions==============================

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = psycopg2.connect(database="defaultdb", user="avnadmin", password=open("avn.txt").read(), host="rpi-all-events-cal-rpi-calendar.l.aivencloud.com", port=20044)
    return conn

def check_edit_auth(id,key):
    if id and key:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT edit_key FROM events WHERE event_id = %s", (id,))
        results = [x[0] for x in cur.fetchall()]
        cur.close()
        conn.close()
        if key.strip() in results:
            return True
        else:
            flash("Wrong ID or edit code")
    else:
        flash("ID or edit key is missing")
    return False

#===============================================================



#=======================Edit event==============================

@app.route('/edit', methods=['GET', 'POST'])
def edit_select():
    if request.method == 'POST':
        if check_edit_auth(request.form['event_id'], request.form['edit_key']):
            return redirect(f"/edit/{request.form['event_id']}/{request.form['edit_key'].strip()}",code=302)
    return render_template("edit_select.html")


@app.route('/edit/<int:id>/<edit_key>', methods=['GET', 'POST'])
def edit(id, edit_key):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM events WHERE event_id = %s AND edit_key = %s",(id,edit_key))
        result = cur.fetchall()
        
        if len(result)<1:
            return "Something went wrong...\nMaybe try going back to the edit auth page?"
    except:
        return "Something went wrong while fetching event details..."
    #print(result)
    result = [(result[0][x].replace("\"","\\\"") if type(result[0][x]) == type("") else result[0][x]) for x in [3,1,2,14,5,10,11,12,4]]
    #print(result)
    column_names = ["event_name","event_start","event_end","repeat","club_name","location","more_info","public","description"]
    autofill = dict(zip(column_names,result))
    
    #to_save = [request.form[n] for n in column_names]
    if request.method == 'POST':
        if check_edit_auth(id,edit_key):
            try:
                to_save = [request.form.get(n,False) for n in column_names]
                if to_save[7] in ['False','on']:
                    to_save[7] = True
                for u in range(len(column_names)): #deal with errors in sql when date isn't set - if the user didn't put something in a 
                    if to_save[u] == '':
                        to_save[u] = None
                cur.execute("UPDATE events SET "+", ".join([n+" = %s" for n in column_names])+" WHERE event_id = %s AND edit_key = %s",(*to_save,id,edit_key))
            
                flash("Saved event!")
                autofill = dict(zip(("event_name","event_start","event_end","repeat","club_name","location","more_info","public","description"),to_save))
                conn.commit()
            except Exception as e:
                print(e)
                flash("Error saving event")
        
        
    cur.close()
    conn.close()
    return render_template("edit.html",event_id=id,autofill=autofill)

#===============================================================



#=======================Serve calendar==========================

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
        cur.execute("SELECT * FROM events WHERE (\"repeat\"=1 and extract('DOW' from \"event_start\") = extract('DOW' from timestamp %s) and \"event_start\"<=%s and (end_repeat is null or end_repeat>=%s)) or DATE(event_start) = %s ORDER BY date_part('hour', event_start), date_part('minute', event_start)", (search_date,search_date,search_date,search_date,))
        results = [[r if r != None else "Unknown" for r in result] for result in cur.fetchall()]
        r2 = []
        for r in results: #remove the date part of the timestamps - I know it's janky, but it works for now
            line = r
            line[1] = line[1].strftime("%I:%M %p")
            if line[2] != "Unknown":
                line[2] = line[2].strftime("%I:%M %p")
            r2.append(line)
        results = r2
        cur.close()
        conn.close()
        #print(results)
        
    return render_template('date_search.html', results=results, search_date=search_date, search_performed=search_performed, today=date.today().strftime('%Y-%m-%d'))
    
#===============================================================



#=======================Create events===========================

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

#===============================================================


#---------------------------API---------------------------------
#=======================Save events=============================

@app.route('/api/new', methods=['POST'])
def api_new_event(dev_key):
    #if dev_key in ["xPpiZz257jFbet"]:
    #print(json.dumps(request.get_json()))
    try:
        json.dumps(request.get_json())
        id_keys = save_events.save_events(json.dumps(request.get_json()),submitted_by="API")
        return '{"errors":'+json.dumps(id_keys[1])+', "id_keys":'+json.dumps(id_keys[0])+"}"
    except Exception as e:
        return 'error: '+str(e)
    #else:
    #    return 'error: wrong/missing key'
    