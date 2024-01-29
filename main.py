from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/products')
def products():
    return render_template('products.html')

@app.route('/designer')
def designer():
    return render_template('designer.html')

if __name__ == '__main__':
    app.run(debug=True)

