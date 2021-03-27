import json

from flask import Flask, render_template, g, request
from os import path
from werkzeug.local import LocalProxy

from data_access.repository import Repository
from data_access.sqlite_connection import create_sqlite_connection


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
    template_folder=path.join(PROJECT_PATH, "src", "web", "templates"),
    static_folder=path.join(PROJECT_PATH, "src", "web", "static")
)


class Context:
    def __init__(self):
        self.connection = create_sqlite_connection(DATABASE_PATH)
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


@app.route("/", endpoint="root")
@app.route("/queues", endpoint="queues")
def queues():
    return render_template(
        "queues.html",
        queues=context.repository.get_queue_page_view(1, 10)
    )


@app.route("/queues/<int:id>")
def edit_queue(id):
    return render_template(
        "edit_queue.html",
        queue_members=context.repository.get_queue_members_by_queue_id(id),
        queue=context.repository.get_queue_by_id(id)
    )


@app.route("/api/queues/<int:id>", methods=["DELETE"])
def delete_queue(id):
    context.repository.delete_queue(id)
    context.repository.commit()
    return "", 204


@app.route("/api/queues/<int:queue_id>/members/<int:user_id>", methods=["DELETE"])
def delete_queue_member(queue_id, user_id):
    context.repository.remove_user_from_queue(user_id, queue_id)
    context.repository.commit()
    return "", 204


@app.route("/api/queues/<int:queue_id>/members/<int:user_id>/crossed", methods=["PUT"])
def set_queue_member_crossed_out(queue_id, user_id):
    context.repository.set_queue_member_crossed_out(user_id, queue_id, int(request.data))
    context.repository.commit()
    return "", 204


app.run()
