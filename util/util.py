import re

def split_into_sentences(text,language):

    if language == '': language = 'en'

    caps = "([A-Z])"
    prefixes = "(Mr|St|Mrs|Ms|Dr|etc|No)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    digits   = "(\d+)[.](\d+)"
    dotlines = "(\s*[\.]){3,}\s*[\d+]*"   # remove contents dot lines
    website1 = '(w{3})[.]'
    website2 = '[.](com|net|org|io|gov)'
    website3 = '[.](hk|cn)'
    text = " " + text + "  "
    text = text.replace("\n",'')
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(website1,"\\1<prd>",text)
    text = re.sub(website2,"<prd>\\1", text)
    text = re.sub(website3, "<prd>\\1", text)
    text = re.sub(digits, "\\1<prd>\\2", text)
    text = re.sub(dotlines,'<stop>',text)
    text = re.sub(r'(\b\d{1,2}\b)[.]', '\\1<prd>', text)  # items such as 1., 2.



    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    if "a.m." in text: text = text.replace("a.m.", "a<prd>m<prd>")
    if "p.m." in text: text = text.replace("p.m.", "p<prd>m<prd>")
    if "e.g." in text: text = text.replace("e.g.", "e<prd>g<prd>")
    if "i.e." in text: text = text.replace("i.e.", "i<prd>e<prd>")

    text = re.sub("\s" + caps + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(caps + "[.]" + caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + caps + "[.]"," \\1<prd>",text)


    if language == 'en':
        if "”" in text: text = text.replace(".”","”.")
        if "\"" in text: text = text.replace(".\"","\".")
        if "!" in text: text = text.replace("!\"","\"!")
        if "?" in text: text = text.replace("?\"","\"?")
        text = text.replace(".",".<stop>")
        text = text.replace("?","?<stop>")
        text = text.replace("!","!<stop>")
    elif language == 'ch':
        if "”" in text: text = text.replace("。”","”。")
        if "\"" in text: text = text.replace("。\"","\"。")
        if "！" in text: text = text.replace("！\"","\"！")
        if "？" in text: text = text.replace("？\"","\"？")
        text = text.replace("。","。<stop>")
        text = text.replace("？","？<stop>")
        text = text.replace("！","！<stop>")

    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    # remove page index
    # pprint(sentences[-1])
    # if u'\u2013' in sentences[-1] or u'\u2014' in sentences[-1]:
    #     pprint("yes")
    #     sentences = sentences[0:-2]
    # else:
    #     pprint("no")
    return sentences