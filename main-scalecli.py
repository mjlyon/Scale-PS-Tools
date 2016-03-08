#!/usr/bin/env python
"""Scale Computing Command Line Input (SCCLI) - v1.0

Usage:
  scalecli --ip <ipaddress> --username <username> --password <password> --show <vm>
  scalecli --ip <ipaddress> --username <username> --password <password> --show <version>
  scalecli --ip <ipaddress> --username <username> --password <password> --show <clustername>
  scalecli --ip <ipaddress> --username <username> --password <password> --show <iso>
  scalecli --ip <ipaddress> --username <username> --password <password> --show <node>
  scalecli --ip <ipaddress> --username <username> --password <password> --description <vmNAME> <newDESCRIPTION>
  scalecli --ip <ipaddress> --username <username> --password <password> --createvm <vmNAME> <vmVCPU> <vmRAM> <vmHDD> <vmVLAN> <vmQUANTITY>
  scalecli --ip <ipaddress> --username <username> --password <password> --vm <vmNAME> <vmACTION>
  scalecli --ip <ipaddress> --username <username> --password <password> --shutdowntag <vmTAG> <ForceShutdown>
  scalecli --ip <ipaddress> --username <username> --password <password> --starttag <vmTAG>
  scalecli --ip <ipaddress> --username <username> --password <password> --clone <vmSOURCENAME> <vmCLONENAME> <numCLONES> <numCLONESSTART> <vmCLONETAG> <vmCLONEDESCRIPTION>
  scalecli --ip <ipaddress> --username <username> --password <password> --export <vmSOURCENAME> <vmDESTINATION>


  scalecli (-h | --help)

Options:
  -h --help                             # Show this screen.
  --show                                # Where [options] can be:-
                                        #
                                        # vm - Display all VM's on clustere
                                        # iso - Display all ISO images and their mounted status
                                        # version - Display firmware version
                                        # clustername - Display current clustername


  --vm                                  # --vm <vmname> stop - Power off running VM non gracefully
                                        # --vm <vmname> start - Power on VM
                                        # --vm <vmname> shutdown - Gracefully shutdown VM

  --shutdown <TagName> <ForceShutdown>  # Shutdown all servers which have a matching tagname.  The <ForceShutdown> parameter can be eith YES or No
                                        # Example: --shutdown Production NO (shutdown all servers tagged with name "Production" safely)
  --ip                                  # IP address of cluster
  --username                            # username of cluster
  --password                            # password for cluster

"""
from docopt import docopt

# Set some default variables
ClusterUsername = ''
ClusterPassword = ''
ClusterIP = ''
DisplayISOList = False
DisplayAllVMList = False
DisplayVMInfo = False
DisplayClusterName = ''
DisplayClusterVersion = ''
HDDGUID = []
HDDSerial = []
listofVM = ''
ListofISO = ''
CreateVM = ''
cluster = ''
result = ''
vmGUID = []
vmNAME_LEN = []
vmOS_LEN = []
vmDESCRIPTION_LEN = ''
vmSTATE = []
vmNAME = []
vmOS = []
vmVCPU = []
vmDESCRIPTION = []
vmMEMORY = []
vmCONSOLE = []
vmTAGS = []
vmISO_NAME = []
vmISO_SIZE = []
vmISO_MOUNT = []
vmNUMBER = 0
vmRUNNINGONNODE = []
Cluster_HCOREVersion = []
Cluster_Name = []
ColumnHeader = ''
ColumnPadding = 2
isoNumber = 0
FoundOption = False
CreateVM = False
nodeSHOW = False
nodeLANIP = []
nodeNUMCORES = []
nodeNUMTHREADS = []
nodeMEMSIZE = []
nodeBACKPLANEIP = []
nodeNUMCPUs = []
nodeHDDCAPACITY = []
nodeGUID = []
vmACTION = False
vmSHUTDOWNbyTAG = ''
vmSHUTDOWNTAG = ''
vmSTARTbyTAG = ''
vmSTARTTAG = ''
vmSHUTDOWNFORCE = ''
vmCLONE = False

