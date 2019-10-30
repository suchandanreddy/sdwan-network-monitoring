import requests
import json
import os
import click

from requests.packages.urllib3.exceptions import InsecureRequestWarning

vmanage_host = os.environ.get("vmanage_host")
vmanage_port = os.environ.get("vmanage_port")
username = os.environ.get("username")
password = os.environ.get("password")

if vmanage_host is None or vmanage_port is None or username is None or password is None:
    print("For Windows Workstation, vManage details must be set via environment variables using below commands")
    print("set vmanage_host=198.18.1.10")
    print("set vmanage_port=443")
    print("set username=admin")
    print("set password=admin")
    print("For MAC OSX Workstation, vManage details must be set via environment variables using below commands")
    print("export vmanage_host=198.18.1.10")
    print("export vmanage_port=443")
    print("export username=admin")
    print("export password=admin")
    exit()

requests.packages.urllib3.disable_warnings()

class rest_api_lib:
    def __init__(self, vmanage_host,vmanage_port, username, password):
        self.vmanage_host = vmanage_host
        self.vmanage_port = vmanage_port
        self.session = {}
        self.login(self.vmanage_host, username, password)

    def login(self, vmanage_host, username, password):

        """Login to vmanage"""

        base_url = 'https://%s:%s/'%(self.vmanage_host, self.vmanage_port)

        login_action = 'j_security_check'

        #Format data for loginForm
        login_data = {'j_username' : username, 'j_password' : password}

        #Url for posting login data
        login_url = base_url + login_action
        #url = base_url + login_url

        #URL for retrieving client token
        token_url = base_url + 'dataservice/client/token'

        sess = requests.session()

        #If the vmanage has a certificate signed by a trusted authority change verify to True

        login_response = sess.post(url=login_url, data=login_data, verify=False)

        if b'<html>' in login_response.content:
            print ("Login Failed")
            exit(0)

        login_token  = sess.get(url=token_url, verify=False)

        if login_token.status_code == 200:
            if b'<html>' in login_token.content:
                print ("Login Token Failed")
                exit(0)

        #update token to session headers
        sess.headers['X-XSRF-TOKEN'] = login_token.content

        self.session[vmanage_host] = sess

    def get_request(self, mount_point):
        """GET request"""
        url = "https://%s:%s/dataservice/%s"%(self.vmanage_host, self.vmanage_port, mount_point)
        #print(url)

        response = self.session[self.vmanage_host].get(url, verify=False)

        return response


vmanage_session = rest_api_lib(vmanage_host, vmanage_port, username, password)

@click.group()
def cli():
    """Command line tool for Monitoring and Configuring CISCO SD-WAN fabric.
    """
    pass

@click.command()
def list_site_ids():

    """ Retrieve and return information about site-id list in SD-WAN fabric.

        Example command:
            ./site-id-list.py list_site_ids
    """
    response = vmanage_session.get_request('device').json()

    items = response['data']

    headers = ["Site IDs"]
    table = list()
    site_ids = list()
    

    for item in items:
        site_ids.append(int(item['site-id']))
    
    site_ids.sort()
    site_ids = list(dict.fromkeys(site_ids))
    sorted_siteids=format_site_ids(site_ids)
    print("\nList of all site-ids retrieved : ", sorted_siteids)

def format_site_ids(site_ids):
    prev_id = min(site_ids) if site_ids else None
    site_list = list()

    for id in sorted(site_ids):
        if id != prev_id+1:
            site_list.append([id])
        elif len(site_list[-1]) > 1:
            site_list[-1][-1] = id
        else:
            site_list[-1].append(id)
        prev_id = id

    return ','.join(['-'.join(map(str,site)) for site in site_list])

cli.add_command(list_site_ids)

if __name__ == "__main__":
    cli()