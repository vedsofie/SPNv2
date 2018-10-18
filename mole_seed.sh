export SOFIEBIO_USERID=1
export DATABASE_URL=sqlite:////tmp/flaskauthenticationdemo.db
export SPARKPOST_API_KEY='klsfjlksdjflsadlfkj'
export SPARKPOST_SANDBOX_DOMAIN=''
export GIT_TOKEN=''
export SESSION_KEY='1540399142ae3395451770f811aeb63a290c31033cdd730d'
source ../bin/activate
python -m seeds.molecules_gen