# Now lets start parsing the command line to see what options we have chosen.
# For reference i'm using docopt as the command line parser
if __name__ == '__main__':
    arguments = docopt(__doc__)

    # Check arguments to see if correct options are given.  Set flags if so.

    if arguments['--ip']:
        ClusterIP = arguments['<ipaddress>']
    if arguments['--username']:
        ClusterUsername = arguments['<username>']
    if arguments['--password']:
        ClusterPassword = arguments['<password>']

    if arguments['--show'] == True:
        if arguments['<vm>'] == 'iso':
            DisplayISOList = True
        if arguments['<vm>'] == 'vm':
            DisplayAllVMList = True
        if arguments['<vm>'] == 'version':
            DisplayClusterVersion = True
        if arguments['<vm>'] == 'clustername':
            DisplayClusterName = True
        if arguments['<vm>'] == 'node':
            nodeSHOW = True
        if arguments['<vm>'] == None:
            DisplayISOList = True
            DisplayAllVMList = True
            DisplayClusterVersion = True
            DisplayClusterName = True

    if arguments['--createvm']:
        CreateVM = True
        CreateVMNAME = arguments['<vmNAME>']
        CreateVMVCPU = int(arguments['<vmVCPU>'])
        CreateVMRAM = int(arguments['<vmRAM>']) * 1024 * 1024 * 1024
        CreateVMHDD = int(arguments['<vmHDD>']) * 1000 * 1000 * 1000
        CreateVMVLAN = int(arguments['<vmVLAN>'])
        CreateVMQUANTITY = int(arguments['<vmQUANTITY>'])

    if arguments['--vm']:
        vmACTION = True
        vmACTIONVMNAME = arguments['<vmNAME>']
        vmACTIONTYPE = arguments['<vmACTION>']

    if arguments['--shutdowntag']:
        vmSHUTDOWNbyTAG = True
        vmSHUTDOWNTAG = arguments['<vmTAG>']
        vmSHUTDOWNFORCE = arguments['<ForceShutdown>']

    if arguments['--starttag']:
        vmSTARTbyTAG = True
        vmSTARTTAG = arguments['<vmTAG>']

    if arguments['--clone']:
        vmCLONE = True
        vmSOURCENAME = arguments['<vmSOURCENAME>']
        vmCLONENAME = arguments['<vmCLONENAME>']
        numCLONES = int(arguments['<numCLONES>'])
        numCLONESSTART = int(arguments['<numCLONESSTART>'])
        vmCLONETAG = arguments['<vmCLONETAG>']
        vmCLONEDESCRIPTION = arguments['<vmCLONEDESCRIPTION>']

    if arguments['--export']:
        vmEXPORT = True
        vmSOURCENAME = arguments['<vmSOURCENAME>']
        vmexportDESTINATION = arguments['<vmDESTINATION>']

    if arguments['--description']:
        vmDESCRIPTIONCHANGE = True
        vmDESCRIPTIONCHANGESOURCENAME = arguments['<vmNAME>']
        vmDESCRIPTIONCHANGETEXT = arguments['<newDESCRIPTION>']

# Import additional libraries to allow us to do our coding.
# Colorama library will allow us to output colour text later on when needed.
import sys
import ssl
from colorama import init

init()

# Code below is the bit that actually opens up the connection to the cluster via the API
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context
from thrift.transport import THttpClient
from thrift.protocol import TJSONProtocol
from scaled.ttypes import *
from scaled import ScaleService

sys.path.append('gen-py')


def InfoPrint(*args):
    CommaPrint = ''
    StandardPrint = ''

    for x in args:
        CommaPrint = CommaPrint + '"' + str(x) + '"' + ','
        StandardPrint = StandardPrint + str(x)
    CommaPrint = CommaPrint[:-1]

    # print CommaPrint
    print StandardPrint


