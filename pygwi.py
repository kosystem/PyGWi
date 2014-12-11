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

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    jsonify
    )
from flask.ext.misaka import Misaka

import os
from docopt import docopt
import git
import time
import codecs


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
uploadDir = 'uploads'

app.config['ALLOWED_EXTENSIONS'] = set([
    'txt',
    'pdf',
    'png',
    'jpg',
    'jpeg',
    'gif'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def asctime(date):
    return time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(date))


def pagelist():
    lsfiles = repo.git().ls_files().splitlines()
    files = []
    for f in lsfiles:
        pagename = f.replace('.md', '').decode('utf-8')
        files.append(pagename)
    return files


def commit(repo, filename, message):
    # commit
    filename = filename.encode('utf-8')
    repo.index.add([filename])
    if repo.index.diff(None, paths=filename, staged=True):
        try:
            repo.index.commit(message)
        except UnicodeEncodeError:
            print 'Encode error'
    else:
        pass


def commitList(filename=None):
    iter_commits = repo.iter_commits(paths=filename)
    commits = []
    for c in iter_commits:
        date = asctime(c.authored_date-c.author_tz_offset)
        # TODO: Chnge to jinja2 filter
        # (http://study-flask.readthedocs.org/ja/latest/07.html)
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
        # di2 = r.head.commit.parents[0].diff(r.head.commit)
        #  l = list(di2.iter_change_type('A'))
        # l[0].b_blob.name
    return commits


@app.route('/')
def index():
    return redirect(url_for('contentView', name='home'))


@app.route('/new')
def newView():
    pageList = pagelist()
    updateList = commitList()
    # TODO: Preveiw page
    # TODO; redirect to edit page
    # TODO: common architecture to edit page
    return render_template('new.html', **locals())


@app.route('/<path:name>/edit')
def editView(name):
    pageList = pagelist()
    updateList = commitList()
    content = codecs.open(
        os.path.join(path, name+'.md'),
        'r',
        encoding='utf-8').read()
    # TODO: Preveiw page
    return render_template('edit.html', **locals())


@app.route('/<path:name>/add', methods=['POST'])
def add_entry(name):
    commitMessage = 'Update: '+name
    if name == 'new':
        name = request.form.get('pagename')
        # name = secure_filename(name)
        name = name.replace('../', '')
        # TODO: safe file name
        # TODO: dose not create directory
        commitMessage = 'Create: '+name

    # TODO: Add commit message form
    if request.form.get('message'):
        commitMessage = request.form.get('message')

    filename = name+'.md'
    fullpath = os.path.join(path, filename)
    try:
        f = open(fullpath, 'w')
    except:
        os.makedirs(os.path.dirname(fullpath))
        f = open(os.path.join(path, filename), 'w')
    text = request.form.get('text').encode('utf-8')
    text = text.replace('\r\n', '\n')
    f.write(text)
    f.close()
    # git commit --------
    commit(repo, filename, commitMessage)
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


@app.route('/upload', methods=['POST'])
def upldfile():
    # TODO: multi byte filename
    updir = os.path.join(path, uploadDir)
    if not os.path.isdir(updir):
        os.makedirs(updir)
    if request.method == 'POST':
        files = request.files['file']
        print files.filename
        if files and allowed_file(files.filename):
            print files.filename
            # filename = secure_filename(files.filename)
            filename = files.filename.replace('../', '')
            print filename
            app.logger.info('FileName: ' + filename)
            files.save(os.path.join(updir, filename))
            commit(repo, os.path.join(uploadDir, filename), 'Upload: %s' % filename)
            file_size = os.path.getsize(os.path.join(updir, filename))
            return jsonify(name=filename, size=file_size)


@app.route('/<path:name>')
def contentView(name):
    pageList = pagelist()
    updateList = commitList()
    if os.path.splitext(name)[1] != '.ico':
        f = codecs.open(os.path.join(path, name+'.md'), 'r', encoding='utf-8')
        pageTitle = f.readline()
        pageTitle = pageTitle.replace('#', '')
        content = f.read()
        # TODO: Create new page when page not found
        return render_template('index.html', **locals())
    else:
        pass

# TODO: Add Delete button
# TODO: Login and logout page and session
# TODO: upload file page
# TODO: delete button in upload file page
# TODO: Add flash message

if __name__ == '__main__':
    args = docopt(__doc__, version='1.0.0')
    if args['<repositoryDir>']:
        path = args['<repositoryDir>']
    repo = git.Repo(path)

    # app.run(debug=True)
    app.run(host='0.0.0.0', debug=True)
