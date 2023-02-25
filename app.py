import io
from flask import Flask, Response, render_template, request, redirect, send_file, url_for
import pandas as pd
from utils import get_user_data
from flask import Flask
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.files['csv_file'].filename.endswith('.csv'):
            df = pd.read_csv(request.files['csv_file'])
            edit_count = request.form['edit_count']
            edit_count = int(edit_count)
            data, _ = get_user_data(df, edit_count)
            data = data.head(5)
            cols = data.columns.tolist()
            data = data.to_csv()
            data = data.encode('utf-8')
            return render_template('index.html', data=data, edit_count=edit_count, cols=cols)
    data = None
    return render_template('index.html', data=data, file=None, edit_count=5)


@app.route('/download', methods=['GET', 'POST'])
def download():
    if request.method == 'POST':
        df_encoded = request.form['df_value'][2:-1]
        # replace \\n with \n, \' with ', \\" with "
        # df_encoded = df_encoded.encode('utf-8')
        df_encoded = df_encoded.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
        # print(f'{df_encoded}', type(df_encoded))
        df = pd.read_csv(io.StringIO(df_encoded))
        print('HERE', df.head())
        csv = df.to_csv(index=False)
        return Response(
            csv,
            mimetype="text/csv",
            headers={"Content-disposition":
                     "attachment; filename=users.csv"})
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
