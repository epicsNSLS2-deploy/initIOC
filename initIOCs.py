#!/usr/bin/python3

# script for auto initialization of IOCs from CONFIGURE file
#
# Author: Jakub Wlodek
#
# This script was taken from the installSynApps set of scripts.
# Usage instructions can be found in the README.md file in this repo.
#

# imports
import os
import re
import subprocess
from sys import platform

# version number
version = "v0.0.2"


class IOCAction:
    """
    Helper class that stores information and functions for each IOC in the CONFIGURE file

    Attributes
    ----------
    ioc_type : str
        name of areaDetector driver instance the IOC is linked to ex. ADProsilica
    ioc_name : str
        name of the IOC ex. cam-ps1
    ioc_port : str
        telnet port on which procserver will run the IOC
    connection : str
        Value used to connect to the device ex. IP, serial num. etc.
    ioc_num : int
        Counter that keeps track of which IOC it is

    Methods
    -------
    process(ioc_top : str, bin_loc : str, bin_flat : bool)
        clones ioc-template instance, sets up appropriate st.cmd.
    update_unique(ioc_top : str, bin_loc : str, bin_flat : bool, prefix : str, engineer : str, hostname : str, ca_ip : str)
        Updates unique.cmd file with all of the required configuration options
    update_config(ioc_top : str, hostname : str)
        updates the config file with appropriate options
    fix_env_paths(ioc_top: str, bin_flat : bool)
        fixes the existing envpaths with new locations
    getIOCbin(bin_loc : str, bin_flat : bool)
        finds the path to the binary for the IOC based on binary top location
    cleanup(ioc_top : str)
        runs cleanup.sh script to remove unwanted files in generated IOC.
    """

    def __init__(self, ioc_type, ioc_name, asyn_port, ioc_port, connection, ioc_num):
        """
        Constructor for the IOCAction class

        Parameters
        ----------
        ioc_type : str
        name of areaDetector driver instance the IOC is linked to ex. ADProsilica
        ioc_name : str
            name of the IOC ex. cam-ps1
        ioc_port : str
            telnet port on which procserver will run the IOC
        connection : str
            Value used to connect to the device ex. IP, serial num. etc.
        ioc_num : int
            Counter that keeps track of which IOC it is
        """

        self.ioc_type   = ioc_type
        self.ioc_name   = ioc_name
        self.asyn_port  = asyn_port
        self.ioc_port   = ioc_port
        self.connection = connection
        self.ioc_num    = ioc_num
    

    def process(self, ioc_top, bin_loc, bin_flat):
        """
        Function that clones ioc-template, and pulls correct st.cmd from startupScripts folder
        The binary for the IOC is also identified and inserted into st.cmd

        Parameters
        ----------
        ioc_top : str
            Path to the top directory to contain generated IOCs
        bin_loc : str
            path to top level of binary distribution
        bin_flat : bool
            flag for deciding if binaries are flat or stacked

        Returns
        -------
        int
            -1 if error, 0 if success
        """

        print("-------------------------------------------")
        print("Setup process for IOC " + self.ioc_name)
        print("-------------------------------------------")
        if os.path.exists(ioc_top + '/' + self.ioc_name):
            print('ERROR - IOC with name {} already exists.'.format(self.ioc_name))
            return -1
        out = subprocess.call(["git", "clone", "--quiet", "https://github.com/epicsNSLS2-deploy/ioc-template", ioc_top + "/" + self.ioc_name])
        if out != 0:
            print("Error failed to clone IOC template for ioc {}".format(self.ioc_name))
            return -1
        else:
            print("IOC template cloned, converting st.cmd")
            ioc_path = ioc_top +"/" + self.ioc_name
            os.remove(ioc_path+"/st.cmd")

            startup_path = ioc_path+"/startupScripts"
            startup_type = self.ioc_type[2:].lower()

            found = False

            for file in os.listdir(ioc_path +"/startupScripts"):
                if startup_type in file.lower():
                    startup_path = startup_path + "/" + file
                    found = True
                    break
            if not found:
                print('ERROR - {} is not yet supported by initIOCs, skipping'.format(self.ioc_type))
                return -1
            
            example_st = open(startup_path, "r+")
            st = open(ioc_path+"/st.cmd", "w+")

            line = example_st.readline()

            while line:
                if "#!" in line:
                    binary_path =  self.getIOCBin(bin_loc, bin_flat) 
                    if binary_path is None:
                        print('ERROR - Could not identify a compiled IOC binary for {}, skipping'.format(self.ioc_type))
                        return -1
                    st.write("#!" + binary_path + "\n")
                elif "envPaths" in line:
                    st.write("< envPaths\n")
                else:
                    st.write(line)

                line = example_st.readline()

            example_st.close()
            st.close()

            autosave_path = ioc_path + "/autosaveFiles"
            autosave_type = self.ioc_type[2:].lower()
            if os.path.exists(autosave_path + "/" + autosave_type + "_auto_settings.req"):
                print("Generating auto_settings.req file for IOC {}.".format(self.ioc_name))
                os.rename(autosave_path + "/" + autosave_type + "_auto_settings.req", ioc_path + "/auto_settings.req")
            else:
                print("Could not find supported auto_settings.req file for IOC {}.".format(self.ioc_name))

            if os.path.exists(ioc_path + "/dependancyFiles"):
                for file in os.listdir(ioc_path + "/dependancyFiles"):
                    if startup_type in file.lower():
                        print('Copying dependency file {} for {}'.format(file, self.ioc_type))
                        os.rename(ioc_path + "/dependancyFiles/" + file, ioc_path + "/" + file)

            return 0


    def update_unique(self, ioc_top, bin_loc, bin_flat, prefix, engineer, hostname, ca_ip):
        """
        Function that updates the unique.cmd file with all of the required configurations

        Parameters
        ----------
        ioc_top : str
            Path to the top directory to contain generated IOCs
        bin_loc : str
            path to top level of binary distribution
        bin_flat : bool
            flag for deciding if binaries are flat or stacked
        prefix : str
            Prefix given to the IOC
        engineer : str
            Name of the engineer deploying the IOC
        hostname : str
            name of the host IOC server on which the IOC will run
        ca_ip : str
            Channel Access IP address
        """

        if os.path.exists(ioc_top + "/" + self.ioc_name +"/unique.cmd"):
            print("Updating unique file based on configuration")
            unique_path = ioc_top + "/" + self.ioc_name +"/unique.cmd"
            unique_old_path = ioc_top +"/" + self.ioc_name +"/unique_OLD.cmd"
            os.rename(unique_path, unique_old_path)

            uq_old = open(unique_old_path, "r")
            uq = open(unique_path, "w")
            line = uq_old.readline()
            while line:
                if not line.startswith('#'):
                    if "SUPPORT_DIR" in line:
                        if bin_flat:
                            uq.write('epicsEnvSet("SUPPORT_DIR", "{}")\n'.format(bin_loc))
                        else:
                            uq.write('epicsEnvSet("SUPPORT_DIR", "{}")\n'.format(bin_loc + "/support"))
                    elif "ENGINEER" in line:
                        uq.write('epicsEnvSet("ENGINEER", "{}")\n'.format(engineer))
                    elif "CAM-CONNECT" in line:
                        uq.write('epicsEnvSet("CAM-CONNECT", "{}")\n'.format(self.connection))
                    elif "HOSTNAME" in line:
                        uq.write('epicsEnvSet("HOSTNAME", "{}")\n'.format(hostname))
                    elif "PREFIX" in line and "CTPREFIX" not in line:
                        uq.write('epicsEnvSet("PREFIX", "{}")\n'.format(prefix + "{{{}}}".format(self.ioc_type[2:] +"-Cam:{}".format(self.ioc_num))))
                    elif "CTPREFIX" in line:
                        uq.write('epicsEnvSet("CTPREFIX", "{}")\n'.format(prefix + "{{{}}}".format(self.ioc_type[2:] +"-Cam:{}".format(self.ioc_num))))
                    elif "IOCNAME" in line:
                        uq.write('epicsEnvSet("IOCNAME", "{}")\n'.format(self.ioc_name))
                    elif "EPICS_CA_ADDR_LIST" in line:
                        uq.write('epicsEnvSet("EPICS_CA_ADDR_LIST", "{}")\n'.format(ca_ip))
                    elif "IOC" in line and "IOCNAME" not in line:
                        uq.write('epicsEnvSet("IOC", "{}")\n'.format("ioc"+self.ioc_type))
                    elif "PORT" in line:
                        uq.write('epicsEnvSet("PORT", "{}")\n'.format(self.asyn_port))
                    else:
                        uq.write(line)
                else:
                    uq.write(line)
                line = uq_old.readline()

            uq_old.close()
            uq.close()
        else:
            print("No unique file found, proceeding to next step")


    def update_config(self, ioc_top, hostname):
        """
        Function that updates the config file with the correct IOC name, port, and hostname

        Parameters
        ----------
        ioc_top : str
            Path to the top directory to contain generated IOCs
        hostname : str
            name of the host IOC server on which the IOC will run
        """

        conf_path = ioc_top + "/" + self.ioc_name + "/config"
        if os.path.exists(conf_path):
            print("Updating config file for procServer connection")
            conf_old_path = ioc_top + "/" + self.ioc_name + "/config_OLD"
            os.rename(conf_path, conf_old_path)
            cn_old = open(conf_old_path, "r")
            cn = open(conf_path, "w")
            line = cn_old.readline()
            while line:
                if "NAME" in line:
                    cn.write("NAME={}\n".format(self.ioc_name))
                elif "PORT" in line:
                    cn.write("PORT={}\n".format(self.ioc_port))
                elif "HOST" in line:
                    cn.write("HOST={}\n".format(hostname))
                else:
                    cn.write(line)
                line = cn_old.readline()
            cn_old.close()
            cn.close()
        else:
            print("No config file found moving to next step")


    def fix_env_paths(self, ioc_top, bin_flat):
        """
        Function that fixes the envPaths file if binaries are not flat

        Parameters
        ----------
        ioc_top : str
            Path to the top directory to contain generated IOCs
        bin_flat : bool
            flag for deciding if binaries are flat or stacked
        """

        env_path = ioc_top + "/" + self.ioc_name + "/envPaths"
        if os.path.exists(env_path):
            env_old_path = ioc_top + "/" + self.ioc_name + "/envPaths_OLD"
            os.rename(env_path, env_old_path)
            env_old = open(env_old_path, "r")
            env = open(env_path, "w")
            line = env_old.readline()
            while line:
                if "EPICS_BASE" in line and not bin_flat:
                    print("Fixing base location in envPaths")
                    env.write('epicsEnvSet("EPICS_BASE", "$(SUPPORT)/../base")\n')
                else:
                    env.write(line)
                line = env_old.readline()
            env_old.close()
            env.close()


    def getIOCBin(self, bin_loc, bin_flat):
        """
        Function that identifies the IOC binary location based on its type and the binary structure

        Parameters
        ----------
        bin_loc : str
            path to top level of binary distribution
        bin_flat : bool
            flag for deciding if binaries are flat or stacked
        
        Return
        ------
        driver_path : str
            Path to the IOC executable located in driverName/iocs/IOC/bin/OS/driverApp
        """

        try:
            if bin_flat:
                # if flat, there is no support directory
                driver_path = bin_loc + "/areaDetector/" + self.ioc_type
            else:
                driver_path = bin_loc + "/support/areaDetector/" + self.ioc_type
            # identify the IOCs folder
            for name in os.listdir(driver_path):
                if "ioc" == name or "iocs" == name:
                    driver_path = driver_path + "/" + name
                    break
            # identify the IOC 
            for name in os.listdir(driver_path):
                if "IOC" in name or "ioc" in name:
                    driver_path = driver_path + "/" + name
                    break 
            # Find the bin folder
            driver_path = driver_path + "/bin"
            # There should only be one architecture
            for name in os.listdir(driver_path):
                driver_path = driver_path + "/" + name
                break
            # We look for the executable that ends with App
            for name in os.listdir(driver_path):
                if 'App' in name:
                    driver_path = driver_path + "/" + name
                    break

            return driver_path
        except FileNotFoundError:
            return None


    def cleanup(self, ioc_top):
        """ Function that runs the cleanup.sh/cleanup.bat script in ioc-template to remove unwanted files """

        cleanup_completed = False

        if platform == "linux":
            if(os.path.exists(ioc_top + "/" + self.ioc_name + "/cleanup.sh")):
                print("Performing cleanup for {}".format(self.ioc_name))
                out = subprocess.call(["bash", ioc_top + "/" + self.ioc_name + "/cleanup.sh"])
                print()
                cleanup_completed = True
        elif platform == "win32":
            if(os.path.exists(ioc_top + "/" + self.ioc_name + "/cleanup.bat")):
                print("Performing cleanup for {}".format(self.ioc_name))
                out = subprocess.call([ioc_top + "/" + self.ioc_name + "/cleanup.bat"])
                print()
                cleanup_completed = True
        if os.path.exists(ioc_top +"/" + self.ioc_name + "/st.cmd"):
            os.chmod(ioc_top +"/" + self.ioc_name + "/st.cmd", 0o755)
        if not cleanup_completed:
            print("No cleanup script found, using outdated version of IOC template")


