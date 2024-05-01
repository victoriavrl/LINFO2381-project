from flask import Flask, redirect, url_for, render_template, request

app = Flask(__name__)

@app.route("/", methods=["POST","GET"])
def home():
    if request.method == "POST":
        return render_template("index.html") 
    return render_template("index.html")



if __name__ == "__main__":
    app.run(debug=True) 