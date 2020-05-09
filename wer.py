from flask import Flask, jsonify, request
from jiwer import wer
import jiwer
import flask
import re
import numpy


app = Flask(__name__)
app.secret_key = b'werTest'

ground_truth = ''
hypothesis = ''

def editDistance(r, h):
    '''
    This function is to calculate the edit distance of reference sentence and the hypothesis sentence.

    Main algorithm used is dynamic programming.

    Attributes: 
        r -> the list of words produced by splitting reference sentence.
        h -> the list of words produced by splitting hypothesis sentence.
    '''
    d = numpy.zeros((len(r)+1)*(len(h)+1), dtype=numpy.uint8).reshape((len(r)+1, len(h)+1))
    for i in range(len(r)+1):
        d[i][0] = i
    for j in range(len(h)+1):
        d[0][j] = j
    for i in range(1, len(r)+1):
        for j in range(1, len(h)+1):
            if r[i-1] == h[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                substitute = d[i-1][j-1] + 1
                insert = d[i][j-1] + 1
                delete = d[i-1][j] + 1
                d[i][j] = min(substitute, insert, delete)
    return d
    
def getStepList(r, h, d):
    '''
    This function is to get the list of steps in the process of dynamic programming.

    Attributes: 
        r -> the list of words produced by splitting reference sentence.
        h -> the list of words produced by splitting hypothesis sentence.
        d -> the matrix built when calulating the editting distance of h and r.
    '''
    x = len(r)
    y = len(h)
    list = []
    while True:
        if x == 0 and y == 0: 
            break
        elif x >= 1 and y >= 1 and d[x][y] == d[x-1][y-1] and r[x-1] == h[y-1]: 
            list.append("e")
            x = x - 1
            y = y - 1
        elif y >= 1 and d[x][y] == d[x][y-1]+1:
            list.append("i")
            x = x
            y = y - 1
        elif x >= 1 and y >= 1 and d[x][y] == d[x-1][y-1]+1:
            list.append("s")
            x = x - 1
            y = y - 1
        else:
            list.append("d")
            x = x - 1
            y = y
    return list[::-1]
    


@app.route('/')
def home_page():
    return flask.render_template('index.html')



@app.route('/calculate', methods=['POST'])
def calculate():

    global ground_truth
    ground_truth = request.form['gold_standard']
    
    global hypothesis
    hypothesis = request.form['translated_machine']

    
    if((len(ground_truth)>2) and (len(hypothesis)>2)):
        ground_truth = re.sub(r"""[,.;@#?!&$]+\ *"""," ", ground_truth, flags=re.VERBOSE)
        hypothesis = re.sub(r"""[,.;@#?!&$]+\ *"""," ", hypothesis, flags=re.VERBOSE)
        measures = jiwer.compute_measures(ground_truth.lower().replace('<br/>', ''), hypothesis.lower().replace('<br/>', ''))
        wer = str("%.2f" % (measures['wer']*100)) + "%"
        mer = str("%.2f" % (measures['mer']*100)) + "%"
        wil = str("%.2f" % (measures['wil']*100)) + "%"
        wip = str("%.2f" % (measures['wip']*100)) + "%"
        
        r = re.sub(' +', ' ',ground_truth).split()
        h = re.sub(' +', ' ',hypothesis).split()

        # find out the manipulation steps
        d = editDistance(r, h)
        list_step = getStepList(r, h, d)

        count_s = [ele for ele in list_step if ele == 's']
        count_d = [ele for ele in list_step if ele == 'd']
        count_i = [ele for ele in list_step if ele == 'i']

        # print the result in aligned way
        result = float(d[len(r)][len(h)]) / len(r) * 100
        result = str("%.2f" % result) + "%"
        #alignedPrint(list_step, r, h, result)
        
        #print(ground_truth.lower().replace('<br/>', ''))
        #print(hypothesis.lower().replace('<br/>', ''))
        #print(wer, mer, wil, wip)
        return flask.render_template('index.html', gold_standard=ground_truth, translated_machine = hypothesis, wer = wer, mer = mer, wil = wil, wip = wip, cs_wer = result, sub = len(count_s), dele = len(count_d), ins = len(count_i))
        
    
    else:
        return flask.render_template('index.html')
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8018)

    
