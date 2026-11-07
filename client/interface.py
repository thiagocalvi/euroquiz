from app import app, CLIENT_PORT

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=CLIENT_PORT, debug=True)
