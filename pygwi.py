# -*- coding: utf-8 -*-
"""PyGWi

Usage:
    manage.py [options]
    manage.py [options] <repositoryDir>

Options:
    -a, --all                  do not ignore entries starting with .

Othres:
        --help      display this help and exit
        --version   output version information and exit

"""

from flask import Flask
from flask import render_template
from flask import redirect
from flask import url_for
from flask import request
from flask.ext.misaka import Misaka
import os
from docopt import docopt
import git

md = Misaka(autolink=True,
            fenced_code=True,
            lax_html=True,
            no_intra_emphasis=True,
            tables=True,
            strikethrough=True,
            # render flags
            toc=True,
            xhtml=True,
            wrap=True)
app = Flask(__name__)
md.init_app(app)

path = '.'
repo = 0


@app.route('/')
def index():
    return redirect(url_for('contentView', name='home'))


@app.route('/new')
def newView():
    return render_template('edit.html', **locals())


@app.route('/<path:name>/add', methods=['POST'])
def add_entry(name):
    f = open(os.path.join(path, name+'.md'), 'w')
    text = request.form.get('text')
    f.write(text)
    return redirect(url_for('contentView', name=name))


@app.route('/<path:name>/edit')
def editView(name):
    content = open(os.path.join(path, name+'.md'), 'r').read()
    # TODO: Preveiw page
    return render_template('edit.html', **locals())


@app.route('/<path:name>/history')
def historyView(name):
    # TODO: get log of current file
    # TODO: decorate logs
    # TODO: Add histroy page
    return render_template('history.html', **locals())


@app.route('/<path:name>/diff')
def diffView(name):
    # TODO: get diff
    # TODO: decorate diff
    # TODO: Add diff page
    return render_template('edit.html', **locals())


@app.route('/<path:name>')
def contentView(name):
    if os.path.splitext(name)[1] != '.ico':
        content = open(os.path.join(path, name+'.md'), 'r').read()
        # TODO: Create new page when page not found
        return render_template('index.html', **locals())
    else:
        pass

# TODO: Login and logout page and session
# TODO: Create layout.html

if __name__ == '__main__':
    args = docopt(__doc__, version='1.0.0')
    if args['<repositoryDir>']:
        path = args['<repositoryDir>']
    repo = git.Repo(path)

    # app.run(debug=True)
    app.run(host='0.0.0.0', debug=True)
