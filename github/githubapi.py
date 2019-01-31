import os
import requests
import json
import random
import httpagentparser
import io
import base64
import csv
from Crypto.Cipher import AES
from flask import Blueprint, render_template, request, Response, g

GIT_OWNER = "SofieBiosciences"
GIT_REPO = "Elixys"
PYELIXYS_BASE_DIR = "https://api.github.com/repos/%s/%s/" % (GIT_OWNER, GIT_REPO)
INSTALLER_BASE_DIR = "https://api.github.com/repos/%s/%s/" % ('SofieBiosciences', 'SofieDeploymentInstaller')
GIT_OATH = os.environ["GIT_TOKEN"]
ENCRYPTION_KEY = '1234567890123456'

github = Blueprint('github', __name__, url_prefix="/github",static_folder='static')

@github.route("/releases/", methods=["GET"])
def releases():
    print "releases"
    url = PYELIXYS_BASE_DIR + "releases"
    response = requests.get(url,headers=git_headers())
    resp = response.json()
    releases = json.dumps(as_assets(resp))

    url = INSTALLER_BASE_DIR + "releases"
    response = requests.get(url,headers=git_headers())
    print response
    resp = response.json()
    installers = json.dumps(as_assets(resp))

    return render_template('/github/downloads.html', releases=releases, installers=installers, runninguser=json.dumps(g.user.to_hash()))

def as_assets(resp):
    spn_domain = os.environ['SOFIE_PROBE_DOMAIN']
    assets = []

    for release in resp:
        #if not release['prerelease'] or spn_domain != 'sofienetwork.com':
        if not release['prerelease']:
            rel = {}
            tag_name = release['tag_name']
            rel['name'] = tag_name
            rel["versions"] = []
            rel['assets_url'] = release['assets_url']
            rel['published_at'] = release['published_at']
            rel['body'] = release['body']
            index = 0
            while index < len(release['assets']):
                if 'linux_pyelixys_' in release['assets'][index]['name']:
                    rel['size'] = round(release['assets'][index]['size'] * 0.000001, 2)
                index += 1
            assets_url = rel['assets_url']
            for asset in release['assets']:
                asset_name = asset['name']
                op_os = asset_name.split('_')
                rel["versions"].append({'name': asset_name, 'url': asset['url'], 'os': op_os[0]})
            assets.append(rel)
    return assets

@github.route("/report/issue", methods=["POST"])
def report_issue():
    release_name = request.form["release"]
    title = request.form["title"]
    message = request.form["message"]
    return "OK"

@github.route("/release/<release>/comments", methods=["GET"])
def get_comments(release):
    url = PYELIXYS_BASE_DIR + "issues"
    resp = requests.get(url, headers=git_headers())
    release_issues = []

    for issue in resp.json():
        for label in issue['labels']:
            if label['name'] == "pyelixys_%s" % release:
                release_issues.append(issue)
                continue

    return Response(json.dumps(release_issues), headers={"Content-Type": "application/json"})

@github.route("/download/asset", methods=["GET"])
def download_asset():
    ref = request.args.get('url', '')
    if ref != "":
        headers = git_headers()
        headers["Accept"] = "application/octet-stream"
        content = requests.get(ref, headers=headers,stream=True)
        disp = content.headers["Content-Disposition"]
        content_type = content.headers["Content-Type"]
        length = content.headers["Content-Length"]
        return Response(response=generate(content),content_type=content_type,headers={"Content-Disposition": disp, "Content-Length": length})
    return ''

@github.route("/latests_exe/", methods=["GET"])
def latests_exe():
    url = PYELIXYS_BASE_DIR + "releases/latest"
    response = requests.get(url,headers=git_headers())
    assets = response.json()["assets"]
    try:
        os = request.args.get("os", None)
        asset = find_asset(assets, os)
        headers = git_headers()
        headers["Accept"] = "application/octet-stream"
        content = requests.get(asset["url"], headers=headers,stream=True)
        disp = content.headers["Content-Disposition"]
        content_type = content.headers["Content-Type"]
        length = content.headers["Content-Length"]
        return Response(response=generate(content),content_type=content_type,headers={"Content-Disposition": disp, "Content-Length": length})
    except Exception as e:
        return "No binary matches your OS"

@github.route("/latests_installer_exe/", methods=["GET"])
def latests_installer_exe():
    url = INSTALLER_BASE_DIR + "releases/latest"
    response = requests.get(url,headers=git_headers())
    assets = response.json()["assets"]
    try:
        os = request.args.get("os", None)
        asset = find_asset(assets, os)
        headers = git_headers()
        headers["Accept"] = "application/octet-stream"
        content = requests.get(asset["url"], headers=headers,stream=True)
        disp = content.headers["Content-Disposition"]
        content_type = content.headers["Content-Type"]
        length = content.headers["Content-Length"]
        return Response(response=generate(content),content_type=content_type,headers={"Content-Disposition": disp, "Content-Length": length})
    except Exception as e:
        return "No binary matches your OS"

def find_asset(assets, os=None):
    user_agent = request.headers['User-Agent']
    requesters_os = httpagentparser.detect(user_agent)
    platform = requesters_os['os']['name'] if os is None else os
    platform = platform.lower()
    for asset in assets:
        if asset["name"].startswith(platform):
            return asset
    return None

