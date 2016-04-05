# SCALE API Demo v0.1
# Written: Leonard Powers - lpowers@scalecomputing.com
#
# History
# 24/03/2016 - Initial release
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

# Libraries to import and use.
import sys
import ssl
from colorama import init
from thrift.transport import THttpClient
from thrift.protocol import TJSONProtocol
from scaled.ttypes import *
from scaled import ScaleService

sys.path.append('gen-py')

# Declare global variables
vmDATA = {}  # Contains all data about VM's (RAM, OS, CPU, HDD, Description etc)
nodeHW = {}  # Contains all data about the individual nodes (memory, No. HDD, HDD Serial No. etc)
clusterDATA = {}  # Contains misc information about the cluster.
commandline = {}  # Contains what we type in on the command line


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


def GetAllVMData():
    global vmTOTALNUMBER  # Total number of VM's on cluster
    vmTOTALNUMBER = 0
    numbernetworkcards = 1
    cluster = client.VirDomainRead(sessionID, 0, VirDomainFilter())
    for vm in cluster:
        vmTOTALNUMBER = vmTOTALNUMBER + 1  # Count the number of VM's on the cluster

        # Get all information about VM's on cluster and store in vmDATA dictionary
        vmDATA['VM' + str(vmTOTALNUMBER) + '_GUID'] = str(vm.guid)
        vmDATA['VM' + str(vmTOTALNUMBER) + '_NAME'] = str(vm.name)
        vmDATA['VM' + str(vmTOTALNUMBER) + '_OS'] = str(vm.operatingSystem)
        vmDATA['VM' + str(vmTOTALNUMBER) + '_VCPU'] = str(vm.numVCPU)
        vmDATA['VM' + str(vmTOTALNUMBER) + '_DESCRIPTION'] = str(vm.description)
        vmDATA['VM' + str(vmTOTALNUMBER) + '_MEMORY'] = str((vm.mem / 1024) / 1024 / 1024)
        vmDATA['VM' + str(vmTOTALNUMBER) + '_CONSOLE'] = str(vm.console)
        if len(vm.console.ip) > 0:
            vmDATA['VM' + str(vmTOTALNUMBER) + '_RUNNINGONNODE'] = str(vm.console.ip)
        if len(vm.console.ip) == 0:
            vmDATA['VM' + str(vmTOTALNUMBER) + '_RUNNINGONNODE'] = '--'
        vmDATA['VM' + str(vmTOTALNUMBER) + '_TAGS'] = str(vm.tags)

        # Turn vmState into meaningful text fields instead of numbers.
        if vm.state == 0:
            vmDATA['VM' + str(vmTOTALNUMBER) + '_STATE'] = "RUNNING"
        elif vm.state == 1:
            vmDATA['VM' + str(vmTOTALNUMBER) + '_STATE'] = "BLOCKED"
        elif vm.state == 2:
            vmDATA['VM' + str(vmTOTALNUMBER) + '_STATE'] = "PAUSED"
        elif vm.state == 3:
            vmDATA['VM' + str(vmTOTALNUMBER) + '_STATE'] = "SHUTDOWN"
        elif vm.state == 4:
            vmDATA['VM' + str(vmTOTALNUMBER) + '_STATE'] = "SHUTOFF"
        elif vm.state == 5:
            vmDATA['VM' + str(vmTOTALNUMBER) + '_STATE'] = "CRASHED"

        # Section of code below now gets all the information about a VM and stores it under the VM name.
        # This allows us to reference data about the VM by it's name (in uppercase)
        vmDATA[str(vm.name).upper() + '_GUID'] = str(vm.guid)
        vmDATA[str(vm.name).upper() + '_NAME'] = str(vm.name)
        vmDATA[str(vm.name).upper() + '_OS'] = str(vm.operatingSystem)
        vmDATA[str(vm.name).upper() + '_VCPU'] = str(vm.numVCPU)
        vmDATA[str(vm.name).upper() + '_DESCRIPTION'] = str(vm.description)
        vmDATA[str(vm.name).upper() + '_MEMORY'] = str((vm.mem / 1024) / 1024 / 1024)
        vmDATA[str(vm.name).upper() + '_CONSOLE'] = str(vm.console)
        if len(vm.console.ip) > 0:
            vmDATA[str(vm.name).upper() + '_RUNNINGONNODE'] = str(vm.console.ip)
        if len(vm.console.ip) == 0:
            vmDATA[str(vm.name).upper() + '_RUNNINGONNODE'] = '--'
        vmDATA[str(vm.name).upper() + '_TAGS'] = str(vm.tags)
        # Turn vmState into meaningful text fields instead of numbers.
        if vm.state == 0:
            vmDATA[str(vm.name).upper() + '_STATE'] = "RUNNING"
        elif vm.state == 1:
            vmDATA[str(vm.name).upper() + '_STATE'] = "BLOCKED"
        elif vm.state == 2:
            vmDATA[str(vm.name).upper() + '_STATE'] = "PAUSED"
        elif vm.state == 3:
            vmDATA[str(vm.name).upper() + '_STATE'] = "SHUTDOWN"
        elif vm.state == 4:
            vmDATA[str(vm.name).upper() + '_STATE'] = "SHUTOFF"
        elif vm.state == 5:
            vmDATA[str(vm.name).upper() + '_STATE'] = "CRASHED"

        # Section of code below now gets all the information about a VM and stores it under the VM GUID.
        # This allows us to reference data about the VM by it's GUID
        vmDATA[str(vm.guid).upper() + '_GUID'] = str(vm.guid)
        vmDATA[str(vm.guid).upper() + '_NAME'] = str(vm.name)
        vmDATA[str(vm.guid).upper() + '_OS'] = str(vm.operatingSystem)
        vmDATA[str(vm.guid).upper() + '_VCPU'] = str(vm.numVCPU)
        vmDATA[str(vm.guid).upper() + '_DESCRIPTION'] = str(vm.description)
        vmDATA[str(vm.guid).upper() + '_MEMORY'] = str((vm.mem / 1024) / 1024 / 1024)
        vmDATA[str(vm.guid).upper() + '_CONSOLE'] = str(vm.console)
        if len(vm.console.ip) > 0:
            vmDATA[str(vm.guid).upper() + '_RUNNINGONNODE'] = str(vm.console.ip)
        if len(vm.console.ip) == 0:
            vmDATA[str(vm.guid).upper() + '_RUNNINGONNODE'] = '--'
        vmDATA[str(vm.name).upper() + '_TAGS'] = str(vm.tags)
        # Turn vmState into meaningful text fields instead of numbers.
        if vm.state == 0:
            vmDATA[str(vm.guid).upper() + '_STATE'] = "RUNNING"
        elif vm.state == 1:
            vmDATA[str(vm.guid).upper() + '_STATE'] = "BLOCKED"
        elif vm.state == 2:
            vmDATA[str(vm.guid).upper() + '_STATE'] = "PAUSED"
        elif vm.state == 3:
            vmDATA[str(vm.guid).upper() + '_STATE'] = "SHUTDOWN"
        elif vm.state == 4:
            vmDATA[str(vm.guid).upper() + '_STATE'] = "SHUTOFF"
        elif vm.state == 5:
            vmDATA[str(vm.guid).upper() + '_STATE'] = "CRASHED"

    vmDATA['VM_TOTALNUMBERVM'] = vmTOTALNUMBER

    # Find MAC address for each network card associated with a VM

    networkcardcount = 1  # Stores the number of network cards in a VM
    for vm in cluster:  # Need to read through all the VM's on the cluster
        for l in (
                vm.netDevs):  # Now we need to read through the network card config.  There could be more than 1 network card so we need to read via a loop
            # temporary variables used when reading the network card config
            tempmacaddress = l.macAddress
            tempvmguid = l.virDomainGUID
            tempvlan = l.vlan
            tempconnectionstatus = l.connected
            # Look up the name of the server based on the GUID returned from the network card.
            # The GUID tells use which VM the network card is attached to.
            tempvmname = queryCLUSTER(tempvmguid + '_NAME').upper()

            # if we get some odd query lookups, filter these out so that we only process real server
            # In testing some queries returned '--' as the server name.  Don't know why this happened
            if tempvmname <> '--':
                # Check to see if we have already created a network card key.  If so, increase the networkcard count
                # and move on
                if tempvmname + '_MACADDRESS' + str(networkcardcount) in vmDATA.keys():
                    networkcardcount = networkcardcount + 1
                else:
                    # So in this section we haven't found an existing network card.  So we store all the network card
                    # details in the correct dictionaries.
                    vmDATA[tempvmname + '_MACADDRESS' + str(networkcardcount)] = tempmacaddress
                    vmDATA[tempvmname + '_MACADDRESS' + str(networkcardcount) + 'VLAN'] = tempvlan
                    vmDATA[tempvmguid + '_MACADDRESS' + str(networkcardcount)] = tempmacaddress
                    vmDATA[tempvmguid + '_MACADDRESS' + str(networkcardcount) + 'VLAN'] = tempvlan

                    networkcardcount = networkcardcount + 1
        # Store the total number of network cards for each VM.  Useful for referencing later on.
        vmDATA[tempvmname + '_TOTALNETWORKCARDS'] = str((networkcardcount - 1))
        vmDATA[tempvmguid + '_TOTALNETWORKCARDS'] = str((networkcardcount - 1))
        networkcardcount = 1

    hddcount = 1
    for vm in cluster:  # Need to read through all the VM's on the cluster
        for l in (
                vm.blockDevs):  # Now we need to read through the network card config.  There could be more than 1 network card so we need to read via a loop
            tempvmhddcapacity = l.capacity / 1000 / 1000 / 1000
            tempvmguid = l.virDomainGUID
            tempvmhddname = l.name
            tempvmname = queryCLUSTER(tempvmguid + '_NAME').upper()
            if tempvmhddcapacity > 0 and tempvmhddname == '':
                if tempvmname + '_HDD' + str(hddcount) in vmDATA.keys():
                    hddcount = hddcount + 1
                else:
                    # So in this section we haven't found an existing network card.  So we store all the network card
                    # details in the correct dictionaries.
                    vmDATA[tempvmname + '_HDD' + str(hddcount)] = tempvmhddcapacity
                    vmDATA[tempvmguid + '_HDD' + str(hddcount)] = tempvmhddcapacity
                    hddcount = hddcount + 1
        # Store the total number of network cards for each VM.  Useful for referencing later on.
        vmDATA[tempvmname + '_TOTALHDD'] = str((hddcount - 1))
        vmDATA[tempvmguid + '_TOTALHDD'] = str((hddcount - 1))
        hddcount = 1


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

        # Find out how many drives are in the particular node them loop through them
        # pulling off information we need.  The code below will allow for nodes of different number
        # of drives to be read correctly
        totalnodedrives = node.drives  # Number of drives in the node being read
        currentdrive = 0
        for l in totalnodedrives:
            # Information about the disks in each node is stored in a dictonary
            dict = l.disks
            for pos in dict:
                nodeHW['NODE' + str(nodetotalnumber) + '_HDD' + str(currentdrive) + 'CAPACITYGB'] = str(
                    int(dict[pos].capacityBytes) / 1000 / 1000 / 1000)
                nodeHW['NODE' + str(nodetotalnumber) + '_HDD' + str(currentdrive) + 'AVAILABILITY'] = dict[
                    pos].availability
                nodeHW['NODE' + str(nodetotalnumber) + '_HDD' + str(currentdrive) + 'SERIALNUMBER'] = l.serialNumber
                nodeHW['NODE' + str(nodetotalnumber) + '_HDD' + str(currentdrive) + 'USEDGB'] = (
                    l.usedBytes / 1000 / 1000 / 1000)
                nodeHW['NODE' + str(nodetotalnumber) + '_HDD' + str(currentdrive) + 'DRIVEDESCRIPTION'] = l.guid
                nodeHW['NODE' + str(nodetotalnumber) + '_HDD' + str(currentdrive) + 'DRIVEGUID'] = dict[pos].driveGUID
            currentdrive = currentdrive + 1
            nodeHW['NODE' + str(nodetotalnumber) + '_HDDTOTAL'] = str(currentdrive)
    clusterDATA['CLUSTER_TOTALNODES'] = nodetotalnumber