#-------------------------------------------------
#----------------MAIN SCRIPT FUNCTIONS------------
#-------------------------------------------------


def read_ioc_config():
    """
    Function for reading the CONFIGURE file. Returns a dictionary of configure options,
    a list of IOCAction instances, and a boolean representing if binaries are flat or not

    Returns
    -------
    ioc_actions : List of IOCAction
        list of IOC actions that need to be performed.
    configuration : dict of str -> str
        Dictionary containing all options read from configure
    bin_flat : bool
        toggle for flat or stacked binary directory structure
    """

    ioc_config_file = open("CONFIGURE", "r+")
    ioc_actions = []
    configuration = {}
    bin_flat = True
    ioc_num_counter = 1

    line = ioc_config_file.readline()
    while line:
        if "=" in line and not line.startswith('#') and "BINARIES_FLAT" not in line:
            line = line.strip()
            split = line.split('=')
            configuration[split[0]] = split[1]
        elif "BINARIES_FLAT" in line:
            if "NO" in line:
                bin_flat = False
        elif not line.startswith('#') and len(line) > 1:
            line = line.strip()
            line = re.sub(' +', ' ', line)
            temp = line.split(' ')
            ioc_action = IOCAction(temp[0], temp[1], temp[2], temp[3], temp[4], ioc_num_counter)
            ioc_num_counter = ioc_num_counter + 1
            ioc_actions.append(ioc_action)

        line = ioc_config_file.readline()

    ioc_config_file.close()
    return ioc_actions, configuration, bin_flat


