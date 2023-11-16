from apiflask import APIBlueprint, abort
from apiflask.fields import String
from flask import g, session

from apiflaskdemo.project.auth.schemas import LoginSchema
from apiflaskdemo.project.models import User

auth_bp = APIBlueprint("auth_bp", __name__)

@auth_bp.before_app_request
def user_checkout():
    user_id = session.get("user_id")
    if user_id is None:
        g.user =None
    else:
        g.user = User.query.filter_by(id=user_id).first()

@auth_bp.post("/login")
@auth_bp.input(LoginSchema)
def login(json_data):
    user = User.query.filter_by(username=json_data["username"]).one_or_none()
    if user and user.password == json_data["password"]:
        session.clear()
        session["user_id"] = user.id
        return {'msg': 'logged in'}
    else:
        abort(403)

@auth_bp.get("/logout")
def logout():
    session.clear()
    return {"msg": "logged out"}