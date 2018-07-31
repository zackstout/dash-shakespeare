
import pandas as pd
from textblob import TextBlob
import dash
from dash.dependencies import Input, Output, State, Event
import dash_core_components as dcc
import dash_html_components as html

df = None

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

active_speakers = [] # Which speakers are on the chart

# Could set up an input field for typing speaker name, get line chart of sentiment for them?
app2 = dash.Dash(__name__)

app2.layout = html.Div([
    html.H2('Sentiment by Speaker in Hamlet'),
    html.Div(children='''
        Speaker:
    '''),
    dcc.Input(id='speaker-in', value='HAMLET', type='text'),
    html.Button('Add to chart', id='btn'),
    html.Div(id='graph-out')
])


@app2.callback(
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


# @app2.callback(
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
                # print(s['text'], s['speaker'])
                total += s['text'].sentiment.polarity
            res.append(total)
    return res




## Hmm I'm very confused why we're getting this KeyError for live-graph.figure....from previous app....
# That is really strange.... only restarting the computer worked.... must be a caching issue..

if __name__ == '__main__':
    app2.run_server(debug=True)

# to be or not to be
