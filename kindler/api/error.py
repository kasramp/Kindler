from flask import render_template, Blueprint, request

error_bp = Blueprint("error", __name__, url_prefix="/error")


@error_bp.route("")
def error():
    message = map_status_code_to_error(request.args.get("status_code"))
    return render_template("error.html", message=message)


def map_status_code_to_error(status_code):
    match status_code:
        case "403":
            return "Website denied access (403)"
        case "404":
            return "URL does not exist (404)"
        case "500":
            return "Encountered internal error (500)"
        case _:
            return None
