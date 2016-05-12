# SCALECLI v2.0
# Written: Leonard Powers - lpowers@scalecomputing.com
#
# History
# 24/03/2016 - Initial release
# 24/03/2016 - LGP - Add in queryWMIC function to allow Windows OS queries to be returned
# 07/04/2016 - LGP - Lots of rewrite.
#              * Can now display columns of text using the write function
#              * Move VM between Nodes
#              * New command line parser written which allows parameters to be placed in any order
#              * Colour option now added for displays
#              * Written command line help
#              * Ability to create audit log of changes with the cluster (BETA)
#              * Ability to query running Windows OS and bring values (WMIC) into the description. ie CPU load, HDD Space
#
# vmDATA keys that can be read with the queryCLUSTER function
#   _GUID
#   _NAME
#   _OS
#   _VCPU
#   _DESCRIPTION
#   _MEMORY
#   _CONSOLE
#   _RUNNINGONNODE
#   _TAGS
#   _STATE
#   _TOTALNUMBERVM
#   _MACADDRESSx
#   _MACADDRESSxVLAN
#   _TOTALNETWORKCARDS
#   _HDDx
#   _TOTALHDD

# nodeHW keys that can be read with the queryCLUSTER function
#   _LANIP
#   _GUID
#   _NUMCORES
#   _NUMTHREADS
#   _MEMSIZE
#   _BACKPLANEIP
#   _NUMCPU
#   _CAPACITY
#   _CPUhz
#   _HDDxCAPACITYGB
#   _HDDxAVAILABILITY
#   _HDDxSERIALNUMBER
#   _HDDxUSEDGB
#   _HDDxDRIVEDESCRIPTION
#   _HDDxDRIVEGUID
#   _HDDTOTAL

# clusterDATA keys that can be read with the queryCLUSTER function
#   CLUSTER_VERSION
#   CLUSTER_NAME
#   CLUSTER_TOTALNODES
#   ISO_TOTALNUMBER
#   ISOx_NAME
#   ISOx_STATUS
#   ISOx_SIZE
#   x_STATUS
#   x_SIZE

# Libraries to import and use.
import sys
import ssl
import os
import time
import wmi
import argparse

from colorconsole import terminal
from colorama import init
from thrift.transport import THttpClient
from thrift.protocol import TJSONProtocol
from scaled.ttypes import *
from scaled import ScaleService

sys.path.append('gen-py')
screen = terminal.get_terminal(conEmu=False)

# Declare global variables
vmDATA = {}         # Contains all data about VM's (RAM, OS, CPU, HDD, Description etc)
vmDATAHISTORY = {}  # Historical audit data
nodeHW = {}         # Contains all data about the individual nodes (memory, No. HDD, HDD Serial No. etc)
clusterDATA = {}    # Contains misc information about the cluster.
isodata = {}        # Contains all info re ISO files
cmdline = {}        # Contains what we type in on the command line

# Colour used for text displays
Black = 0
Blue = 1
Green = 2
Cyan = 3
Red = 4
Purple = 5
Brown = 6
LightGray = 7
DarkGray = 8
LightBlue = 9
LightGreen = 10
LightCyan = 11
LightRed = 12
LightPurple = 13
Yellow = 14
White = 15


def OpenConnectionToCluster(clusterIP, clusterUSERNAME, clusterPASSWORD):
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

    # Make socket
    global transport, protocol, client, ses, sessionID
    transport = THttpClient.THttpClient('https://' + clusterIP + '/api/')
    protocol = TJSONProtocol.TJSONProtocol(transport)
    client = ScaleService.Client(protocol)
    transport.open()
    ses = Session(username=clusterUSERNAME, password=clusterPASSWORD)
    sessionID = client.SessionCreate(ses).createdGUID
    return sessionID

def GetAllVMData(vmDATASTORAGE):
    global vmTOTALNUMBER
    # global vmDATA,vmDATAHISTORY
    vmTOTALNUMBER = 0
    numbernetworkcards = 1
    cluster = client.VirDomainRead(sessionID, 0, VirDomainFilter())
    for vm in cluster:
        vmTOTALNUMBER = vmTOTALNUMBER + 1  # Count the number of VM's on the cluster

        # Get all information about VM's on cluster and store in vmDATA dictionary
        vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_GUID'] = str(vm.guid)
        vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_NAME'] = str(vm.name)
        vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_OS'] = str(vm.operatingSystem)
        vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_VCPU'] = str(vm.numVCPU)
        vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_DESCRIPTION'] = str(vm.description)
        vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_MEMORY'] = str((vm.mem / 1024) / 1024 / 1024)
        vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_CONSOLE'] = str(vm.console)
        if len(vm.console.ip) > 0:
            vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_RUNNINGONNODE'] = str(vm.console.ip)
        if len(vm.console.ip) == 0:
            vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_RUNNINGONNODE'] = '--'
        vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_TAGS'] = str(vm.tags)

        # Turn vmState into meaningful text fields instead of numbers.
        if vm.state == 0:
            vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_STATE'] = "RUNNING"
        elif vm.state == 1:
            vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_STATE'] = "BLOCKED"
        elif vm.state == 2:
            vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_STATE'] = "PAUSED"
        elif vm.state == 3:
            vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_STATE'] = "SHUTDOWN"
        elif vm.state == 4:
            vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_STATE'] = "SHUTOFF"
        elif vm.state == 5:
            vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_STATE'] = "CRASHED"

        # Adding in dummy place holders for network cards.  Will be used for CSV export
        for maxnumnetworkcards in range(1, 9):
            vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_MACADDRESS' + str(maxnumnetworkcards)] = ''
            vmDATASTORAGE['VM' + str(vmTOTALNUMBER) + '_MACADDRESS' + str(maxnumnetworkcards) + 'VLAN'] = ''

        # Section of code below now gets all the information about a VM and stores it under the VM name.
        # This allows us to reference data about the VM by it's name (in uppercase)
        vmDATASTORAGE[str(vm.name).upper() + '_GUID'] = str(vm.guid)
        vmDATASTORAGE[str(vm.name).upper() + '_NAME'] = str(vm.name)
        vmDATASTORAGE[str(vm.name).upper() + '_OS'] = str(vm.operatingSystem)
        vmDATASTORAGE[str(vm.name).upper() + '_VCPU'] = str(vm.numVCPU)
        vmDATASTORAGE[str(vm.name).upper() + '_DESCRIPTION'] = str(vm.description)
        vmDATASTORAGE[str(vm.name).upper() + '_MEMORY'] = str((vm.mem / 1024) / 1024 / 1024)
        vmDATASTORAGE[str(vm.name).upper() + '_CONSOLE'] = str(vm.console)
        if len(vm.console.ip) > 0:
            vmDATASTORAGE[str(vm.name).upper() + '_RUNNINGONNODE'] = str(vm.console.ip)
        if len(vm.console.ip) == 0:
            vmDATASTORAGE[str(vm.name).upper() + '_RUNNINGONNODE'] = '--'
        vmDATASTORAGE[str(vm.name).upper() + '_TAGS'] = str(vm.tags)
        # Turn vmState into meaningful text fields instead of numbers.
        if vm.state == 0:
            vmDATASTORAGE[str(vm.name).upper() + '_STATE'] = "RUNNING"
        elif vm.state == 1:
            vmDATASTORAGE[str(vm.name).upper() + '_STATE'] = "BLOCKED"
        elif vm.state == 2:
            vmDATASTORAGE[str(vm.name).upper() + '_STATE'] = "PAUSED"
        elif vm.state == 3:
            vmDATASTORAGE[str(vm.name).upper() + '_STATE'] = "SHUTDOWN"
        elif vm.state == 4:
            vmDATASTORAGE[str(vm.name).upper() + '_STATE'] = "SHUTOFF"
        elif vm.state == 5:
            vmDATASTORAGE[str(vm.name).upper() + '_STATE'] = "CRASHED"

        # Adding in dummy place holders for network cards.  Will be used for CSV export
        for maxnumnetworkcards in range(1, 9):
            vmDATASTORAGE[str(vm.name).upper() + '_MACADDRESS' + str(maxnumnetworkcards)] = ''
            vmDATASTORAGE[str(vm.name).upper() + '_MACADDRESS' + str(maxnumnetworkcards) + 'VLAN'] = ''

        # Section of code below now gets all the information about a VM and stores it under the VM GUID.
        # This allows us to reference data about the VM by it's GUID
        vmDATASTORAGE[str(vm.guid).upper() + '_GUID'] = str(vm.guid)
        vmDATASTORAGE[str(vm.guid).upper() + '_NAME'] = str(vm.name)
        vmDATASTORAGE[str(vm.guid).upper() + '_OS'] = str(vm.operatingSystem)
        vmDATASTORAGE[str(vm.guid).upper() + '_VCPU'] = str(vm.numVCPU)
        vmDATASTORAGE[str(vm.guid).upper() + '_DESCRIPTION'] = str(vm.description)
        vmDATASTORAGE[str(vm.guid).upper() + '_MEMORY'] = str((vm.mem / 1024) / 1024 / 1024)
        vmDATASTORAGE[str(vm.guid).upper() + '_CONSOLE'] = str(vm.console)
        if len(vm.console.ip) > 0:
            vmDATASTORAGE[str(vm.guid).upper() + '_RUNNINGONNODE'] = str(vm.console.ip)
        if len(vm.console.ip) == 0:
            vmDATASTORAGE[str(vm.guid).upper() + '_RUNNINGONNODE'] = '--'
        vmDATASTORAGE[str(vm.name).upper() + '_TAGS'] = str(vm.tags)
        # Turn vmState into meaningful text fields instead of numbers.
        if vm.state == 0:
            vmDATASTORAGE[str(vm.guid).upper() + '_STATE'] = "RUNNING"
        elif vm.state == 1:
            vmDATASTORAGE[str(vm.guid).upper() + '_STATE'] = "BLOCKED"
        elif vm.state == 2:
            vmDATASTORAGE[str(vm.guid).upper() + '_STATE'] = "PAUSED"
        elif vm.state == 3:
            vmDATASTORAGE[str(vm.guid).upper() + '_STATE'] = "SHUTDOWN"
        elif vm.state == 4:
            vmDATASTORAGE[str(vm.guid).upper() + '_STATE'] = "SHUTOFF"
        elif vm.state == 5:
            vmDATASTORAGE[str(vm.guid).upper() + '_STATE'] = "CRASHED"

        # Adding in dummy place holders for network cards.  Will be used for CSV export
        for maxnumnetworkcards in range(1, 9):
            vmDATASTORAGE[str(vm.guid).upper() + '_MACADDRESS' + str(maxnumnetworkcards)] = ''
            vmDATASTORAGE[str(vm.guid).upper() + '_MACADDRESS' + str(maxnumnetworkcards) + 'VLAN'] = ''
    vmDATASTORAGE['VM_TOTALNUMBERVM'] = vmTOTALNUMBER

    # Find MAC address for each network card associated with a VM
    tempcount = 1
    for vm in cluster:  # Need to read through all the VM's on the cluster
        tempvmguid = vm.guid
        tempvmname = queryCLUSTER(tempvmguid + '_NAME').upper()
        networkcardcount = 1  # Stores the number of network cards in a VM
        for l in (vm.netDevs):  # Now we need to read through the network card config.  There could be more than 1 network card so we need to read via a loop
            # temporary variables used when reading the network card config
            tempmacaddress = l.macAddress
            tempvlan = l.vlan
            # print tempmacaddress
            tempconnectionstatus = l.connected
            # Look up the name of the server based on the GUID returned from the network card.
            # The GUID tells use which VM the network card is attached to.

            vmDATASTORAGE['VM' + str(tempcount) + '_MACADDRESS' + str(networkcardcount)] = tempmacaddress
            vmDATASTORAGE['VM' + str(tempcount) + '_MACADDRESS' + str(networkcardcount) + 'VLAN'] = tempvlan
            vmDATASTORAGE[tempvmname + '_MACADDRESS' + str(networkcardcount)] = tempmacaddress
            vmDATASTORAGE[tempvmname + '_MACADDRESS' + str(networkcardcount) + 'VLAN'] = tempvlan
            vmDATASTORAGE[tempvmguid + '_MACADDRESS' + str(networkcardcount)] = tempmacaddress
            vmDATASTORAGE[tempvmguid + '_MACADDRESS' + str(networkcardcount) + 'VLAN'] = tempvlan
            networkcardcount = networkcardcount + 1
        tempcount = tempcount + 1
        vmDATASTORAGE[tempvmname + '_TOTALNETWORKCARDS'] = str((networkcardcount - 1))
        vmDATASTORAGE[tempvmguid + '_TOTALNETWORKCARDS'] = str((networkcardcount - 1))

    # Get number of HDD attached to a VM
    hddcount = 1
    tempcount = 1

    for l in range(1, vmTOTALNUMBER):
        for maxnumdrives in range(1, 9):
            tempvmname = queryCLUSTER('VM' + str(l) + '_NAME').upper()
            # print tempvmname, maxnumdrives
            vmDATASTORAGE[tempvmname + '_HDD' + str(maxnumdrives)] = ''
            vmDATASTORAGE[str(vm.guid).upper() + '_HDD' + str(maxnumdrives)] = ''
            vmDATASTORAGE['VM' + str(l) + '_HDD' + str(maxnumdrives)] = ''

    for vm in cluster:  # Need to read through all the VM's on the cluster
        hddcount = 1
        for l in (
        vm.blockDevs):  # Now we need to read through the HDD config.  There could be more than 1 HDD so we need to read via a loop
            tempvmhddcapacity = l.capacity / 1000 / 1000 / 1000
            tempvmguid = vm.guid
            tempvmhddname = l.name
            tempvmhddtype = l.type
            tempvmname = queryCLUSTER(tempvmguid + '_NAME').upper()

            # Check to see that it is a HDD and not a CDDrive.
            if tempvmhddtype == 2:
                vmDATASTORAGE[tempvmname + '_HDD' + str(hddcount)] = tempvmhddcapacity
                vmDATASTORAGE[tempvmguid + '_HDD' + str(hddcount)] = tempvmhddcapacity
                hddcount = hddcount + 1

        # Store the total number of network cards for each VM.  Useful for referencing later on.
        vmDATASTORAGE[tempvmname + '_TOTALHDD'] = str((hddcount - 1))
        vmDATASTORAGE[tempvmguid + '_TOTALHDD'] = str((hddcount - 1))
        hddcount = 1
        tempcount = tempcount + 1
    return

