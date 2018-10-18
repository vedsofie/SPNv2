source ../bin/activate
sudo pyinstaller -p ../bin/python -y osx_run_pyelixys_server.spec
export USR=$USER
sudo mkdir -p dist/sofieprobenetwork/webassets/filter
sudo chown -R $USR dist