def GetAllCLUSTERData():
    # Any other misc info about the cluster will be gathered here.  The clusterDATA dictionary will also
    # contain
    cluster = client.ClusterRead(sessionID, -1, VirDomainFilter())
    for i in cluster:
        clusterDATA['CLUSTER_VERSION'] = str(i.icosVersion)
        clusterDATA['CLUSTER_NAME'] = i.clusterName


def queryCLUSTER(*args):
    found = False
    returnedqueryCLUSTER = []  # Contains returned values when we perform a cluster query
    numberofargs = len(args)
    for l in range(0, numberofargs):
        queryFIELD = args[l].upper()
        if queryFIELD in vmDATA:
            returnedqueryCLUSTER.append(vmDATA[queryFIELD])
            found = True
        elif queryFIELD in nodeHW:
            returnedqueryCLUSTER.append(nodeHW[queryFIELD])
            found = True
        elif queryFIELD in clusterDATA:
            returnedqueryCLUSTER.append(clusterDATA[queryFIELD])
            found = True
        if found == True:
            found = False
            return returnedqueryCLUSTER[0]
        elif found == False:
            return '--'


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


def vmACTION(vm, action, tag):
    # Actions that we can take on a VM include STOP, START, SHUTDOWN.
    # STOP - power off the VM (not recommended - same effect as hitting the power button)
    # START - Power on a VM
    # SHUTDOWN - Perform a controlled safe shutdown.  Recommended way but only works at login screen.
    found = False
    vm = vm.upper()
    action = action.upper()
    tag = tag.upper()

    # This section will shutdown VM's based on their TAG as long as no VM name is specified
    if vm == '' and tag <> '':
        for l in range(1, queryCLUSTER('VM_TOTALNUMBERVM')):  # Get the number of VM's on the cluster
            tempvmtag = queryCLUSTER('VM' + str(l) + '_TAGS')  # Get the tags associated with each VM
            tempguid = queryCLUSTER('VM' + str(l) + '_GUID')  # Get the VM GUID which will be use to shutdown the VM
            tempvmtag = tempvmtag.split(
                ",")  # If a VM has multiple tags, split them at the comma and store them in a list
            for t in range(0,
                           len(tempvmtag)):  # Run though the tag list and perform the action based on the tag we find
                if tempvmtag[t].upper() == tag.upper():
                    if action == "STOP":
                        result = client.VirDomainAction(sessionID,
                                                        [VirDomainActionDescription(virDomainGUID=tempguid,
                                                                                    actionType=VirDomainActionType.STOP)])
                    if action == "START":
                        result = client.VirDomainAction(sessionID,
                                                        [VirDomainActionDescription(virDomainGUID=tempguid,
                                                                                    actionType=VirDomainActionType.START)])
                    if action == "SHUTDOWN":
                        result = client.VirDomainAction(sessionID,
                                                        [VirDomainActionDescription(virDomainGUID=tempguid,
                                                                                    actionType=VirDomainActionType.SHUTDOWN)])
        return (0)

    # Perform an action on a single VM
    if vm <> '' and vmEXIST(vm) == True:
        vm = vm.upper()
        action = action.upper()
        found = True
        tempguid = vmDATA[vm + '_GUID']
        # We can now STOP (simulate power button being pressed) , START or SHUTDOWN (Graceful shutdown) a VM
        if action == "STOP":
            result = client.VirDomainAction(sessionID, [
                VirDomainActionDescription(virDomainGUID=tempguid, actionType=VirDomainActionType.STOP)])
        if action == "START":
            result = client.VirDomainAction(sessionID, [
                VirDomainActionDescription(virDomainGUID=tempguid, actionType=VirDomainActionType.START)])
        if action == "SHUTDOWN":
            result = client.VirDomainAction(sessionID, [
                VirDomainActionDescription(virDomainGUID=tempguid, actionType=VirDomainActionType.SHUTDOWN)])

    # if the VM doesnt exist display error message
    if found == False:
        print "Error - Unable to find VM.  Check the name"
        sys.exit(100)
    return (0)


