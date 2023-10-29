from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

@app.route('/nearest')
def nearest():
    """
    - Check cache
    - If not in cache, get stops within radius from TfL API (maybe create Stop objects?)
    - Return next departures from nearest stops
    - Optional: if user profile exists, filter/sort by preferences
    """
    lat, lon = request.form["lat"], request.form["lon"]
    return []

if __name__ == '__main__':
    app.run()
 