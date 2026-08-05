from app import create_app
# importing the application factory function so we can build the app instance.

app = create_app()  # builds the flask application and returns it.

if __name__ == '__main__':
    app.run(debug=True)
    # debug mode active therefore the server automatically picks up changes.