def vmUPDATEDESCRIPTION(vm, newdescription):
    # Change the description on a VM
    if vmEXIST(vm) == True:
        # Update info for a VM
        tempguid = vmDATA[vm + '_GUID']
        tempvm = client.VirDomainRead(sessionID, -1, VirDomainFilter(virDomainGUID=tempguid))[0]
        tempvm.description = newdescription
        result = client.VirDomainUpdate(sessionID, tempvm)
    return (0)


def keyEXIST(key, dictionarytocheck):
    found = False
    if key in dictionarytocheck.keys():
        found = True
    return found


def vmCLONE(sourcevm, destinationvm, numclones, startnum, clonedescription, clonetags):
    sourcevm = sourcevm.upper()
    readyclones = []
    destinationvm = destinationvm.upper()

    # Check to see if the source VM exists
    if vmEXIST(sourcevm) == False:
        print "Source VM not found"
        sys.exit(100)
    sourcevmguid = vmDATA[sourcevm + '_GUID']  # VM doesn't exist so we need to find the source VM GUID

    # Now we check that an existing VM doesn't have the same name as the cloned named
    # Need to take into account that the clones VM name will have a number appended to it.

    for l in range(startnum, (startnum + numclones)):
        if destinationvm + str(l) + '_NAME' in vmDATA.keys():
            print "VM Name: " + destinationvm + str(l) + " already exists.  Please choose another name"
            sys.exit(100)

    for l in range(startnum, (startnum + numclones)):
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


