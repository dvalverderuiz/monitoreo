from flask import Flask, render_template
import psutil

app = Flask(__name__)

@app.route('/')
def index():
    net_io = psutil.net_io_counters()
    data = {
        "bytes_sent": net_io.bytes_sent,
        "bytes_recv": net_io.bytes_recv,
        "packets_sent": net_io.packets_sent,
        "packets_recv": net_io.packets_recv,
    }
    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
