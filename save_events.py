import psycopg2, json, anthropic, base64, pillow_heif
from io import BytesIO
from PIL import Image, ImageOps

SITE_LOCATION = "http://localhost:5000"

 
events_list = """{\n  "name": "ON-SITE BUILD AT PITTSFIELD, MA",\n  "start": "2024-08-31 07:30",\n  "end": "N/A",\n  "cost": "N/A",\n  "repeat": 0,\n  "club": "Rensselaer Polytechnic Institute Habitat for Humanity Campus Chapter",\n  "location": "Pittsfield, MA",\n  "more_info": "Scan QR code to sign up",\n  "public": true,\n  "description": "Freshman NRB Block event. No experience needed. Lunch & Transportation provided. Leaving from Union Horseshoe at 7:30 AM."\n}"""
#print(events_list)

key_map = {"name":"event_name",
    "start":"event_start",
    "end":"event_end",
    "repeat":"repeat",
    "club":"club_name",
    "location":"location",
    "more_info":"more_info",
    "public":"public",
    "description":"description"}
 

pillow_heif.register_heif_opener()

def resize_image(img: Image.Image) -> Image.Image:
    """
    Thanks Claude!!!
    """
    max_size = 1000
    width, height = img.size
    
    if width <= max_size and height <= max_size:
        return img
    
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))
    
    return img.resize((new_width, new_height), Image.LANCZOS)

def save_events(events1,submitted_by="",image_id=""):
    try:
        events = json.loads(events1)
    except:
        print(events1)
        raise Exception("can't joad json of event(s)")
    db_connection = psycopg2.connect(database="defaultdb", user="avnadmin", password=open("avn.txt").read(), host="rpi-all-events-cal-rpi-calendar.l.aivencloud.com", port=20044)
    cursor = db_connection.cursor()
    edit_pairs = []
    errors = []
    if type(events) == type({"":""}):
        events = [events]
    if submitted_by == "":
        raise Exception("must have submitted_by value")
    for event in events:
        keys = [x for x in event.keys() if event[x] != "N/A" and x in key_map.keys()]
        #print(f"INSERT INTO events ({','.join([key_map[k] for k in keys])}) VALUES ({','.join(['%s' for x in range(len(keys))])});")
        #items = []
        try:
            cursor.execute(f"INSERT INTO events ({','.join([key_map[k] for k in keys])},verified,submitted_by,needs_correction,edit_key,image_id,created) VALUES ({','.join(['%s' for x in range(len(keys)+3)])},gen_random_uuid(),%s,CURRENT_TIMESTAMP) RETURNING (event_id,edit_key);", (*[event[x] for x in keys],False,submitted_by,True,image_id))
            data = cursor.fetchone() 
            edit_pairs.append(data[0][1:len(data[0])-1].split(","))
        except Exception as e:
            try:
                errors.append((e,f"INSERT INTO events ({','.join([key_map[k] for k in keys])},verified,submitted_by,needs_correction,edit_key) VALUES ({','.join(['{}' for x in range(len(keys)+3)])},gen_random_uuid()) RETURNING (event_id,edit_key);".format(*[event[x] for x in keys],False,submitted_by,True),event["name"]))
            except Exception as error:
                print(error)
             
    db_connection.commit()
    cursor.close()
    db_connection.close()
    edit_pairs = [[p[0],p[1],SITE_LOCATION+f"/edit/{p[0]}/{p[1]}"] for p in edit_pairs]
    return (edit_pairs, errors)
#print(save_events(events_list,submitted_by="test"))
def process_image(img):
    image = ImageOps.exif_transpose(Image.open(img))
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    image.save(img)
    message = anthropic.Anthropic(api_key=open("anthropic_key.txt").read()).messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=3000,
        temperature=0,
        system="""You are an a event poster/image processer. You respond with a JSON object of events in the following format from the given image. Respond with only the JSON object. If a given category is not applicable for the event, put N/A in it. If there is more than one event on the poster, output a JSON list of the events in the same format. For repeating events, use the date and time of a likely first event for the start time. If the event doesn't specify a year, use 2024. In an event has multiple dates, create a seperate event for each one. {"name":"name of the event","start":"date and time of event start (in the format '2024-10-10 24:59')","end":"date and time of event end (in the format '2024-10-10 24:59', if applicable)","cost":"how much does the event cost?","repeat":(int) 0 for non-repeating; 1 for weekly; 2 for bi-weekly; 3 for monthly (same day); and 4 for monthly (same day of _ week ex. second sunday of every month),"club":"what's the name of the club hosting the event?","location":"where is the event happening?","more_info":"where can more info about the event be found? Any links belong here","public":(true or false) is this a public event like a concert or intrest-gathering event?,"description":"any info that didn't go in any other category? (don't include take-down date) (do not include description of poster)"}""",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img64,
                        }
                    }
                ]
            }
        ]
    )
    return message.content[0].text
    #return ""

#print(process_image(r"C:\Users\corbi\Downloads\IMG_5454.jpg"))

def edit_event(event_id, edit_key, info):
    pass
    

