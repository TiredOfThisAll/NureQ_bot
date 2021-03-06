import sqlite3
import json

from flask import Flask, render_template, g
from os import path
from werkzeug.local import LocalProxy

from data_access.repository import Repository

# constants
PROJECT_PATH = path.abspath(path.join(__file__, "..", ".."))

# configuration
config_file_path = path.join(PROJECT_PATH, "config", "configuration.json")
with open(config_file_path) as configuration_file:
    configuration = json.loads(configuration_file.read())

DATABASE_PATH = path.join(PROJECT_PATH, configuration["database"])

# flask set-up
app = Flask(
    __name__,
    template_folder=path.join(PROJECT_PATH, "src", "web", "templates")
)


class Context:
    def __init__(self):
        self.connection = sqlite3.connect(DATABASE_PATH)
        self.repository = Repository(self.connection)

    def __enter__(self):
        self.connection.__enter__()

    def __exit__(self):
        self.connection.close()


def inject_context():
    if "context" not in g:
        g.context = Context()
    return g.context


@app.teardown_appcontext
def teardown_context(exception):
    context = g.pop("context", None)
    if context is not None:
        context.__exit__()


context = LocalProxy(inject_context)


@app.route("/")
def queues():
    return render_template("queues.html", queues=context.repository
                           .get_queue_page_view(1, 10))


app.run()
