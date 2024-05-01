from flask import Flask, redirect, url_for, render_template, request

app = Flask(__name__)


@app.route("/", methods=["POST", "GET"])
def home():
    message = None  # Initialize message variable

    if request.method == "POST":
        # Check if the POST request has a file part
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        # If the user does not select a file, the browser submits an empty file without a filename
        if file.filename == '':
            return redirect(request.url)

        # If file is present and valid, you can process it here
        # For example, save it to a specific location or do further processing
        print(file.filename)

        message = "Archive Soumise"  # Set message to be displayed

    return render_template("index.html", message=message)  # Pass message to template


if __name__ == "__main__":
    app.run(debug=True)
