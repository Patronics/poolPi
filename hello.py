from flask import Flask
app = Flask(__name__)

@app.route("/test")
def hello():
    return "Hello World! <br> simple test!"
if __name__ == "__main__":

	app.run('0.0.0.0')