def vmCREATE(*args):
    vmcreatedata = {}
    vmcreatemaxhddsize = (8000 * 1000 * 1000 * 1000)
    vmcreatenumber = 0
    vmcreatetags = ''
    vmcreatehdd1 = 0
    vmcreatehdd2 = 0
    vmcreatehdd3 = 0
    vmcreatehdd4 = 0
    vmcreatehdd5 = 0
    vmcreatehdd6 = 0
    vmcreatehdd7 = 0
    vmcreatehdd8 = 0
    vmcreatestartnumber = 0
    numberofargs = len(args)
    for l in range(0, numberofargs):
        temp = args[l].split('=')  # Read through arguments in function and split them at the equals sign
        temp[0] = temp[0].upper()  # Convert the field into uppercase for storing in the dictionary
        vmcreatedata[temp[0]] = temp[1]  # Create dictionary data

    if keyEXIST('NAME', vmcreatedata) == True:
        vmcreatename = vmcreatedata['NAME']
    if keyEXIST('VCPU', vmcreatedata) == True:
        vmcreatevcpu = int(vmcreatedata['VCPU'])
    if keyEXIST('RAM', vmcreatedata) == True:
        vmcreateram = int(vmcreatedata['RAM']) * 1024 * 1024 * 1024
    if keyEXIST('VLAN', vmcreatedata) == True:
        vmcreatevlan = int(vmcreatedata['VLAN'])
    if keyEXIST('DESCRIPTION', vmcreatedata) == True:
        vmcreatedescription = vmcreatedata['DESCRIPTION']
    if keyEXIST('TAGS', vmcreatedata) == True:
        vmcreatetags = vmcreatedata['TAGS']
    if keyEXIST('NUMBER', vmcreatedata) == True:
        vmcreatenumber = int(vmcreatedata['NUMBER'])
    if keyEXIST('STARTNUM', vmcreatedata) == True:
        vmcreatestartnum = int(vmcreatedata['STARTNUM'])

    # The maximum size of a single HDD in a VM is 8TB.  There is a maximum of 8 HDD limit as as well.
    if keyEXIST('HDD1', vmcreatedata) == True:
        vmcreatehdd1 = int(vmcreatedata['HDD1']) * 1000 * 1000 * 1000
        if vmcreatehdd1 > vmcreatemaxhddsize:
            print "Error - HDD1 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)
    if keyEXIST('HDD2', vmcreatedata) == True:
        print 'found hdd2'
        vmcreatehdd2 = int(vmcreatedata['HDD2']) * 1000 * 1000 * 1000
        if vmcreatehdd2 > vmcreatemaxhddsize:
            print "Error - HDD2 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)
    if keyEXIST('HDD3', vmcreatedata) == True:
        vmcreatehdd3 = int(vmcreatedata['HDD3']) * 1000 * 1000 * 1000
        if vmcreatehdd3 > vmcreatemaxhddsize:
            print "Error - HDD3 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)
    if keyEXIST('HDD4', vmcreatedata) == True:
        vmcreatehdd4 = int(vmcreatedata['HDD4']) * 1000 * 1000 * 1000
        if vmcreatehdd4 > vmcreatemaxhddsize:
            print "Error - HDD4 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)
    if keyEXIST('HDD5', vmcreatedata) == True:
        vmcreatehdd5 = int(vmcreatedata['HDD5']) * 1000 * 1000 * 1000
        if vmcreatehdd5 > vmcreatemaxhddsize:
            print "Error - HDD5 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)
    if keyEXIST('HDD6', vmcreatedata) == True:
        vmcreatehdd6 = int(vmcreatedata['HDD6']) * 1000 * 1000 * 1000
        if vmcreatehdd6 > vmcreatemaxhddsize:
            print "Error - HDD6 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)
    if keyEXIST('HDD7', vmcreatedata) == True:
        vmcreatehdd7 = int(vmcreatedata['HDD7']) * 1000 * 1000 * 1000
        if vmcreatehdd7 > vmcreatemaxhddsize:
            print "Error - HDD7 Size is too large.  Maximum size for a single drive is 8TB (8000gb)"
            sys.exit(100)
    if keyEXIST('HDD8', vmcreatedata) == True:
        vmcreatehdd8 = int(vmcreatedata['HDD8']) * 1000 * 1000 * 1000
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

    if vmcreatenumber == 0:
        if vmcreatehdd1 <> 0 and vmcreatehdd2 == 0 and vmcreatehdd3 == 0 and vmcreatehdd4 == 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,
                                                        numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                                    type=VIRTIO)],
                                                        blockDevs=[VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,
                                                                                        allocation=0,
                                                                                        cacheMode=WRITETHROUGH,
                                                                                        type=VIRTIO_DISK, physical=0),
                                                                   VirDomainBlockDevice(slot=9, capacity=0,
                                                                                        allocation=0,
                                                                                        cacheMode=WRITETHROUGH,
                                                                                        type=IDE_CDROM, physical=0)]))
        if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 == 0 and vmcreatehdd4 == 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,
                                                        numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                                    type=VIRTIO)], blockDevs=
                                                        [VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                              cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                              physical=0), ]))
        if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 == 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,
                                                        numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                                    type=VIRTIO)], blockDevs=
                                                        [VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                              cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                              physical=0), ]))
        if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,
                                                        numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                                    type=VIRTIO)], blockDevs=
                                                        [VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                              cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                              physical=0), ]))
        if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,
                                                        numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                                    type=VIRTIO)], blockDevs=
                                                        [VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                              cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                              physical=0), ]))
        if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 <> 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,
                                                        numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                                    type=VIRTIO)], blockDevs=
                                                        [VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=5, capacity=vmcreatehdd6,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                              cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                              physical=0), ]))
        if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 <> 0 and vmcreatehdd7 <> 0 and vmcreatehdd8 == 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,
                                                        numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                                    type=VIRTIO)], blockDevs=
                                                        [VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=5, capacity=vmcreatehdd6,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=6, capacity=vmcreatehdd7,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                              cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                              physical=0), ]))
        if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 <> 0 and vmcreatehdd7 <> 0 and vmcreatehdd8 <> 0:
            client.VirDomainCreate(sessionID, VirDomain(name=vmcreatename, operatingSystem="os_windows_server_2012",
                                                        description=vmcreatedescription, mem=vmcreateram,
                                                        numVCPU=vmcreatevcpu, tags=vmcreatetags,
                                                        netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                                    type=VIRTIO)], blockDevs=
                                                        [VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=5, capacity=vmcreatehdd6,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=6, capacity=vmcreatehdd7,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=7, capacity=vmcreatehdd8,
                                                                              allocation=0, cacheMode=WRITETHROUGH,
                                                                              type=VIRTIO_DISK, physical=0),
                                                         VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                              cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                              physical=0), ]))
        return (0)

    # So now we want to create multiple VM's.  Same code as above.  Ugly but it works.
    if vmcreatenumber > 0:
        for l in range(vmcreatestartnum, (vmcreatestartnum + vmcreatenumber)):
            if vmEXIST((vmcreatename + str(l))) == True:
                print "Error - Duplicate VM Name"
                sys.exit(100)

        for l in range(vmcreatestartnum, (vmcreatestartnum + vmcreatenumber)):
            if vmcreatehdd1 <> 0 and vmcreatehdd2 == 0 and vmcreatehdd3 == 0 and vmcreatehdd4 == 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
                client.VirDomainCreate(sessionID,
                                       VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",
                                                 description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,
                                                 tags=vmcreatetags,
                                                 netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                             type=VIRTIO)],
                                                 blockDevs=[
                                                     VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,
                                                                          cacheMode=WRITETHROUGH,
                                                                          type=VIRTIO_DISK, physical=0),
                                                     VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                          cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                          physical=0)]))
            if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 == 0 and vmcreatehdd4 == 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
                client.VirDomainCreate(sessionID,
                                       VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",
                                                 description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,
                                                 tags=vmcreatetags,
                                                 netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                             type=VIRTIO)], blockDevs=
                                                 [VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                       physical=0), ]))
            if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 == 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
                client.VirDomainCreate(sessionID,
                                       VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",
                                                 description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,
                                                 tags=vmcreatetags,
                                                 netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                             type=VIRTIO)], blockDevs=
                                                 [VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                       physical=0), ]))
            if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 == 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
                client.VirDomainCreate(sessionID,
                                       VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",
                                                 description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,
                                                 tags=vmcreatetags,
                                                 netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                             type=VIRTIO)], blockDevs=
                                                 [VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                       physical=0), ]))
            if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 == 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
                client.VirDomainCreate(sessionID,
                                       VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",
                                                 description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,
                                                 tags=vmcreatetags,
                                                 netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                             type=VIRTIO)], blockDevs=
                                                 [VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                       physical=0), ]))
            if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 <> 0 and vmcreatehdd7 == 0 and vmcreatehdd8 == 0:
                client.VirDomainCreate(sessionID,
                                       VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",
                                                 description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,
                                                 tags=vmcreatetags,
                                                 netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                             type=VIRTIO)], blockDevs=
                                                 [VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=5, capacity=vmcreatehdd6, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                       physical=0), ]))
            if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 <> 0 and vmcreatehdd7 <> 0 and vmcreatehdd8 == 0:
                client.VirDomainCreate(sessionID,
                                       VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",
                                                 description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,
                                                 tags=vmcreatetags,
                                                 netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                             type=VIRTIO)], blockDevs=
                                                 [VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=5, capacity=vmcreatehdd6, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=6, capacity=vmcreatehdd7, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                       physical=0), ]))
            if vmcreatehdd1 <> 0 and vmcreatehdd2 <> 0 and vmcreatehdd3 <> 0 and vmcreatehdd4 <> 0 and vmcreatehdd5 <> 0 and vmcreatehdd6 <> 0 and vmcreatehdd7 <> 0 and vmcreatehdd8 <> 0:
                client.VirDomainCreate(sessionID,
                                       VirDomain(name=vmcreatename + str(l), operatingSystem="os_windows_server_2012",
                                                 description=vmcreatedescription, mem=vmcreateram, numVCPU=vmcreatevcpu,
                                                 tags=vmcreatetags,
                                                 netDevs=[VirDomainNetDevice(vlan=vmcreatevlan, connected=True,
                                                                             type=VIRTIO)], blockDevs=
                                                 [VirDomainBlockDevice(slot=0, capacity=vmcreatehdd1, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=1, capacity=vmcreatehdd2, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=2, capacity=vmcreatehdd3, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=3, capacity=vmcreatehdd4, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=4, capacity=vmcreatehdd5, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=5, capacity=vmcreatehdd6, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=6, capacity=vmcreatehdd7, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=7, capacity=vmcreatehdd8, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=VIRTIO_DISK,
                                                                       physical=0),
                                                  VirDomainBlockDevice(slot=9, capacity=0, allocation=0,
                                                                       cacheMode=WRITETHROUGH, type=IDE_CDROM,
                                                                       physical=0), ]))
        return (0)


