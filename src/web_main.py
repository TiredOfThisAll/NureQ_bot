from flask import Flask

app = Flask(__name__)

@app.route("/")
def queues():
    return "Queues Page"

app.run()
