# __init__.py

import eventlet
# import gevent
eventlet.monkey_patch()
import base64
from flask import Flask, render_template, Response, request, redirect, url_for
from flask.json import jsonify
from camera import IpCamera
import time
from flask_socketio import SocketIO
from urllib.parse import urlparse
import sqlite3
import os
import sys
from werkzeug.utils import secure_filename
from collections import defaultdict
import re
import urllib.request
import json
import codecs
import requests
from requests.auth import HTTPBasicAuth
from threading import Thread
import threading


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__, template_folder=resource_path('templates'))
# app.jinja_loader = jinja2.FileSystemLoader(resource_path('templates'))
    #     app.jinja_loader = jinja2.FileSystemLoader(resource_path(template_folder))
#        from os.path import abspath, dirname; 
# socketio.run(app, host='127.0.0.1', port=int("80"), debug=False)
app.root_path = resource_path('.')


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'secret2!'
app.config['TEMPLATES_AUTO_RELOAD'] = True
socketio = SocketIO(app, async_mode='eventlet')

c={}

    
def get_vs(online=-1, type='list', vsnum=''):
    # type='list' for IP-List, type='views' for views list
    conn = sqlite3.connect(resource_path('db\cameras.db'))
    c = conn.cursor()
    statinfo = os.stat(resource_path('db\cameras.db'))
    if statinfo.st_size == 0:
        c.execute('''CREATE TABLE Cameras
                 (id INTEGER PRIMARY KEY, url TEXT, title TEXT, org TEXT, country TEXT, city TEXT, region TEXT, online INTEGER, lastseen TEXT)''')
        c.execute('''CREATE TABLE CamTags
                 (id INTEGER PRIMARY KEY, CamerasId INTEGER, TagsId INTEGER)''')
        c.execute('''CREATE TABLE Tags
                 (id INTEGER PRIMARY KEY, tag TEXT NOT NULL UNIQUE)''')
        c.execute('''CREATE TABLE Settings
                 (recordpath TEXT)''')
        c.execute('''INSERT INTO Settings (recordpath) VALUES ('')
                ''')
    
    if type=='list':
        videosources = defaultdict(dict)
        if vsnum != '' and online == -1:
            c.execute("SELECT id, url, title, org, country, city, region, online, lastseen FROM Cameras WHERE id = ?", (vsnum, ))
        elif vsnum == '' and online != -1:
            c.execute("SELECT id, url, title, org, country, city, region, online, lastseen FROM Cameras WHERE online = ?", (str(online), ))
        resultset = c.fetchall()
        if resultset:
            for row in resultset:
                c.execute("SELECT Tags.tag FROM Tags JOIN CamTags ON CamTags.CamerasId = Cameras.id JOIN Cameras ON Tags.id = CamTags.TagsId WHERE Cameras.id = ?", (row[0], ))
                resultsettags = c.fetchall()
                if resultsettags:
                    for row2 in resultsettags:
                        videosources[row[0]]['taglist']=row2
                videosources[row[0]]['taglist'] = resultsettags
                videosources[row[0]]['id'] = row[0]
                videosources[row[0]]['url'] = row[1]
                u = urlparse(row[1]).netloc
                if u.find(':')!=-1: 
                    videosources[row[0]]['ip'] = u[u.find('@')+1:u.find(':')]
                else:
                    videosources[row[0]]['ip'] = u[u.find('@')+1:]
                if videosources[row[0]]['ip']=='': 
                    videosources[row[0]]['ip'] = re.findall( r'[0-9]+(?:\.[0-9]+){3}', row[1] )[0]
                videosources[row[0]]['title'] = row[2]
                videosources[row[0]]['org'] = row[3]
                videosources[row[0]]['country'] = row[4]
                videosources[row[0]]['city'] = row[5]
                videosources[row[0]]['region'] = row[6]
                videosources[row[0]]['online'] = row[7]
                videosources[row[0]]['lastseen'] = row[8]
    
    elif type=='taglist':
        videosources = dict()
        c.execute("SELECT Tags.id, Tags.tag FROM Tags JOIN CamTags ON CamTags.CamerasId = Cameras.id JOIN Cameras ON Tags.id = CamTags.TagsId WHERE Cameras.id = ?", (vsnum, ))
        resultset = c.fetchall()
        if resultset:
            for row in resultset:
                videosources.update({row[0]:row[1]})
    
    elif type=='views':
        videosources = dict()
        c.execute("SELECT id, url, online FROM Cameras WHERE online = ? LIMIT 12", (str(online), ))
        resultset = c.fetchall()
        if resultset:
            for row in resultset:
                videosources.update({row[0]:row[1]})

    conn.commit()
    conn.close()
    return videosources

    
    
def get_settings():
    conn = sqlite3.connect(resource_path('db\cameras.db'))
    c = conn.cursor()
    settings = []
    c.execute("SELECT recordpath FROM Settings")
    resultset = c.fetchall()
    if resultset:
        for row in resultset:
            settings.append(row[0])
    conn.commit()
    conn.close()
    return settings
    

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

    
           
