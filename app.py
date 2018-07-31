
import pandas as pd
from textblob import TextBlob
import dash
import re
from dash.dependencies import Input, Output, State, Event
import dash_core_components as dcc
import dash_html_components as html
from collections import defaultdict
# from flask import Flask
import os
# Not sure whether we need this, with textblob...
import nltk # Interesting, if you run this with python instead of python3, it can't find nltk.
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk import FreqDist
import nltk.text
from nltk.corpus import wordnet as wn

df = None
stop_words = [
'the', 'thee', 'am', 'are', 'o', 'hath', 'have', 'of', 'than', 'my', 'thy', 'upon', 'or', 'and', 'if', 'when',
'is', "'t", 'nay', 'come', 'from', 'do', ']', '[', 'thou', 'let', 'them', 'for', 'him', 'her', 'they', 'i', 'be', 'since',
'will', 'this', 'i', 'a', 'though', 'so', 'again', 'like', 'in', 'been', 'was', '?', ',', '.', 'go', 'by', 'there',
'here', 'as', 'how', 'would', 'ay', 'ah', 'alas', 'nor', 'sir', 'madam'
]

# Split this up please:
def prepare_play():
    global df
    df = pd.read_csv('Hamlet.csv')

    hamlet = ''
    char_count = [-1, -1] # To get right number in list.
    total = 0

    # Ok weird idea: we add a column to the dataframe that keeps track of how many characters have appeared so far. So first line gets 0. Then next line gets 13. Then 57. Etc.
    for line in df['Lines'][2:]:
        hamlet += line + ' '
        char_count.append(total) # Will we need to trim off the quote marks again? Seems like pandas automatically ignores them..
        total += len(line) + 1 # add one because of the space
        # Can also check whether a word is in a line.

    df['char_count'] = pd.Series(char_count, index=df.index) # Add a column to the df

    # Initialize TB object of play text:
    hamlet_blob = TextBlob(hamlet)
    sentences = hamlet_blob.sentences # Hmmm, but we'd like to attach the speaker to each one...
    hamlet_list = [] # Will contain objects that have a sentence text and a speaker.


    doNLTK(hamlet)


    # Populate list of sentences with speakers attached:
    for s in sentences: # Since we're now going through all lines, takes a bit longer
        if (len(df[df['char_count'] == s.start].values) > 0):
            hamlet_list.append({
                'text': s,
                'speaker': df[df['char_count'] == s.start].values[0][3] # Wow.... Ok.
            })

    # print(hamlet_list)
    return hamlet_list


hamlet_list = prepare_play()


# print(df.head(30))


#############################################################################################################

# So for a network chart...we would want size of each node to represent frequency of word.
# And breadth of each edge to represent strength of collocation -- can nltk offer that?
def doNLTK(play):
    # Initialize NLTK object:
    toks = word_tokenize(play)
    full_text = nltk.Text(toks)
    context = nltk.text.ContextIndex(toks) # Yes, this has similar_words, this is what we need!

    allwords = []
    # print(full_text.concordance('madness')) # No need to print. Returns None, like similar().
    # print(full_text.similar('death'))
    fdist = FreqDist(full_text)
    # commons = fdist.most_common(250)
    commons = [f for f in fdist.keys() if fdist[f] > 8] # Can also check it's not a stop word here
    commons_str = '  '.join(commons)
    commons_toks = word_tokenize(commons_str)
    commons_tags = nltk.pos_tag(commons_toks)
    # Hideous -- figure out regex:
    commons_imp = [(c[0]) for c in commons_tags if (c[1] == 'NN') or (c[1] == 'NNP') or ('VB' in c[1]) or ('JJ' in c[1])]
    commons_imp_nostop = [c for c in commons_imp if c.lower() not in stop_words]
    # print(commons_imp_nostop)

    for w in commons_imp_nostop:
        # x = full_text.ContextIndex.similar_words(w) # What? Why does this return None but just print?
        x = context.similar_words(w)
        # print(x)
        for idx, x in enumerate(context.similar_words(w)):
            if x.lower() not in stop_words and x not in allwords:
                allwords.append(x.lower())
                print('{} is similar to {} by degree {}'.format(w, x.lower(), idx))

    # print(allwords)

#############################################################################################################

active_speakers = [] # Which speakers are on the chart

# Could set up an input field for typing speaker name, get line chart of sentiment for them?
app = dash.Dash(__name__)
server = app.server # Adding for deployment
# server = Flask(__name__)

