from flask import Flask, request, redirect, url_for
import os
import nbconvert
import subprocess
import time

#uploads 파일 사전 생성 필요
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Convert notebook to Python file
        python_filename = os.path.splitext(filename)[0] + '.py'
        subprocess.run(['jupyter', 'nbconvert', '--to', 'script', filename])
        
        # Run Python file
        subprocess.run(['python', python_filename])

        # Delay the response by 20 seconds
        time.sleep(20)

        # Return hyperlink to Chat_Wiki
        return'''<script>
            setTimeout(function() {
                window.location.href = "https://www.notion.so/laonm/DEMO-VER1-1-5MIN-af75e4858ae34fdca651c9668884afca?pvs=4";
            }, 20000);
        </script>
        <div style="display: flex; justify-content: center; align-items: center; height: 100vh;">
        <a href="https://www.notion.so/laonm/DEMO-VER1-1-5MIN-af75e4858ae34fdca651c9668884afca?pvs=4">Chat_Wiki 생성!</a>'''

    
    return '''
    <!doctype html>
    <html>
    <head>
    <style>
    /* 정렬 */
    body {
        height: 100vh; /* 화면 전체 높이만큼 지정 */
        display: flex;
        flex-direction: column;
        justify-content: center; /* 수직 중앙 정렬 */
        align-items: center; /* 수평 중앙 정렬 */
    }
    </style>
    </head>
    <body>
    <h1>File Upload</h1>
    <form method="post" enctype="multipart/form-data">
      <input type="file" name="file">
      <input type="submit" value="Upload">
    </form>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
