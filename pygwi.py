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
import time

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


def asctime(date):
    return time.asctime(time.gmtime(date))


@app.route('/')
def index():
    return redirect(url_for('contentView', name='home'))


@app.route('/new')
def newView():
    return render_template('edit.html', **locals())


@app.route('/<path:name>/add', methods=['POST'])
def add_entry(name):
    filename = name+'.md'
    f = open(os.path.join(path, filename), 'w')
    text = request.form.get('text')
    text = text.replace('\r\n', '\n')
    f.write(text)
    f.close()
    repo.index.add([filename])
    if repo.index.diff(None, paths=filename, staged=True):
        repo.index.commit('Update: '+name)
    else:
        print filename + ': not updated'
    return redirect(url_for('contentView', name=name))


@app.route('/<path:name>/edit')
def editView(name):
    content = open(os.path.join(path, name+'.md'), 'r').read()
    # TODO: Preveiw page
    return render_template('edit.html', **locals())


@app.route('/<path:name>/history')
def historyView(name):
    filename = name+'.md'
    commits = repo.iter_commits(paths=filename)
    dates = []
    for c in commits:
        date = asctime(c.authored_date-c.author_tz_offset)
        dates.append(date)
    commits = repo.iter_commits(paths=filename)
    # TODO: selectable history
    return render_template('history.html', **locals())


@app.route('/<path:name>/diff', methods=['POST'])
def diffView(name):
    import difflib
    filename = name+'.md'
    sha1 = request.form.getlist('sha-1')
    commit1 = repo.commit(sha1[0]).tree[filename].data_stream.read()
    commit2 = repo.commit(sha1[1]).tree[filename].data_stream.read()
    content = 'Diff\n\n```Diff\n'
    for buf in difflib.unified_diff(
            commit2.splitlines(),
            commit1.splitlines(),
            fromfile=sha1[0],
            tofile=sha1[1]):
        content += buf + '\n'
    content += '```'
    print content
    # TODO: get diff
    # TODO: decorate diff
    # TODO: Add diff page
    return render_template('diff.html', **locals())


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
