#!/usr/bin/python3

# script for auto initialization of IOCs from CONFIGURE file
#
# Author: Jakub Wlodek
#
# This script was taken from the installSynApps set of scripts.
# Usage instructions can be found in the README.md file in this repo.
#

import os
import re
import subprocess


#
# Helper class that stores information and functions for each IOC in the CONFIGURE file
#
class IOCAction:

    def __init__(self, ioc_type, ioc_name, ioc_port, connection, ioc_num):
        self.ioc_type = ioc_type
        self.ioc_name = ioc_name
        self.ioc_port = ioc_port
        self.connection = connection
        self.ioc_num = ioc_num
    

    #
    # Function that clones ioc-template, and pulls correct st.cmd from startupScripts folder
    # The binary for the IOC is also identified and inserted into st.cmd
    #
    def process(self, ioc_top, bin_loc, bin_flat):
        out = subprocess.call(["git", "clone", "https://github.com/epicsNSLS2-deploy/ioc-template", ioc_top + "/" + self.ioc_name])
        if out != 0:
            print("Error failed to clone IOC template for ioc {}".format(self.ioc_name))
        else:
            print("Initializing IOC template for " + self.ioc_name)
            ioc_path = ioc_top +"/" + self.ioc_name
            os.remove(ioc_path+"/st.cmd")

            startup_path = ioc_path+"/startupScripts"
            startup_type = self.ioc_type[2:].lower()

            for file in os.listdir(ioc_path +"/startupScripts"):
                if startup_type in file.lower():
                    startup_path = startup_path + "/" + file
                    break
            example_st = open(startup_path, "r+")
            st = open(ioc_path+"/st.cmd", "w+")

            line = example_st.readline()

            while line:
                if "#!" in line:
                    st.write("#!" + self.getIOCBin(bin_loc, bin_flat) + "\n")
                elif "envPaths" in line:
                    st.write("< envPaths\n")
                else:
                    st.write(line)

                line = example_st.readline()

            example_st.close()
            st.close()
    

    #
    # Function that updates the unique.cmd file with all of the required configurations
    #
    def update_unique(self, ioc_top, bin_loc, bin_flat, prefix, engineer, hostname, ca_ip):
        if os.path.existis(ioc_top + "/" + self.ioc_name +"/unique.cmd":
            unique_path = ioc_top + "/" + self.ioc_name +"/unique.cmd"
            unique_old_path = ioc_top +"/" + self.ioc_name +"/unique_OLD.cmd"
            os.rename(unique_path, unique_old_path)

            uq_old = open(unique_old_path, "r")
            uq = open(unique_path, "w")
            line = uq_old.readline()
            while line:
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
                elif "PREFIX" in line:
                    uq.write('epicsEnvSet("PREFIX", "{}")\n'.format(prefix + "{{{}}}".format(self.ioc_type[2:] +"-Cam:"+self.ioc_num)))
                elif "CTPREFIX" in line:
                    uq.write('epicsEnvSet("CTPREFIX", "{}")\n'.format(prefix + "{{{}}}".format(self.ioc_type[2:] +"-Cam:"+self.ioc_num)))
                elif "IOCNAME" in line:
                    uq.write('epicsEnvSet("IOCNAME", "{}")\n'.format(ca_ip))
                elif "EPICS_CA_ADDR_LIST" in line:
                    uq.write('epicsEnvSet("EPICS_CA_ADDR_LIST", "{}")\n'.format(ca_ip))
                elif "IOC" in line and "IOCNAME" not in line:
                    uq.write('epicsEnvSet("IOC", "{}")\n'.format("ioc"+self.ioc_type))
                elif "PORT" in line:
                    uq.write('epicsEnvSet("PORT", "{}")\n'.format(self.ioc_type[2:]+"1"))
                else:
                    uq.write(line)
                line = uq_old.readline()

            uq_old.close()
            uq.close()


    #
    # Function that updates the config file with the correct IOC name, port, and hostname
    #
    def update_config(self, ioc_top, hostname):
        conf_path = ioc_top + "/" + self.ioc_name + "/config"
        if os.path.exists(conf_path):
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


    #
    # Function that fixes the envPaths file if binaries are not flat
    #
    def fix_env_paths(self, ioc_top, bin_flat):
        env_path = ioc_top + "/" + self.ioc_name + "/envPaths"
        if os.path.exists(env_path):
            env_old_path = ioc_top + "/" + self.ioc_name + "/envPaths_OLD"
            os.rename(env_path, env_old_path)
            env_old = open(env_old_path, "r")
            env = open(env_path, "w")
            line = env_old.readline()
            while line:
                if "EPICS_BASE" in line and not bin_flat:
                    env.write('epicsEnvSet("EPICS_BASE", "$(SUPPORT)/../base)\n')
                else:
                    env.write(line)
                line = env_old.readline()
            env_old.close()
            env.close()


    #
    # Function that identifies the IOC binary location based on its type and the binary structure
    #
    def getIOCBin(self, bin_loc, bin_flat):
        if bin_flat:
            driver_path = bin_loc + "/areaDetector/" + self.ioc_type
        else:
            driver_path = bin_loc + "/support/areaDetector/" + self.ioc_type
        for name in os.listdir(driver_path):
            if "ioc" == name or "iocs" == name:
                driver_path = driver_path + "/" + name
                break
        for name in os.listdir(driver_path):
            if "IOC" in name or "ioc" in name:
                driver_path = driver_path + "/" + name
                break 
        driver_path = driver_path + "/bin"
        for name in os.listdir(driver_path):
            driver_path = driver_path + "/" + name
            break
        for name in os.listdir(driver_path):
            driver_path = driver_path + "/" + name
            break
        return driver_path


    #
    # Function that runs the cleanup.sh script in ioc-template to remove unwanted files
    #
    def cleanup(self, ioc_top):
        if(os.path.exists(ioc_top + "/" + self.ioc_name + "/cleanup.sh")):
            print("Performing cleanup for {}".format(self.ioc_name))
            out = subprocess.call(["bash", ioc_top + "/" + self.ioc_name + "/cleanup.sh"])
        else:
            print("No cleanup script found, using outdated version of IOC template")


#----------------MAIN SCRIPT FUNCTIONS------------

#
# Function for reading the CONFIGURE file. Returns a dictionary of configure options,
# a list of IOCAction instances, and a boolean representing if binaries are flat or not
#
def read_ioc_config():
    ioc_config_file = open("CONFIGURE", "r+")
    ioc_actions = []
    configuration = {}
    bin_flat = True
    ioc_num_counter = 0

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
            ioc_action = IOCAction(temp[0], temp[1], temp[2], temp[3], ioc_num_counter)
            ioc_num_counter = ioc_num_counter + 1
            ioc_actions.append(ioc_action)

        line = ioc_config_file.readline()

    ioc_config_file.close()
    return ioc_actions, configuration, bin_flat


#
# If the IOC directory does not yet exist, we create it
#
def init_ioc_dir(ioc_top):
    if ioc_top == "":
        print("Error: IOC top not initialized")
        exit()
    elif os.path.exists(ioc_top) and os.path.isdir(ioc_top):
        print("IOC Dir already exits.")
    else:
        os.mkdir(ioc_top)


#
# Main driver function. First calls read_ioc_config, then for each instance of IOCAction
# perform the process, update_unique, update_config, fix_env_paths, and cleanup functions
#
def init_iocs():
    actions, configuration, bin_flat = read_ioc_config()
    init_ioc_dir(configuration["IOC_DIR"])
    for action in actions:
        action.process(configuration["IOC_DIR"], configuration["TOP_BINARY_DIR"], bin_flat)
        action.update_unique(configuration["IOC_DIR"], configuration["TOP_BINARY_DIR"], bin_flat, 
            configuration["PREFIX"], configuration["ENGINEER"], configuration["HOSTNAME"], 
            configuration["CA_ADDRESS"])
        action.update_config(configuration["IOC_DIR"], configuration["HOSTNAME"])
        action.fix_env_paths(configuration["IOC_DIR"], bin_flat)
        action.cleanup(configuration["IOC_DIR"])


# Run the script
init_iocs()



