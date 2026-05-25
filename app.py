import os

from apiflaskdemo import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",  # noqa: S104
        port=3000,
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