@github.route('/release_notes/', methods=['GET'])
def get_release_notes():
    if not (g.user and g.user.role.Name == 'super-admin'):
        return ''
    release_version = 'Purification Formulation'#request.args.get('version', None)
    if release_version:
        MILESTONES_URL = 'https://api.github.com/repos/%s/%s/milestones?state=all' % (GIT_OWNER, GIT_REPO)
        re = requests.get(MILESTONES_URL, headers=git_headers())

        def find_version_number(version, request):
            for req in request.json():
                if 'title' in req and req['title'] == version:
                    return req['number']
            return None

        def get_issue_bodies(request):
            bodies = []
            for req in request.json():
                if 'body' in req:
                    bodies.append(req['body'])
            return bodies

        version_id = find_version_number(release_version, re)

        if not version_id and 'link' in re.headers:
            pages = re.headers['link'].split(',')
            next_page = pages[0].split(';')
            last_page = pages[1].split(';')[0]
            while True and not version_id:
                url = next_page[0][1:len(next_page[0])-1]
                re = requests.get(url, headers=git_headers())
                version_id = find_version_number(release_version, re)
                if next_page[0] == last_page[1::] or version_id:
                    break
                pages = re.headers['link'].split(',')
                next_page = pages[0].split(';')

        if version_id:
            ISSUES_FOR_REPO_URL = 'https://api.github.com/repos/%s/%s/issues?milestone=%s&state=closed' % (GIT_OWNER, GIT_REPO, version_id)
            re = requests.get(ISSUES_FOR_REPO_URL, headers=git_headers())
            bodies = []
            bodies.extend(get_issue_bodies(re))
            if 'link' in re.headers and re.headers['link']:
                pages = re.headers['link'].split(',')
                next_page = pages[0].split(';')
                last_page = pages[1].split(';')[0]
                while True and not version_id:
                    url = next_page[0][1:len(next_page[0])-1]
                    re = requests.get(url, headers=git_headers())
                    bodies.extend(get_issue_bodies(re))
                    if next_page[0] == last_page[1::]:
                        break
                    pages = re.headers['link'].split(',')
                    next_page = pages[0].split(';')

            bodies = '\n\n'.join(bodies)
            re = requests.post("https://api.github.com/markdown", data=json.dumps({'text': bodies}), headers=git_headers())

            return Response(re.content, headers={'Content-Type': 'text/html'})
        return Response('')
    else:
        return Response('')

@github.route("/software_standards/")
def get_software_standards():
    if g.user and g.user.role.Name == 'super-admin':
        re = requests.get('https://api.github.com/repos/jcatterson/SoftwareStandards/readme?ref=sop')
        file = re.json()
        readme = base64.decodestring(file['content'])
        re = requests.post("https://api.github.com/markdown", data=json.dumps({'text': readme}), headers=git_headers())
        return Response(re.content, headers={'Content-Type': 'text/html'})
    return ''

@github.route("/issue_history/", methods=["GET"])
def get_issue_history():
    if not (g.user and g.user.role.Name == 'super-admin'):
        return ''
    ISSUES_FOR_REPO_URL = 'https://api.github.com/repos/%s/%s/issues?state=all' % (GIT_OWNER, GIT_REPO)
    re = requests.get(ISSUES_FOR_REPO_URL, headers=git_headers())
    output = io.BytesIO()
    csvout = csv.writer(output)
    csvout.writerow(('id', 'Title', 'Body', 'Created At', 'Updated At', 'Closed At', 'Validation Method', 'Release Revision'))
    write_issues(re, csvout)

    if 'link' in re.headers:
        pages = re.headers['link'].split(',')
        next_page = pages[0].split(';')
        last_page = pages[1].split(';')[0]
        while True:
            url = next_page[0][1:len(next_page[0])-1]
            re = requests.get(url, headers=git_headers())
            write_issues(re, csvout)
            pages = re.headers['link'].split(',')
            if next_page[0] == last_page[1::]:
                break
            next_page = pages[0].split(';')

    resp = output.getvalue()
    return Response(resp, content_type='text/csv', headers={"Content-Length": len(resp)})


def write_issues(response, csvout):
    if not response.status_code == 200:
        raise Exception(response.status_code)

    for issue in response.json():
        release_revision = issue['milestone']['title'] if 'milestone' in issue and issue['milestone'] is not None else ''
        validation_method = get_validation_method(issue)
        csvout.writerow([issue['number'], issue['title'].encode('utf-8'), issue['body'].encode('utf-8'), issue['created_at'], issue['updated_at'], issue['closed_at'], validation_method, release_revision])

def get_validation_method(issue):
    if issue['closed_at']:
        comments_url = issue['comments_url']
        re = requests.get(comments_url, headers=git_headers())
        comments = re.json()
        if 'link' in re.headers:
            pages = re.headers['link'].split(',')
            next_page = pages[0].split(';')
            last_page = pages[1].split(';')[0]
            re = requests.get(last_page, headers=git_headers())
            comments = re.json()

        if len(comments) > 0:
            last_comment = comments[len(comments)-1]
            print 'last comment %s' % last_comment['body']
            return last_comment['body']

    return ''

def generate(stream):
    for stream in stream.raw.stream():
        yield stream

def generate_encrypted(stream):
    iv = ''.join(chr(random.randint(0, 0xFF)) for i in range(16))
    encryptor = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, iv)
    yield iv
    for stream in stream.raw.stream():
        if len(stream) % 16 != 0:
            stream += ' ' * (16 - len(stream) % 16)

        yield encryptor.encrypt(stream)

def git_headers():
    token = GIT_OATH
    return {
        "Authorization": "token %s " % token
    }
