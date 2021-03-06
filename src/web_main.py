from flask import Flask, render_template
from os import path

PROJECT_PATH = path.abspath(path.join(__file__, "..", ".."))

app = Flask(
    __name__,
    template_folder=path.join(PROJECT_PATH, "src", "web", "templates")
)

@app.route("/")
def queues():
    return render_template("queues.html")

app.run()
