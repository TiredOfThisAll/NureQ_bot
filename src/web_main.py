import json

from flask import Flask, render_template, g, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required
from os import path
from werkzeug.local import LocalProxy

from data_access.repository import Repository
from data_access.sqlite_connection import create_sqlite_connection
from web.models.user import User


# constants
PROJECT_PATH = path.abspath(path.join(__file__, "..", ".."))

# configuration
config_file_path = path.join(PROJECT_PATH, "config", "configuration.json")
with open(config_file_path) as configuration_file:
    configuration = json.loads(configuration_file.read())

DATABASE_PATH = path.join(PROJECT_PATH, configuration["database"])
TOKEN_PATH = path.join(PROJECT_PATH, configuration["token"])

with open(TOKEN_PATH, "rb") as token_file:
    TOKEN = token_file.readline()
    if TOKEN[-1] == "\n":
        TOKEN = TOKEN[:-1]

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


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/telegram-login-successful")
def telegram_login_successful():
    # и у нас тут будет в query parameter-ах приходить объект с полями id, hash, auth_date
    user = User(request.args["id"])
    admins = context.repository.get_admins_id()
    if int(user.user_id) not in admins:
        return redirect(url_for("login"))
    login_user(user)

    # 1. спарсить query parameter-ы (там будет user ID, username и т.д.)
    # 2. проверить что этот пользователь есть в нашей таблице админов
    #   (в таблице админов будет только user ID)
    # 3. если все ок, то засунуть пользователю сессию в карман (я не знаю куда именно)
    #   если неок, то вернуть на логин и сказать, что чел не в списке админов
    # 4. потом перенаправить на главную страницу
    # P.S.: нужно в каждом запросе чекать что пользователь аутентифицирован воистину
    # P.P.S.: нужно еще как-то валидировать хэш, который нам сюда приходит
    return redirect(url_for("root"))


@app.route("/api/queues/<int:id>", methods=["DELETE"])
@login_required
def delete_queue(id):
    context.repository.delete_queue(id)
    context.repository.commit()
    return "", 204


@app.route("/api/queues/<int:queue_id>/members/<int:user_id>", methods=["DELETE"])
@login_required
def delete_queue_member(queue_id, user_id):
    context.repository.remove_user_from_queue(user_id, queue_id)
    context.repository.commit()
    return "", 204


@app.route("/api/queues/<int:queue_id>/members/<int:user_id>/crossed", methods=["PUT"])
@login_required
def set_queue_member_crossed_out(queue_id, user_id):
    context.repository.set_queue_member_crossed_out(user_id, queue_id, int(request.data))
    context.repository.commit()
    return "", 204


@app.route("/api/queues/<int:queue_id>/<action>", methods=["PUT"])
@login_required
def pull_down_queue_member(queue_id, action):
    if action == "move-up":
        error = context.repository.move_up_queue_member(queue_id, int(request.data))
    elif action == "move-down":
        error = context.repository.move_down_queue_member(queue_id, int(request.data))
    else:
        return "", 404
    if error == "INVALID_POSITION":
        return "", 400
    if error is not None:
        return "", 500
    context.repository.commit()
    return "", 204


app.run(port=80)