# CreateFormattedColumns function will take a list of strings and add additional spaces so that
# all the strings are the same lenght.  This makes it very easy to have columns of text
# lining up all in a straight line.
def CreateFormattedColumns(*args):
    NumberOfArgs = len(args)
    MaxColumnWidth = 0
    for l in range(0, NumberOfArgs):
        MaxColumnWidth = len(max(args[l], key=len))
        for vm in range(1, len((args[l]))):
            if len(args[l][vm]) < MaxColumnWidth:
                for pad in range(1, (MaxColumnWidth - len(args[l][vm])) + 1):
                    args[l][vm] = args[l][vm] + " "


# RemoveFormattedColumns will remove additional spaces from the end of strings in a list.
def RemoveFormattedColumns(*args):
    for l in range(1, len((args[0]))):
        args[0][l] = args[0][l].rstrip()


def vmEXIST(vmTOSEARCH):
    # Check to see if the source VM exists.  We first check by name and then by GUID
    vmSOURCENAMEFOUND = False
    for l in range(0, vmNUMBER):
        if vmTOSEARCH.upper() == vmNAME[l].upper():
            vmSOURCENAMEFOUND = True
            vmSOURCENAMEGUID = vmGUID[l]

        # Check by GUID to see if we can get a match
        if vmTOSEARCH.upper() == vmGUID[l].upper():
            print vmGUID[l]
            vmSOURCENAMEFOUND = True
            vmSOURCENAMEGUID = vmGUID[l]

    if vmSOURCENAMEFOUND == False:
        print "Source VM not found"
    return vmSOURCENAMEFOUND


# vmGETINFO (<vmname>|<vmGUID>, <vmguid> <vmvcpu> <vmmemory> <vmstate>)
# Function is used to return the value you want from a VM.  Can either use vm name or vm GUID

def vmGETINFO(vmTOSEARCH, vmINFO):
    vmGETINFORETURNED = ''
    for l in range(0, vmNUMBER):
        if vmTOSEARCH.upper() == vmNAME[l].upper():
            if vmINFO.upper() == 'VMGUID':
                vmGETINFORETURNED = vmGUID[l]
            if vmINFO.upper() == 'VMVCPU':
                vmGETINFORETURNED = vmVCPU[l]
            if vmINFO.upper() == 'VMMEMORY':
                vmGETINFORETURNED = vmMEMORY[l]
            if vmINFO.upper() == 'VMSTATE':
                vmGETINFORETURNED = vmSTATE[l]
        # Check to see if we have a match via the vmGUID
        if vmTOSEARCH.upper() == vmGUID[l].upper():
            if vmINFO.upper() == 'VMGUID':
                vmGETINFORETURNED = vmGUID[l]
            if vmINFO.upper() == 'VMVCPU':
                vmGETINFORETURNED = vmVCPU[l]
            if vmINFO.upper() == 'VMMEMORY':
                vmGETINFORETURNED = vmMEMORY[l]
            if vmINFO.upper() == 'VMSTATE':
                vmGETINFORETURNED = vmSTATE[l]
    return vmGETINFORETURNED


# Make socket
transport = THttpClient.THttpClient('https://' + ClusterIP + '/api/')
protocol = TJSONProtocol.TJSONProtocol(transport)
client = ScaleService.Client(protocol)
transport.open()
ses = Session(username=ClusterUsername, password=ClusterPassword)
sessionID = client.SessionCreate(ses).createdGUID

# Start of the main code.  The idea is to read eveyrthing about the cluster and to store that information
# info lists.  Once we have all that information we can display it or manipulate it.

