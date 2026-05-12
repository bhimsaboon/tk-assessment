from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/health")
def health() -> tuple[dict[str, str], int]:
    return {"status": "healthy"}, 200


@app.route("/")
def index() -> tuple[dict[str, str], int]:
    return {"message": "TechKraft API v1.0"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

