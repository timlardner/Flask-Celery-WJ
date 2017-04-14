# Usage

# sudo apt-get install rabbitmq-server
# pip install celery
# celery -A wj.celery worker
# python wj.py
# Visit http://localhost:5000 for a demo

import os
import uuid
import random
import string
from io import BytesIO
import time
import json
import datetime
import pickle

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from flask import Flask, request, redirect, flash, url_for, session, g
from flask import render_template, render_template_string
from flask import Blueprint, make_response, abort
from celery import Celery, current_task
from celery.result import AsyncResult


celery = Celery(os.path.splitext(__file__)[0],
        backend='rpc://',
        broker='amqp://localhost')


@celery.task
def get_data_from_strava():
    current_task.update_state(state='PROGRESS')
    time.sleep(2)
    fig=Figure()
    ax=fig.add_subplot(111)
    x=[]
    y=[]
    now=datetime.datetime.now()
    delta=datetime.timedelta(days=1)
    for i in range(10):
        x.append(now)
        now+=delta
        y.append(random.randint(0, 1000))
    ax.plot_date(x, y, '-')
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    canvas=FigureCanvas(fig)
    png_output = BytesIO()
    canvas.print_png(png_output)
    out = png_output.getvalue()
    filename = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20)) + '.png'
    pickle.dump(out,open(filename,'wb'))
    return filename


app = Flask(__name__)

@app.route('/progress')
def progress():
    jobid = request.values.get('jobid')
    if jobid:
        job = AsyncResult(jobid, app=celery)
        print(job.state)
        print(job.result)


        # If you have different stages here, you could actually update this
        # and have a progress bar while the image is being generated.

        if job.state == 'PROGRESS':
            return json.dumps(dict(
                state=job.state,
                progress=0,
            ))
        elif job.state == 'SUCCESS':
            return json.dumps(dict(
                state=job.state,
                progress=1,
            ))
    return '{}'

@app.route('/result.png')
def result():
    jobid = request.values.get('jobid')
    if jobid:
        job = AsyncResult(jobid, app=celery)
        filename = job.get()
        png_output = pickle.load(open(filename,'rb'))
        os.remove(filename)
        response=make_response(png_output)
        response.headers['Content-Type'] = 'image/png'
        return response
    else:
        return 404    

@app.route('/image_page')
def image_page():
    job = get_data_from_strava.delay()
    return render_template_string('''\

<h3>Awesome Asynchronous Image Generation</h3>
<div id="imgpl">Image not ready. Please wait.</div>
<script src="//code.jquery.com/jquery-2.1.1.min.js"></script>
<script>
function poll() {
    $.ajax("{{url_for('.progress', jobid=JOBID)}}", {
        dataType: "json"
        , success: function(resp) {
            if(resp.progress == 1) {
                $("#imgpl").html('<img src="result.png?jobid={{JOBID}}">')
                return;
            } else {
                setTimeout(poll, 500.0);
            }

        }
    });

}

$(function() {
    var JOBID = "{{ JOBID }}";
    poll();

});
</script>
''', JOBID=job.id)


@app.route('/')
def index():
    return render_template_string('''\

<a href="{{ url_for('.image_page') }}">Whatever you click to get data from Strava...</a>
''')


if __name__ == '__main__':
    app.run(debug=True)