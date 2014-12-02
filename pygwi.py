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
    return time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(date))


def pagelist():
    lsfiles = repo.git().ls_files().splitlines()
    files = []
    for f in lsfiles:
        files.append(f.replace('.md', ''))
    return files


def commitList(filename=None):
    iter_commits = repo.iter_commits(paths=filename)
    commits = []
    for c in iter_commits:
        date = asctime(c.authored_date-c.author_tz_offset)
        author = c.author.name
        message = c.message
        hexsha = c.hexsha
        commit = {
            'date': date,
            'author': author,
            'message': message,
            'hexsha': hexsha
            }
        commits.append(commit)
    return commits


@app.route('/')
def index():
    return redirect(url_for('contentView', name='home'))


@app.route('/new')
def newView():
    pageList = pagelist()
    updateList = commitList()
    # TODO: Preveiw page
    return render_template('new.html', **locals())


@app.route('/<path:name>/edit')
def editView(name):
    pageList = pagelist()
    updateList = commitList()
    content = open(os.path.join(path, name+'.md'), 'r').read()
    # TODO: Preveiw page
    return render_template('edit.html', **locals())


@app.route('/<path:name>/add', methods=['POST'])
def add_entry(name):
    commitMessage = 'Update: '+name
    if name == 'new':
        name = request.form.get('pagename')
        # TODO: safe file name
        commitMessage = 'Create: '+name

    # TODO: Add commit message form
    if request.form.get('message'):
        commitMessage = request.form.get('message')

    filename = name+'.md'
    f = open(os.path.join(path, filename), 'w')
    text = request.form.get('text')
    text = text.replace('\r\n', '\n')
    f.write(text)
    f.close()
    repo.index.add([filename])
    if repo.index.diff(None, paths=filename, staged=True):
        repo.index.commit(commitMessage)
    else:
        pass
    return redirect(url_for('contentView', name=name))


@app.route('/<path:name>/history')
def historyView(name):
    pageList = pagelist()
    updateList = commitList()
    filename = name+'.md'
    commits = commitList(filename)
    return render_template('history.html', **locals())


@app.route('/<path:name>/diff', methods=['POST'])
def diffView(name):
    pageList = pagelist()
    updateList = commitList()
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
    return render_template('diff.html', **locals())
    # TODO: single diff


@app.route('/<path:name>')
def contentView(name):
    pageList = pagelist()
    updateList = commitList()
    if os.path.splitext(name)[1] != '.ico':
        content = open(os.path.join(path, name+'.md'), 'r').read()
        # TODO: Create new page when page not found
        return render_template('index.html', **locals())
    else:
        pass

# TODO: Add Delete button
# TODO: Login and logout page and session
# TODO: Side menu
# TODO: Upload file
# TODO: Upload by ajax
# TODO: Update log in side menu
# TODO: Page tree in side menu
# TODO: Add flash message

if __name__ == '__main__':
    args = docopt(__doc__, version='1.0.0')
    if args['<repositoryDir>']:
        path = args['<repositoryDir>']
    repo = git.Repo(path)

    # app.run(debug=True)
    app.run(host='0.0.0.0', debug=True)
