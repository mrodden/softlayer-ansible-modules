#!/usr/bin/python
import base64
import hashlib

try:
    import SoftLayer
    from SoftLayer.managers import sshkey
    HAS_SOFTLAYER = True
except ImportError:
    HAS_SOFTLAYER = False

DOCUMENTATION = '''
---
module: sl_sshkey
short_description: Creates/Deletes SSH Keys from SoftLayer
author: "Evan Blackwell (@blackwel)"
description:
   - Ensures that SSH Keys are created or deleted from a SoftLayer account
options:
   username:
     description:
        - The username for the SoftLayer account to be used
     required: true
   api_key:
     description:
        - The api_key for the SoftLayer account to be used
     required: true
   state:
     description:
        - Whether the SSH Key should be present or absent
     choices: [present, absent]
     default: present
   label:
     description:
        - The label of the SSH Key to create/delete
     required: true
   public_key:
     description:
        - The public_key to be used as the SSH Key. If a key exists with the
          same fingerprint on the account, the information for the existing
          key will be returned and no key will be created. Must be present when
          creating, not necessary when deleting
     default: None
requirements:
    - "python >= 2.6:
    - "softlayer"
'''

EXAMPLES = '''
# Creates a key pair with the user's public key
- sl_sshkey:
    username: user
    api_key: jumbledpassword
    state: present
    label: key1
    public_key: {{ lookup('file','~/.ssh/id_rsa.pub') }}

# Removes a key pair from SoftLayer with the given label
- sl_sshkey:
    username: user
    api_key: jumbledpassword
    state: absent
    label: key1
'''

def _create_key(module, mgr):
    """Checks if the given key already exists by looking for its fingerprint.
    Returns the existing key if it finds a match, creates a new key if not"""
    label = module.params['label']
    public_key = module.params['public_key']
    finger = _get_fingerprint(public_key)
    keys = mgr.list_keys()
    for k in keys:
        if k['fingerprint'] == finger:
            if k['label'] == label:
                module.exit_json(changed=False, key=k)
            else:
                module.exit_json(changed=False, key=k,
                                 msg=("A key with this fingerprint already exists on "
                                      "this account, using key %s" % k['label']))
        if k['label'] == label:
            module.fail_json(msg=("A key with label %s already exists with " % label +
                                  "a different public key on this account"))

    if not public_key:
        module.fail_json(msg="A key must be given. No sshkey created.")

    key = mgr.add_key(public_key, label)

    if key:
        module.exit_json(changed=True, key=key)
    else:
        module.fail_json(msg="The key was not succesfully created")

def _get_fingerprint(public_key):
    """Determines and returns the fingerprint for the given public_key"""
    key = base64.b64decode(public_key.strip().split()[1].encode('ascii'))
    fp_plain = hashlib.md5(key).hexdigest()
    return ':'.join(a+b for a,b in zip(fp_plain[::2], fp_plain[1::2]))

def _delete_key(module, mgr):
    """Deletes the key with the given label"""
    label = module.params['label']
    keys = mgr.list_keys(label=label)
    if len(keys) > 1:
        module.fail_json(msg="More than one sshkey named %s. No keys deleted" % label)
    elif keys:
        mgr.delete_key(keys[0]['id'])
        module.exit_json(changed=True)
    else:
        module.exit_json(changed=False)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            username     = dict(required=True, type='str'),
            api_key      = dict(required=True, type='str'),
            state        = dict(default='present', choices=['present', 'absent']),
            label        = dict(required=True, type='str'),
            public_key   = dict(default=None, type='str')
        )
    )

    if not HAS_SOFTLAYER:
        module.fail_json(msg='softlayer is required for this module')

    client = SoftLayer.Client(username=module.params['username'],
                              api_key=module.params['api_key'])
    mgr = SoftLayer.SshKeyManager(client)
    state = module.params['state']

    if state == 'present':
        _create_key(module, mgr)
    elif state == 'absent':
        _delete_key(module, mgr)
    else:
        module.fail_json(msg="%s is not a valid state." % module.params['state'])

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
