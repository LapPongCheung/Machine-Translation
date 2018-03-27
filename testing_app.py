from flask import Flask, make_response, redirect, url_for, flash
from flask import request, session
from flask import render_template
from subprocess import call
from form import Table, Row
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory
import re
import pyperclip
import sys
import itertools
sys.path.extend(["./preprocess", "./util"])

from preprocess import subword
from web_util import *
from util import split_into_sentences


UPLOAD_FOLDER = './uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def empty_function(raw_text_path, decoded_text_path):
    """the function to be replaced"""
    return None


@app.route('/')
def my_form():

    return render_template("homepage2.html")

@app.route('/enter', methods = ['GET', 'POST'])
def enter():
    if request.method == 'GET':
        return render_template("enter_text.html")
    else:
        return redirect(url_for('preprocess'))

@app.route('/preprocess', methods = ['POST', 'GET'])
def preprocess():
    global paragraph_nums
    global raw_text_path
    global display_text_path

    def reformat(text, is_file):
        global paragraph_nums

        text = text.strip(' ')
        if text[-1] != '.':
            text += '.'

        if is_file == False:
            text = text.replace('\r\n', '\r\n ')
            data = text.split('\r\n')

        else:
            data = text.split('\n')

        en_para = []
        temp = []
        for i, sent in enumerate(data):
            if sent == '' or sent == ' ' or sent == '\n':
                en_para.append(''.join(temp))
                temp = []
            elif i == len(data) -1:
                temp.append(sent)
                en_para.append(''.join(temp))
            else:
                temp.append(sent)



        data = [para for para in en_para if para != '']
        en_text = []
        for paragraph in data:
            paragraph = re.sub('\s+', ' ', paragraph)
            paragraph = re.sub('\.+', '.', paragraph)
            para_text = [para for para in split_into_sentences(paragraph, 'en') if para != '.']
            en_text.extend(para_text)
            paragraph_nums.append(paragraph_nums[-1]+len(para_text))


        return en_text

    #try to pick the filename
    filename = request.args.get('filename')
    

    if filename is None:
        text = request.form['text']
        en_text = reformat(text, False)
        
        file = open(raw_text_path, 'w', encoding = 'utf-8')
        file.write("\n".join([en_sent.lower() for en_sent in en_text]))
        file.close()

        file = open(display_text_path, 'w', encoding = 'utf-8')
        file.write("\n".join(en_text))
        file.close()
    else:
        file = open(os.path.join(app.config['UPLOAD_FOLDER'], filename), encoding = 'utf-8')
        sentences = file.readlines()
        text = ''.join(sentences)
        en_text = reformat(text, True)
        
        file = open(raw_text_path, 'w', encoding = 'utf-8')
        file.write("\n".join([en_sent.lower() for en_sent in en_text]))
        file.close()

        file = open(display_text_path, 'w', encoding = 'utf-8')
        file.write("\n".join(en_text))
        file.close()
    return redirect(url_for('my_form_post'))

@app.route('/translating', methods=['POST', 'GET'])
def my_form_post():
    #form handler
    global paragraph_nums
    global final_para_nums
    global display_text_path
    global decoded_text_path

    #=====================original code==================
    # subword()

    # call('python tensorflow/decode.py')
    
    # file = open(display_text_path, 'r', encoding = 'utf-8')
    # en_text = file.readlines()
    
    # postprocess()
    # file = open(decoded_text_path, 'r', encoding = 'utf-8')
    # ch_text = file.readlines()

    #======================original code==================
    empty_function(raw_text_path, decoded_text_path)

    #read the display texts for chinese and english
    file = open(display_text_path, 'r', encoding = 'utf-8')
    en_text = file.readlines()

    file = open(decoded_text_path, 'r', encoding = 'utf-8')
    ch_text = file.readlines()

    ch_para = []
    en_para = []

    for i in range(1, len(paragraph_nums)):
        ch_para.append(''.join(ch_text[paragraph_nums[i-1]:paragraph_nums[i]]))
        en_para.append(''.join(en_text[paragraph_nums[i-1]:paragraph_nums[i]]))


    text = zip(en_para, ch_para)
    table = Table()
    for pair in text:
        row = Row()
        row.chinese = pair[1]
        table.rows.append_entry(row)

    ch_para = []
    for i in range(1, len(paragraph_nums)):
        ch_para.append(ch_text[paragraph_nums[i-1]:paragraph_nums[i]])

    all_table = []
    for i in range(1, len(paragraph_nums)):
        table = Table()
        for ch_sent in ch_text[paragraph_nums[i-1]:paragraph_nums[i]]:
            row = Row()
            row.chinese = ch_sent
            table.rows.append_entry(row)
        all_table.append(table)

    en_para = []
    ch_para
    for i in range(1, len(paragraph_nums)):
        en_para.append(en_text[paragraph_nums[i-1]:paragraph_nums[i]])
        ch_para.append(ch_text[paragraph_nums[i-1]:paragraph_nums[i]])

    table = zip(en_para, all_table, ch_para)

    final_para_nums = paragraph_nums
    paragraph_nums = [0]

    return render_template("testing_result.html", table = table)

@app.route('/result')
def result(): 
    return render_template("final.html", result = request.args.get('final'))


@app.route('/upload', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        #check whether the post requests has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        #get the file
        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('preprocess', filename = filename))

    return render_template('upload.html')


@app.route('/finalize', methods = ['POST', 'GET'])
def finalize():
    global final_para_nums
    global paragraph_nums
    global ch_result

    form = dict(request.form)
    ch_text = list(itertools.chain.from_iterable(form.values()))
    #ch_text = ''.join(ch_text[:-1])
    ch_para = []
    for i in range(1, len(final_para_nums)):
        ch_para.append(''.join(ch_text[final_para_nums[i-1]:final_para_nums[i]]))
    

    file = open(display_text_path, 'r', encoding = 'utf-8')
    en_text = file.readlines()
    en_para = []
    for i in range(1, len(final_para_nums)):
        en_para.append(''.join(en_text[final_para_nums[i-1]:final_para_nums[i]]))
    ch_result = ch_para
    
    paragraph_nums = [0]
    #final_para_nums = [0]
    return render_template('translated.html', text = (en_para, ch_para))

@app.route('/copy', methods = ['POST', 'GET'])
def copy():
    global ch_result
    text = [result.replace('\r\n', '') for result in ch_result]
    text = '\r\n'.join(ch_result)

    pyperclip.copy(text)
    flash('Done!')
    return redirect(url_for('my_form'))

@app.route('/download', methods = ['POST', 'GET'])
def download():
    global ch_result
    global result_text_path
    text = [result.replace('\r\n', '') for result in ch_result]
    text = '\r\n'.join(ch_result)
    file = open(result_text_path, 'w', encoding = 'utf-8')
    file.write(text)
    file.close()

    name = 'result.txt'
    return send_from_directory(directory = app.root_path, filename=name, as_attachment=True)

@app.route('/buttons', methods = ['POST', 'GET'])
def buttons():
    return render_template('buttons.html')


if __name__ == '__main__':
    paragraph_nums = [0]
    final_para_nums = [0]
    ch_result = []
    SECRET_KEY = 'many random bytes'
    raw_text_path = '/data/raw_text.src'
    display_text_path = '/data/display_text.src'
    result_text_path = '/data/result_text.txt'
    decoded_text_path = '/data/output.de'




    # or set directly on the app
    app.secret_key = 'many random bytes'
    app.run(debug = True)