def GetAllNODEData():
    global nodetotalnumber
    # Read Node Version and Name details
    cluster = client.NodeRead(sessionID, -1, VirDomainFilter())
    nodetotalnumber = 0
    for node in cluster:
        nodetotalnumber = nodetotalnumber + 1  # Total number of nodes in the cluster
        nodeHW['NODE' + str(nodetotalnumber) + '_LANIP'] = str(node.lanIP)
        nodeHW['NODE' + str(nodetotalnumber) + '_GUID'] = str(node.guid)
        nodeHW['NODE' + str(nodetotalnumber) + '_NUMCORES'] = str(node.numCores)
        nodeHW['NODE' + str(nodetotalnumber) + '_NUMTHREADS'] = str(node.numThreads)
        nodeHW['NODE' + str(nodetotalnumber) + '_MEMSIZE'] = str(node.memSize / 1024 / 1024 / 1024 + 1)
        nodeHW['NODE' + str(nodetotalnumber) + '_BACKPLANEIP'] = str(node.backplaneIP)
        nodeHW['NODE' + str(nodetotalnumber) + '_NUMCPU'] = str(node.numCPUs)
        nodeHW['NODE' + str(nodetotalnumber) + '_CAPACITY'] = str(node.capacity / 1000 / 1000 / 1000)
        nodeHW['NODE' + str(nodetotalnumber) + '_CPUHZ'] = str(node.CPUhz / 1000 / 1000)

        # Store all node information by Node IP Address
        nodeHW[str(node.lanIP) + '_LANIP'] = str(node.lanIP)
        nodeHW[str(node.lanIP) + '_GUID'] = str(node.guid)
        nodeHW[str(node.lanIP) + '_NUMCORES'] = str(node.numCores)
        nodeHW[str(node.lanIP) + '_NUMTHREADS'] = str(node.numThreads)
        nodeHW[str(node.lanIP) + '_MEMSIZE'] = str(node.memSize / 1024 / 1024 / 1024 + 1)
        nodeHW[str(node.lanIP) + '_BACKPLANEIP'] = str(node.backplaneIP)
        nodeHW[str(node.lanIP) + '_NUMCPU'] = str(node.numCPUs)
        nodeHW[str(node.lanIP) + '_CAPACITY'] = str(node.capacity / 1000 / 1000 / 1000)
        nodeHW[str(node.lanIP) + '_CPUHZ'] = str(node.CPUhz / 1000 / 1000)

        # Find out how many drives are in the particular node them loop through them
        # pulling off information we need.  The code below will allow for nodes of different number
        # of drives to be read correctly
        totalnodedrives = node.drives  # Number of drives in the node being read
        currentdrive = 1
        for l in totalnodedrives:

            # Information about the disks in each node is stored in a dictonary
            dict = l.disks
            for pos in dict:
                nodeHW['NODE' + str(nodetotalnumber) + '_HDD' + str(currentdrive) + 'CAPACITYGB'] = str(int(dict[pos].capacityBytes) / 1000 / 1000 / 1000)
                nodeHW['NODE' + str(nodetotalnumber) + '_HDD' + str(currentdrive) + 'AVAILABILITY'] = dict[pos].availability
                nodeHW['NODE' + str(nodetotalnumber) + '_HDD' + str(currentdrive) + 'SERIALNUMBER'] = l.serialNumber
                nodeHW['NODE' + str(nodetotalnumber) + '_HDD' + str(currentdrive) + 'USEDGB'] = (l.usedBytes / 1000 / 1000 / 1000)
                nodeHW['NODE' + str(nodetotalnumber) + '_HDD' + str(currentdrive) + 'DRIVEDESCRIPTION'] = l.guid
                nodeHW['NODE' + str(nodetotalnumber) + '_HDD' + str(currentdrive) + 'DRIVEGUID'] = dict[pos].driveGUID

                # Store all drive infomation by IP address
                nodeHW[str(node.lanIP) + '_HDD' + str(currentdrive) + 'CAPACITYGB'] = str(int(dict[pos].capacityBytes) / 1000 / 1000 / 1000)
                nodeHW[str(node.lanIP) + '_HDD' + str(currentdrive) + 'AVAILABILITY'] = dict[pos].availability
                nodeHW[str(node.lanIP) + '_HDD' + str(currentdrive) + 'SERIALNUMBER'] = l.serialNumber
                nodeHW[str(node.lanIP) + '_HDD' + str(currentdrive) + 'USEDGB'] = (l.usedBytes / 1000 / 1000 / 1000)
                nodeHW[str(node.lanIP) + '_HDD' + str(currentdrive) + 'DRIVEDESCRIPTION'] = l.guid
                nodeHW[str(node.lanIP) + '_HDD' + str(currentdrive) + 'DRIVEGUID'] = dict[pos].driveGUID
            currentdrive = currentdrive + 1
            nodeHW[str(node.lanIP) + '_HDDTOTAL'] = str(currentdrive)
    clusterDATA['CLUSTER_TOTALNODES'] = nodetotalnumber

def GetAllCLUSTERData():
    # Any other misc info about the cluster will be gathered here.  The clusterDATA dictionary will also
    # contain
    cluster = client.ClusterRead(sessionID, -1, VirDomainFilter())
    for i in cluster:
        clusterDATA['CLUSTER_VERSION'] = str(i.icosVersion)
        clusterDATA['CLUSTER_NAME'] = i.clusterName

    # Read list of ISO images and whether they are mounted or not.
    domains = client.ISORead(sessionID, VirDomainFilter())
    isonumber = 0
    for iso in domains:
        isonumber = isonumber + 1
        isodata['ISO' + str(isonumber) + '_NAME'] = str(iso.name)
        isodata['ISO' + str(isonumber) + '_SIZE'] = str((iso.size / 1024 / 1024))
        isodata[str(iso.name).upper() + '_SIZE'] = str((iso.size / 1024 / 1024))

        if len(iso.mounts) <> 0:
            isodata['ISO' + str(isonumber) + '_STATUS'] = 'MOUNTED'
            isodata[str(iso.name).upper() + '_STATUS'] = 'MOUNTED'
        else:
            isodata['ISO' + str(isonumber) + '_STATUS'] = 'NOT MOUNTED'
            isodata[str(iso.name).upper() + '_STATUS'] = 'NOT MOUNTED'
        isodata['ISO_TOTALNUMBER'] = isonumber

def queryCLUSTER(*args):
    found = False
    returnedqueryCLUSTER = []  # Contains returned values when we perform a cluster query
    numberofargs = len(args)
    for l in range(0, numberofargs):
        queryFIELD = args[l].upper()
        if queryFIELD in vmDATA.keys():
            returnedqueryCLUSTER.append(vmDATA[queryFIELD])
            found = True
        elif queryFIELD in nodeHW.keys():
            returnedqueryCLUSTER.append(nodeHW[queryFIELD])
            found = True
        elif queryFIELD in clusterDATA.keys():
            returnedqueryCLUSTER.append(clusterDATA[queryFIELD])
            found = True
        elif queryFIELD in isodata.keys():
            returnedqueryCLUSTER.append(isodata[queryFIELD])
            found = True
        if found == True:
            return returnedqueryCLUSTER[0]
        elif found == False:
            return '----'

def resizeFIELDDATA(object, field, auto):
    numberofnodes = queryCLUSTER('CLUSTER_TOTALNODES')
    numberofvm = queryCLUSTER('VM_TOTALNUMBERVM')
    numberofvm = numberofvm
    object = object.upper()
    field = field.upper()

    if object == 'VM':
        maxlength = 0
        # strip away any spaces so that we start with a clean field before we pad with additional spaces
        for l in range(1, numberofvm + 1):
            newstring = vmDATA['VM' + str(l) + '_' + field].rstrip(' ')
            vmDATA['VM' + str(l) + '_' + field] = newstring
        # Find the longest string and store that value in maxlength
        for l in range(1, numberofvm + 1):
            if len(vmDATA['VM' + str(l) + '_' + field]) > maxlength:
                maxlength = len(vmDATA['VM' + str(l) + '_' + field])
        # Now we have the length of the longest string, resize all the other strings to be the same length
        if auto.upper() <> 'AUTO':
            maxlength = int(auto)
        for l in range(1, numberofvm + 1):
            newstring = vmDATA['VM' + str(l) + '_' + field] + ' ' * (
                maxlength - len(vmDATA['VM' + str(l) + '_' + field]))
            vmDATA['VM' + str(l) + '_' + field] = newstring
        return (maxlength)

    if object == 'NODE':
        maxlength = 0
        # strip away any spaces so that we start with a clean field before we pad with additional spaces
        for l in range(1, numberofnodes + 1):
            newstring = nodeHW['NODE' + str(l) + '_' + field].rstrip(' ')
            nodeHW['NODE' + str(l) + '_' + field] = newstring
        # Find the longest string and store that value in maxlength
        for l in range(1, numberofnodes + 1):
            if len(nodeHW['NODE' + str(l) + '_' + field]) > maxlength:
                maxlength = len(nodeHW['NODE' + str(l) + '_' + field])
        # Now we have the length of the longest string, resize all the other strings to be the same length
        if auto.upper() <> 'AUTO':
            maxlength = int(auto)
        for l in range(1, numberofnodes + 1):
            newstring = nodeHW['NODE' + str(l) + '_' + field] + ' ' * (
                maxlength - len(nodeHW['NODE' + str(l) + '_' + field]))
            nodeHW['NODE' + str(l) + '_' + field] = newstring
        return (maxlength)
    if object == 'ISO':
        maxlength = 0
        # strip away any spaces so that we start with a clean field before we pad with additional spaces
        for l in range(1, queryCLUSTER('ISO_TOTALNUMBER')):
            newstring = isodata['ISO' + str(l) + '_' + field].rstrip(' ')
            isodata['ISO' + str(l) + '_' + field] = newstring
        # Find the longest string and store that value in maxlength
        for l in range(1, queryCLUSTER('ISO_TOTALNUMBER') + 1):
            if len(isodata['ISO' + str(l) + '_' + field]) > maxlength:
                maxlength = len(isodata['ISO' + str(l) + '_' + field])
        # Now we have the length of the longest string, resize all the other strings to be the same length
        if auto.upper() <> 'AUTO':
            maxlength = int(auto)
        for l in range(1, queryCLUSTER('ISO_TOTALNUMBER')):
            newstring = isodata['ISO' + str(l) + '_' + field] + ' ' * (
                maxlength - len(isodata['ISO' + str(l) + '_' + field]))
            isodata['ISO' + str(l) + '_' + field] = newstring
        return (maxlength)

