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


class IOCAction:

    def __init__(self, ioc_type, ioc_name):
        self.ioc_type = ioc_type
        self.ioc_name = ioc_name
    

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
            self.cleanup(ioc_top)


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


    def cleanup(self, ioc_top):
        if(os.path.exists(ioc_top + "/" + self.ioc_name + "/cleanup.sh")):
            print("Performing cleanup for {}".format(self.ioc_name))
            out = subprocess.call(["bash", ioc_top + "/" + self.ioc_name + "/cleanup.sh"])
        else:
            print("No cleanup script found, using outdated version of IOC template")




def read_ioc_config():
    ioc_config_file = open("CONFIGURE", "r+")
    ioc_actions = []
    ioc_top = ""
    bin_top = ""
    bin_flat = True

    line = ioc_config_file.readline()
    while line:
        if "IOC_DIR" in line:
            ioc_top = line.strip().split('=')[1]
        elif "TOP_BINARY_DIR" in line:
            bin_top = line.strip().split('=')[1]
        elif "BINARIES_FLAT" in line:
            if "NO" in line:
                bin_flat = False
        elif not line.startswith('#') and len(line) > 1:
            line = line.strip()
            line = re.sub(' +', ' ', line)
            temp = line.split(' ')
            ioc_action = IOCAction(temp[0], temp[1])
            ioc_actions.append(ioc_action)

        line = ioc_config_file.readline()
    return ioc_actions, ioc_top, bin_top, bin_flat


def init_ioc_dir(ioc_top):
    if ioc_top == "":
        print("Error: IOC top not initialized")
        exit()
    elif os.path.exists(ioc_top) and os.path.isdir(ioc_top):
        print("IOC Dir already exits.")
    else:
        os.mkdir(ioc_top)


def init_iocs():
    actions, ioc_top, bin_top, bin_flat = read_ioc_config()
    print(read_ioc_config())
    init_ioc_dir(ioc_top)
    for action in actions:
        action.process(ioc_top, bin_top, bin_flat)


init_iocs()



