import ast
import io
from flask import Flask, Response, render_template, request, redirect, send_file, url_for
import pandas as pd
from utils import get_user_data
from flask import Flask
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'csv_file' in request.files:
            if request.files['csv_file'].filename.endswith('.csv'):
                df = pd.read_csv(request.files['csv_file'])
                edit_count = request.form['edit_count']
                activity_count = request.form['activity_count']
                edit_count = int(edit_count)
                activity_count = int(activity_count)
                data, _ = get_user_data(df, edit_count, activity_count)
                data = data.head(5)
                cols = list(data.columns)
                data = data.to_csv(index=False)
                data = data.encode('utf-8')
                data = str(data)[2:-3]
                return render_template('index.html', data=data, edit_count=edit_count, cols=cols, activity_count=activity_count)
        else:
            df_encoded = request.form['df_value'][2:-1]
            cols = request.form.getlist('filter_csv')
            edit_count = request.form['edit_count']
            activity_count = request.form['activity_count']
            df_encoded = df_encoded.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
            df = pd.read_csv(io.StringIO(df_encoded))
            if cols:
                df = df[cols]
            data = df.to_csv(index=False)
            data = data.encode('utf-8')
            data = str(data)[2:-3]
            return render_template('index.html', data=data, edit_count=edit_count, cols=cols, activity_count=activity_count)
    data = None
    return render_template('index.html', data=data, edit_count=5, activity_count=0)


@app.route('/download', methods=['GET', 'POST'])
def download():
    if request.method == 'POST':
        df_encoded = request.form['df_value'][2:-1]
        cols = request.form.getlist('filter_csv')
        print(cols)
        df_encoded = df_encoded.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
        df = pd.read_csv(io.StringIO(df_encoded))
        if cols:
            df = df[cols]
        csv = df.to_csv(index=False)
        return Response(
            csv,
            mimetype="text/csv",
            headers={"Content-disposition":
                     "attachment; filename=users.csv"})
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