def queryCOMMANDLINE(*args):
    # Start of the command line paser.  Have decided to write my own as 3rd parties were not good enough or very limted
    # in how you could use them.
    numberofargs = len(sys.argv)
    commandline['COMMANDLINE'] = sys.argv[1].upper()  # Store the command we are trying to execute
    for l in range(2, numberofargs):
        temp = sys.argv[l].split(':')
        commandline[temp[0].upper()] = temp[1]
    return ()


# ***************************
# **** Start of main code ***
# ***************************

OpenConnectionToCluster('192.168.1.50', 'admin',
                        'scale')  # Initiate connection to the cluster.  Must be 1st thing we do
GetAllVMData()  # Read everything about our VM's and store them in a dictionary structure
GetAllNODEData()  # Read everything about our Nodes in the cluster and store them in a dictionary structure
GetAllCLUSTERData()  # Read misc items about the entire cluster and store them in a dictionary structure

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

# EXAMPLE: Create VM or multiple VM's
# Notes:   The values used in the function can be placed in any order.
#          When listing the HDD sizes, you MUST have at least 1 HDD (HDD1=xxx) but
#          other HDD values are optional
#          Mandatory values are: <vmname> <vCPU> <ram> <hdd1>
#
# Usage:   vmCREATE('name=<vmname>','vcpu=<numcpu>','ram=<memory>','hdd1=<size in GB>','hdd2=<size in GB>','vlan=<vlan num>','description=<description text>','hdd3=<size in GB>','hdd4=<size in GB>','hdd5=<size in GB>','hdd6=<size in GB>','hdd7=<size in GB>','hdd8=<size in GB>','number=<num of VM's to create>', 'startnum=<numbering start>')
# Returns: N/A
#

