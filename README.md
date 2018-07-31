# Shakespeare Sentiments
Users can view charts of the sentiments of speakers in Shakespeare's plays, and get information about words used.

## Built With:
- Dash

## Screenshot:
![screen shot 2018-07-31 at 12 14 51 am](https://user-images.githubusercontent.com/29472568/43439064-e94b6f04-9456-11e8-9143-da24fbd040e0.png)

## Personal Notes:
- Awesome for datasets: `req=urllib2.Request("https://raw.githubusercontent.com/plotly/datasets/master/miserables.json")`
- Use pip freeze > requirements.txt to generate this.
- Ok the road to deployment was long and strange.
  - I think the main issue was that we weren't importing *all* of the NLTK data modules...One of them must be needed for sentiment analysis.
  - Then because we brought in Flask and forgot the URL.
  - Also I think example had superfluous semicolon in Procfile.
  - A few red herrings -- the line endings thing, the /bin idea
- Keep in mind the difference between `.similar()` and `.similar_words` -- the latter requires `nltk.text.ContextIndex`.
## Next Steps:
- Would be cool if clicking a point brought up the surrounding text.
- HMM, nltk gives 22 matches for 'madness' (via `concordance()`), whereas our query only found 13...
