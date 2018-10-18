import os
from simple_salesforce import Salesforce

sfdc_url = os.getenv("SFDC_URL")

def get_instance():
    sfdc_username = os.getenv("SFDC_USERNAME")
    sfdc_password = os.getenv("SFDC_PASSWORD")
    sfdc_security_token = os.getenv("SFDC_SECURITY_TOKEN")

    return Salesforce(username=sfdc_username, password=sfdc_password, security_token=sfdc_security_token)

