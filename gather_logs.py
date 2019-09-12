import json
from cvplibrary import RestClient, Device, CVPGlobalVariables, GlobalVariableNames
import ssl
import jsonrpclib

### User variables
## Don't run 'show tech-support', it'll time out.
configletPrefix = 'techspt_'
commandList = ['show ip bgp summary', 'show ip arp', 'show bgp evpn summary', 'show mac address-table']
overwrite_configlets = True # Set to False if you want to protect configlets from overwrite.

# Ignore untrusted certificate for eAPI call.
ssl._create_default_https_context = ssl._create_unverified_context

### CVP REST - Puts Configlets in CVP.
cvpserver = 'https://localhost:443'
rest_add_configlet = '/cvpservice/configlet/addConfiglet.do'
rest_get_configlet_by_name = '/cvpservice/configlet/getConfigletByName.do?name='
rest_update_configlet = '/cvpservice/configlet/updateConfiglet.do'
device_ip = CVPGlobalVariables.getValue(GlobalVariableNames.CVP_IP) # Get Device IP
user = CVPGlobalVariables.getValue(GlobalVariableNames.CVP_USERNAME)
passwd = CVPGlobalVariables.getValue(GlobalVariableNames.CVP_PASSWORD)
#SESSION SETUP FOR eAPI TO DEVICE
url = "https://%s:%s@%s/command-api" % (user, passwd, device_ip)
ss = jsonrpclib.Server(url)


def check_configlet_exists(configlet_name):
    client = RestClient(cvpserver+rest_get_configlet_by_name+configlet_name,'GET')
    if client.connect():
      output = json.loads(client.getResponse())
      if 'errorCode' in output:
        if output['errorCode'] == '132801':
          #print 'Configlet not found. Moving to create new configlet.'
          return False
      else:
        print 'Configlet found. Updating.'
        configlet_key = output['key']
        return configlet_key

def update_configlet(configlet_data,configlet_name,configlet_key):
  data = {
    "config": configlet_data,
    "key": configlet_key,
    "name": configlet_name,
    "waitForTaskIds": False,
    "reconciled": False
  }
  if not overwrite_configlets:
      print 'Failure - configlet overwriting disabled.'
      return
  client = RestClient(cvpserver+rest_update_configlet,'POST')
  client.setRawData(json.dumps(data))
  if client.connect():
      output = json.loads(client.getResponse())
      print output

def add_configlet(configlet_data,configlet_name):
  data = {
    "config": configlet_data,
    "name": configlet_name
  }
  client = RestClient(cvpserver+rest_add_configlet,'POST')
  client.setRawData(json.dumps(data))
  if client.connect():
      output = json.loads(client.getResponse())
      if 'errorCode' in output:
        if output['errorCode'] == '132518':
          if overwrite_configlets:
            print 'Configlet already exists. This is odd...'
        else:
          print 'Unknown Error.'
        if not overwrite_configlets:
            print 'Failure - configlet overwriting disabled.'
      print 'Configlet Added.'
def main():
    tempconfiglet = []
    device = Device(device_ip)
    hostname = device.runCmds(['show hostname'],)[0]['response']['hostname']
    for command in commandList:
        tempconfiglet.append('============'+command+'============')
        try:
            output = ss.runCmds(1,['enable',command],'text')[1]['output']
        except:
            output = 'Error: command not supported'
        tempconfiglet.append(output)
    configletName = configletPrefix+hostname
    configletBody = '\n'.join(tempconfiglet)
    configletExists = check_configlet_exists(configletName)
    if configletExists:
        configletKey = configletExists
        update_configlet(configletBody,configletName,configletKey)
    else:
        add_configlet(configletBody,configletName)
if __name__ == "__main__":
    main()
