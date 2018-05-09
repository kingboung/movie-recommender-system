from flask import Flask
from eip_controller import eip_worker

app = Flask(__name__)


@app.route('/')
def change_eip():
    eip_worker()
    return 'Done'


if __name__ == '__main__':
    app.run(host='0.0.0.0')
