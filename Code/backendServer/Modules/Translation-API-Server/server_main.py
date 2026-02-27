from flask import Flask
from flask import request
from flask_cors import CORS, cross_origin
from waitress import serve
import re
import time
import getopt, sys, os, json, signal
import json

#===========================================================
# INITIALIATION
#===========================================================
user_settings_file = open("../../../../User-Settings.json", encoding="utf-8")
user_settings_data = json.load(user_settings_file)

current_translator = user_settings_data["Translation_API_Server"]["current_translator"]
port = user_settings_data["Translation_API_Server"][current_translator]["HTTP_port_number"]
host = '0.0.0.0'


#===========================================================
# MAIN APPLICATION
#===========================================================

from Translator import Main_Translator


translator = Main_Translator()
translator.activate()
# translator = Translator_API(Sugoi_Translator())

        
app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/", methods = ['POST','GET'])
@cross_origin()

def sendSugoi():
    tic = time.perf_counter()
    data = request.get_json(True)
    message = data.get("message")
    content = data.get("content")

    if (message == "close server"):
        if (current_translator == "DeepL"):
            translator.close()
        shutdown_server()
        return
    
    if (message == "check if server is ready"):
        result = translator.translator_ready_or_not
        return json.dumps(result)

    if (message == "translate sentences"):
        start = time.time()
        print("translation request received")
        translation = translator.translate(content)
        print(translation)
        end = time.time()
        print(end - start)
        return json.dumps(translation, ensure_ascii=False)
    
    if (message == "translate batch"):
        print("translation request received")
        translation = translator.translate_batch(content)
        return json.dumps(translation, ensure_ascii=False)
    
    if (message == "change input language"):
        return json.dumps(translator.change_input_language(content))
    
    if (message == "change output language"):
        return json.dumps(translator.change_output_language(content))
    
    if (message == "pause"):
        return json.dumps(translator.pause())
    
    if (message == "resume"):
        return json.dumps(translator.resume())
    


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

# if __name__ == "__main__":
#     #app.run(host=host, port=port)
#     serve(app, host=host, port=port)

serve(app, host=host, port=port)