domains = client.VirDomainRead(sessionID, 0, VirDomainFilter())
for vm in domains:

    # Code below will read in MAC address from VM.
    # netd=vm.netDevs
    # snap=vm.snapUIDs
    # print vm
    # for l in snap:
    #    print l
    # print netd, len(netd)
    # for l in netd:
    #    print l, "    ", l.macAddress


    vmNUMBER = vmNUMBER + 1
    vmGUID.append(str(vm.guid))
    vmNAME.append(str(vm.name))
    vmOS.append(str(vm.operatingSystem))
    vmVCPU.append(str(vm.numVCPU))
    vmDESCRIPTION.append(str(vm.description))
    vmMEMORY.append(str((vm.mem / 1024) / 1024 / 1024))
    vmCONSOLE.append(str(vm.console))
    if len(vm.console.ip) > 0:
        vmRUNNINGONNODE.append(str(vm.console.ip))
    if len(vm.console.ip) == 0:
        vmRUNNINGONNODE.append('--')
    vmTAGS.append(str(vm.tags))
    # Turn vmState into meaniful text fields instead of numbers.
    if vm.state == 0:
        vmSTATE.append("RUNNING")
    elif vm.state == 1:
        vmSTATE.append("BLOCKED")
    elif vm.state == 2:
        vmSTATE.append("PAUSED")
    elif vm.state == 3:
        vmSTATE.append("SHUTDOWN")
    elif vm.state == 4:
        vmSTATE.append("SHUTOFF")
    elif vm.state == 5:
        vmSTATE.append("CRASHED")

# Read list of ISO images and whether they are mounted or not.
domains = client.ISORead(sessionID, VirDomainFilter())
for iso in domains:
    isoNumber = isoNumber + 1
    vmISO_NAME.append(str(iso.name))
    vmISO_SIZE.append(str(iso.size / 1024 / 1024))
    if len(iso.mounts) <> 0:
        vmISO_MOUNT.append("MOUNTED")
    else:
        vmISO_MOUNT.append("NOT MOUNTED")

# Read Cluster Version and Name details
domains = client.ClusterRead(sessionID, -1, VirDomainFilter())
for hcos in domains:
    Cluster_HCOREVersion.append(str(hcos.icosVersion))
    Cluster_Name.append(hcos.clusterName)

# Read Node Version and Name details
domains = client.NodeRead(sessionID, -1, VirDomainFilter())
NumberNodes = 0
for node in domains:
    nodeGUID.append(node.guid)
    nodeLANIP.append(node.lanIP)
    nodeNUMCORES.append(node.numCores)
    nodeNUMTHREADS.append(node.numThreads)
    nodeMEMSIZE.append(node.memSize)
    nodeBACKPLANEIP.append(node.backplaneIP)
    nodeNUMCPUs.append(node.numCPUs)
    nodeHDDCAPACITY.append(node.capacity)
    NumberNodes = NumberNodes + 1

# print "Nodes:",NumberNodes
# print "Threads:" , nodeNUMTHREADS
# print "Ram per node:", nodeMEMSIZE[1]/1024/1024/1024+1
# print "Node BackPlane:", nodeBACKPLANEIP
# print "Number CPU's per node:", nodeNUMCPUs
# print "HDD Capacity per node:", str(nodeHDDCAPACITY[1]/1000/1000/1000)+"gb"



if DisplayAllVMList == True:
    # CreateFormattedColumns function will take the lists presented as arguments and read through them.  It will find the
    # longest string and then make sure all the other strings are the same lenght.  This means when we display them on the
    # screen, they all line up in neat columns
    CreateFormattedColumns(vmSTATE, vmNAME, vmMEMORY, vmVCPU, vmDESCRIPTION, vmGUID, vmRUNNINGONNODE, vmTAGS)
    print "GUID                                   Mem Alloc   CPUs  State     Node            Name                              Description                                                        TAGS"

    for c in range(1, len(vmNAME)):
        InfoPrint(vmGUID[c], "   ", vmMEMORY[c], '          ', vmVCPU[c], '     ', vmSTATE[c], '   ',
                  vmRUNNINGONNODE[c], '    ', vmNAME[c], '         ', vmDESCRIPTION[c], '   ', vmTAGS[c])
    print  ""

    # Since all the lists now contain all spaces on the end of the strings, we want to remove all the spaces
    # This will be useful for later on when we can export the lists as .csv or XML files.
    RemoveFormattedColumns(vmGUID)
    RemoveFormattedColumns(vmRUNNINGONNODE)
    RemoveFormattedColumns(vmNAME)
    RemoveFormattedColumns(vmOS)
    RemoveFormattedColumns(vmVCPU)
    RemoveFormattedColumns(vmDESCRIPTION)
    RemoveFormattedColumns(vmMEMORY)
    RemoveFormattedColumns(vmCONSOLE)
    RemoveFormattedColumns(vmTAGS)
    sys.exit(0)

