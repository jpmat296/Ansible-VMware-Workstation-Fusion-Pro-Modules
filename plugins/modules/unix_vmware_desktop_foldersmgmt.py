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
module: unix_vmware_desktop_foldersmgmt

short_description: Implement the Shared Folders Management part of the API

version_added: "2.4"

description:
    - "Manage VMware Workstation Pro Shared Folders"

options:
    target_vm:
        description:
            - This is the target VM to interact with
        required: true

    action: infos || create || delete || update
        description:
            - This is the action we want to do.
        required: true   

    folder_name: "myFolderName"
        description:
            - Name of the shared folder
        required: Only for create & update & delete

    folder_path: C:\Users\qsypoq\Desktop\odbg110
        description:
            - Path of shared folder
        required: Only for create & update, the folder need to be reachable

    access: r || rw
    description:
        - Choose which kind of access the VM have to the folder
    required: false, default is read-only, you only need to use this when access needed is rw
    
    username "api-username"
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

author:
    - Adam Magnier (@qsypoq)  
'''

EXAMPLES = r'''
### List all shared folders mounted on VM ID 42
- name: "List shared folders"
  unix_vmware_desktop_foldersmgmt:
    target_vm: "42"
    action: "infos"
    username: "api-username"
    password: "api-password"

### Create shared folder named ODBG110 on VM ID 42
- name: "Create shared folder"
  unix_vmware_desktop_foldersmgmt:
    target_vm: "42"
    folder_name: "ODBG110"
    folder_path: C:\Users\qsypoq\Desktop\odbg110
    access: "rw"
    action: "create"
    username "api-username"
    password: "api-password"

### Update shared folder named ODBG110 with new path and access rights
- name: "Update ODBG110"
  unix_vmware_desktop_foldersmgmt:
    target_vm: "42"
    folder_name: "ODBG110"
    folder_path: C:\Users\qsypoq\Desktop
    access: "r"
    action: "update"
    username "api-username"
    password: "api-password"

### Delete shared folder named ODBG110 on VM ID 42
- name: "Delete shared folder named ODBG110 on VM ID 42"
  unix_vmware_desktop_foldersmgmt:
    target_vm: "42"
    folder_name: "ODBG110"
    action: "delete"
    username "api-username"
    password: "api-password"
'''

RETURN = r'''
### List all shared folders mounted on VM ID 42
{
    "Count": 1, "value": [
        {
            "flags": 0,
            "folder_id": "ODBG110",
            "host_path": "C:\\Users\\qsypoq\\Desktop"
        }
    ]
}

### Create shared folder named ODBG110 on VM ID 42
{
    "Count": 1, "value": [
        {
            "flags": 4,
            "folder_id": "ODBG110",
            "host_path": "C:\\Users\\qsypoq\\Desktop\\odbg110"
        }
    ]
}

### Update shared folder named ODBG110 with new path and access rights
{
    "Count": 1, "value": [
        {
            "flags": 0,
            "folder_id": "ODBG110",
            "host_path": "C:\\Users\\qsypoq\\Desktop"
        }
    ]
}

### Delete shared folder named ODBG110 on VM ID 42
empty
'''

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

def run_module():
    module_args = dict(
        username=dict(type='str', required=True),
        password=dict(type='str', required=True),
        target_vm=dict(type='str', required=False),
        target_vm_name=dict(type='str', required=False, default=''),
        action=dict(type='str', required=True),
        folder_name=dict(type='str', required=False),
        folder_path=dict(type='str', required=False),
        access=dict(type='str', required=False),
        api_url=dict(type='str', default='http://127.0.0.1'),
        api_port=dict(type='str', default='8697'),
        validate_certs=dict(type='bool', default='no'),
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

    target_vm = module.params['target_vm']
    action = module.params['action']
    folder_name = module.params['folder_name']
    folder_path = module.params['folder_path']
    access = module.params['access']

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

    if access == "rw":
        flags = 4
    else:
        flags = 0

    if action == "infos":
        method = "Get"
        body = {}
        request_url = request_server + ':' + request_port + '/api/vms/' + target_vm + '/sharedfolders'

    if action == "create":
        method = "Post"
        body = {"folder_id": folder_name, "host_path": folder_path, "flags": flags}
        request_url = request_server + ':' + request_port + '/api/vms/' + target_vm + '/sharedfolders'

    if action == "update":
        method = "Put"
        body = {"host_path": folder_path, "flags": flags}
        request_url = request_server + ':' + request_port + '/api/vms/' + target_vm + '/sharedfolders/' + folder_name

    if action == "delete":
        method = "DELETE"
        body = {"id": target_vm}
        request_url = request_server + ':' + request_port + '/api/vms/' + target_vm + '/sharedfolders/' + folder_name

    bodyjson = json.dumps(body)

    req, info = fetch_url(module, request_url, data=bodyjson, headers=headers, method=method)

    if action == "delete":
        result['msg'] = info

    if action != "delete":
        result['msg'] = info

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
