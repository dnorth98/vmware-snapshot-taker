"""
Python program for listing the vms on an ESX / vCenter host
"""

import atexit

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

import tools.cli as cli

import json
import datetime

def get_vm_info(virtual_machine):
    summary = virtual_machine.summary

    return summary

def print_vm_info(virtual_machine):
    """
    Print information for a particular virtual machine or recurse into a
    folder with depth protection
    """
    summary = virtual_machine.summary
    print("Name       : ", summary.config.name)
    print("Template   : ", summary.config.template)
    print("Path       : ", summary.config.vmPathName)
    print("Guest      : ", summary.config.guestFullName)
    print("Instance UUID : ", summary.config.instanceUuid)
    print("Bios UUID     : ", summary.config.uuid)
    annotation = summary.config.annotation
    if annotation:
        print("Annotation : ", annotation)
    print("State      : ", summary.runtime.powerState)
    if summary.guest is not None:
        ip_address = summary.guest.ipAddress
        tools_version = summary.guest.toolsStatus
        if tools_version is not None:
            print("VMware-tools: ", tools_version)
        else:
            print("Vmware-tools: None")
        if ip_address:
            print("IP         : ", ip_address)
        else:
            print("IP         : None")
    if summary.runtime.question is not None:
        print("Question  : ", summary.runtime.question.text)
    print("")

def create_snapshot(si, uuid):
    snapshot_created = False

    instance_search = True  # we're using instance UUIDs
    vm = si.content.searchIndex.FindByUuid(None, uuid, True, instance_search)

    date_str = datetime.datetime.today().strftime('%Y-%m-%d')

    desc = "Automated Snapshot taken on " + date_str
    snapshot_name = "Backup-" + date_str

    if vm is None:
        snapshot_created = False
    else:
        task = vm.CreateSnapshot_Task(name=snapshot_name,
                                      description=desc,
                                      memory=True,
                                      quiesce=False)
        if task:
            snapshot_created = True

    return snapshot_created

def main():
    """
    Simple command-line program for listing the virtual machines on a system.
    """

    vm_names_to_snap = []

    parser = cli.build_arg_parser()
    parser.add_argument('-f', '--file', required=True,
                        help="File containing a list of VMs to snapshot.")
    args = parser.parse_args()

    # Grab the file containing the VMs to snapshot
    with open(args.file, 'r') as f:
        vms_to_snap = json.load(f)

    for snapshot_vm in vms_to_snap:
        vm_names_to_snap.append(snapshot_vm['Name'])

    try:
        if args.disable_ssl_verification:
            service_instance = connect.SmartConnectNoSSL(host=args.host,
                                                         user=args.user,
                                                         pwd=args.password,
                                                         port=int(args.port))
        else:
            service_instance = connect.SmartConnect(host=args.host,
                                                    user=args.user,
                                                    pwd=args.password,
                                                    port=int(args.port))

        atexit.register(connect.Disconnect, service_instance)

        content = service_instance.RetrieveContent()

        container = content.rootFolder  # starting point to look into
        viewType = [vim.VirtualMachine]  # object types to look for
        recursive = True  # whether we should look into it recursively
        containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive)

        children = containerView.view
        for child in children:
            info = get_vm_info(child)

            if info.config.name in vm_names_to_snap:
                uuid = info.config.instanceUuid

                if uuid is not None:
                    if create_snapshot(service_instance, uuid):
                        print "Snapshot triggered for " + info.config.name
                    else:
                        print "Error trigging snapshot for " + info.config.name
                else:
                    print "Error obtaining UUID for " + info.config.name + " - Unable to trigger snapshot"

    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0

# Start program
if __name__ == "__main__":
    main()