# --SHOW ISO command line option has been used so we need to display all the ISO from the lists we read in earlier on.
if DisplayISOList == True:
    CreateFormattedColumns(vmISO_NAME, vmISO_SIZE, vmISO_MOUNT)
    for c in range(1, len(vmISO_NAME)):
        InfoPrint(vmISO_NAME[c], '   ', vmISO_SIZE[c], '   ', vmISO_MOUNT[c])
    print""
    sys.exit(0)

# --SHOW CLUSTERNAME command line option has been used so we need to display all relevant list we read earlier on.
if DisplayClusterName == True:
    InfoPrint(Cluster_Name[0])
    print ""
    sys.exit(0)

# --SHOW VERSION command line option has been used so we need to display all relevant list we read earlier on.
if DisplayClusterVersion == True:
    InfoPrint(Cluster_HCOREVersion[0])
    print ""
    sys.exit(0)

# --SHOW NODE command line option has been used so we need to display all relevant list we read earlier on.
if nodeSHOW == True:
    print "Peer GUID                                   Backplane         LAN              RAM    CPUs   CORES  Threads"
    for n in range(0, NumberNodes):
        print n, '  ', nodeGUID[n], ' ', nodeBACKPLANEIP[n], '     ', nodeLANIP[n], '   ', (
            nodeMEMSIZE[n] / 1024 / 1024 / 1024 + 1), '   ', nodeNUMCPUs[n], '    ', nodeNUMCORES[n], '    ', \
            nodeNUMTHREADS[n]
    sys.exit(0)

# Create a VM.  Variables below make it easy to see how the command is built up.  Don't change any of them!!
if CreateVM == True:
    # Types of network cards
    RTL8139 = 0
    INTEL_E1000 = 1
    VIRTIO = 2

    # Types of HDD
    IDE_DISK = 0
    SCSI_DISK = 1
    VIRTIO_DISK = 2
    IDE_CDROM = 3
    IDE_FLOPPY = 4

    # Types of caching for HDD
    NONE = 0,
    WRITEBACK = 1
    WRITETHROUGH = 2

    # Lets do some check to make sure the VM is a valid type of system.  No duplicate number or overprovisioned resources
    # So first lets make sure the name doesn't exist, either a single VM or multiple VMs
    for vm in range(1, vmNUMBER):
        if CreateVMNAME.upper() == vmNAME[vm].upper():
            print "Error - Duplicate VM Name"
            sys.exit(0)

    # Check to see that we don't create a drive bigger than 8TB
    if int(CreateVMHDD) > (8000 * 1000 * 1000 * 1000):
        print "Error - HDD Size is too large.  Maximum size is 8TB (8000gb)"
        sys.exit(0)

    # If we just want to create a single VM, use the code below.
    if CreateVMQUANTITY == 1:
        client.VirDomainCreate(sessionID, VirDomain(name=CreateVMNAME, operatingSystem="os_windows_server_2012",
                                                    description="SCALECLI Created",
                                                    mem=CreateVMRAM, numVCPU=CreateVMVCPU, netDevs=[
                VirDomainNetDevice(vlan=CreateVMVLAN, connected=True, type=VIRTIO)],
                                                    blockDevs=[
                                                        VirDomainBlockDevice(slot=0, capacity=CreateVMHDD, allocation=0,
                                                                             cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                             physical=0)]))
    # But if we want to create more than 1 VM, create the VM inside a loop.
    if CreateVMQUANTITY > 1:
        for loop in range(1, CreateVMQUANTITY + 1):
            client.VirDomainCreate(sessionID,
                                   VirDomain(name=(CreateVMNAME + str(loop)), operatingSystem="os_windows_server_2012",
                                             description="SCALECLI Created",
                                             mem=CreateVMRAM, numVCPU=CreateVMVCPU, netDevs=[
                                           VirDomainNetDevice(vlan=CreateVMVLAN, connected=True, type=VIRTIO)],
                                             blockDevs=[VirDomainBlockDevice(slot=0, capacity=CreateVMHDD, allocation=0,
                                                                             cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                             physical=0)]))
    sys.exit(0)

