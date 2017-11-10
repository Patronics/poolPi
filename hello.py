from flask import Flask
app = Flask(__name__)

@app.route("/test")
def hello():
    return "Hello World! <br> simple test!"
	#printedText = "Hello World! This is a basic Python script that concatenates the integer "+str(5)+" with the rest of this string!"
	#printedTextLen = "The length of the previous sentence is "+str(len(printedText))+" characters."
	#return printedText + "<br>" + printedTextLen
	#return "test"
if __name__ == "__main__":

	app.run('0.0.0.0')

