from sparkpost import SparkPost
import os, json
from threading import Thread
import modules.sfdc as sfdc
sp = SparkPost()

sofie_probe_domain = os.environ.get("SOFIE_PROBE_DOMAIN", "http://localhost:8080")
if not sofie_probe_domain.startswith('http://'):
    sofie_probe_domain = 'https://www.' + sofie_probe_domain

sofie_issue_email = os.environ.get("SOFIE_ISSUE_EMAIL_USERS", "taegyum.kim@sofie.com")
sofie_bug_report_email_address = os.environ.get("SOFIE_BUG_REPORT_EMAIL_ADDRESS", "taegyum.kim@sofie.com")
SOFIEBIO_USERID = int(os.environ.get("SOFIEBIO_USERID"))
send_email_method = sp.transmission.send
emails_skipped = []
def send_emails(do_send):
    if not do_send:
        def skip_sending(**kwargs):
            print "Not sending emails"
            emails_skipped.append(kwargs)
        sp.transmission.send = skip_sending
    else:
        sp.transmission.send = send_email_method

def do_send(**kwargs):
    print kwargs
    resp = sp.transmission.send(**kwargs)
    print resp

def welcome_user(user):
    reset_url = user.ResetCode
    reset_link = "%s/user/password_reset/%s" % (sofie_probe_domain, reset_url)
    html = \
            "<h1>Welcome %s %s</h1>" % (user.FirstName, user.LastName) + \
            "<p>" + \
            "    You have been recently added to the Sofie Probe Network.  You will now be able" + \
            "    to share your Probe sequences with the rest of the world!" + \
            "</p>" + \
            "<h2>Your username will be %s</h2>" % user.username + \
            "<h3>Please Login and Change Your Password.</h3>" + \
            "<div>Click below to reset your Password</div>" + \
            "<a href='%s'>%s</a>" % (reset_link, reset_link)

    kwargs = {"recipients": [str(user.Email)],
              "from_email": 'software@sofie.com',
              "subject": "Welcome to the Sofie Probe Network",
              "reply_to" : sofie_bug_report_email_address,
              "html": str(html)
              }

    thread = Thread(target=do_send, kwargs=kwargs)
    thread.start()

def auto_report_bug(err, username='Unknown'):

    kwargs = {"recipients": [str(sofie_bug_report_email_address)],
              "from_email": "software@sofie.com",
              "subject": "Sofie Probe Network unhandled exception",
              "text": "%s has reported the following bug\n%s\nin %s" % (username, err, sofie_probe_domain)}
    thread = Thread(target=sp.transmission.send, kwargs=kwargs)
    thread.start()

def report_issue(forum, subject):
    from models.account import Account
    from models.user import User
    case_info = "<a href='%s%s'>%s</a>" % (sfdc.sfdc_url, forum.SFDC_ID, forum.Subject) if forum.SFDC_ID else "SFDC case number failed to be generated."

    html = \
            "<html>" +\
            "    <div>{{UserName}} at {{AccountName}} is reporting an issue</div>" + \
            "    <div>Further Details: {{Subtitle}}</div>" + \
            "    <div>%s</div>" % case_info + \
            "<div>click <a href='%s/user/dashboard?forum_id=%s'>here</a> to view the message</div>" % (sofie_probe_domain, forum.ForumID) + \
            "</html>"

    user = forum.user
    account = forum.account

    subject = "%s @ %s has reported an issue: %s" % (user.Name, account.name, subject)


    kwargs = {"recipients": [str(sofie_issue_email)],
              "from_email": "elixys.support@sofie.com",
              "subject": subject,
              "reply_to": user.Email,
              "html": html,
              "substitution_data": {"AccountName": account.name,
                                    "UserName" : user.Name,
                                    "Subtitle": forum.Subtitle

              }}
    thread = Thread(target=do_send, kwargs=kwargs)
    thread.start()

