#!/usr/bin/python

try:
    import SoftLayer
    from SoftLayer.managers import vs
    HAS_SOFTLAYER = True
except ImportError:
    HAS_SOFTLAYER = False

DOCUMENTATION = '''
---
module: sl_vs_server
short_description: Order/Cancel Virtual Servers using SoftLayer
author: "Evan Blackwell (@blackwel)"
description:
   - Order or Cancel virtual servers using SoftLayer. If a server
     already exists with the same name, the information for that
     server will be returned. If multiple servers exist all fitting
     the given specifications, all matching orders will be canceled.
options:
   username:
     description:
        - The username for the SoftLayer account to be used
     required: true
   api_key:
     description:
        - The api_key used for logging into the SoftLayer CLI
     require: true
   hostname:
     description:
        - The hostname of the virtual server to order/cancel
     required: true
   domain:
     description:
        - The domain of the virtual server to order/cancel
     required: true
   state:
     description:
       - Should the resource be present or absent
     choices: [present, absent]
     default: present
   cpus:
     description:
       - The number of vcpu's for this order
     required: false
     default: 8
   memory:
     description:
       - The number of GB's of RAM for this order
     required: false
     default: 16
   hourly:
     description:
       - Enter 'True' to use an hourly billing period. Enter
         'False' to use a monthly billing period.
     required: false
     default: True
   local_disk:
     description:
       - Enter 'True' for a local disk, 'False' for a SAN disk
     required: false
     default: True
   datacenter:
     description:
       - The short name of the data center in which the VS
         should reside
       require: true
   os_code:
     description:
       - The code of the operating system to use, formatted as
         <OS_PRODUCT>_<VERSION>_<32/64>. VERSION can be specified
         as a major version of the project or as the most recent
         version by entering 'LATEST' for the value. Either this
         or image_id must be specified, but not both.
     required: false
   image_id:
     description:
       - The id number of an image on the SoftLayer client. Either this
         or os_code must be specified, but not both.
     required: false
   dedicated:
     description:
       - Enter 'True' if this should be hosted on a dedicated host, 'False'
         for a shared host.
     required: false
     default: False
   public_vlan:
     description:
       - The ID of the public VLAN to place this VS on
     required: false
   private_vlan:
     description:
       - The ID of the private VLAN to place this VS on
     required: false
   disks:
     description:
       - A list of disk capacities for this server
     required: false
   post_uri:
     description:
       - The URI of the post-install script to run after reload
     required: false
   private:
     description:
       - Enter 'True' for the VS to only have access to the private
         network.
     required: false
     defualt: False
   ssh_keys:
     description:
       - A list of SSH keys to add to the root user of the VS
     required: false
   nic_speed:
     description:
       - The value which to set the port speed
     required: false
   tags:
     description:
       - A string of tags seperated by commas to set on the VS
     required: false
   public_ip:
     description:
       - Only for canceling an order, the public_ip of the VS
         to cancel
     required: false
   private_ip:
     description:
       - Only for canceling an order, the private_ip of the VS
         to cancel
     required: false
   wait_for_ready:
     description:
       - if False, do not block on wait_for_ready, just return after calling
         out to the API; if True, call wait_for_ready, blocking until the VS
         is created
     required: false
     default: True
requirements:
    - "python >= 2.6:
    - "softlayer"
'''

EXAMPLES = '''
# Orders a new virtual server with the latest Ubuntu product installed
# and the authorized key with the given id
- sl_vs_server:
    username: user1
    api_key: long_random_code
    hostname: vm1
    domain: domain1.com
    state: present
    datacenter: data1
    os_code: UBUNTU_LATEST
    ssh_keys:
      - 0123456789

# Orders a virtual machine with a specific image on a monthly billing rate
# that has 8GB of RAM and 4 VCPU's
- sl_vs_server:
    username: user1
    api_key: long_random_code
    hostname: vm1
    domain: domain1.com
    state: present
    datacenter: data1
    os_code: 987654321
    hourly: False
    memory: 8
    cpus: 4

# Deletes all VS with the given hostname and domain with 4 VCPU's
- sl_vs_server:
    username: user1
    api_key: blahhhhhhhh
    hostname: to_delete
    domain: trash-it.com
    state: absent
    cpus: 4

# Orders a VS with 32 bit RedHat 6 installed on a SAN disk
- sl_vs_server:
    username: user1
    api_key: long_random_code
    hostname: vm1
    domain: domain1.com
    state: present
    datacenter: data2
    local_disk: False
    os_code: REDHAT_6_32

# Orders a VS on a dedicated server with access only to the private network
# with the given ip address and vlan network
- sl_vs_server:
    username: user1
    api_key: long_random_code
    hostname: vm1
    domain: domain1.com
    state: present
    datacenter: data2
    dedicated: True
    private: True
    private_vlan: 111111
    private_ip: 1.2.3.4

# Orders a VS with the given tags
- sl_vs_server:
    username: user1
    api_key: long_random_code
    hostname: vm1
    domain: domain1.com
    state: present
    datacenter: data2
    tags:
      - yellow
      - blue
      - green
'''

