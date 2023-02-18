from flask import Flask, render_template, send_from_directory, url_for, redirect, session, jsonify
from flask import request
import json, codecs
import os
import requests
#import subprocess
from flask_cors import CORS #comment this on deployment
from cryptography.fernet import Fernet
from pymongo import MongoClient
from dotenv import load_dotenv
from difflib import SequenceMatcher

load_dotenv() 

app = Flask(__name__, static_folder='static')
client = MongoClient(os.getenv("MONGO_CONNECT"))
db = client.DMRSearch
entryCol = db.entries

@app.route("/")
def homepage():
    return render_template("index.html")

@app.route("/search")
def search():
    if 'searchterm' in request.args:        
        return render_template("search.html", search_result=internal_search(request.args['searchterm']))
    else:
        return render_template("search.html")

@app.route("/add")
def add():
    return render_template("add.html")

@app.route("/tag_info")
def tag_info():
    return render_template("tag_info.html")

@app.route("/api/add", methods=["GET", "POST"])
def api_add():
    entry_obj = {
        "primary_name": request.args['main_name'].lower(),
        "url":request.args['url'],
        "img_url":request.args.get('img', url_for('static', filename='css/base.css')),
        "names": [s.strip().lower() for s in request.args['alt_names'].split("\n") + [request.args['main_name']]], #This is quick&dirty but there's no reason for it not to work
        "tags": [s.strip().lower() for s in request.args['tags'].split(",")]
    }

    name_list = request.args['alt_names'].split("\n")

    entryCol.insert_one(entry_obj)
    return redirect(url_for("add"))

@app.route("/api/search")
def api_search():
    return jsonify(internal_search(request.args['search_term']))

def internal_search(query):
    terms = set(query.split())
      
    #Rating Function
    def rate_entry(entry):
        # SequenceMatcher determines how similar two strings are. This way the algorithm is forgiving to typos and abbrviations
        similarity = max([SequenceMatcher(None, query, n).ratio() for n in entry["names"]])

        tags_matched = len(terms.intersection(set(entry['tags'])))

        return similarity * tags_matched
    
    # Pull all entries in the DB to run search algorithm on. This WILL be a problem down the line.
    # I could work my magic with mongo aggregations to make this more efficient but I'm on a deadline here
    # If you're reading this, make a pull request with a better approach
    all_entries = list(entryCol.find({},projection={"_id":0}))

    #Order all entries by how well it matches the search and return list   
    all_entries.sort(key=rate_entry,reverse=True)
    return all_entries

if __name__ == '__main__':    
    #pgcr_thread = subprocess.run(['python', 'PGCRscanner.py'], capture_output=True, text=True, check=True)
    #CORS(app) #comment this on deployment
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    #pgcr_thread.terminate()