# Actions that we can take on a VM include STOP, START, SHUTDOWN.
# STOP - power off the VM (not recommended - same effect as hitting the power button)
# START - Power on a VM
# SHUTDOWN - Perform a controlled safe shutdown.  Recommended way but only works at login screen.
if vmACTION == True:
    found = False
    if vmEXIST(vmACTIONVMNAME) == True:
        found = True
        tempGUID = vmGETINFO(vmACTIONVMNAME, 'VMGUID')
        # We can now STOP (simulate power button being pressed) , START or SHUTDOWN (Graceful shutdown) a VM
        if vmACTIONTYPE.upper() == "STOP":
            result = client.VirDomainAction(sessionID, [
                VirDomainActionDescription(virDomainGUID=tempGUID, actionType=VirDomainActionType.STOP)])
        if vmACTIONTYPE.upper() == "START":
            result = client.VirDomainAction(sessionID, [
                VirDomainActionDescription(virDomainGUID=tempGUID, actionType=VirDomainActionType.START)])
        if vmACTIONTYPE.upper() == "SHUTDOWN":
            result = client.VirDomainAction(sessionID, [
                VirDomainActionDescription(virDomainGUID=tempGUID, actionType=VirDomainActionType.SHUTDOWN)])

    # if the VM doesnt exist display error message
    if found == False:
        print "Error - Unable to find VM.  Check the name"
        sys.exit(100)
    sys.exit(0)

# Shutting down by TAG is really useful to be able close lots of VM's based in the TAG id.
if vmSHUTDOWNbyTAG == True:
    found = False
    for l in range(1, vmNUMBER):
        # print vmTAGS[l], vmSHUTDOWNTAG
        if vmTAGS[l].upper() == vmSHUTDOWNTAG.upper():
            found = True
            # print vmNAME[l], " ", vmSTATE[l]
            if vmSTATE[l] == "RUNNING":
                if vmSHUTDOWNFORCE.upper() == "FORCE":
                    result = client.VirDomainAction(sessionID, [
                        VirDomainActionDescription(virDomainGUID=vmGUID[l], actionType=VirDomainActionType.STOP)])
                if vmSHUTDOWNFORCE.upper() == "SAFE":
                    result = client.VirDomainAction(sessionID, [
                        VirDomainActionDescription(virDomainGUID=vmGUID[l], actionType=VirDomainActionType.SHUTDOWN)])
    if found == False:
        print "Error - Unable to find TAG.  Check the TAG name"
        sys.exit(0)
    sys.exit(0)

# Start VM's based on their TAG id.
if vmSTARTbyTAG == True:
    found = False
    for l in range(1, vmNUMBER):
        # print vmTAGS[l], vmSTARTTAG
        if vmTAGS[l].upper() == vmSTARTTAG.upper():
            found = True
            # print vmNAME[l], " ", vmSTATE[l]

            if vmSTATE[l] == "SHUTOFF":
                # print "Starting ", vmNAME[l]
                # We can now STOP (simulate power button being pressed) , START or SHUTDOWN (Graceful shutdown) a VM
                result = client.VirDomainAction(sessionID, [
                    VirDomainActionDescription(virDomainGUID=vmGUID[l], actionType=VirDomainActionType.START)])
    if found == False:
        print "Error - Unable to find TAG.  Check the TAG name"
        sys.exit(0)
    sys.exit(0)