def vmEXIST(vmtosearch):
    # Check to see if the source VM exists.  We first check by name and then by GUID
    vmSOURCENAMEFOUND = False
    vmtosearch = vmtosearch.upper()  # Turn search into all uppercase

    # Search by name to find a match
    if vmtosearch.upper() + '_NAME' in vmDATA.keys():
        vmSOURCENAMEFOUND = True
    # Search by GUID to find a match
    if vmtosearch.upper() + '_GUID' == vmDATA.keys():
        vmSOURCENAMEFOUND = True
    return vmSOURCENAMEFOUND

def vmACTION(**args):
    # Actions that we can take on a VM include STOP, START, SHUTDOWN.
    # STOP - power off the VM (not recommended - same effect as hitting the power button)
    # START - Power on a VM
    # SHUTDOWN - Perform a controlled safe shutdown.  Recommended way but only works at login screen.
    if keyEXIST('ACTION', args) == True:
        action = args['ACTION'].upper()
    if keyEXIST('VM', args) == True:
        vm = args['VM'].upper()
        runningonnodeguid = queryCLUSTER(queryCLUSTER(vm + '_runningonnode') + '_GUID')
    if keyEXIST('TAGS', args) == True:
        tags = args['TAGS']
    if keyEXIST('NODE', args) == True:
        node = args['NODE']
    if keyEXIST('DESCRIPTION', args) == True:
        description = args['DESCRIPTION']
        if description == '':
            description = 'SCALE CLI Created SNAPSHOT'

    found = False

    # This section will shutdown VM's based on their TAG as long as no VM name is specified
    if vm == '' and tags <> '':
        for l in range(1, queryCLUSTER('VM_TOTALNUMBERVM')):  # Get the number of VM's on the cluster
            tempvmtag = queryCLUSTER('VM' + str(l) + '_TAGS')  # Get the tags associated with each VM
            tempguid = queryCLUSTER('VM' + str(l) + '_GUID')  # Get the VM GUID which will be use to shutdown the VM
            tempvmtag = tempvmtag.split(",")  # If a VM has multiple tags, split them at the comma and store them in a list
            for t in range(0,len(tempvmtag)):  # Run though the tag list and perform the action based on the tag we find
                if tempvmtag[t].upper() == tags.upper():
                    if action == "STOP":
                        result = client.VirDomainAction(sessionID, [VirDomainActionDescription(virDomainGUID=tempguid, actionType=VirDomainActionType.STOP)])
                    if action == "START":
                        result = client.VirDomainAction(sessionID, [VirDomainActionDescription(virDomainGUID=tempguid, actionType=VirDomainActionType.START)])
                    if action == "SHUTDOWN":
                        result = client.VirDomainAction(sessionID, [VirDomainActionDescription(virDomainGUID=tempguid, actionType=VirDomainActionType.SHUTDOWN)])
        return (0)

    # Perform an action on a single VM
    if vm <> '' and vmEXIST(vm) == True:
        found = True
        tempguid = vmDATA[vm + '_GUID']
        # We can now STOP (simulate power button being pressed) , START or SHUTDOWN (Graceful shutdown) a VM
        if action == "STOP":
            result = client.VirDomainAction(sessionID, [VirDomainActionDescription(virDomainGUID=tempguid, actionType=VirDomainActionType.STOP)])
        if action == "START":
            result = client.VirDomainAction(sessionID, [VirDomainActionDescription(virDomainGUID=tempguid, actionType=VirDomainActionType.START)])
        if action == "SHUTDOWN":
            result = client.VirDomainAction(sessionID, [VirDomainActionDescription(virDomainGUID=tempguid, actionType=VirDomainActionType.SHUTDOWN)])
        if action == "LIVEMIGRATE" and runningonnodeguid <> queryCLUSTER('NODE' + str(node) + '_GUID'):
            result = client.VirDomainAction(sessionID, [VirDomainActionDescription(virDomainGUID=tempguid, actionType=VirDomainActionType.LIVEMIGRATE,nodeGUID=queryCLUSTER('NODE' + str(node) + '_GUID'))])
        elif runningonnodeguid == queryCLUSTER('NODE' + str(node) + '_GUID'):
            print 'VM already on NODE:', node
            # return(100)
        if action == "SNAPSHOT":
            result = client.VirDomainSnapshotCreate(sessionID, tempguid, description)
        if action == "EXPORT":
            result = client.VirDomainExport(sessionID, target=[VirDomainExportTarget(pathURI='smb://sysadmin:J1amboree1024@192.168.1.221/exportvm', format='', definitionFileName='test', compress=True)],sourceVirDomainGUID='27cc77eb-0db0-4da3-a82a-dcf270961c7b', snapshotGUID='',vmTemplate='')

    # if the VM doesnt exist display error message
    if found == False:
        print "Error - Unable to find VM.  Check the name"
        sys.exit(100)
    return (0)

def vmUPDATEDESCRIPTION(**args):
    # Change the description on a VM
    sourcevm = ''
    if keyEXIST('VM', args) == True:
        sourcevm = args['VM']
    if keyEXIST('DESCRIPTION', args) == True:
        newdescription = args['DESCRIPTION']
    if vmEXIST(sourcevm) == True:
        # Update info for a VM
        tempguid = queryCLUSTER(sourcevm + '_GUID')
        tempvm = client.VirDomainRead(sessionID, -1, VirDomainFilter(virDomainGUID=tempguid))[0]
        tempvm.description = newdescription
        result = client.VirDomainUpdate(sessionID, tempvm)
        return (0)
    else:
        print 'Error: VM not found'
        return (100)

def keyEXIST(key, dictionarytocheck):
    found = False
    if key in dictionarytocheck.keys():
        found = True
    return found

def vmCLONE(**args):
    vmcreatedata = {}
    numclones = 1
    clonetags = ''
    sourcevm = ''
    startnum = 1
    numberofargs = len(args)

    if keyEXIST('VM', args) == True:
        sourcevm = args['VM']
    if keyEXIST('VLAN', args) == True:
        vmcreatevlan = int(args['VLAN'])
    if keyEXIST('DESCRIPTION', args) == True:
        clonedescription = args['DESCRIPTION']
    if keyEXIST('TAGS', args) == True:
        clonetags = args['TAGS']
    if keyEXIST('NUMBER', args) == True:
        vmcreatenumber = int(args['NUMBER'])
    if keyEXIST('STARTNUM', args) == True:
        vmcreatestartnum = int(args['STARTNUM'])
    if keyEXIST('DESTVM', args) == True:
        destinationvm = args['DESTVM']

    # sourcevm, destinationvm, numclones, startnum, clonedescription, clonetags
    sourcevm = sourcevm.upper()
    readyclones = []

    # Check to see if the source VM exists
    if vmEXIST(sourcevm) == False:
        print "Source VM not found"
        sys.exit(100)
    sourcevmguid = vmDATA[sourcevm + '_GUID']  # VM doesn't exist so we need to find the source VM GUID

    # Now we check that an existing VM doesn't have the same name as the cloned named
    # Need to take into account that the clones VM name will have a number appended to it.

    for l in range(vmcreatestartnum, (vmcreatestartnum + vmcreatenumber)):
        if destinationvm.upper() + str(l) + '_NAME' in vmDATA.keys():
            print "VM Name: " + destinationvm + str(l) + " already exists.  Please choose another name"
            sys.exit(100)

    for l in range(vmcreatestartnum, (vmcreatestartnum + vmcreatenumber)):
        template = VirDomain(name=destinationvm + str(l), description=clonedescription, tags=clonetags)
        result = client.VirDomainClone(sessionID, sourcevmguid, template)
        vmCLONEDomain = client.VirDomainRead(sessionID, 0, VirDomainFilter(virDomainGUID=result.createdGUID))

        # Wait until the CLONE is created before we create another one.  Code below checks to see if the length of the
        # VM properties is more than zero.
        vmCLONEFINISHED = False
        while vmCLONEFINISHED == False:
            CLONESTATUS = client.TaskTagStatusRead(sessionID, TaskTagFilter(taskTag=result.taskTag))
            for l in CLONESTATUS:
                if l.progressPercent == 100:
                    vmCLONEFINISHED = True
    return (0)

