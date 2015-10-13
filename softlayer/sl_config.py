#!/usr/bin/python

from os.path import expanduser

DOCUMENTATION = '''
---
module: sl_config
short_description: Writes the softlayer config file for CLI commands
author: "Evan Blackwell (@blackwel)"
description:
   - Creates the .softlayer file in the home directory
options:
   username:
     description:
        - The username for the SoftLayer account to be used
     required: true
   api_key:
     description:
        - The api_key for the SoftLayer account to be used
     required: true
   timeout:
     description:
        - Value (seconds) to be used as the timeout for CLI commands
     required: false
     default: 600
   custom_url:
     description:
        - Enter a value if you desire to use any other url besides the default
          for the endpoint url
     required: false
requirements:
    - "python >= 2.6:
'''

EXAMPLES = '''
# Writes the .softlayer configuaration file with a timeout of 60 seconds
- sl_config:
    username: user1
    api_key: blahblahblah
    timeout: 60

# Writes a standards configuartion file
-sl_config:
    username: user2
    api_key: yadayadayada

# Writes a configuration file with a custom url
- sl_config:
    username: user3
    api_key: abcdefghijklmnopqrstuvwxyz123456789
    custom_url: http://mysoftlayer.com
'''

def _update_credentials(module):
    """Write the configuration file with the given information"""
    contents = "[softlayer]\n"
    contents += "username = %s\n" % module.params['username']
    contents += "api_key = %s\n" % module.params['api_key']
    if module.params['custom_url']:
        contents += "endpoint_url = %s\n" % module.params['custom_url']
    else:
        contents += "endpoint_url = https://api.softlayer.com/xmlrpc/v3.1/\n"
    contents += "timeout = %d" % module.params['timeout']

    home = expanduser("~")
    with open('%s/.softlayer' % home, 'w') as config:
        config.write(contents)

    module.exit_json(changed=True)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            username      = dict(required=True, type='str'),
            api_key       = dict(required=True, type='str'),
            timeout       = dict(default=600, type='int'),
            custom_url    = dict(default=None, type='str')
        )
    )

    _update_credentials(module)

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
