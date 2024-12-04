from flask import Flask, jsonify
from flask_mysqldb import MySQL
import requests

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'sakila'
mysql = MySQL(app)

@app.route('/process_query', methods=['POST'])
def process_query():
    cur = mysql.connection.cursor()
    query = requests.json['query']
    cur.execute(query)
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'query procesed'})


if __name__ == '__main__':
    app.run(debug=True)