# CLONE a VM.
if vmCLONE == True:
    newCLONEVMNAME = ''
    vmSOURCENAMEFOUND = False

    # Check to see if the source VM exists
    for vm in range(0, vmNUMBER):
        if vmSOURCENAME.upper() == vmNAME[vm].upper():
            vmSOURCENAMEFOUND = True
            vmSOURCENAMEGUID = vmGUID[vm]
    if vmSOURCENAMEFOUND == False:
        print "Source VM not found"
        sys.exit(0)

    # Now we check that an existing VM doesn't have the same name as the cloned named
    # Need to take into account that the clones VM name will have a number appended to it.
    for vm in range(numCLONESSTART, numCLONESSTART + numCLONES):
        newCLONEVMNAME = vmCLONENAME + str(vm)
        if newCLONEVMNAME.upper() == vmNAME[vm].upper():
            print "VM Name: " + newCLONEVMNAME + " already exists.  Please choose another name"
            sys.exit(0)

    for vm in range(numCLONESSTART, numCLONESSTART + numCLONES):
        template = VirDomain(name=vmCLONENAME + str(vm), description=vmCLONEDESCRIPTION, tags=vmCLONETAG)
        result = client.VirDomainClone(sessionID, vmSOURCENAMEGUID, template)
        vmCLONEDomain = client.VirDomainRead(sessionID, 0, VirDomainFilter(virDomainGUID=result.createdGUID))

        # Wait until the CLONE is created before we create another one.  Code below checks to see if the length of the
        # VM properties is more than zero. Terrible way of doing it but it's the only way I could figure out.
        vmCLONEFINISHED = False
        while vmCLONEFINISHED == False:
            CLONESTATUS = client.TaskTagStatusRead(sessionID, TaskTagFilter(taskTag=result.taskTag))
            for l in CLONESTATUS:
                if l.progressPercent == 100:
                    vmCLONEFINISHED = True

# Change the description on a VM
if vmDESCRIPTIONCHANGE == True:
    if vmEXIST(vmDESCRIPTIONCHANGESOURCENAME) == True:
        # print vmGETINFO(vmDESCRIPTIONCHANGESOURCENAME,'vmGUID')
        # print vmGETINFO(vmDESCRIPTIONCHANGESOURCENAME,'vmMEMORY')
        # print vmGETINFO(vmDESCRIPTIONCHANGESOURCENAME,'vmVCPU')
        # print vmGETINFO(vmDESCRIPTIONCHANGESOURCENAME,'vmSTATE')

        # Update info for a VM
        tempGUID = vmGETINFO(vmDESCRIPTIONCHANGESOURCENAME, 'vmGUID')
        vm = client.VirDomainRead(sessionID, -1, VirDomainFilter(virDomainGUID=tempGUID))[0]
        vm.description = vmDESCRIPTIONCHANGETEXT
        result = client.VirDomainUpdate(sessionID, vm)






        # Export a VM - None of the code works yet below.
        # if vmEXPORT == True:
        #    print "Exporting vm"
        #    result = ""
        #    vmTemplate = VirDomain(name="TEST123", description="VM Description")
        #    print vmTemplate
        #    exportTarget = VirDomainExportTarget("192.168.1.221/exportvm", '', '', '')
        #    print exportTarget
        #    result = client.VirDomainExport(sessionID, "192.168.1.221/exportvm", '34baa638-e4f6-4135-9986-a5fa2d794f8e', "",vmTemplate)
        #    print result
        #    client.VirDomainExport()
