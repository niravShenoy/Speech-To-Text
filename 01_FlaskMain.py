from os import environ, path

from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *
from pydub import AudioSegment
import base64
import json

from flask import Flask, redirect, jsonify, request, render_template, url_for
app = Flask(__name__)


words_to_numbers = {
    'zero': 0,
    'zero(1)': 0,
    'one': 1,
    'two': 2,
    'three': 3,
    'three(1)': 3,
    'four': 4,
    'four(1)': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'eight(1)': 8,
    'nine': 9,
    'ten': 10,
    'eleven': 11,
    'twelve': 12,
    'thirteen': 13,
    'fourteen': 14,
    'fifteen': 15,
    'sixteen': 16,
    'seventeen': 17,
    'eighteen': 18,
    'nineteen': 19,
    'twenty': 20,
    'thirty': 30,
    'thirty(1)': 30,
    'forty': 40,
    'fifty': 50,
    'sixty': 60,
    'seventy': 70,
    'eighty': 80,
    'ninety': 90,
    'hundred': 100,
    'thousand': 1000,
    'million': 1000000,
    'billion': 1000000000,
    'point': '.'
}

def decodeNumber(num):
    multipliers = [100,1000,1000000,1000000000]
    double_digs = [10,11,12,13,14,15,16,17,18,19,20,30,40,50,60,70,80,90]
    number = 0
    decimal_flag = 0
    dec_pow = 1
    next_add = 0
    prev_number = 0
    for word in num:
        if word not in multipliers and word != '.':
            if decimal_flag:
                number += word/pow(10,dec_pow)
                dec_pow += 1
            else:
                prev_number *= 10
                if next_add:
                    prev_number /= 10
                    next_add = 0
                prev_number += word
        if word == '.':
            decimal_flag = 1
        if word in multipliers:
            next_add = 1
            if prev_number == 0:
                prev_number = word
            else:
                prev_number *= word
            number += prev_number
            prev_number = 0
        if word in double_digs:
            next_add = 1
    number += prev_number
    return number

def detectSpeech(audio_data):

    file_data = base64.b64decode(audio_data)

    with open("audio.wav", 'wb') as file:
        file.write(file_data)

    sound = AudioSegment.from_file("audio.wav", format="wav")

    file_handle = sound.export("audio1.raw", format="raw")

    MODELDIR = "pocketsphinx/model"
    DATADIR = ""
    config = Decoder.default_config()
    config.set_string('-hmm', path.join(MODELDIR, 'en-us/en-us'))
    config.set_string('-lm', path.join(MODELDIR, 'en-us/en-us.lm.bin'))
    config.set_string('-dict', path.join(MODELDIR, 'en-us/alpha-num-en-us.dict'))

    # Decode streaming data.
    decoder = Decoder(config)
    decoder.start_utt()
    stream = open(path.join(DATADIR, 'audio1.raw'), 'rb')
    while True:
        buf = stream.read(1024)
        if buf:
            decoder.process_raw(buf, False, False)
        else:
            break
    decoder.end_utt()
    num_words = words_to_numbers.keys()
    digits = []
    speech = ''
    for seg in decoder.seg():
        if seg.word == '<sil>' or seg.word == '<s>' or seg.word == '[SPEECH]' or seg.word == '</s>':
            speech += ''
            continue
        if digits:
            if seg.word == 'to':
                digits.append(2)
                continue
            if seg.word == 'and':
                continue
            elif seg.word not in num_words:
                # call function to decode number
                number = decodeNumber(digits)
                speech += str(number) + ' '
                del digits[:]
        if seg.word in num_words:
            digits.append(words_to_numbers[seg.word])
        else:
            speech += seg.word + ' '
    if digits:
        number = decodeNumber(digits)
        speech += str(number) + ' '
    return speech

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        data = request.get_json()
        print(type(data))
        j = json.loads(data)
        audio_data = j["key"]
        result = detectSpeech(audio_data)
        print('Success!')
#        food = ["Cheese", "Tuna", "Chicken"]
#       return render_template('cart.html', food=food)
        print(result)
        return json.dumps({'success':True, 'result':result}), 200, {'ContentType':'application/json'}
    else:
        return render_template('index.html')
    #return 'Method used: %s' % request.method

#@app.route('/link', methods=['GET','POST'])
#def link():
#    if request.method == 'POST':
#        data = request.get_json()
#        audio_data = data['key']
#        result = detectSpeech(audio_data)
#        return render_template('index.html', result=result)
#    else:
#        return render_template('index.html')

if __name__=="__main__":
    app.run(debug=True) #host='0.0.0.0' extra parameter to run on all IP