vmCREATE('name=FINANCE_SERVER', 'vcpu=4', 'ram=4', 'hdd1=100', 'vlan=10','description=Finance Server')  # Create a 1 x server (4 x vCPU, 4GB Ram, 100GB HDD, vLAN 10)
vmCREATE('name=SALESPC', 'vcpu=2', 'ram=2', 'hdd1=100', 'hdd2=50', 'vlan=0', 'description=Sales VDI PC', 'number=10','startnum=100')  # Create a 10 x PC (2 x vCPU, 2GB Ram, 100GB HDD, 50GB HDD, vLAN 0) - Named SALESPC100, SALESPC101, SALESPC102 etc

# EXAMPLE: Clone a VM multiple times
# Notes:   VM's are currently clones one at a time
#
# Usage:   vmCLONE (<sourcevm>, <destinationvm>, <number of clones>, <start numbering from>, <clone description>,<clonetags>)
# Returns: N/A
#
vmCLONE('Master', 'VDIPC', 3, 100, 'This IS a clone VDI','FINANCE')  # Creates 3 clones of a VM called Master.  Each clone will be called VDIPC100, VDIPC101, VDIPC102

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
    print queryCLUSTER('vm' + pos + '_guid'), ' ', queryCLUSTER('vm' + pos + '_memory'), '       ', queryCLUSTER('vm' + pos + '_vcpu'), '   ', \
        queryCLUSTER('vm' + pos + '_state'), ' ', queryCLUSTER('vm' + pos + '_runningonnode'), '  ', queryCLUSTER('vm' + pos + '_name'), '    ', \
        queryCLUSTER('vm' + pos + '_description'), '', queryCLUSTER('vm' + pos + '_tags')
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
    print l, '  ', queryCLUSTER('node' + str(l) + '_GUID'), ' ', queryCLUSTER('node' + str(l) + '_BACKPLANEIP'), '      ', \
        queryCLUSTER('node' + str(l) + '_LANIP'), '   ', queryCLUSTER('node' + str(l) + '_MEMSIZE'), '   ', \
        queryCLUSTER('node' + str(l) + '_NUMCPU'), '    ', queryCLUSTER('node' + str(l) + '_NUMCORES'), '    ', \
        queryCLUSTER('node' + str(l) + '_NUMTHREADS'), '       ', queryCLUSTER('node' + str(l) + '_CAPACITY'), '        ', \
        queryCLUSTER('node' + str(l) + '_CPUhz')
print