def _create_server(module, mgr):
    """Creates a virtual server on softlayer with the given specifications"""
    hostname = module.params['hostname']
    domain = module.params['domain']
    # These are the basic specifications that need to be specified
    instance_specs = dict(
        domain=domain,
        hostname=hostname,
        memory=module.params['memory'],
        cpus=module.params['cpus'],
        datacenter=module.params['datacenter'],
        hourly=module.params['hourly']
    )
    # Make sure all necessary keys have values
    for key in instance_specs:
        if not instance_specs[key]:
            module.fail_json(msg='%s must be specified to order instance' % key)

    # Check that either one of but not both of image_id and os_code were given
    image_id = module.params['image_id']
    os_code = module.params['os_code']
    if(module.params['image_id'] and module.params['os_code']):
        module.fail_json(msg='image_id and os_code cannot both be specified')
    elif image_id:
        instance_specs['image_id'] = image_id
    elif os_code:
        instance_specs['os_code'] = os_code
    else:
        module.fail_json(msg='You must specify either the OS code or image id')

    # These will always have a boolean value stored
    instance_specs['local_disk'] = module.params['local_disk']
    instance_specs['dedicated'] = module.params['dedicated']

    #Add any additional specifications
    for optional_param in ('public_vlan', 'private_vlan', 'disks',
                           'post_uri', 'private', 'ssh_keys',
                           'nic_speed', 'tags'):
        if module.params[optional_param]:
            instance_specs[optional_param] = module.params[optional_param]

    # Create instance
    mgr.create_instance(**instance_specs)
    inst = mgr.list_instances(hostname=hostname, domain=domain)[0]

    if module.params['wait_for_ready']:
        # wait for it to be ready
        is_ready = mgr.wait_for_ready(inst['id'], 900)
        if is_ready:
            module.exit_json(changed=True, server=inst)
        else:
            module.fail_json(msg='Timeout while waiting for server. It may not be ready.')

    inst = mgr.get_instance(inst['id'])
    module.exit_json(changed=True, server=inst)

def _delete_server(module, mgr):
    """Deletes server(s) with the given hostname and domain. If multiple instances
    exist with the same hostname and domain, they will all be deleted. Additional
    specifiers can be added"""
    inst = _find_servers(module, mgr)

    if not inst:
        module.exit_json(changed=False, msg='no servers were found with this specification')

    for server in inst:
        mgr.wait_for_transaction(server['id'], 900)
        mgr.cancel_instance(server['id'])

    module.exit_json(changed=True)

def _find_servers(module, mgr):
    """Returns a list of servers that match the given paramaters"""
    # Domain and hostname should always be specified
    instance_specs = dict(domain=module.params['domain'],
                          hostname=module.params['hostname'])

    # These paramaters are optional to narrow the list
    for optional_param in ['datacenter']:
        if module.params[optional_param]:
            instance_specs[optional_param] = module.params[optional_param]

    return mgr.list_instances(**instance_specs)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            username       = dict(required=True, type='str'),
            api_key        = dict(required=True, type='str'),
            hostname       = dict(required=True, type='str'),
            domain         = dict(required=True, type='str'),
            state          = dict(default='present', choices=['present', 'absent']),
            cpus           = dict(default=8, type='int'),
            memory         = dict(default=16, type='int'),
            hourly         = dict(default=True, type='bool'),
            local_disk     = dict(default=True, type='bool'),
            datacenter     = dict(default=None, type='str'),
            os_code        = dict(default=None, type='str'),
            image_id       = dict(default=None, type='int'),
            dedicated      = dict(default=False, type='bool'),
            public_vlan    = dict(default=None, type='int'),
            private_vlan   = dict(default=None, type='int'),
            disks          = dict(default=None, type='list'),
            post_uri       = dict(default=None, type='str'),
            private        = dict(default=None, type='bool'),
            ssh_keys       = dict(default=None, type='list'),
            nic_speed      = dict(default=None, type='int'),
            tags           = dict(default=None, type='str'),
            public_ip      = dict(default=None, type='str'),
            private_ip     = dict(default=None, type='str'),
            wait_for_ready = dict(default=True, type='bool')
        )
    )

    if not HAS_SOFTLAYER:
        module.fail_json(msg='softlayer is required for this module')

    client = SoftLayer.Client(username=module.params['username'],
                              api_key=module.params['api_key'])
    mgr = SoftLayer.VSManager(client)
    state = module.params['state']
    hostname = module.params['hostname']
    domain = module.params['domain']

    # Order a server if state is present, cancel an order if absent
    if state == 'present':
        # If a server exists with that hostname and domain, return it
        # Create a new server otherwise
        inst = mgr.list_instances(hostname=hostname, domain=domain)
        if inst:
            inst = mgr.get_instance(inst[0]['id'])
            module.exit_json(changed=False, server=inst)
        else:
            _create_server(module, mgr)
    elif state == 'absent':
        _delete_server(module, mgr)
    else:
        module.fail_json(msg="State %s is not a valid state." % state)

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