def vmCREATE(**args):
    vmcreatedata = {}
    vmcreatemaxhddsize = (8000 * 1000 * 1000 * 1000)
    vmcreatenumber = 1
    vmcreatetags = ''
    vmcreatehdd1 = 0
    vmcreatehdd2 = 0
    vmcreatehdd3 = 0
    vmcreatehdd4 = 0
    vmcreatehdd5 = 0
    vmcreatehdd6 = 0
    vmcreatehdd7 = 0
    vmcreatehdd8 = 0
    vmcreatename = ''
    vmcreatestartnumber = 0
    numberofargs = len(args)

    if keyEXIST('VM', args) == True:
        vmcreatename = args['VM']
    if keyEXIST('VCPU', args) == True:
        vmcreatevcpu = int(args['VCPU'])
    if keyEXIST('RAM', args) == True:
        vmcreateram = int(args['RAM']) * 1024 * 1024 * 1024
    if keyEXIST('VLAN', args) == True:
        vmcreatevlan = int(args['VLAN'])
    if keyEXIST('DESCRIPTION', args) == True:
        vmcreatedescription = args['DESCRIPTION']
    if keyEXIST('TAGS', args) == True:
        vmcreatetags = args['TAGS']
    if keyEXIST('NUMBER', args) == True:
        vmcreatenumber = int(args['NUMBER'])
    if keyEXIST('STARTNUM', args) == True:
        vmcreatestartnum = int(args['STARTNUM'])

    # The maximum size of a single HDD in a VM is 8TB.  There is a maximum of 8 HDD limit as as well.
    if keyEXIST('HDD1', args) == True:
        vmcreatehdd1 = int(args['HDD1']) * 1000 * 1000 * 1000
        if vmcreatehdd1 > vmcreatemaxhddsize:
            print "Error - HDD1 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)
    if keyEXIST('HDD2', args) == True:
        vmcreatehdd2 = int(args['HDD2']) * 1000 * 1000 * 1000
        if vmcreatehdd2 > vmcreatemaxhddsize:
            print "Error - HDD2 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)
    if keyEXIST('HDD3', args) == True:
        vmcreatehdd3 = int(args['HDD3']) * 1000 * 1000 * 1000
        if vmcreatehdd3 > vmcreatemaxhddsize:
            print "Error - HDD3 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)
    if keyEXIST('HDD4', args) == True:
        vmcreatehdd4 = int(args['HDD4']) * 1000 * 1000 * 1000
        if vmcreatehdd4 > vmcreatemaxhddsize:
            print "Error - HDD4 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)
    if keyEXIST('HDD5', args) == True:
        vmcreatehdd5 = int(args['HDD5']) * 1000 * 1000 * 1000
        if vmcreatehdd5 > vmcreatemaxhddsize:
            print "Error - HDD5 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)
    if keyEXIST('HDD6', args) == True:
        vmcreatehdd6 = int(args['HDD6']) * 1000 * 1000 * 1000
        if vmcreatehdd6 > vmcreatemaxhddsize:
            print "Error - HDD6 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)
    if keyEXIST('HDD7', args) == True:
        vmcreatehdd7 = int(args['HDD7']) * 1000 * 1000 * 1000
        if vmcreatehdd7 > vmcreatemaxhddsize:
            print "Error - HDD7 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)
    if keyEXIST('HDD8', args) == True:
        vmcreatehdd8 = int(args['HDD8']) * 1000 * 1000 * 1000
        if vmcreatehdd8 > vmcreatemaxhddsize:
            print "Error - HDD8 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)

    # Create a VM.  Variables below make it easy to see how the command is built up.  Don't change any of them!!

    # We checked that the HDD sizes are ok, now check that the VM doesn't already exist.
    if vmEXIST(vmcreatename) == True:
        print "Error - Duplicate VM Name"
        sys.exit(100)

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

    # If we just want to create a single VM, use the code below.  It's pretty sloppy but does allow us to create a VM
    # with 1 to 8 HDD attached.  All VM's by default have 2 x CDROM drives attached

    if vmcreatenumber == 1:
        if vmcreatehdd1 <> 0 and vmcreatehdd2 == 0 and vmcreatehdd3 == 0 and vmcreatehdd4 == 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                        blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,allocation=0,cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=9, capacity=0,allocation=0,cacheMode=WRITETHROUGH,type=IDE_CDROM, physical=0)]))
        if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 == 0 and vmcreatehdd4 == 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                        blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
        if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 == 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                        blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
        if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                        blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
        if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                        blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
        if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 <> 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                        blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=5, capacity=vmcreatehdd6,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
        if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 <> 0 and vmcreatehdd7 <> 0 and vmcreatehdd8 == 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                        blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=5, capacity=vmcreatehdd6,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=6, capacity=vmcreatehdd7,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
        if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 <> 0 and vmcreatehdd7 <> 0 and vmcreatehdd8 <> 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                        blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=5, capacity=vmcreatehdd6,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=6, capacity=vmcreatehdd7,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=7, capacity=vmcreatehdd8,allocation=0, cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
        return (0)

    # So now we want to create multiple VM's.  Same code as above.  Ugly but it works.
    if vmcreatenumber > 1:
        for l in range(vmcreatestartnum, (vmcreatestartnum + vmcreatenumber)):
            if vmEXIST((vmcreatename + str(l))) == True:
                print "Error - Duplicate VM Name"
                sys.exit(100)

        for l in range(vmcreatestartnum, (vmcreatestartnum + vmcreatenumber)):
            if vmcreatehdd1 <> 0 and vmcreatehdd2 == 0 and vmcreatehdd3 == 0 and vmcreatehdd4 == 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
                client.VirDomainCreate(sessionID,VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",
                                                 description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,tags=vmcreatetags,
                                                 netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                 blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,cacheMode=WRITETHROUGH,type=VIRTIO_DISK, physical=0),
                                                            VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
            if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 == 0 and vmcreatehdd4 == 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
                client.VirDomainCreate(sessionID,VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",
                                                 description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,tags=vmcreatetags,
                                                 netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                 blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
            if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 == 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
                client.VirDomainCreate(sessionID,VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,
                                                 tags=vmcreatetags,netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                 blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
            if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
                client.VirDomainCreate(sessionID,VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,
                                                 tags=vmcreatetags,netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                 blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
            if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
                client.VirDomainCreate(sessionID,VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,
                                                 tags=vmcreatetags,netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                 blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
            if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 <> 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
                client.VirDomainCreate(sessionID,VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,
                                                 tags=vmcreatetags,netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                 blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=5, capacity=vmcreatehdd6, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
            if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 <> 0 and vmcreatehdd7 <> 0 and vmcreatehdd8 == 0:
                client.VirDomainCreate(sessionID,VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,
                                                 tags=vmcreatetags,netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                 blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=5, capacity=vmcreatehdd6, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=6, capacity=vmcreatehdd7, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
            if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 <> 0 and vmcreatehdd7 <> 0 and vmcreatehdd8 <> 0:
                client.VirDomainCreate(sessionID,VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,
                                                 tags=vmcreatetags,netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,type=VIRTIO)],
                                                 blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=5, capacity=vmcreatehdd6, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=6, capacity=vmcreatehdd7, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=7, capacity=vmcreatehdd8, allocation=0,cacheMode=WRITETHROUGH, type=VIRTIO_DISK,physical=0),
                                                            VirDomainBlockDevice(slot=9, capacity=0, allocation=0,cacheMode=WRITETHROUGH, type=IDE_CDROM,physical=0)]))
        return (0)

def queryCOMMANDLINE(*args):
    # Start of the command line parser.  Have decided to write my own as 3rd parties were not good enough or very limited
    # in how you could use them.
    global exportfile, monitoring

    cmdline = {
        'VM': '',
        'IP': '',
        'CLUSTERUSERNAME': '',
        'CLUSTERPASSWORD': '',
        'ACTION': '',
        'HDD1': '0',
        'HDD2': '0',
        'HDD3': '0',
        'HDD4': '0',
        'HDD5': '0',
        'HDD6': '0',
        'HDD7': '0',
        'HDD8': '0',
        'VCPU': '',
        'RAM': '0',
        'DESCRIPTION': '',
        'STARTNUM': '1',
        'NUMBER': '1',
        'VLAN': '0',
        'TAGS': '',
        'FIELD': '',
        'DESTVM': '',
        'NODE': ''
    }
    # If we are not calling this function internally and are instead calling it via the command line
    # we need to convert the command line into a list and then back into a tuple which can then be parsed
    # as if we were calling it internally.
    cmdlinelist = []
    if args[0].upper() == 'PARSECMDLINE':
        for l in range(1, len(sys.argv)):
            cmdlinelist.append(sys.argv[l])
        args = tuple(cmdlinelist)

    numberofargs = len(args)
    if numberofargs < 2 or args[0].upper() == '/HELP' or args[0].upper() == '/H':
        displayHELP()
        return (0)

    for l in range(0, numberofargs):
        fullcmdline = args[l].split(':')
        cmdlineoption = fullcmdline[0].upper().strip('/')
        cmdlinevalue = fullcmdline[1].strip('"')
        cmdline[cmdlineoption.strip('/')] = cmdlinevalue

    vmname = cmdline['VM'].strip('"')
    ip = cmdline['IP']
    clusterusername = cmdline['CLUSTERUSERNAME']
    clusterpassword = cmdline['CLUSTERPASSWORD']
    action = cmdline['ACTION'].upper()
    hdd1 = cmdline['HDD1']
    hdd2 = cmdline['HDD2']
    hdd3 = cmdline['HDD3']
    hdd4 = cmdline['HDD4']
    hdd5 = cmdline['HDD5']
    hdd6 = cmdline['HDD6']
    hdd7 = cmdline['HDD7']
    hdd8 = cmdline['HDD8']
    vcpu = cmdline['VCPU']
    ram = cmdline['RAM']
    description = cmdline['DESCRIPTION']
    vmcreatestartnum = cmdline['STARTNUM']
    vmcreatestartnum = cmdline['NUMBER']
    vlan = cmdline['VLAN']
    tags = cmdline['TAGS']
    node = cmdline['NODE']
    queryfield = cmdline['FIELD'].upper()
    destvm = cmdline['DESTVM']

    OpenConnectionToCluster(ip, clusterusername,clusterpassword)    # Initiate connection to the cluster.  Must be 1st thing we do
    GetAllVMData(vmDATA)                                            # Read everything about our VM's and store them in a dictionary structure
    GetAllVMData(vmDATAHISTORY)                                     # Read everything about our VM's and store them in a dictionary structure
    GetAllNODEData()                                                # Read everything about our Nodes in the cluster and store them in a dictionary structure
    GetAllCLUSTERData()                                             # Read misc items about the entire cluster and store them in a dictionary structure

    if action in {'START', 'STOP', 'SHUTDOWN', 'LIVEMIGRATE', 'SNAPSHOT', 'EXPORT'}:
        vmACTION(**cmdline)
        return ()
    if action == 'QUERYCLUSTER':
        print queryCLUSTER(queryfield)
        return ()
    if action == 'CREATEVM':
        vmCREATE(**cmdline)
        return ()
    if action == 'CLONEVM':
        vmCLONE(**cmdline)
        return ()
    if action == 'UPDATEDESCRIPTION':
        vmUPDATEDESCRIPTION(**cmdline)
        return (0)
    if action == 'SHOWVM':
        showVM()
        return ()
    if action == 'SHOWNODE':
        showNODE()
        return ()
    if action == 'SHOWISO':
        showISO()
        return ()
    return ()

def queryWMIC(server, username, password, wmic):
    result = []
    cmd = 'WMIC /node:' + server + ' /user:' + username + ' /password:' + password + ' ' + wmic
    response = os.popen(cmd + ' 2>&1', 'r').read().strip('').split("\r\n")
    for load in response[1:]:
        result.append(load)
    return result[0]

def vmUPDATEDESCRIPTIONWMIC(vmname, ipaddress, usertext, username, password, wmic):
    updatetext = ''
    if wmic.upper() == 'CPU GET LOADPERCENTAGE':
        updatetext = 'CPU:' + str(queryWMIC(ipaddress, username, password, 'CPU GET LoadPercentage')).strip(' ') + '%'

    if wmic.upper() == 'OS GET FREEPHYSICALMEMORY':
        updatetext = updatetext + 'RAM:' + str(
            int(queryWMIC(ipaddress, username, password, 'OS get FreePhysicalMemory')) / 1024) + 'mb'

    if wmic.upper() == 'LOGICALDISK C: GET FREESPACEOS':
        updatetext = updatetext + 'HDD1:' + str(
            int(queryWMIC(ipaddress, username, password, 'logicaldisk c: get FreeSpace')) / 1024 / 1024 / 1024) + 'gb'

    if wmic.upper() == 'NICCONFIG WHERE IPENABLED=TRUE GET IPADDRESS':
        updatetext = updatetext + str(
            queryWMIC(ipaddress, username, password, 'NICCONFIG WHERE IPEnabled=true GET IPAddress')).strip(' {}"')

    vmUPDATEDESCRIPTION(vmname, usertext + 'IP:' + str(queryWMIC(ipaddress, username, password, 'NICCONFIG WHERE IPEnabled=true GET IPAddress')).strip(' {}"'))
    # vmUPDATEDESCRIPTION(vmname, usertext + 'IP:' + str(queryWMIC(ipaddress, username, password, 'NICCONFIG WHERE IPEnabled=true GET IPAddress')).strip(' {}"') +
    #                    ',  CPU:' + str(queryWMIC(ipaddress, username, password, 'CPU GET LoadPercentage')).strip(' ') + '%' +
    #                    ',  RAM:' + str(int(queryWMIC(ipaddress, username, password, 'OS get FreePhysicalMemory')) / 1024) + 'mb' +
    #                    ',  HDD1:' + str(int(queryWMIC(ipaddress, username, password, 'logicaldisk c: get FreeSpace')) / 1024 / 1024 / 1024) + 'gb')

    return

def makeCSV(*args):
    numberofargs = len(args)  # Get number of arguments
    csvstring = ''  # New CSV formatted string stored here
    for l in range(0, numberofargs):
        csvstring = csvstring + '"' + str(args[l]) + '"' + ','  # Add in quotes around all fields
    return csvstring[:-1]  # Return the final CSV formatted string minus the last character which is a comma

def recordeventlogVM(exportfilename, timeout, pause, tempverbose):
    # global vmDATAHISTORY,vmDATA
    print 'Reading Live VM Data and storing into historical data'
    GetAllVMData(vmDATAHISTORY)
    lastreadexportstring = {}
    verbose = False
    nochange = True
    clearscreen = False
    if pause == 0:
        interval = 1
    if timeout == 0:
        timeout = 3153600000  # Timeout set to expire in 100 years time if we want continuous
    tempverbose = tempverbose.split('=')
    if tempverbose[1].upper() == 'YES':
        verbose = True
    screen = terminal.get_terminal(conEmu=False)
    screen.set_color(terminal.colors["WHITE"], terminal.colors["BLUE"])
    screen.clear()

    timeout = time.time() + 60 * timeout  # Timeout set to expire x minutes time from now
    while True:
        GetAllVMData(vmDATAHISTORY)
        numberofvm = queryCLUSTER('VM_TOTALNUMBERVM')
        if clearscreen == True:
            screen.clear()
            clearscreen = False
        screen.set_title("SCALE COMPUTING - Event Log Monitor - Monitoring " + str(numberofvm) + " VM's")
        GetAllVMData(vmDATA)  # Read everything about our VM's and store them in a dictionary structure
        x = 1
        y = 5

        for l in range(1, numberofvm):
            temptime = time.localtime()
            year = str(temptime.tm_year)
            month = str(temptime.tm_mon)
            day = str(temptime.tm_mday)
            hour = str(temptime.tm_hour)
            minute = str(temptime.tm_min)
            second = str(temptime.tm_sec)
            daysintoyear = str(temptime.tm_yday)
            currenttime = hour + ':' + minute + ':' + second
            currentdate = day + '/' + month + '/' + year
            tempvmname = queryCLUSTER('VM' + str(l) + '_NAME').upper()

            if tempvmname + '_NAME' in vmDATAHISTORY.keys():
                livevm = makeCSV(vmDATA[tempvmname + '_GUID'], vmDATA[tempvmname + '_NAME'],
                                 vmDATA[tempvmname + '_VCPU'], vmDATA[tempvmname + '_MEMORY'],
                                 vmDATA[tempvmname + '_RUNNINGONNODE'], vmDATA[tempvmname + '_DESCRIPTION'],
                                 vmDATA[tempvmname + '_TAGS'], vmDATA[tempvmname + '_STATE'],
                                 vmDATA[tempvmname + '_HDD1'], vmDATA[tempvmname + '_HDD2'],
                                 vmDATA[tempvmname + '_HDD3'], vmDATA[tempvmname + '_HDD4'],
                                 vmDATA[tempvmname + '_HDD5'], vmDATA[tempvmname + '_HDD6'],
                                 vmDATA[tempvmname + '_HDD7'], vmDATA[tempvmname + '_HDD8'],
                                 vmDATA[tempvmname + '_MACADDRESS1'], vmDATA[tempvmname + '_MACADDRESS1VLAN'],
                                 vmDATA[tempvmname + '_MACADDRESS2'], vmDATA[tempvmname + '_MACADDRESS2VLAN'],
                                 vmDATA[tempvmname + '_MACADDRESS3'], vmDATA[tempvmname + '_MACADDRESS3VLAN'],
                                 vmDATA[tempvmname + '_MACADDRESS4'], vmDATA[tempvmname + '_MACADDRESS4VLAN'],
                                 vmDATA[tempvmname + '_MACADDRESS5'], vmDATA[tempvmname + '_MACADDRESS5VLAN'],
                                 vmDATA[tempvmname + '_MACADDRESS6'], vmDATA[tempvmname + '_MACADDRESS6VLAN'],
                                 vmDATA[tempvmname + '_MACADDRESS7'], vmDATA[tempvmname + '_MACADDRESS7VLAN'],
                                 vmDATA[tempvmname + '_MACADDRESS8'], vmDATA[tempvmname + '_MACADDRESS8VLAN'])

                livevmhistory = makeCSV(vmDATAHISTORY[tempvmname + '_GUID'], vmDATAHISTORY[tempvmname + '_NAME'],
                                        vmDATAHISTORY[tempvmname + '_VCPU'], vmDATAHISTORY[tempvmname + '_MEMORY'],
                                        vmDATAHISTORY[tempvmname + '_RUNNINGONNODE'],
                                        vmDATAHISTORY[tempvmname + '_DESCRIPTION'], vmDATAHISTORY[tempvmname + '_TAGS'],
                                        vmDATAHISTORY[tempvmname + '_STATE'],
                                        vmDATAHISTORY[tempvmname + '_HDD1'], vmDATAHISTORY[tempvmname + '_HDD2'],
                                        vmDATAHISTORY[tempvmname + '_HDD3'], vmDATAHISTORY[tempvmname + '_HDD4'],
                                        vmDATAHISTORY[tempvmname + '_HDD5'], vmDATAHISTORY[tempvmname + '_HDD6'],
                                        vmDATAHISTORY[tempvmname + '_HDD7'], vmDATAHISTORY[tempvmname + '_HDD8'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS1'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS1VLAN'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS2'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS2VLAN'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS3'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS3VLAN'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS4'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS4VLAN'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS5'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS5VLAN'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS6'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS6VLAN'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS7'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS7VLAN'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS8'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS8VLAN'])

                if livevm == livevmhistory:
                    # os.system('cls')

                    screen.set_color(fg=Yellow, bk=Blue)
                    screen.print_at(1, 5, 'GUID                                   VM                                 vCPU RAM NODE            STATE    DESCRIPTION')
                    screen.set_color(fg=White, bk=Blue)
                    screen.print_at(x, y + 1, vmDATAHISTORY[tempvmname + '_GUID'])
                    screen.print_at(x + 39, y + 1, vmDATAHISTORY[tempvmname + '_NAME'])
                    screen.print_at(x + 74, y + 1, vmDATAHISTORY[tempvmname + '_VCPU'])
                    screen.print_at(x + 79, y + 1, vmDATAHISTORY[tempvmname + '_MEMORY'])
                    screen.print_at(x + 83, y + 1, vmDATAHISTORY[tempvmname + '_RUNNINGONNODE'])
                    if vmDATAHISTORY[tempvmname + '_STATE'] == 'SHUTOFF':
                        screen.set_color(fg=White, bk=Red)
                        screen.print_at(x + 99, y + 1, vmDATAHISTORY[tempvmname + '_STATE'])
                        screen.set_color(fg=White, bk=Blue)
                    else:
                        screen.set_color(fg=White, bk=Green)
                        screen.print_at(x + 99, y + 1, vmDATAHISTORY[tempvmname + '_STATE'])
                        screen.set_color(fg=White, bk=Blue)
                    screen.print_at(x + 108, y + 1, vmDATAHISTORY[tempvmname + '_DESCRIPTION'])
                    screen.print_at(x, 5 + numberofvm, '-' * 190)
                    print''
                    if y < (5 + numberofvm):
                        y = y + 1
                else:
                    vmDATAHISTORY[tempvmname + '_GUID'] = vmDATA[tempvmname + '_GUID']
                    vmDATAHISTORY[tempvmname + '_NAME'] = vmDATA[tempvmname + '_NAME']
                    vmDATAHISTORY[tempvmname + '_VCPU'] = vmDATA[tempvmname + '_VCPU']
                    vmDATAHISTORY[tempvmname + '_MEMORY'] = vmDATA[tempvmname + '_MEMORY']
                    vmDATAHISTORY[tempvmname + '_RUNNINGONNODE'] = vmDATA[tempvmname + '_RUNNINGONNODE']
                    vmDATAHISTORY[tempvmname + '_DESCRIPTION'] = vmDATA[tempvmname + '_DESCRIPTION']
                    vmDATAHISTORY[tempvmname + '_TAGS'] = vmDATA[tempvmname + '_TAGS']
                    vmDATAHISTORY[tempvmname + '_STATE'] = vmDATA[tempvmname + '_STATE']
                    vmDATAHISTORY[tempvmname + '_HDD1'] = vmDATA[tempvmname + '_HDD1']
                    vmDATAHISTORY[tempvmname + '_HDD2'] = vmDATA[tempvmname + '_HDD2']
                    vmDATAHISTORY[tempvmname + '_HDD3'] = vmDATA[tempvmname + '_HDD3']
                    vmDATAHISTORY[tempvmname + '_HDD4'] = vmDATA[tempvmname + '_HDD4']
                    vmDATAHISTORY[tempvmname + '_HDD5'] = vmDATA[tempvmname + '_HDD5']
                    vmDATAHISTORY[tempvmname + '_HDD6'] = vmDATA[tempvmname + '_HDD6']
                    vmDATAHISTORY[tempvmname + '_HDD7'] = vmDATA[tempvmname + '_HDD7']
                    vmDATAHISTORY[tempvmname + '_HDD8'] = vmDATA[tempvmname + '_HDD8']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS1'] = vmDATA[tempvmname + '_MACADDRESS1']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS2'] = vmDATA[tempvmname + '_MACADDRESS2']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS3'] = vmDATA[tempvmname + '_MACADDRESS3']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS4'] = vmDATA[tempvmname + '_MACADDRESS4']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS5'] = vmDATA[tempvmname + '_MACADDRESS5']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS6'] = vmDATA[tempvmname + '_MACADDRESS6']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS7'] = vmDATA[tempvmname + '_MACADDRESS7']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS8'] = vmDATA[tempvmname + '_MACADDRESS8']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS1VLAN'] = vmDATA[tempvmname + '_MACADDRESS1VLAN']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS2VLAN'] = vmDATA[tempvmname + '_MACADDRESS2VLAN']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS3VLAN'] = vmDATA[tempvmname + '_MACADDRESS3VLAN']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS4VLAN'] = vmDATA[tempvmname + '_MACADDRESS4VLAN']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS5VLAN'] = vmDATA[tempvmname + '_MACADDRESS5VLAN']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS6VLAN'] = vmDATA[tempvmname + '_MACADDRESS6VLAN']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS7VLAN'] = vmDATA[tempvmname + '_MACADDRESS7VLAN']
                    vmDATAHISTORY[tempvmname + '_MACADDRESS8VLAN'] = vmDATA[tempvmname + '_MACADDRESS8VLAN']

                    file = open(exportfilename, 'a')
                    csvdata = makeCSV(currentdate, currenttime) + ',' + livevm
                    screen.set_color(fg=Yellow, bk=Blue)
                    screen.print_at(1, 8 + numberofvm, 'Writing new data......')
                    screen.set_color(fg=White, bk=Blue)
                    screen.print_at(x, 10 + numberofvm, csvdata)
                    file.write(csvdata + '\n')
                    file.close()
                    clearscreen = True

            else:
                vmDATAHISTORY[tempvmname + '_GUID'] = vmDATA[tempvmname + '_GUID']
                vmDATAHISTORY[tempvmname + '_NAME'] = vmDATA[tempvmname + '_NAME']
                vmDATAHISTORY[tempvmname + '_VCPU'] = vmDATA[tempvmname + '_VCPU']
                vmDATAHISTORY[tempvmname + '_MEMORY'] = vmDATA[tempvmname + '_MEMORY']
                vmDATAHISTORY[tempvmname + '_RUNNINGONNODE'] = vmDATA[tempvmname + '_RUNNINGONNODE']
                vmDATAHISTORY[tempvmname + '_DESCRIPTION'] = vmDATA[tempvmname + '_DESCRIPTION']
                vmDATAHISTORY[tempvmname + '_TAGS'] = vmDATA[tempvmname + '_TAGS']
                vmDATAHISTORY[tempvmname + '_STATE'] = vmDATA[tempvmname + '_STATE']
                vmDATAHISTORY[tempvmname + '_HDD1'] = vmDATA[tempvmname + '_HDD1']
                vmDATAHISTORY[tempvmname + '_HDD2'] = vmDATA[tempvmname + '_HDD2']
                vmDATAHISTORY[tempvmname + '_HDD3'] = vmDATA[tempvmname + '_HDD3']
                vmDATAHISTORY[tempvmname + '_HDD4'] = vmDATA[tempvmname + '_HDD4']
                vmDATAHISTORY[tempvmname + '_HDD5'] = vmDATA[tempvmname + '_HDD5']
                vmDATAHISTORY[tempvmname + '_HDD6'] = vmDATA[tempvmname + '_HDD6']
                vmDATAHISTORY[tempvmname + '_HDD7'] = vmDATA[tempvmname + '_HDD7']
                vmDATAHISTORY[tempvmname + '_HDD8'] = vmDATA[tempvmname + '_HDD8']
                vmDATAHISTORY[tempvmname + '_MACADDRESS1'] = vmDATA[tempvmname + '_MACADDRESS1']
                vmDATAHISTORY[tempvmname + '_MACADDRESS2'] = vmDATA[tempvmname + '_MACADDRESS2']
                vmDATAHISTORY[tempvmname + '_MACADDRESS3'] = vmDATA[tempvmname + '_MACADDRESS3']
                vmDATAHISTORY[tempvmname + '_MACADDRESS4'] = vmDATA[tempvmname + '_MACADDRESS4']
                vmDATAHISTORY[tempvmname + '_MACADDRESS5'] = vmDATA[tempvmname + '_MACADDRESS5']
                vmDATAHISTORY[tempvmname + '_MACADDRESS6'] = vmDATA[tempvmname + '_MACADDRESS6']
                vmDATAHISTORY[tempvmname + '_MACADDRESS7'] = vmDATA[tempvmname + '_MACADDRESS7']
                vmDATAHISTORY[tempvmname + '_MACADDRESS8'] = vmDATA[tempvmname + '_MACADDRESS8']
                vmDATAHISTORY[tempvmname + '_MACADDRESS1VLAN'] = vmDATA[tempvmname + '_MACADDRESS1VLAN']
                vmDATAHISTORY[tempvmname + '_MACADDRESS2VLAN'] = vmDATA[tempvmname + '_MACADDRESS2VLAN']
                vmDATAHISTORY[tempvmname + '_MACADDRESS3VLAN'] = vmDATA[tempvmname + '_MACADDRESS3VLAN']
                vmDATAHISTORY[tempvmname + '_MACADDRESS4VLAN'] = vmDATA[tempvmname + '_MACADDRESS4VLAN']
                vmDATAHISTORY[tempvmname + '_MACADDRESS5VLAN'] = vmDATA[tempvmname + '_MACADDRESS5VLAN']
                vmDATAHISTORY[tempvmname + '_MACADDRESS6VLAN'] = vmDATA[tempvmname + '_MACADDRESS6VLAN']
                vmDATAHISTORY[tempvmname + '_MACADDRESS7VLAN'] = vmDATA[tempvmname + '_MACADDRESS7VLAN']
                vmDATAHISTORY[tempvmname + '_MACADDRESS8VLAN'] = vmDATA[tempvmname + '_MACADDRESS8VLAN']

                livevmhistory = makeCSV(vmDATAHISTORY[tempvmname + '_GUID'], vmDATAHISTORY[tempvmname + '_NAME'],
                                        vmDATAHISTORY[tempvmname + '_VCPU'], vmDATAHISTORY[tempvmname + '_MEMORY'],
                                        vmDATAHISTORY[tempvmname + '_RUNNINGONNODE'],
                                        vmDATAHISTORY[tempvmname + '_DESCRIPTION'], vmDATAHISTORY[tempvmname + '_TAGS'],
                                        vmDATAHISTORY[tempvmname + '_STATE'],
                                        vmDATAHISTORY[tempvmname + '_HDD1'], vmDATAHISTORY[tempvmname + '_HDD2'],
                                        vmDATAHISTORY[tempvmname + '_HDD3'], vmDATAHISTORY[tempvmname + '_HDD4'],
                                        vmDATAHISTORY[tempvmname + '_HDD5'], vmDATAHISTORY[tempvmname + '_HDD6'],
                                        vmDATAHISTORY[tempvmname + '_HDD7'], vmDATAHISTORY[tempvmname + '_HDD8'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS1'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS1VLAN'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS2'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS2VLAN'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS3'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS3VLAN'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS4'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS4VLAN'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS5'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS5VLAN'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS6'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS6VLAN'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS7'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS7VLAN'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS8'],
                                        vmDATAHISTORY[tempvmname + '_MACADDRESS8VLAN'])

                file = open(exportfilename, 'a')
                csvdata = makeCSV(currentdate, currenttime) + ',' + livevm
                print 'New data detected. Writing new data.........'
                print csvdata
                file.write(csvdata + '\n')
                file.close()
                print livevmhistory
                clearscreen = True

        time.sleep(pause)  # delays for x seconds
        if time.time() > timeout:
            break

def write(text, columntext, gapbetweencolumns):
    columntext = len(columntext)
    datatodisplaylength = len(text)
    padspace = columntext + gapbetweencolumns - datatodisplaylength
    write = sys.stdout.write
    write(text + ' ' * padspace)
    return (0)

def showVM():
    print
    screen.set_color(fg=Yellow)
    print 'GUID                                   RAM   VCPU  STATE     NODE            VM NAME                        DESCRIPTION                                                            TAGS'
    screen.set_color(fg=White)
    for l in range(1, (queryCLUSTER('VM_TOTALNUMBERVM')) + 1):
        pos = str(l)
        write(queryCLUSTER('VM' + pos + '_GUID'), 'GUID', 35)
        write(queryCLUSTER('VM' + pos + '_MEMORY'), 'RAM', 3)
        write(queryCLUSTER('VM' + pos + '_VCPU'), 'VCPU', 2)
        if vmDATA['VM' + pos + '_STATE'] == 'SHUTOFF':
            screen.set_color(fg=White, bk=Red)
            write(queryCLUSTER('VM' + pos + '_STATE'), 'STATE', 2)
            screen.set_color(fg=White, bk=Black)
            print '   ',
        else:
            screen.set_color(fg=White, bk=Green)
            write(queryCLUSTER('VM' + pos + '_STATE'), 'STATE', 2)
            screen.set_color(fg=White, bk=Black)
            print '   ',
        write(queryCLUSTER('VM' + pos + '_RUNNINGONNODE'), 'NODE', 12)
        write(queryCLUSTER('VM' + pos + '_NAME')[:30], 'VM NAME', 24)
        write(queryCLUSTER('VM' + pos + '_DESCRIPTION')[:67], 'DESCRIPTION', 60)
        write(queryCLUSTER('VM' + pos + '_TAGS'), 'TAGS', 0)
        print
    return (0)

def showNODE():
    print
    screen.set_color(fg=Yellow)
    print 'Peer GUID                                   BACKPLANE          LAN               RAM    CPUs   CORES  THREADS   STORAGE(GB)   CPU(Mhz) HDD1 HDD2 HDD3 HDD4 HDD5 HDD6 HDD7 HDD8'
    screen.set_color(fg=White)
    for l in range(1, (queryCLUSTER('CLUSTER_TOTALNODES') + 1)):
        pos = str(l)
        write(pos, 'Peer', 1)
        write(queryCLUSTER('NODE' + pos + '_GUID'), 'GUID', 35)
        write(queryCLUSTER('NODE' + pos + '_BACKPLANEIP'), 'BACKPLANE', 10)
        write(queryCLUSTER('NODE' + pos + '_LANIP'), 'LAN', 15)
        write(queryCLUSTER('NODE' + pos + '_MEMSIZE'), 'RAM', 4)
        write(queryCLUSTER('NODE' + pos + '_NUMCPU'), 'CPUs', 3)
        write(queryCLUSTER('NODE' + pos + '_NUMCORES'), 'CORES', 2)
        write(queryCLUSTER('NODE' + pos + '_NUMTHREADS'), 'THREADS', 3)
        write(queryCLUSTER('NODE' + pos + '_CAPACITY'), 'STROAGE(GB)', 3)
        write(queryCLUSTER('NODE' + pos + '_CPUHZ'), 'CPU(Mhz)', 1)
        write(queryCLUSTER('NODE' + pos + '_HDD1CAPACITYGB'), 'HDD1', 1)
        write(queryCLUSTER('NODE' + pos + '_HDD2CAPACITYGB'), 'HDD2', 1)
        write(queryCLUSTER('NODE' + pos + '_HDD3CAPACITYGB'), 'HDD3', 1)
        write(queryCLUSTER('NODE' + pos + '_HDD4CAPACITYGB'), 'HDD4', 1)
        write(queryCLUSTER('NODE' + pos + '_HDD5CAPACITYGB'), 'HDD5', 1)
        write(queryCLUSTER('NODE' + pos + '_HDD6CAPACITYGB'), 'HDD6', 1)
        write(queryCLUSTER('NODE' + pos + '_HDD7CAPACITYGB'), 'HDD7', 1)
        write(queryCLUSTER('NODE' + pos + '_HDD8CAPACITYGB'), 'HDD8', 1)
        print
    return (0)

def showISO():
    print
    screen.set_color(fg=Yellow)
    print 'NUMBER  ISO                                                                              SIZE(MB)    STATUS'
    screen.set_color(fg=White)
    for l in range(1, (queryCLUSTER('ISO_TOTALNUMBER'))):
        pos = str(l)
        write('{: >3}'.format(str(pos)), 'NUMBER', 2)
        write(queryCLUSTER('ISO' + pos + '_NAME')[:80], 'ISO', 78)
        write(queryCLUSTER('ISO' + pos + '_SIZE'), 'SIZE(MB)', 4)
        write(queryCLUSTER('ISO' + pos + '_STATUS'), 'STATUS', 0)
        print ''
    return (0)

def displayHELP():
    print ''
    print 'SCALECLI /IP:<ipaddress> /CLUSTERUSERNAME:<username> /CLUSTERPASSWORD:<password> /ACTION:<actiontype>'
    print '         [/HDDx:<hdsize>] [/VCPU:<cpunum>] [/RAM:<ram>] [/DESCRIPTION:<text>] [/STARTNUM:<number> '
    print '         [/NUMBER:<number>] [/NODE:<nodenumber>] [/VM:<vmname>] [/VLAN:<vlannumber>] [/DESTVM:<vmname>]'
    print '         [/FIELD:<fieldtext>]'
    print
    print 'Description:'
    print '     This tool enable the user the perform actions on the HC3 Cluster'
    print''
    print 'Parameter List:'
    print '   /IP:                                    Specifies the IP address of a node in the HC3 cluster'
    print ''
    print '   /CLUSTERUSERNAME:       username        Specifies the admin username of the HC3 cluster'
    print ''
    print '   /CLUSTERPASSWORD:       password        Specifies the admin password of the HC3 cluster'
    print ''
    print '   /ACTION:                action          Specifies the action to perform on the cluster.'
    print '                                           See table below for actions that can be performed'
    print '                                           Depending on the actin chosen, other parameters will'
    print '                                           need to be specified.  See examples at the end of'
    print '                                           this help.'
    print ''
    print 'ACTIONS'
    print '   Action Type           Other options to use                Description'
    print '   -----------           --------------------                -----------'
    print '   CREATEVM              /VM: /HDDx: /RAM: /VCPU:            CREATEVM is used to create a VM'
    print '                         [/DESCRIPTION:] [/STARTNUM:]        You must specifiy at least VM, VCPU, RAM'
    print '                         [/NUMBER:] [/TAGS:] [/VLAN:]        and HDD1 size for the VM to be created'
    print '                                                             Other parameters are optional'
    print ''
    print '   CLONEVM               /VM: /DESTVM: [/DESCRIPTION:]       CLONEVM is used to clone a VM. You'
    print '                         [/STARTNUM:] [/NUMBER:] [/VLAN:]    must specify the source VM (/VM:)'
    print '                                                             and destination vm name (/DESTVM:)'
    print '                                                             as a minimum.  Other parameters are'
    print '                                                             optional and allow you to customise'
    print '                                                             your clone or create multiple clones'
    print ''
    print '   START                 /VM: [/TAGS:]                       START is used to power on a VM. You'
    print '                                                             must specify the VM name (/VM:). If'
    print '                                                             you use the /TAGS: option, you can '
    print '                                                             power on VMs based on their TAGS'
    print '                                                             membership'
    print ''
    print '   STOP                  /VM: [/TAGS:]                       STOP is used to forcibly power off a VM'
    print '                                                             You must specify the VM name (/VM:). If'
    print '                                                             you use the /TAGS: option, you can '
    print '                                                             power off VMs based on their TAGS'
    print '                                                             membership'
    print ''
    print '   SHUTDOWN              /VM: [/TAGS:]                       SHUTDOWN is used to soft power down a VM.'
    print '                                                             You must specify the VM name (/VM:). If'
    print '                                                             you use the /TAGS: option, you can '
    print '                                                             soft power down VMs based on their TAGS'
    print '                                                             membership'
    print ''
    print '   SHOWVM                                                    SHOWVM is used to display list of all'
    print '                                                             VMs on the cluster.'
    print ''
    print '   SHOWNODE                                                  SHOWNODE is used to display technical'
    print '                                                             information about the cluster nodes'
    print ''
    print '   SHOWISO                                                   SHOWISO is used to display a list of all'
    print '                                                             ISO images on the cluster'
    print ''
    print '   LIVEMIGRATE           /VM: /NODE:                         LIVEMIGRATE allows you to move a VM to'
    print '                                                             another NODE in the cluster.  You must'
    print '                                                             specify the source VM (/VM:) and the NODE'
    print '                                                             number you want to move the VM to.'
    print ''
    print '   SNAPSHOT              /VM: [/DESCRIPTION:]                SNAPSHOT is used to perform a manual VM'
    print '                                                             snapshot.  You can give the snapshot a'
    print '                                                             description with the /DESCRIPTION: option.'
    print ''
    print '   UPDATEDESCRIPTION     /VM: /DESCRIPTION                   UPDATEDESCRIPTION is used to update the VM'
    print '                                                             description field.  If you need to have'
    print '                                                             spaces in the text, make sure you enclose'
    print '                                                             the text with " quotes'
    print ''
    print '   QUERYCLUSTER          /FIELD:                             QUERYCLUSTER is used return values about'
    print '                                                             the cluster, nodes and VMs.  See list below'
    print '                                                             for fields you can query.'
    print ''
    print 'FIELDS'
    print '   Field Type (VM)          Description'
    print '   ---------------          -----------'
    print ''
    print '   _GUID                    GUID of VM'
    print '   _NAME                    VM name'
    print '   _OS                      Internal OS template used to build VM'
    print '   _VCPU                    Number of vCPU in VM'
    print '   _DESCRIPTION             VM Description'
    print '   _MEMORY                  Amount of RAM assigned to VM'
    print '   _CONSOLE                 --------------'
    print '   _RUNNINGONNODE           NODE that the VM is currently running on'
    print '   _TAGS                    TAGS assigned to the VM'
    print '   _STATE                   Running state of the VM'
    print '   _TOTALNUMBERVM           Number of VMs on the cluster'
    print '   _MACADDRESSx             Assigned MAC address for VM'
    print '   _MACADDRESSxVLAN         Assigned vLAN for VM'
    print '   _TOTALNETWORKCARDS       Number of network cards a VM has assigned'
    print '   _HDDx                    Size of HDD'
    print '   _TOTALHDD                Total number of HDD in VM'
    print ''
    print 'Examples:'
    print '   /ACTION:QUERYFIELD /FIELD:CortosaDC_GUID          - Returns GUID for VM called CortosaDC'
    print '   /ACTION:QUERYFIELD /FIELD:CortosaDC_HDD2          - Returns size in GB of HDD2 attached to VM'
    print '   /ACTION:QUERYFIELD /FIELD:CortosaDC_MACADDRESS1   - Returns mac address of NIC1 attached to VM'
    print ''
    print '   Field Type (NODE)        Description'
    print '   -----------------        -----------'
    print ''
    print '   _GUID                    GUID of NODE'
    print '   _LANIP                   LANIP assigned to NODE'
    print '   _BACKPLANEIP             BACKPLANE IP assigned to NODE'
    print '   _NUMCORES                Number of CPU cores in NODE'
    print '   _NUMTHREADS              Number of threads per CPU core'
    print '   _MEMSIZE                 Amount of physical memory in NODE'
    print '   _NUMCPU                  Number of physical CPUs in NODE'
    print '   _CAPACITY                Total HDD capacity (GB) of NODE'
    print '   _CPUHZ                   CPU speed in Megahertz in NODE'
    print '   _HDDxCAPACITYGB          Size of HDD in NODE'
    print '   _HDDxAVAILABILITY        Status of HDD in NODE'
    print '   _HDDxSERIALNUMBER        HDD Serial number'
    print '   _HDDxUSEDGB              Amount of space used on HDD'
    print '   _HDDxDRIVEDESCRIPTION    Internal HDD description text'
    print '   _HDDxDRIVEGUID           HDD GUID'
    print '   _HDDTOTAL                Total number of HDD in NODE'
    print ''
    print 'Examples:'
    print '   /ACTION:QUERYFIELD /FIELD:NODE1_GUID              - Returns GUID for NODE1'
    print '   /ACTION:QUERYFIELD /FIELD:NODE1_HDD2CAPACITY      - Returns size in GB of HDD2 attached to NODE1'
    print '   /ACTION:QUERYFIELD /FIELD:NODE3_LANIP             - Returns LAN IP of NODE 3'
    print ''
    print '   Field Type (CLUSTER)     Description'
    print '   --------------------     -----------'
    print ''
    print '   CLUSTER_VERSION          Returns current Hypercore version of firmware'
    print '   CLUSTER_NAME             Returns current cluster name'
    print '   CLUSTER_TOTALNODES       Returns number of NODES in a cluster'
    print '   ISO_TOTALNUMBER          Number of ISO images loaded onto cluster'
    print '   ISOx_NAME                The filename of a particular ISO number'
    print '   ISOx_STATUS              Status of ISO if it is mounted or not mounted'
    print '   ISOx_SIZE                Size in GB of ISO image'
    print '   x_STATUS                 Status of ISO if it is mounted or not mounted'
    print '   x_SIZE                   Size in GB of ISO image'
    print ''
    print 'Examples:'
    print '   /ACTION:QUERYFIELD /FIELD:ISO5_NAME               - Returns name of ISO image no. 5 on cluster'
    print '   /ACTION:QUERYFIELD /FIELD:Windows_2012R2_STATUS   - Returns mount status of ISO'
    print '   /ACTION:QUERYFIELD /FIELD:CLUSTER_TOTALNODES      - Returns number of NODES in cluster'
    print''
    print 'Other Examples:'
    print 'SCALECLI /IP:192.168.1.50 /CLUSTERUSERNAME:admin /CLUSTERPASSWORD:scale /ACTION:CREATEVM /VM:SOPHOS1 /VCPU:2 /RAM:4 /HDD1:200 /DESCRIPTION:"Sophos Antivirus Server"'
    print 'SCALECLI /IP:192.168.1.50 /CLUSTERUSERNAME:admin /CLUSTERPASSWORD:scale /ACTION:CREATEVM /VM:FILESERVER /VCPU:4 /RAM:4 /HDD1:200 /NUMBER:10 /STARTNUM:100 /DESCRIPTION:"Student file servers for testing"'
    print 'SCALECLI /IP:192.168.1.50 /CLUSTERUSERNAME:admin /CLUSTERPASSWORD:scale /ACTION:CLONEVM /VM:VDITEMPLATE /DESTVM:VDIPC /NUMBER:10 /STARTNUM:100 /DESCRIPTION:"Student VDI PC for testing"'
    print 'SCALECLI /IP:192.168.1.50 /CLUSTERUSERNAME:admin /CLUSTERPASSWORD:scale /ACTION:LIVEMIGRATE /VM:SCALE_DC /NODE:2'
    print 'SCALECLI /IP:192.168.1.50 /CLUSTERUSERNAME:admin /CLUSTERPASSWORD:scale /ACTION:SNAPSHOT /VM:SCALE_DC /DESCRIPTION:"Before month end procedure"'
    print 'SCALECLI /IP:192.168.1.50 /CLUSTERUSERNAME:admin /CLUSTERPASSWORD:scale /ACTION:UPDATEDESCRIPTION /VM:SCALE_DC /DESCRIPTION:"Domain Controller New York"'
    print 'SCALECLI /IP:192.168.1.50 /CLUSTERUSERNAME:admin /CLUSTERPASSWORD:scale /ACTION:UPDATEDESCRIPTION /VM:SCALE_DC /DESCRIPTION:"Domain Controller New York"'
    print 'SCALECLI /IP:192.168.1.50 /CLUSTERUSERNAME:admin /CLUSTERPASSWORD:scale /ACTION:SHOWVM'
    print 'SCALECLI /IP:192.168.1.50 /CLUSTERUSERNAME:admin /CLUSTERPASSWORD:scale /ACTION:SHOWNODE'
    print 'SCALECLI /IP:192.168.1.50 /CLUSTERUSERNAME:admin /CLUSTERPASSWORD:scale /ACTION:SHOWISO'
    print 'SCALECLI /IP:192.168.1.50 /CLUSTERUSERNAME:admin /CLUSTERPASSWORD:scale /ACTION:QUERYCLUSTER /FIELD:NODE1_HDD1SERIALNUMBER'
    print 'SCALECLI /IP:192.168.1.50 /CLUSTERUSERNAME:admin /CLUSTERPASSWORD:scale /ACTION:QUERYCLUSTER /FIELD:NODE1_NUMCPU'
    print ''
    print 'NOTE: Where a parameter has an x, this x can be replaced by a number.  ie HDD1 or MACADDRESS1'
    return (0)



# ***************************
# **** Start of main code ***
# ***************************
queryCOMMANDLINE('PARSECMDLINE', None)
sys.exit(0)










# Now we have read in everything about our cluster, we can start to use the data.  Examples are shown below

# EXAMPLE: Check to see if VM exists on cluster
# Notes:   You can use either the display name or GUID to reference the VM
#
# Usage:   vmEXIST (<vm name/vm GUID>)
# Returns: True or False
#
print
if vmEXIST('SCALE_UK_PRTG_Paessler') == True:
    print 'SCALE_UK_PRTG_Paessler server exists'
else:
    print 'Unable to find SCALE_UK_PRTG_Paessler'
print

# EXAMPLE: Query cluster to pull in stored values about VM's or nodes
# Notes:   All data is stored in Python Dictionary structures
#          vmDATA[] - Everything about VMs
#          nodeDATA[] - Everything about the physical nodes
#          clusterDATA[] - Misc data about cluster
#
# Usage:   queryCLUSTER('<key>')
# Returns: value stored in the key
#
print
print 'VM Name           :', queryCLUSTER('SCALE_UK_PRTG_Paessler_NAME')
print 'VM Memory         :', str(queryCLUSTER('SCALE_UK_PRTG_Paessler_MEMORY')) + 'GB'
print 'VM vCPU           :', queryCLUSTER('SCALE_UK_PRTG_Paessler_VCPU')
print 'VM HDD 1          :', str(queryCLUSTER('SCALE_UK_PRTG_Paessler_HDD1')) + 'GB'
print 'VM HDD 2          :', str(queryCLUSTER('SCALE_UK_PRTG_Paessler_HDD2')) + 'GB'
print 'VM Network MAC    :', queryCLUSTER('SCALE_UK_PRTG_Paessler_MACADDRESS1')
print 'VM Running on Node:', queryCLUSTER('SCALE_UK_PRTG_Paessler_RUNNINGONNODE')
print
print
print 'Node 1 HDD3 Serial Number:', queryCLUSTER('node1_hdd1serialnumber')
print 'Node 1 HDD3 Description  :', queryCLUSTER('node1_hdd3drivedescription')
print 'Node 3 total capacity    :', queryCLUSTER('node3_capacity') + 'GB'
print 'Node 3 CPU Threads       :', queryCLUSTER('node3_numthreads')
print 'Node 3 LAN IP            :', queryCLUSTER('node3_LANIP')
print
sys.exit(0)
# EXAMPLE: Create VM or multiple VM's
# Notes:   The values used in the function can be placed in any order.
#          When listing the HDD sizes, you MUST have at least 1 HDD (HDD1=xxx) but
#          other HDD values are optional
#          Mandatory values are: <vmname> <vCPU> <ram> <hdd1>
#
# Usage:   vmCREATE('name=<vmname>','vcpu=<numcpu>','ram=<memory>','hdd1=<size in GB>','hdd2=<size in GB>','vlan=<vlan num>','description=<description text>','hdd3=<size in GB>','hdd4=<size in GB>','hdd5=<size in GB>','hdd6=<size in GB>','hdd7=<size in GB>','hdd8=<size in GB>','number=<num of VM's to create>', 'startnum=<numbering start>')
# Returns: N/A
#

vmCREATE('name=FINANCE_SERVER', 'vcpu=4', 'ram=4', 'hdd1=100', 'vlan=10',
         'description=Finance Server')  # Create a 1 x server (4 x vCPU, 4GB Ram, 100GB HDD, vLAN 10)
vmCREATE('name=SALESPC', 'vcpu=2', 'ram=2', 'hdd1=100', 'hdd2=50', 'vlan=0', 'description=Sales VDI PC', 'number=10',
         'startnum=100')  # Create a 10 x PC (2 x vCPU, 2GB Ram, 100GB HDD, 50GB HDD, vLAN 0) - Named SALESPC100, SALESPC101, SALESPC102 etc

# EXAMPLE: Clone a VM multiple times
# Notes:   VM's are currently clones one at a time
#
# Usage:   vmCLONE (<sourcevm>, <destinationvm>, <number of clones>, <start numbering from>, <clone description>,<clonetags>)
# Returns: N/A
#
vmCLONE('Master', 'VDIPC', 3, 100, 'This IS a clone VDI',
        'FINANCE')  # Creates 3 clones of a VM called Master.  Each clone will be called VDIPC100, VDIPC101, VDIPC102

# EXAMPLE: Perform action on VM
# Notes:   Values that can used are
#          START - Start a VM
#          STOP - Power off VM (same as hitting power button)
#          SHUTDOWN - Soft shutdown of VM
#          If you want to perform an action on VM's based on their TAGS, you must not have a value for the VM.
#          This must be left blank and just the action and tag used.
#
# Usage: vmACTION(<vmname/vmGUID>,<action>,<tag>)
# Returns: N/A
#

vmACTION('VDIPC100', 'START', '')  # Power on each of the cloned PC's created above
vmACTION('VDIPC101', 'START', '')
vmACTION('VDIPC102', 'START', '')

vmACTION('', 'STOP', 'FINANCE')  # Power off all tagged FINANCE VMs - Remember don't use any VM names.

# EXAMPLE: Update description on VM
# Notes:   You are able to use environment variables as part of the description (command line feature)
#          This command is could be use to display current logged in user if ran from within the guest VM
#
# Usage:   vmUPDATEDESCRIPTION(<vmname/vmGUID>,<new description>)
# Returns: N/A
#
vmUPDATEDESCRIPTION('VDIPC100', 'Engineering PC')

# EXAMPLE: Display list of all VM's on cluster in columns
# Notes:   Since python doesn't allow text to be postion at x,y, you need to resize fields to all be
#          the same size.  The resizeFIELDDATA function will resize all fields, padding with spaces
#
# Usage:   N/A
# Returns: N/A
#

resizeFIELDDATA('vm', 'description', 'auto')  # Resize the description key in the VM dictionary structure
resizeFIELDDATA('vm', 'runningonnode', 'auto')
resizeFIELDDATA('vm', 'memory', 'auto')
resizeFIELDDATA('vm', 'name', 'auto')

print
print "GUID                                   Mem Alloc  CPUs  State     Node            Name                                       Description                                                          TAGS"
for l in range(1, (queryCLUSTER('VM_TOTALNUMBERVM'))):
    pos = str(l)
    print queryCLUSTER('vm' + pos + '_guid'), ' ', queryCLUSTER('vm' + pos + '_memory'), '       ', queryCLUSTER('vm' + pos + '_vcpu'), '   ', queryCLUSTER('vm' + pos + '_state'), ' ', queryCLUSTER('vm' + pos + '_runningonnode'), '  ', queryCLUSTER('vm' + pos + '_name'), '    ', queryCLUSTER('vm' + pos + '_description'), '', queryCLUSTER('vm' + pos + '_tags')
print
resizeFIELDDATA('vm', 'description', '0')  # Remove padding from all keys
resizeFIELDDATA('vm', 'runningonnode', '0')
resizeFIELDDATA('vm', 'memory', '0')
resizeFIELDDATA('vm', 'name', '0')

# EXAMPLE: Display list of all nodes in cluster
# Notes:   Since python doesn't allow text to be postion at x,y, you need to resize fields to all be
#          the same size.  The resizeFIELDDATA function will resize all fields, padding with spaces
#
# Usage:   N/A
# Returns: N/A
#

resizeFIELDDATA('node', 'backplaneip', 'auto')
resizeFIELDDATA('node', 'lanip', 'auto')
resizeFIELDDATA('node', 'memsize', 'auto')
resizeFIELDDATA('node', 'numcpu', 'auto')
resizeFIELDDATA('node', 'numcores', 'auto')
resizeFIELDDATA('node', 'numthreads', 'auto')
resizeFIELDDATA('node', 'backplaneip', 'auto')

print
print "Peer GUID                                   Backplane          LAN              RAM    CPUs   CORES  Threads   Storage(GB)   CPU(Mhz)"
for l in range(1, queryCLUSTER('cluster_totalnodes') + 1):
    print l, '  ', queryCLUSTER('node' + str(l) + '_GUID'), ' ', queryCLUSTER('node' + str(l) + '_BACKPLANEIP'), '      ', queryCLUSTER('node' + str(l) + '_LANIP'), '   ', queryCLUSTER('node' + str(l) + '_MEMSIZE'), '   ', queryCLUSTER('node' + str(l) + '_NUMCPU'), '    ', queryCLUSTER('node' + str(l) + '_NUMCORES'), '    ', queryCLUSTER('node' + str(l) + '_NUMTHREADS'), '       ', queryCLUSTER('node' + str(l) + '_CAPACITY'), '        ', queryCLUSTER('node' + str(l) + '_CPUhz')
print


# Command line demo stuff to keep for reference

# queryCOMMANDLINE('/ip:192.168.1.50','/clusterusername:admin','/clusterpassword:scale','/action:snapshot','/vm:SCALE_UK_HPPrint','/description:"See if this works"')
# queryCOMMANDLINE('/ip:192.168.1.50','/clusterusername:admin','/clusterpassword:scale','/action:livemigrate','/vm:SCALE_UK_HPPrint','/node:1')
# queryCOMMANDLINE('/ip:192.168.1.50','/clusterusername:admin','/clusterpassword:scale','/action:querycluster','/field:SCALE_UK_HPPrint_GUID"')
# queryCOMMANDLINE('/ip:192.168.1.50','/clusterusername:admin','/clusterpassword:scale','/action:createvm','/vm:VDIPC','/vcpu:2','/ram:4','/description:"new PC test"','/vlan:999','/hdd1:300','/hdd2:500','startnum:555','number:2')
# queryCOMMANDLINE('/ip:192.168.1.50','/clusterusername:admin','/clusterpassword:scale','/action:clonevm','/vm:master','destvm:newpcvdi','/description:"new cloned PC test"','/vlan:800','startnum:555','number:3','tags:AA1,AA2')
# queryCOMMANDLINE('/ip:192.168.1.50','/clusterusername:admin','/clusterpassword:scale','/action:updatedescription','/vm:master-clone','/description:"new cloned PC test"')
# queryCOMMANDLINE('/ip:192.168.1.50','/clusterusername:admin','/clusterpassword:scale','/action:showvm')
# queryCOMMANDLINE('/ip:192.168.1.50','/clusterusername:admin','/clusterpassword:scale','/action:showiso')
# queryCOMMANDLINE('/ip:192.168.1.50','/clusterusername:admin','/clusterpassword:scale','/action:export','/vm:SCALE_UK_HPPrint')

# vmUPDATEDESCRIPTIONWMIC('SCALE_UK_WSUS_Kaspersky', '192.168.1.158', 'WSUS / Antivirus - ', 'sysadmin@scalecomputing.com', 'Pa55w0rd')
# vmUPDATEDESCRIPTIONWMIC('SCALE_UK_DFSRoot', '192.168.1.152', 'DFS ROOT - ', 'sysadmin@scalecomputing.com', 'Pa55w0rd')
# vmUPDATEDESCRIPTIONWMIC('SCALE_UK_MDT_2012', '192.168.1.155', 'Microsoft MDT 2012 - ', 'sysadmin@scalecomputing.com', 'Pa55w0rd')
# vmUPDATEDESCRIPTIONWMIC('SCALE_UK_PRTG_Paessler', '192.168.1.156', 'PRTG Paessler - ', 'sysadmin@scalecomputing.com', 'Pa55w0rd')
# vmUPDATEDESCRIPTIONWMIC('SCALE_UK_HPPRINT', '192.168.1.153', 'HP Print - ', 'sysadmin@scalecomputing.com', 'Pa55w0rd')
# vmUPDATEDESCRIPTIONWMIC('SCALE_UK_CLOUDBERRYBACKUP', '192.168.1.144', 'CloudBerry Backup - ', 'sysadmin@scalecomputing.com', 'Pa55w0rd')
# vmUPDATEDESCRIPTIONWMIC('SCALE_UK_DC', '192.168.1.150', 'Domain Controller UK - ', 'sysadmin@scalecomputing.com', 'Pa55w0rd')

# recordeventlogVM('192.168.1.50-allvmhistory.csv',0,5,'verbose=yes')