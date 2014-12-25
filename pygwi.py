# -*- coding: utf-8 -*-
"""PyGWi

Usage:
    manage.py [options]
    manage.py [options] <repositoryDir>

Options:
    -a, --all                   do not ignore entries starting with .
    -d, --debug                 debug mode
    -p <PORT>, --port=PORT      port number [default: 5000]

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
    send_from_directory,
    jsonify
    )

import misaka
import os
from docopt import docopt
import git
import time
import codecs

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import houdini as h


class BleepRenderer(misaka.HtmlRenderer, misaka.SmartyPants):
    def list(self, text, is_ordered):
        if '[ ] ' in text and '[x] ' in text:
            text = text.replace('[ ]', '<input type="checkbox" disabled>')
            text = text.replace('[x]', '<input type="checkbox" checked disabled>')
            text = '\n<ul class="check-list">\n%s</ul>\n' % text
        else:
            text = '\n<ul>\n%s</ul>\n' % text
        return text

    def block_code(self, text, lang):
        if not lang:
            return ('\n<pre><code>%s</code></pre>\n'
                    % h.escape_html(text.strip()))
        lexer = get_lexer_by_name(lang, stripall=True)
        formatter = HtmlFormatter()
        return highlight(text, lexer, formatter)


misaka_ext = (misaka.EXT_AUTOLINK |
              misaka.EXT_FENCED_CODE |
              misaka.EXT_LAX_HTML_BLOCKS |
              misaka.EXT_NO_INTRA_EMPHASIS |
              # misaka.EXT_SPACE_HEADERS |
              misaka.EXT_STRIKETHROUGH |
              misaka.EXT_SUPERSCRIPT |
              misaka.EXT_TABLES)

misaka_flags = (misaka.HTML_USE_XHTML |
                misaka.HTML_TOC |
                # misaka.HTML_TOC_TREE |
                misaka.HTML_HARD_WRAP)

app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

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
           filename.rsplit('.', 1)[1].lower() in \
           app.config['ALLOWED_EXTENSIONS']


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
    # TODO: edit commit author
    filename = filename.encode('utf-8')
    if repo.index.diff(None, paths=filename, staged=True):
        try:
            repo.index.commit(message)
        except UnicodeEncodeError:
            print 'Encode error'
    else:
        pass


def add_commit(repo, filename, message):
    repo.index.add([filename.encode('utf-8')])
    commit(repo, filename, message)


def remove_commit(repo, filename, message):
    repo.index.remove([filename.encode('utf-8')])
    commit(repo, filename, message)


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
    if request.args.get('pageName'):
        newPageName = request.args.get('pageName')
    newpage = True
    return render_template('edit.html', **locals())


@app.route('/<path:name>/edit')
def editView(name):
    pageList = pagelist()
    updateList = commitList()
    content = codecs.open(
        os.path.join(path, name+'.md'),
        'r',
        encoding='utf-8').read()
    # TODO: cancel button
    # TODO: noticfy trantison page
    newpage = False
    return render_template('edit.html', **locals())


@app.route('/<path:name>/add', methods=['POST'])
def add_entry(name):
    if name == 'new':
        name = request.form.get('pagename')
        name = name.replace('../', '')
        commitMessage = 'Create: '+name
    else:
        name = name[:-5]
        commitMessage = 'Update: '+name

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
    add_commit(repo, filename, commitMessage)
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
    # TODO: uft8
    # TODO: show page name
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
    rndr = BleepRenderer(flags=misaka_flags)
    md = misaka.Markdown(rndr, extensions=misaka_ext)
    content = md.render(content)
    return render_template('diff.html', **locals())
    # TODO: single diff


@app.route('/<path:name>/delete')
def deletePage(name):
    filename = name+'.md'
    fullpath = os.path.join(path, filename)
    try:
        commitMessage = 'Delete: '+name
        remove_commit(repo, filename, commitMessage)
        os.remove(fullpath)
    except:
        pass
        # TODO: error message
    # git commit --------
    return redirect('/')


@app.route('/preview', methods=['POST'])
def preview():
    text = request.json
    text = text.replace('\r\n', '\n')
    rndr = BleepRenderer(flags=misaka_flags)
    md = misaka.Markdown(rndr, extensions=misaka_ext)
    content = md.render(text)
    return jsonify(preview=content)


@app.route('/upload', methods=['POST'])
def upldfile():
    updir = os.path.join(path, uploadDir)
    if not os.path.isdir(updir):
        os.makedirs(updir)
    if request.method == 'POST':
        files = request.files['file']
        print files.filename
        if files and allowed_file(files.filename):
            print files.filename
            filename = files.filename.replace('../', '')
            print filename
            app.logger.info('FileName: ' + filename)
            files.save(os.path.join(updir, filename))
            add_commit(
                repo,
                os.path.join(uploadDir, filename),
                'Upload: %s' % filename)
            file_size = os.path.getsize(os.path.join(updir, filename))
            return jsonify(name=filename, size=file_size)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    updir = os.path.join(path, uploadDir)
    return send_from_directory(updir, filename)


@app.route('/<path:name>')
def contentView(name):
    pageList = pagelist()
    updateList = commitList()
    if os.path.splitext(name)[1] != '.ico':
        try:
            f = codecs.open(
                os.path.join(path, name+'.md'),
                'r',
                encoding='utf-8')
            pageTitle = f.readline()
            pageTitle = pageTitle.replace('#', '')
            text = f.read()
            rndr = BleepRenderer(flags=misaka_flags)
            md = misaka.Markdown(rndr, extensions=misaka_ext)
            content = md.render(text)
            toc = misaka.html(text, misaka_ext, misaka.HTML_TOC_TREE)
            return render_template('content.html', **locals())
        except:
            # TODO: page not found message in flash
            return redirect(url_for('newView', pageName=name))
    else:
        return 0

# TODO: Login and logout page and session
# TODO: upload file list page
# TODO: delete button in uploaded file
# TODO: Add flash message
# TODO: Link update to page
# TODO: update time in view content
# TODO: recent update count over flow
# TODO: Add arrow in acordion menu
# TODO: add title h1 in preview page

# TODO: Custom markdown

# TODO: config file
    # TODO: navibar link
    # TODO: sidemenu
    # TODO: user manegemant

if __name__ == '__main__':
    args = docopt(__doc__, version='1.0.0')
    if args['<repositoryDir>']:
        path = args['<repositoryDir>']
    repo = git.Repo(path)

    if args['--port']:
        port = int(args['--port'])

    app.run(host='0.0.0.0', port=port, debug=args['--debug'])
