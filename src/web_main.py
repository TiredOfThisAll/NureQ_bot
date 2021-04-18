from flask import Flask, render_template, g, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user
import json
from os import path
import time
from werkzeug.local import LocalProxy

from data_access.repository import Repository
from data_access.sqlite_connection import create_sqlite_connection
from services.telegram.authentication import validate_login_hash
from web.models.user import User


# constants
PROJECT_PATH = path.abspath(path.join(__file__, "..", ".."))
TELEGRAM_LOGIN_EXPIRY_TIME = 24 * 60 * 60  # 24 hours in seconds

# configuration
config_file_path = path.join(PROJECT_PATH, "config", "configuration.json")
with open(config_file_path) as configuration_file:
    configuration = json.loads(configuration_file.read())

DATABASE_PATH = path.join(PROJECT_PATH, configuration["database"])
TOKEN_PATH = path.join(PROJECT_PATH, configuration["token"])

with open(TOKEN_PATH) as token_file:
    TOKEN = token_file.readline()
    if TOKEN[-1] == "\n":
        TOKEN = TOKEN[:-1]
    TOKEN = TOKEN.encode()

# flask set-up
app = Flask(
    __name__,
    template_folder=path.join(PROJECT_PATH, "src", "web", "templates"),
    static_folder=path.join(PROJECT_PATH, "src", "web", "static")
)
app.secret_key = TOKEN
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@login_manager.unauthorized_handler
def unathorized():
    return redirect(url_for("login"))


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
@login_required
def queues():
    return render_template(
        "queues.html",
        queues=context.repository.get_queue_page_view(1, 10)
    )


@app.route("/queues/<int:id>")
@login_required
def edit_queue(id):
    return render_template(
        "edit_queue.html",
        queue_members=context.repository.get_queue_members_by_queue_id(id),
        queue=context.repository.get_queue_by_id(id)
    )


@app.route("/queues/<int:queue_id>/swap-queue-members")
@login_required
def swap_queue_members(queue_id):
    queue = context.repository.get_queue_by_id(queue_id)
    queue_members = context.repository.get_queue_members_by_queue_id(queue_id)
    return render_template(
        "swap_queue_members.html",
        queue=queue,
        queue_members=queue_members
    )


@app.route("/login")
def login():
    # page navigation
    if not request.args:
        return render_template("login.html")
    # redirect from telegram login page after login attempt
    user_id_str = request.args["id"]
    is_login_valid = validate_login_hash(request.args, TOKEN)
    if not is_login_valid:
        return render_template(
            "login.html",
            error="Ошибка верификации данных, попробуйте еще раз или "
            + "обратитесь к разработчикам"
        )
    if time.time() - int(request.args["auth_date"]) \
            >= TELEGRAM_LOGIN_EXPIRY_TIME:
        return render_template(
            "login.html",
            error="Ваша сессия истекла, попробуйте еще раз или обратитесь к "
            + "разработчикам"
        )
    if not context.repository.is_user_admin(int(user_id_str)):
        return render_template(
            "login.html",
            error="Вы не входите в список администраторов, обратитесь к "
            + "разработчикам, если считаете, что это ошибка"
        )
    user = User(user_id_str)
    login_user(user)

    return redirect(url_for("root"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/api/queues/<int:id>", methods=["DELETE"])
@login_required
def delete_queue(id):
    context.repository.delete_queue(id)
    context.repository.commit()
    return "", 204


@app.route(
    "/api/queues/<int:queue_id>/members/<int:user_id>",
    methods=["DELETE"]
)
@login_required
def delete_queue_member(queue_id, user_id):
    context.repository.remove_user_from_queue(user_id, queue_id)
    context.repository.commit()
    return "", 204


@app.route(
    "/api/queues/<int:queue_id>/members/<int:user_id>/crossed",
    methods=["PUT"]
)
@login_required
def set_queue_member_crossed_out(queue_id, user_id):
    new_is_crossed_out = int(request.data)
    context.repository.set_queue_member_crossed_out(
        user_id,
        queue_id,
        new_is_crossed_out
    )
    context.repository.commit()
    return "", 204


@app.route("/api/queues/<int:queue_id>/<action>", methods=["PUT"])
@login_required
def pull_down_queue_member(queue_id, action):
    current_position = int(request.data)
    if action == "move-up":
        error = context.repository.move_up_queue_member(
            queue_id,
            current_position
        )
    elif action == "move-down":
        error = context.repository.move_down_queue_member(
            queue_id,
            current_position
        )
    else:
        return "", 404
    if error == "INVALID_POSITION":
        return "", 400
    if error is not None:
        return "", 500
    context.repository.commit()
    return "", 204


app.run(port=80)
