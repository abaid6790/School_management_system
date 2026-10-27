import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Development server only. Defaults to localhost so the Flask debugger is not
    # exposed to the rest of the network; set APP_HOST=0.0.0.0 deliberately if you
    # need LAN access (never in production -- use a real WSGI server, see
    # docs/INSTALLATION.md).
    app.run(
        host=os.environ.get("APP_HOST", "127.0.0.1"),
        port=int(os.environ.get("APP_PORT", "5000")),
    )
