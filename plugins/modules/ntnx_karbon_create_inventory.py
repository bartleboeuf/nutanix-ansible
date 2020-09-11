#!/usr/bin/env python3
# Copyright (c) 2020 Yannick Struyf
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = r"""
---
module: ntnx_karbon_create_inventory
short_description: Create an Ansible inventory file from a Nutanix Karbon cluster.
description:
- Retrieves the SSH certificates for a Nutanix Karbon cluster through the REST API.
- Allows SSH certificates to be used for remote login on Nutanix Karbon cluster.
- Create a simple ansible inventory file with master and workers nodes.
author:
    - Yannick Struyf (@yannickstruyf)
    - Bart Leboeuf (@bartleboeuf)
version_added: '2.9.5'
requirements:
- python 3
- Nutanix Karbon 2.0
options:
  name:
    description:
    - Name of the target Karbon cluster
    required: yes
    type: str
  state:
    description:
    - The state of the inventory file
    required: yes
    default: present
    choices: [ present, absent ]
    type: str
  pc_host:
    description:
    - Prism Central hostname
    required: yes
    type: str
  pc_port:
    description:
    - Prism Central port
    default: 9440
    type: str
  pc_username:
    description:
    - Prism Central username
    required: yes
    type: str
  pc_password:
    description:
    - Prism Central password
    required: yes
    type: str
  ssl_verify:
    description:
    - Use explicit ssl verification
    default: no
    type: bool
  ssh_certificates_download_path:
    description:
    - Target path of the SSH certificate files
    default: ./KARBON-cluster
    type: str
  inventory_cluster_filepath:
    description:
    - Target file path of the ansible inventory file generated for the Karbon cluster
    default: ./KARBON-cluster-inventory
    type: str
  debug:
    description:
    - Enables debug mode. Results in a log file being written to disk
    default: no
    type: bool
"""

EXAMPLES = r"""
- name: Karbon create ansible inventory
  ntnx_karbon_create_inventory:
    name: << cluster_name >>
    state: present
    pc_host: << pc_host >>
    pc_username: << pc_username >>
    pc_password: << pc_password >>
    ssh_certificates_download_path: "./KARBON-<< cluster_name >>"
    inventory_cluster_filepath: "./KARBON-<< cluster_name >>-inventory"
    ssl_verify: False

"""

RETURN = r"""
ssh_public_key_path:
    description: Full path to the public SSH certificate
    returned: success
    type: str
    sample: '/tmp/my-key.pub'
ssh_private_key_path:
    description: Full path to the private SSH certificate
    returned: success
    type: str
    sample: '/tmp/my-key'
inventory_cluster_filepath:
    description: Full path to the generated ansible inventory
    returned: success
    type: str
    sample: '/tmp/KARBON-mycluster-inventory'
"""

try:
    import base64
    import json
    import os
    import time

    import requests
    from ansible.module_utils.basic import AnsibleModule

    from ansible_collections.yst.ntnx.plugins.module_utils.ntnx_karbon_utils import (
        NtnxKarbonClusterManager,
    )
    from ansible_collections.yst.ntnx.plugins.module_utils.ntnx_utils import (
        FinalState,
        NtnxLogger,
    )
except Exception as e:
    raise Exception(f"Failed to perform imports: {e}")


module = AnsibleModule(
    argument_spec=dict(
        debug=dict(required=False, type="bool", default=False),
        name=dict(required=True),
        state=dict(default="present", choices=["absent", "present"]),
        pc_host=dict(required=True),
        pc_port=dict(default="9440"),
        pc_username=dict(required=True),
        pc_password=dict(required=True, no_log=True),
        ssl_verify=dict(required=False, type="bool", default=False),
        ssh_certificates_download_path=dict(default="./KARBON-cluster"),
        inventory_cluster_filepath=dict(default="./KARBON-cluster-inventory"),
    ),
)


def main():
    logger = NtnxLogger(
        "ntnx_karbon_create_inventory", debug_enabled=module.params["debug"]
    )
    final_state = FinalState()
    module.params["ssh_certificates_download"] = True
    ntnx_cluster_manager = NtnxKarbonClusterManager(logger, module, final_state)
    state = ntnx_cluster_manager.state

    if state == "present":
        cluster_obj = ntnx_cluster_manager.get_cluster_obj()
        if not cluster_obj:
            module.fail_json(msg="Karbon cluster does not exist!")
        else:
            ntnx_cluster_manager.get_ssh_certificates(cluster_obj)
            ntnx_cluster_manager.get_inventory_file(cluster_obj)
            final_state.state = "present"
            final_state.changed = True

    elif state == "absent":
        logger.info("absent")
        ntnx_cluster_manager.delete_ssh_certificates()
        ntnx_cluster_manager.delete_inventory_file()
        final_state.state = "absent"
    else:
        module.fail_json(msg=f"Unexpected state used! State: {state}")
    logger.info(final_state.get_final_state())
    module.exit_json(**final_state.get_final_state())


main()