def init_ioc_dir(ioc_top):
    """
    Function that creates ioc directory if it has not already been created.

    Parameters
    ----------
    ioc_top : str
        Path to the top directory to contain generated IOCs
    """

    if ioc_top == "":
        print("Error: IOC top not initialized")
        exit()
    elif os.path.exists(ioc_top) and os.path.isdir(ioc_top):
        print("IOC Dir already exits.")
        print()
    else:
        os.mkdir(ioc_top)


def print_start_message():
    """
    Function for printing initial message
    """

    print("+----------------------------------------------------------------+")
    print("+ initIOCs, Version: " + version +"                                      +")
    print("+ Author: Jakub Wlodek                                           +")
    print("+ Copyright (c): Brookhaven National Laboratory 2018-2019        +")
    print("+ This software comes with NO warranty!                          +")
    print("+----------------------------------------------------------------+")
    print()


def init_iocs():
    """
    Main driver function. First calls read_ioc_config, then for each instance of IOCAction
    perform the process, update_unique, update_config, fix_env_paths, and cleanup functions
    """

    print_start_message()
    actions, configuration, bin_flat = read_ioc_config()
    init_ioc_dir(configuration["IOC_DIR"])
    for action in actions:
        out = action.process(configuration["IOC_DIR"], configuration["TOP_BINARY_DIR"], bin_flat)
        if out == 0:
            action.update_unique(configuration["IOC_DIR"], configuration["TOP_BINARY_DIR"], bin_flat, 
                configuration["PREFIX"], configuration["ENGINEER"], configuration["HOSTNAME"], 
                configuration["CA_ADDRESS"])
            action.update_config(configuration["IOC_DIR"], configuration["HOSTNAME"])
            action.fix_env_paths(configuration["IOC_DIR"], bin_flat)
            action.cleanup(configuration["IOC_DIR"])


# Run the script
init_iocs()



