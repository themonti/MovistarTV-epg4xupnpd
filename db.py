from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)
# 'postgres://vccnjnlifunbnm:9kFmSDyg8BWTe5wFDdf4IOau0Q@ec2-54-247-170-228.eu-west-1.compute.amazonaws.com:5432/d9msst1obko80b'
