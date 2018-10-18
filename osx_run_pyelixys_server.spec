# -*- mode: python -*-

block_cipher = None


a = Analysis(['chat_server.py'],
             pathex=['/Users/jcatterson/sofiebio/heroku_sofie/sofiebio/'],
             binaries=None,
             datas=[('sequence_modules.txt', '.'), ('/tmp/flaskauthenticationdemo.db', '.')],
             hiddenimports=['flask.ext', 'flask_script', 'flask_sqlalchemy','flask_sqlalchemy._compat', 'flask_triangle', 'flask_assets', 'flask_bcrypt'],#'tornado',
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

def extra_datas(mydir):
    def rec_glob(p, files):
        import os
        import glob
        for d in glob.glob(p):
            if os.path.isfile(d):
                files.append(d)
            rec_glob("%s/*" % d, files)
    files = []
    print mydir
    rec_glob("%s/*" % mydir, files)
    extra_datas = []
    for f in files:
        print f
        extra_datas.append((f, f, 'DATA'))

    return extra_datas
###########################################

# append the 'data' dir
a.datas += extra_datas('./static/')
a.datas += extra_datas('./templates/')
a.datas += extra_datas('./seeds/')
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='spn',
          debug=True,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='sofieprobenetwork')
