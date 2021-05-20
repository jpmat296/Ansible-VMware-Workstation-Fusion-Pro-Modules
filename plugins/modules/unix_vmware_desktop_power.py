#!/usr/bin/python

import base64
import json
import re
import sys
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
module: unix_vmware_desktop_power

short_description: Change VMware Workstation Pro VM PowerState

version_added: "2.4"

description:
    - "Change VMware Workstation Pro VM PowerState"

options:
    target_vm:
        description:
            - This is the target VM to interact with
        required: true

    state: on || off || shutdown || suspend || pause || unpause
        description:
            - This is the power state we want, if not set, module will return actual VM power state
        required: false

    username: "api-username"
        description:
            - Your workstation API username
        required: true

    password: "api-password"
        description:
            - Your workstation API password
        required: true

    api_url: "http://127.0.0.1"
        description:
            - Your workstation API URL
        required: false
        default: "http://127.0.0.1"

    api_port: "8697"
        description:
            - Your workstation API PORT
        required: false
        default: "8697"

    validate_certs: "no || yes"
        description:
            - Validate Certificate it HTTPS connection
        required: false

    timeout: 30
        description:
            - Specifies a timeout in seconds for communicating with vmrest
        required: false
        default: 30

author:
    - Adam Magnier (@qsypoq)
'''

EXAMPLES = r'''
### Boot the VM with ID 42
- name: "Start VM"
  unix_vmware_desktop_power:
    target_vm: "42"
    state: "on"
    username: "api-username"
    password: "api-password"
    api_url: "http://127.0.0.1"
    api_port: "8697"

### Get power state of the VM with ID 42
- name: "Get power state"
  unix_vmware_desktop_power:
    target_vm: "42"
    username: "api-username"
    password: "api-password"
'''

RETURN = r'''
### Get power state of the VM with ID 42
"power_state": "poweredOff"

### Boot the VM with ID 42
"power_state": "poweredOn"
'''

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

def run_module():
    module_args = dict(
        username=dict(type='str', required=True),
        password=dict(type='str', required=True),
        target_vm=dict(type='str', required=False),
        target_vm_name=dict(type='str', required=False, default=''),
        state=dict(type='str', required=False, default=''),
        api_url=dict(type='str', default='http://127.0.0.1'),
        api_port=dict(type='str', default='8697'),
        validate_certs=dict(type='bool', default='no'),
        timeout=dict(type='int', required=False, default=30),
    )

    result = dict(
        changed=False,
        msg=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    api_username = module.params['username']
    api_password = module.params['password']
    creds = api_username + ':' + api_password
    if PY3:
        encodedBytes = base64.b64encode(creds.encode("utf-8"))
        request_creds = str(encodedBytes, "utf-8")
    else:
        encodedBytes = base64.b64encode(creds)
        request_creds = str(encodedBytes).encode("utf-8")
    request_server = module.params['api_url']
    request_port = module.params['api_port']
    headers = {'Accept': 'application/vnd.vmware.vmw.rest-v1+json', 'Content-Type': 'application/vnd.vmware.vmw.rest-v1+json', 'Authorization': 'Basic ' + request_creds}
    timeout = module.params['timeout']

    target_vm = module.params['target_vm']
    state = module.params['state']

    target_vm_name = module.params['target_vm_name']
    vmlist = []
    if target_vm_name != "":
        requestnamesurl = request_server + ':' + request_port + '/api/vms'
        reqname, infoname = fetch_url(module, requestnamesurl, headers=headers, method="Get")
        responsename = json.loads(reqname.read())

        for vm in responsename:
            currentvmx = vm['path']
            with open(currentvmx, 'r') as vmx:
                for line in vmx:
                    if re.search(r'^displayName', line):
                        currentname = line.split('"')[1]
            finalname = currentname.lower()
            vm.update({'name': finalname})
            vmlist.append(vm)

        vm_name_search = target_vm_name.lower()
        for vm in vmlist:
            if vm['name'] == vm_name_search:
                target_vm = vm['id']

    request_url = request_server + ':' + request_port + '/api/vms/' + target_vm + "/power"

    if state != "":
        method = "Put"
        req, info = fetch_url(module, request_url, data=state, headers=headers,
                              method=method, timeout=timeout)
    else:
        method = "Get"
        req, info = fetch_url(module, request_url, headers=headers,
                              method=method, timeout=timeout)

    if req is None:
        module.fail_json(msg=info['msg'])

    result['msg'] = json.loads(req.read())
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
