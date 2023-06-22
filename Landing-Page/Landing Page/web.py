from flask import Flask, request, redirect, url_for, render_template, flash
import os
import subprocess
import time

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads/"
app.secret_key = "your_secret_key"


@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            flash("선택된 파일이 없습니다.", "error")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("선택된 파일이 없습니다.", "error")
            return redirect(request.url)

        filename = file.filename
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        return render_template("loading.html")

    return render_template("home.html")


@app.route("/redirect", methods=["GET"])
def redirect_to_notion():
    time.sleep(5)  # Wait for 5 seconds
    return redirect(
        "https://www.notion.so/laonm/DEMO-VER1-1-5MIN-af75e4858ae34fdca651c9668884afca?pvs=4"
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
