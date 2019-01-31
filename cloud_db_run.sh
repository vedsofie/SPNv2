# This is an alternate version of the run.sh file. This should only be used when a local Postgres database has been setup
# postgresql://DB_USER:PASSWORD@HOST/DATABASE
export APPROVAL_PROCESS_LIST=5
export SOFIEBIO_USERID=9
export SOFIEBIO_ACCOUNTID=1
export SOFIE_AUTO_FOLLOWING_USERS=8,11,10,2
export SOFIE_PROBE_DOMAIN='http://localhost:8080'
#export DATABASE_URL='postgres://lpkadwdozinetv:85ZCBh5ZpUCjZ01lrk-eTxgcsr@ec2-54-83-12-22.compute-1.amazonaws.com:5432/d98eis88j9809l'
export DATABASE_URL='postgres://dhrjmllkgioqqc:hnjSlkJi_syLobm2ckElh8QOk7@ec2-23-21-42-29.compute-1.amazonaws.com:5432/d8t20s2445or8f'
export SPARKPOST_API_KEY='klsfjlksdjflsadlfkj'
export SPARKPOST_SANDBOX_DOMAIN=''
export GIT_TOKEN='e19b9e49160411c07a51fcb2b6ea14f87741805b'
export SFDC_URL='https://na29.salesforce.com/'
export SFDC_USERNAME='justin.catterson@sofiebio.com'
export SFDC_PASSWORD='1zqa2xws'
export SFDC_SECURITY_TOKEN='R11yx8jRL7FPdCyr4DhYNyse6'
export SOFIE_ISSUE_EMAIL_USERS='justin.catterson@sofie.com'
export SESSION_KEY='1540399142ae3395451770f811aeb63a290c31033cdd730d'ㅋ
export SIM_PRODUCTS=True
source ../bin/activate
# python generate_db.py
python chat_server.py -m no
#foreman start
#gunicorn -w 4 -b 127.0.0.1:4000 chat_server:app