app.layout = html.Div([
    html.H2('Sentiment by Speaker in Hamlet'),
    html.Div(children='''
        Speaker:
    '''),
    dcc.Input(id='speaker-in', value='HAMLET', type='text'),
    html.Button('Add to chart', id='btn'),
    html.Div(id='graph-out'),
    dcc.Input(id='word-in', value='madness', type='text'),
    html.Div(id='word-out', style={
        "color": "tomato",
        "text-align": "center",
        "font-family": "Georgia"
    })
])

#############################################################################################################

# Update word info:
@app.callback(
    Output('word-out', 'children'),
    [Input('word-in', 'value')]
)
# I wonder how costly it'll be to call this every keystroke -- apparently not very!:
def update(word):
    total = 0
    total_sent = 0
    total_sent_mag = 0
    speakers_count = defaultdict(int) # Nice, much cleaner

    for s in hamlet_list:
        if word in s['text']:
            total += 1
            total_sent += s['text'].sentiment.polarity
            total_sent_mag += abs(s['text'].sentiment.polarity)
            speakers_count[s['speaker']] += 1

    x = []
    for spk in speakers_count:
        x.append(html.P('{}: {}'.format(spk, speakers_count[spk])))

    # NOTE: Must ensure we're not dividing by zero!!!
    return(
        html.Div([
            html.P('Total: {}'.format(total)),
            html.P('Mean sentiment: {}'.format(total_sent / total)),
            html.P('Mean sentiment magnitude: {}'.format(total_sent_mag / total)),
            *x # Nice, python's way of spreading.
        ])
    )



#############################################################################################################

# Update the chart:
@app.callback(
    Output('graph-out','children'),
    [Input('btn', 'n_clicks')], # Must be passing this so we don't have to say state=, events=.
    # Input('speaker-in', 'value')], # Ok this works, but we don't want it to trigger every time the speaker-in value changes...
    [State('speaker-in', 'value')],
    # [Event('btn', 'click')]
)
# Nice, needs to take in one parameter for each input, state (and event?):
def on_click(clicks, input_value):
    active_speakers.append(input_value.upper())
    data = []

    for spk in active_speakers:
        sents = getSpeakerSentiment(spk)
        data.append({
            'x': df.index,
            'y': sents,
            'type': 'line',
            'name': spk
        })

    return dcc.Graph(
            id = 'whatev',
            figure = {
                'data': data,
                'layout': {
                    'title': 'HAMLET'
                }
            }
        )

#############################################################################################################

## The idea is to just draw the new line in addition to old lines without having to click enter.
# Problem: Dash won't let us assign multiple callbacks to one output: each output is controlled by one callback.
# And if we pass in the input as an Input, it triggers every time we type anything, appending that and all.....
# OOOoh you know, the hacky solution could be:
#   - Only fire the append code if button click is higher than it was previously.
#   - Ahh nuts, no. Because how do we know when the button is being pressed?
#   - Yeah the whole problem is that it *doesn't* know its previous number of clicks.


# @app.callback(
#     Output('graph-out', 'children'), # Output is the 'children' property of component that has id='output-graph'
#     [Input('speaker-in', 'value')] # Input is the 'value' property of component that has id='input'
# )
# def update_value(data):
#     for spk in active_speakers:
#         sents = getSpeakerSentiment(spk)
#         data.append({
#             'x': df.index,
#             'y': sents,
#             'type': 'line',
#             'name': spk
#         })
#     sents = getSpeakerSentiment(data.upper())
#     data.append({
#         'x': df.index,
#         'y': sents,
#         'type': 'line',
#         'name': spk
#     })
#
#     return dcc.Graph(
#             id = 'whatev',
#             figure = {
#                 'data': [
#                     {'x': df.index, 'y': sents, 'type': 'line', 'name': 'Hamlet'},
#                 ],
#                 'layout': {
#                     'title': 'HAMLET'
#                 }
#             }
#         )

#############################################################################################################

# Generate list of values tracking speaker's sentiment through the play:
def getSpeakerSentiment(speaker):
    total = 0
    res = []
    for s in hamlet_list:
        if s['speaker']:
            if s['speaker'] == speaker:
                total += s['text'].sentiment.polarity
            res.append(total)
    return res


#############################################################################################################

## Hmm I'm very confused why we're getting this KeyError for live-graph.figure....from previous app....
# That is really strange.... only restarting the computer worked.... must be a caching issue..

if __name__ == '__main__':
    app.run_server(debug=True)

# to be or not to be
