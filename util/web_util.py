ALLOWED_EXTENSIONS = set(['txt'])

#check the uploaded file
def allowed_file(filename):
    return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def postprocess():
    file = open('data/output.de', 'r', encoding = 'utf-8')
    ch_text = file.readlines()
    new_ch_text = []

    for sent in ch_text:
        sent = sent.replace("@", "")
        sent = sent.replace(" ", "")        	
        new_ch_text.append(sent)

    file = open('data/output.de', 'w', encoding = 'utf-8')
    file.write("".join(new_ch_text))
    file.close()