@app.route('/', methods=['GET'])
def index():
    global c
    online = request.values.get('online') or 1
    videosourceslist = get_vs(online=online, type='list')
    activevsnum = []
    for i in c:
        if c[i].status == 0:
            activevsnum.append(c[i].vsnum)
        else:
            c[i].status == 0
    # if getattr(sys, 'frozen', False):
    #     application_path = os.path.dirname(sys.executable)
    # elif __file__:
    #     application_path = os.path.dirname(__file__)
    # recordpath = os.path.join(application_path, 'RECORDS')            
    return render_template('index.html', videosourceslist=videosourceslist, activevsnum=activevsnum)

    
@app.route('/import', methods=['GET', 'POST'])
def importcams():
    if request.method == 'POST':
        if 'datei' not in request.files:
            flash('Keine Datei')
            return redirect(request.url)
        file = request.files['datei']
        if file.filename == '':
            flash('Keine Datei')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(resource_path(os.path.join(app.config['UPLOAD_FOLDER'], filename).replace("\\","/")))

            conn = sqlite3.connect(resource_path('db\cameras.db'))
            c = conn.cursor()
            fobj = open(resource_path(os.path.join(app.config['UPLOAD_FOLDER'], filename).replace("\\","/")), "r")            
            c.execute("SELECT max(id) FROM Cameras")
            # lastid = c.fetchone()
            # if lastid[0]: i = lastid[0]
            # else: i = 0
            for line in fobj:
                l = line.rstrip()
                if l!='':
            #         i += 1
                    c.execute("INSERT INTO Cameras (url, online) VALUES (?,1)", (l,))
            fobj.close()
            conn.commit()
            conn.close()
    return redirect(url_for('index'))

    
@app.route('/updateviews', methods=['GET'])
def updateviews():
    vsnum = request.values.get('vsnum')
    action = request.values.get('action')
    videosources = get_vs(type='list', vsnum=vsnum)
    if action=='add':
        for i in videosources: 
            eventlet.spawn(on_connect, vsnum=vsnum) 
    return jsonify(videosources[int(vsnum)])

    

@app.route('/tags', methods=['GET'])
def tags():
    vsnum = request.values.get('vsnum')
    tag = request.values.get('tag').strip()
    action = request.values.get('action')
    conn = sqlite3.connect(resource_path('db\cameras.db'))
    c = conn.cursor()
    if action=='add':
        try:
            c.execute("INSERT INTO Tags (tag) VALUES (?)", (tag,))
        except sqlite3.IntegrityError:
            pass
        c.execute("SELECT (id) FROM Tags WHERE tag = ?", (tag,))
        r = c.fetchone()
        if r[0]: i = r[0]
        else: i = 0
        c.execute("SELECT (id) FROM CamTags WHERE TagsId = ? AND CamerasId = ?", (i,vsnum))
        r2 = c.fetchone()
        if not r2:
            c.execute("INSERT INTO CamTags (CamerasId, TagsId) VALUES (?,?)", (vsnum,i))
            ret = 'plus'
        else:
            ret = 'none'
    elif action=='remove':
        c.execute("SELECT (id) FROM Tags WHERE tag = ?", (tag,))
        r = c.fetchone()
        c.execute("DELETE FROM CamTags WHERE TagsId=? AND CamerasId=?", (r[0],vsnum))
        c.execute("SELECT (id) FROM CamTags WHERE TagsId = ?", (r[0],))
        r2 = c.fetchone()
        if not r2: c.execute("DELETE FROM Tags WHERE id = ?", (r[0],))
        ret = 'minus'
    conn.commit()
    conn.close()
    # videosources = get_vs(type='list', vsnum=vsnum) DB ABFRAGE BADGE
    return ret
    # jsonify(videosources[int(vsnum)]['taglist']) DB ABFRAGE BADGE
    
    
@app.route('/hide', methods=['GET'])
def switchcam():
    vsnum = request.values.get('vsnum')
    videosources = get_vs(type='list', vsnum=vsnum)
    conn = sqlite3.connect(resource_path('db\cameras.db'))
    c = conn.cursor()
    for id in videosources:
        if videosources[id]['online'] == 0:
            c.execute("UPDATE Cameras SET online = 1 WHERE id = ?", (vsnum, ))
        else:
            c.execute("UPDATE Cameras SET online = 0 WHERE id = ?", (vsnum, ))
    conn.commit()
    conn.close()
    return 'ok'


    
