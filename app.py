import io
from flask import Flask, render_template, request, redirect, send_file, url_for
import pandas as pd
from utils import get_user_data
from flask import Flask
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.files['file'].filename.endswith('.csv'):
            df = pd.read_csv(request.files['file'])
            data, _ = get_user_data(df)
            data = data.to_csv()
            data = data.encode('utf-8')
            return render_template('index.html', data=data)
    data = None
    return render_template('index.html', data=data)


@app.route('/download', methods=['GET', 'POST'])
def download():
    print(request.form)
    if request.method == 'POST':
        html = request.form['download_csv']
        print(html)
        df = pd.read_html(html)[0]
        csv = df.to_csv(index=False)
        return send_file(
            pd.compat.StringIO(csv),
            mimetype='text/csv',
            attachment_filename='data.csv',
            as_attachment=True
        )
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