def contact_account(user_making_contact, account, message):
    recipients = []
    if account.primary_contact is not None and \
       account.primary_contact.Email != "" and \
       account.primary_contact.Email is not None:
        recipients.append(str(account.primary_contact.Email))
    else:
        users = account.users

        for user in account.users:
            user_email = user.Email
            if user_email is not None and str(user_email) != "":
                recipients.append(str(user_email))
    kwargs = {"recipients": recipients,
              "from_email": "software@sofie.com",
              "subject": "%s %s is contacting your organization" % (user_making_contact.FirstName, user_making_contact.LastName),
              "reply_to": user_making_contact.Email,
              "text": str(message)
              }
    thread = Thread(target=sp.transmission.send, kwargs=kwargs)
    thread.start()

def send_email_to_issue_followers(comment, subject, following, reply_to, exclude=[]):
    recipients = []

    for follower in following:
        if follower.UserID not in exclude:
            recipients.append(follower.UserID)

    from models.user import User
    users = User.query.filter(User.UserID.in_(recipients)).all()
    recipients = []

    for usr in users:
        recipients.append(str(usr.Email))

    kwargs = {"recipients": recipients,
              "from_email": "elixys.support@sofie.com",
              "reply_to": reply_to,
              "subject": subject,
              "html": "<p>%s</p>" % comment.Message if comment.UserID == SOFIEBIO_USERID else
                      "click <a href='%s/user/dashboard?forum_id=%s'>here</a> to view the message" % (sofie_probe_domain, comment.ParentID)}
    thread = Thread(target=sp.transmission.send, kwargs=kwargs)
    thread.start()

def contact_probe_owner(name, email, sequence, message):
    user_sequence_owner = sequence.owner
    message = "<html>" + \
              "    <body>" + \
              "        <p>Hello %s %s</p>" % (user_sequence_owner.FirstName, user_sequence_owner.LastName) + \
              "        <p>I am interested in <a href='%s/sequence/%s'>%s</a><br/>%s</p>" % (sofie_probe_domain, sequence.SequenceID, sequence.Name, message) + \
              "    </body>" + \
              "</html>"
    kwargs = {"recipients":[str(user_sequence_owner.Email)],
              "from_email": "software@sofie.com",
              "subject": "%s is interested in your probe" % name,
              "reply_to": email,
              "html": str(message)
              }
    thread = Thread(target=sp.transmission.send, kwargs=kwargs)
    thread.start()

def comment_on_probe(user_making_contact, sequence, message):
    recipients = []
    user_sequence_owner = sequence.owner
    recipients.append(str(user_sequence_owner.Email))
    for follower in sequence.following:
        if follower.Email is not None and str(follower.Email) != "":
            recipients.append(str(follower.Email))
    kwargs = {
        "recipients":recipients,
        "template":'sofie-probe-network-comment-probe',
        "substitution_data":{"from": str(user_making_contact.Email),
                             "from_first_name": str(user_making_contact.FirstName),
                             "from_last_name": str(user_making_contact.LastName),
                             "to_first_name": str(user_sequence_owner.FirstName),
                             "to_last_name": str(user_sequence_owner.LastName),
                             "message": str(message),
                             "sequence_name": str(sequence.Name),
                             "sequence_url": str("%s/sequence/%s" % (sofie_probe_domain, sequence.SequenceID))
        }
    }
    thread=Thread(target=sp.transmission.send, kwargs=kwargs)
    thread.start()

def forgot_your_email(user, reset_url):
    kwargs = {
        "recipients":[str(user.Email)],
        "template":'sofie-probe-network-forgot-password',
        "substitution_data":{"reset_url": "%s/%s" % (sofie_probe_domain, str(reset_url)),
                           "first_name": str(user.FirstName),
                           "last_name": str(user.LastName)}
    }
    thread=Thread(target=sp.transmission.send, kwargs=kwargs)
    thread.start()