@app.route('/resolve', methods=['GET'])
def resolve_cam():
    vsnum = request.values.get('vsnum')
    videosources = get_vs(type="list", vsnum=int(vsnum))
    # geolocation
    for id in videosources:
        if (not videosources[id]['city'] and not videosources[id]['country'] and not videosources[id]['org']):
            conn = sqlite3.connect(resource_path('db\cameras.db'))
            c = conn.cursor()
            url = 'http://ipinfo.io/' + videosources[id]['ip'] + '/json'
            reader = codecs.getreader("utf-8")
            response = urllib.request.urlopen(url)
            data = json.load(reader(response))
            org=data['org']
            city = data['city']
            country=data['country']
            region=data['region']
            c.execute("UPDATE Cameras SET org = ?, city = ?, country = ?, region = ? WHERE id = ?", (org, city, country, region, vsnum))
            conn.commit()
            conn.close()
            return jsonify(data)
        else:
            return jsonify(videosources[id])

    
   
@app.route('/lastseen', methods=['GET'])
def lastseen():
    vsnum = request.values.get('vsnum')
    lastseen = request.values.get('lastseen')
    # videosources = get_vs(type="list", vsnum=int(vsnum))
    # for id in videosources:
    conn = sqlite3.connect(resource_path('db\cameras.db'))
    c = conn.cursor()
    c.execute("UPDATE Cameras SET lastseen = ? WHERE id = ?", (lastseen, vsnum))
    conn.commit()
    conn.close()
    return 'ok'

    
@app.route('/clearDB', methods=['GET'])
def cleardb():
    conn = sqlite3.connect(resource_path('db\cameras.db'))
    c = conn.cursor()
    c.execute("DELETE FROM Tags")
    c.execute("DELETE FROM Cameras")
    c.execute("DELETE FROM CamTags")
    conn.commit()
    conn.close()
    return 'ok'


        
@app.route('/settings', methods=['POST'])
def settings():
    if request.values.get('action') == 'read':
        settings = get_settings()
        return jsonify(settings)
    elif request.values.get('action') == 'write':
        recordpath = request.values.get('recordpath')
        conn = sqlite3.connect(resource_path('db\cameras.db'))
        c = conn.cursor()
        c.execute("UPDATE Settings SET recordpath = ?", (recordpath, ))
        conn.commit()
        conn.close()
    return 'ok'


@app.route('/checkonline', methods=['GET'])
def checkonline():
    vsnum = request.values.get('vsnum')
    videosources = get_vs(type="list", vsnum=int(vsnum))
    for id in videosources:
        url = videosources[id]['url']
    ret = 'success'
    try:
        u = urlparse(url)
        r = requests.get(url, auth=(u.username, u.password), stream=True, timeout=6, verify=False)
        r.connection.close()
        if (r.status_code < 400):
            return jsonify({'vsnum': vsnum, 'lastseen': ret})
        # x = r.raw.read(100)
        # if x == b'': raise
        # r.raise_for_status()
    except:
        ret = 'error'
    finally:
        conn = sqlite3.connect(resource_path('db\cameras.db'))
        c = conn.cursor()
        c.execute("UPDATE Cameras SET lastseen = ? WHERE id = ?", (ret, vsnum))
        conn.commit()
        conn.close()
        return jsonify({'vsnum': vsnum, 'lastseen': ret})


    
def showcambackground(vsnum):
    global c
    videosources = get_vs(type="list", vsnum=vsnum)
    f = open(resource_path('static/load.jpg'), 'rb')
    bi = f.read()
    f.close()
    socketio.emit('sendpic', {'vsnum': vsnum, 'buffer': bi, 'status': 0})  
    recordpath = get_settings()[0]    
    c[vsnum] = IpCamera(dict(videosources)[int(vsnum)]['url'], int(vsnum), recordpath);
    while c[vsnum].status == 0 and c[vsnum].camclose == False:
        buffer = c[vsnum].get_frame()
        socketio.emit('sendpic', { 'vsnum': vsnum, 'buffer': buffer, 'status': 0 })
    if c[vsnum].status != 0:
        f = open(resource_path('static/fail.jpg'), 'rb')
        bi = f.read()
        f.close()
        socketio.emit('sendpic', {'vsnum': vsnum, 'buffer': bi, 'status': 1}) 
        eventlet.sleep(120)
    return 'ok'

thread = {}
# @socketio.on('connect')
def on_connect(vsnum):
    global thread
    # if not vsnum in thread:
    thread[vsnum] = Thread(target=showcambackground, name='thread-'+vsnum, args=(vsnum, ))
    thread[vsnum].start()
    return 'ok'

@socketio.on('camrecstart')
def camrecstart(data):
    global c
    c[data['vsnum']].camrec = True
@socketio.on('camrecstop')
def camrecstop(data):
    global c
    c[data['vsnum']].camrec = False
@socketio.on('camsnapstart')
def camsnapstart(data):
    global c
    c[data['vsnum']].camsnap = True
@socketio.on('camsnapstop')
def camsnapstop(data):
    global c
    c[data['vsnum']].camsnap = False
@socketio.on('camsnapsingle')
def camsnapsingle(data):
    global c
    c[data['vsnum']].camsnapsingle = True
@socketio.on('camstop')
def camstop(data):
    global c
    c[data['vsnum']].camclose = True

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=int("80"), debug=False)
