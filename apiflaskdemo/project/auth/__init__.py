from functools import wraps

from flask import abort, g


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return abort(403)
        return view(*args, **kwargs)

    return wrapped_view
