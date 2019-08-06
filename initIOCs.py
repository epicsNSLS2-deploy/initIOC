#!/usr/bin/python3

"""
Script for auto initialization of IOCs from CONFIGURE file.

This script was taken from the installSynApps set of scripts.
Usage instructions can be found in the README.md file in this repo.

Author: Jakub Wlodek
"""

# imports
from tkinter import *
import os
import re
import subprocess
import argparse
from sys import platform

# version number
version = "v0.0.4"

# Some constants
KERNEL_PATH_LIMIT = 127

supported_drivers = {
    'ADProsilica',
    'ADUVC',
    'ADPointGrey',
    'ADLambda',
    'ADSimDetector',
    'ADMerlin',
    'ADPerkinElmer',
    'ADPilatus',
    'ADSpinnaker',
    'ADAndor3',
    'ADURL'
}


class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = 0
        self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(tw, text=self.text, justify=LEFT,
                      background="#ffffe0", relief=SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)



class IOCAction:
    """
    Helper class that stores information and functions for each IOC in the CONFIGURE file

    Attributes
    ----------
    ioc_type : str
        name of areaDetector driver instance the IOC is linked to ex. ADProsilica
    ioc_name : str
        name of the IOC ex. cam-ps1
    ioc_prefix : str
        Prefix used by the IOC
    asyn_port : str
        asyn port used for outputting NDArrays
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


    def __init__(self, ioc_type, ioc_name, ioc_prefix, asyn_port, ioc_port, connection, ioc_num):
        """
        Constructor for the IOCAction class

        Parameters
        ----------
        ioc_type : str
            name of areaDetector driver instance the IOC is linked to ex. ADProsilica
        ioc_name : str
            name of the IOC ex. cam-ps1
        ioc_prefix : str
            Prefix used by the IOC
        asyn_port : str
            asyn port used for outputting NDArrays
        ioc_port : str
            telnet port on which procserver will run the IOC
        connection : str
            Value used to connect to the device ex. IP, serial num. etc.
        ioc_num : int
            Counter that keeps track of which IOC it is
        """

        self.ioc_type   = ioc_type
        self.ioc_name   = ioc_name
        self.ioc_prefix = ioc_prefix
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
        binary_path =  self.getIOCBin(bin_loc, bin_flat) 
        if binary_path is None:
            print('ERROR - Could not identify a compiled IOC binary for {}, skipping'.format(self.ioc_type))
            print('Make sure that the binary exists and is compiled in the expected location, and make sure BINARIES_FLAT is correct.')
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

            for file in os.listdir(ioc_path +"/startupScripts"):
                if startup_type in file.lower():
                    startup_path = startup_path + "/" + file
                    break
            
            exe_written = False

            example_st = open(startup_path, "r+")
            if platform =='win32':
                st_exe = open(ioc_path+'/st.cmd', 'w+')
                st_exe.write(binary_path+' st_base.cmd\n')
                st_exe.close()
                st = open(ioc_path+"/st_base.cmd", "w+")
                exe_written = True
            elif len(binary_path) > KERNEL_PATH_LIMIT:     # The path length limit for shebangs (#!/) on linux is usually kernel based and set to 127
                print('WARNING - Path to executable exceeds legal bash limit, generating st.cmd and st_base.cmd')
                st_exe = open(ioc_path + '/st.cmd', 'w+')
                st_exe.write(binary_path + ' st_base.cmd\n')
                st = open(ioc_path+"/st_base.cmd", "w+")
                st_exe.close()
                exe_written = True
            else:
                st = open(ioc_path+"/st.cmd", "w+")

            line = example_st.readline()

            while line:
                if "#!" in line:
                    if not exe_written:
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
                    if file.lower().startswith(startup_type):
                        print('Copying dependency file {} for {}'.format(file, self.ioc_type))
                        # Copy all required dependency files
                        os.rename(ioc_path + "/dependancyFiles/" + file, ioc_path + "/" + file.split('_', 1)[-1])
                        self.fix_macros(ioc_path + '/' + file.split('_', 1)[-1])

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
                if line.startswith('epicsEnvSet("ARCH",'):
                    if platform == 'win32':
                        env.write('epicsEnvSet("ARCH",       "windows-x64-static")\n')
                    else:
                        env.write('epicsEnvSet("ARCH",       "linux-x86_64")\n')
                elif "EPICS_BASE" in line and not bin_flat:
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
            Path to the IOC executable located in driverName/iocs/IOC/bin/OS/driverApp or None if not found
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
                # Add check to see if NOIOC in name - occasional problems generating ADSimDetector
                if "IOC" in name or "ioc" in name and "NOIOC" not in name.upper():
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


    def fix_macros(self, file_path):
        """
        Function that replaces certain macros in given filepath (used primarily for substitution files)

        Parameters
        ----------
        file_path : str
            path to the target file
        """

        os.rename(file_path, file_path + '_OLD')
        old = open(file_path+'_OLD', 'r')
        contents = old.read()
        contents = contents.replace('$(PREFIX)', self.ioc_prefix)
        contents = contents.replace('$(PORT)', self.asyn_port)
        new = open(file_path, 'w')
        new.write(contents)
        old.close()
        new.close()
        os.remove(file_path+'_OLD')


    def create_path_scripts(self, bin_loc, bin_flat, ioc_top):
        """
        Function that attempts to create scripts for setting the dev environment for the IOC given the location of the binaries.

        Parameters
        ----------
        bin_loc : str
            given path to binaries
        bin_flat : bool
            toggle that determines if the binaries have a flat structure or not
        ioc_top : str
            path to the ioc output_directory
        """

        if platform == "win32":
            delimeter = ';'
            closer = '%PATH%"'
            arch='windows-x64-static'
            path_file = open(ioc_top + '/' + self.ioc_name + '/dllPath.bat', 'w+')
            path_file.write('@ECHO OFF\n')
            path_file.write('SET "PATH=')
        else:
            delimeter = ':'
            closer = '$LD_LIBRARY_PATH'
            arch = 'linux-x86_64'
            path_file = open(ioc_top + '/' + self.ioc_name + '/ldpath.sh', 'w+')
            path_file.write('export LD_LIBRARY_PATH=')
        path_file.write(bin_loc + '/base/bin/' + arch)
        path_file.write(delimeter)
        path_file.write(bin_loc + '/base/lib/' + arch)
        path_file.write(delimeter)
        if bin_flat:
            support_dir = bin_loc
        else:
            support_dir = bin_loc + '/support'

        if os.path.exists(support_dir) and os.path.isdir(support_dir):
            for dir in os.listdir(support_dir):
                if os.path.isdir(support_dir + '/' + dir) and dir != "base" and dir != "areaDetector":
                    path_file.write(support_dir + '/' + dir + '/bin/' + arch)
                    path_file.write(delimeter)
                    path_file.write(support_dir + '/' + dir + '/lib/' + arch)
                    path_file.write(delimeter)

        ad_dir = support_dir + '/areaDetector'
        if os.path.exists(ad_dir) and os.path.isdir(ad_dir):
            for dir in os.listdir(ad_dir):
                if os.path.isdir(ad_dir + '/' + dir) and dir.startswith('AD'):
                    path_file.write(ad_dir + '/' + dir + '/bin/' + arch)
                    path_file.write(delimeter)
                    path_file.write(ad_dir + '/' + dir + '/lib/' + arch)
                    path_file.write(delimeter)

        path_file.write(closer)
        path_file.close()


    def cleanup(self, ioc_top):
        """ Function that runs the cleanup.sh/cleanup.bat script in ioc-template to remove unwanted files """

        cleanup_completed = False

        if platform == "win32":
            if(os.path.exists(ioc_top + "/" + self.ioc_name + "/cleanup.bat")):
                print("Performing cleanup for {}".format(self.ioc_name))
                out = subprocess.call([ioc_top + "/" + self.ioc_name + "/cleanup.bat"])
                print()
                cleanup_completed = True
        else:
            if(os.path.exists(ioc_top + "/" + self.ioc_name + "/cleanup.sh")):
                print("Performing cleanup for {}".format(self.ioc_name))
                out = subprocess.call(["bash", ioc_top + "/" + self.ioc_name + "/cleanup.sh"])
                print()
                cleanup_completed = True
        if os.path.exists(ioc_top +"/" + self.ioc_name + "/st.cmd"):
            os.chmod(ioc_top +"/" + self.ioc_name + "/st.cmd", 0o755)
        if not cleanup_completed:
            print("No cleanup script found, using outdated version of IOC template")


#-------------------------------------------------
#----------------MAIN SCRIPT FUNCTIONS------------
#-------------------------------------------------


def parse_line_into_action(line, prefix, ioc_num_counter):
    """
    Function that parses a line in the CONFIGURE table into an IOCAction object

    Parameters
    ----------
    line : str
        The line to parse from the table
    ioc_num_counter : int
        the ioc counter
    
    Returns
    -------
    ioc_action : IOCAction
        the IOCAction object that contains information parsed from the line
    """

    line = line.strip()
    line = re.sub('\t', ' ', line)
    line = re.sub(' +', ' ', line)
    temp = line.split(' ')
    ioc_action = IOCAction(temp[0], temp[1], prefix, temp[2], temp[3], temp[4], ioc_num_counter)
    return ioc_action


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
            ioc_action = parse_line_into_action(line, configuration['PREFIX'], ioc_num_counter)
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
    """ Function for printing initial message """

    print("+----------------------------------------------------------------+")
    print("+ initIOCs, Version: " + version +"                                      +")
    print("+ Author: Jakub Wlodek                                           +")
    print("+ Copyright (c): Brookhaven National Laboratory 2018-2019        +")
    print("+ This software comes with NO warranty!                          +")
    print("+----------------------------------------------------------------+")
    print()


def print_supported_drivers():
    """ Function that prints list of supported drivers """

    print('Supported Drivers:')
    print("+-----------------------------+")
    for driver in supported_drivers:
        print('+ {}'.format(driver))
    print()


def execute_ioc_action(action, configuration, bin_flat):
    """
    Function that runs all required IOC action functions with a given configuration

    Parameters
    ----------
    action : IOCAction
        currently executing IOC action
    configuration : dict of str to str
        configuration settings as read from CONFIGURE or inputted by user
    bin_flat : bool
        toggle that tells the script if binaries are flat of not
    """

    # Perform the overall process action
    out = action.process(configuration["IOC_DIR"], configuration["TOP_BINARY_DIR"], bin_flat)
    # if successfull, update any remaining required files
    if out == 0:
        action.update_unique(configuration["IOC_DIR"], configuration["TOP_BINARY_DIR"], bin_flat, 
            configuration["PREFIX"], configuration["ENGINEER"], configuration["HOSTNAME"], 
            configuration["CA_ADDRESS"])
        action.update_config(configuration["IOC_DIR"], configuration["HOSTNAME"])
        action.fix_env_paths(configuration["IOC_DIR"], bin_flat)
        action.create_path_scripts(configuration["TOP_BINARY_DIR"], bin_flat, configuration["IOC_DIR"])
        action.cleanup(configuration["IOC_DIR"])


def guided_init():
    """ Function that guides the user through generating a single IOC through the CLI """

    print_start_message()
    print('Welcome to initIOC!')
    configuration = {}
    configuration['IOC_DIR'] = input('Enter the ioc output location. > ')
    configuration['TOP_BINARY_DIR'] = input('Enter the location of your compiled binaries. > ')
    temp = input('Is the binary structure flat? (i.e. asyn, areaDetector etc. are in same directory as base) (y/n). > ')
    bin_flat = False
    if temp == 'y':
        bin_flat = True
    configuration['PREFIX'] = input('Enter the IOC Prefix (without the camera specific portion ex. XF:10IDC-BI). > ')
    configuration['HOSTNAME'] = input('Enter the IOC server hostname. > ')
    configuration['ENGINEER'] = input('Enter your name and contact information. > ')
    configuration['CA_ADDRESS'] = input('Enter the CA_ADDRESS IP. > ')
    another_ioc = True
    while another_ioc:
        driver_type = None
        while driver_type is None:
            driver_type = input('What driver type would you like to generate? > ')
            if driver_type not in supported_drivers:
                driver_type = None
                print('The selected driver type is not supported. See list of supported drivers below.')
                print_supported_drivers()
        ioc_name = input('What should the IOC name be? > ')
        asyn_port = input('What asyn port should the IOC use? (ex. PS1). > ')
        ioc_port = input('What telnet port should procServer use to run the IOC? > ')
        connection = input('Enter the connection param for your device. (ex. IP, serial number etc.) enter NA if not sure. > ')
        ioc_action = IOCAction(driver_type, ioc_name, configuration['PREFIX'], asyn_port, ioc_port, connection, 1)
        execute_ioc_action(ioc_action, configuration, bin_flat)
        another = input('Would you like to generate another IOC? (y/n). > ')
        if another != 'y':
            another_ioc = False


def init_iocs():
    """
    Main driver function. First calls read_ioc_config, then for each instance of IOCAction
    perform the process, update_unique, update_config, fix_env_paths, and cleanup functions
    """

    print_start_message()
    actions, configuration, bin_flat = read_ioc_config()
    init_ioc_dir(configuration["IOC_DIR"])
    for action in actions:
        if action.ioc_type not in supported_drivers:
            print('ERROR - {} is not currently a supported driver!'.format(action.ioc_type))
            print_supported_drivers()
            print('To request support for {} to be added to initIOC, please create an issue on:'.format(action.ioc_type))
            print('https://github.com/epicsNSLS2-deploy/initIOC/issues')
        else:
            execute_ioc_action(action, configuration, bin_flat)

def init_iocs_GUI(actions, configuration, bin_flat):
    for action in actions:
        print("I am in here " +  configuration[0])
        print(bin_flat)
        out = action.process(configuration[0], configuration[1], bin_flat)
        if out == 0:
            action.update_unique(configuration[0], configuration[1], bin_flat,
                configuration[3], configuration[4], configuration[5], 
                configuration[6])
            action.update_config(configuration[0], configuration[5])
            action.fix_env_paths(configuration[0], bin_flat)
            action.cleanup(configuration[0])


class Window(Frame):



# Define settings upon initialization. Here you can specify
    def __init__(self, master=None):     
        # parameters that you want to send through the Frame class. 
        Frame.__init__(self, master)   

        #reference to the master widget, which is the tk window                 
        self.master = master

        #with that, we want to then run init_window, which doesn't yet exist
        self.init_window()
    

    #Creation of init_window
    def init_window(self):
        check = False
        check2 = False 
        preffixValue = ""
        arr = []
        iocActions = []
        configfile = Text(wrap=WORD, width=100, height= 10)
        with open("CONFIGURE.txt", 'r+') as f:
            for line in f:
                line = line.strip()
                if line.startswith("#------------MAIN"):
                    check = True
                if check == True and  line != "":
                    arr.append(line)
                if line.startswith("# IOC Type"):
                    check = False
                    configfile.insert(INSERT, line)
                    configfile.pack(fill="none", expand=TRUE, side = RIGHT)
                if line.startswith("AD"):
                    configfile.insert(END, "\n")
                    configfile.insert(END, line)
                    stringInfo = preffixValue

                    r = stringInfo.split("=")
                    line = line + " " +r[1]
                    configfile.pack(fill="none", expand=TRUE, side = RIGHT)
                    iocActions.append(self.iocActionMaker(line))
                if line.startswith("#------------ADDITIONAL"):
                    check2 = True
                if check2 == True and line != "":
                    arr.append(line)
                if line.startswith("PREFIX"):
                    preffixValue = line
        
        commentArray = []
        fillinArray = []
        for i in range(len(arr)):
            if arr[i].startswith("#"):
                commentArray.append(arr[i])
            if arr[i].startswith("#") != True:
                fillinArray.append(arr[i])



        """ THIS IS MAKING ENTRY FOR THE USERS"""
        status1 = StringVar()
        status2 = StringVar()
        status3 = StringVar()
        status4 = StringVar()
        status5 = StringVar()
        status6 = StringVar()
        status7 = StringVar()


        stringInfo = fillinArray[0]
        r = stringInfo.split("=")
        strLable = str(r[0])

        ioc_Lable = Label(self, text = strLable)
        ioc_Lable.pack()
        ioc_Lable.place(x=0, y=0)

        strEntry = str(r[1])
        ioc_dir = Entry(self, textvariable = status1)
        ioc_dir.pack()
        ioc_dir.place(x=50, y=0)
        ioc_dir.insert(0, strEntry)
        
        stringInfo = fillinArray[1]
        r = stringInfo.split("=")
        strLable = str(r[0])
        top_Lable = Label(self, text=strLable)
        top_Lable.pack()
        top_Lable.place(x=1, y = 30)

        CreateToolTip(ioc_dir, commentArray[1])
        
        strEntry = str(r[1])
        top_binary = Entry(self, textvariable = status2)
        top_binary.pack()
        top_binary.place(x = 100, y = 30)
        top_binary.insert(0,strEntry)

        stringInfo = fillinArray[2]
        r = stringInfo.split("=")
        strLable = str(r[0])


        
        binary_Label = Label(self, text=strLable)
        binary_Label.pack()
        binary_Label.place(x = 2, y = 60)

        CreateToolTip(top_binary, commentArray[2])
        strEntry = str(r[1])
        binary_flat = Entry(self,textvariable=status3)
        binary_flat.pack()
        binary_flat.place(x = 90 , y = 60)
        binary_flat.insert(0, strEntry)
        

        
        stringInfo = fillinArray[3]
        r = stringInfo.split("=")
        strLable = str(r[0])

        CreateToolTip(binary_flat, commentArray[3])
        prefix_Label = Label(self, text=strLable)
        prefix_Label.pack()
        prefix_Label.place(x=3, y= 90)

        strEntry = str(r[1])
        prefix = Entry(self, textvariable=status4)
        prefix.pack()
        prefix.insert(0,strEntry)
        prefix.place(x = 45 , y = 90)

        doubleComment = commentArray[4] + "\n" +commentArray[5]

        CreateToolTip(prefix, doubleComment)

        
        
        stringInfo = fillinArray[4]
        r = stringInfo.split("=")
        strLable = str(r[0])

        engineer_label = Label(self, text=strLable)
        engineer_label.pack()
        engineer_label.place(x = 4 , y=110)

        

        strEntry = str(r[1])
        engineer = Entry(self, textvariable=status5)
        engineer.pack()
        engineer.insert(0,strEntry)
        engineer.place(x=65, y=110)

        CreateToolTip(engineer, commentArray[12])
        

        
        stringInfo = fillinArray[5]
        r = stringInfo.split("=")
        strLable = str(r[0])

        hostname_label = Label(self, text=strLable)
        hostname_label.pack()
        hostname_label.place(x=5,y=140)

        strEntry = str(r[1])
        hostname = Entry(self,textvariable=status6)
        hostname.pack()
        hostname.insert(0,strEntry)
        hostname.place(x = 75, y = 140)
        
        CreateToolTip(hostname, commentArray[13])

        
        stringInfo = fillinArray[6]
        r = stringInfo.split("=")
        strLable = str(r[0])

        ca_address_label = Label(self, text=strLable)
        ca_address_label.pack()
        ca_address_label.place(x=6, y=170)

       

        strEntry = str(r[1])
        ca_address = Entry(self,textvariable=status7)
        ca_address.pack()
        ca_address.insert(0,strEntry)
        ca_address .place(x=80, y=170)

        CreateToolTip(ca_address, commentArray[14])
   
        #v1 = StringVar()
        #v2 = StringVar()
        #v3 = StringVar()
        
        # changing the title of our master widget      
        self.master.title("initIOC_GUI")

        # allowing the widget to take the full space of the root window
        self.pack(fill=BOTH, expand=1)
        iocActions2 = []
        # creating a button instance
        saveButton = Button(self, text="Save",command=lambda: self.save(configfile)) 
        runButton = Button(self, text="Run", command=lambda: self.exe(status1,status2,status3,status4,status5,status6,status7,iocActions))
        addButton = Button(self, text = "Add IOC", command=lambda: iocActions.append(self.add_ioc(configfile,iocActions2)))
        # placing the button on my window
        addButton.place(x = 600, y = 150)
        addButton.pack()
        #saveButton.place(x=10, y=20)
        runButton.place(x=10, y=40)
        runButton.pack()
        #saveButton.pack()
        #advanceButton.place(x=200, y =2)

    def exe(self,status1,status2,status3,status4,status5,status6, status7, iocActions):
        bin_flats = False
        configurations = []
        configurations.append(status1.get())
        print(configurations[0])
        configurations.append(status2.get())
        configurations.append(status3.get())
        configurations.append(status4.get())
        configurations.append(status5.get())
        configurations.append(status6.get())
        configurations.append(status7.get())
        
        if  configurations[2] == "NO":
            bin_flats = False
        elif configurations[2] == "YES":
            bin_flats = True

        init_iocs_GUI(iocActions,configurations,bin_flats)


    def iocActionMaker(self,line):
        arr = []
        line = line.strip()
        while len(line) > 0:
            line = line.strip()
            info = line.split(" ")
            arr.append(info[0])
            print(info[0])
            line = line.replace(info[0], "")
        action = IOCAction(arr[0],arr[1], arr[5],   arr[2],arr[3], arr[4], 10)
        return action


    def save(self,configfile):
        file = open("CONFIGURE.txt", 'r+')
        if file != None:
        # slice off the last character from get, as an extra return is added
            data = configfile.get('1.0', END+'-1c')
            file.write(data)
            file.close()

    def client_exit(self):
        exit()

    def add_ioc(self, configfile,iocActions2):
        newWindow = Toplevel(self)

        
        #display = Label(newWindow, text = "Add IOC")
        #   display.pack()
        v1 = StringVar()
        v2 = StringVar()
        v3 = StringVar()
        v4 = StringVar()
        v5 = StringVar()

        # changing the title of our master widget      

        w = Label(newWindow, text="ioc_type")
        w.pack()
        w.place(x=30,y=50)

        e1 = Entry(newWindow, textvariable=v1)
        e1.place(x=80,y=50)

        w = Label(newWindow, text = "")
        w.pack()

        w = Label(newWindow, text="ioc_name")
        w.pack()
        w.place(x=30, y=70)
        
        e2 = Entry(newWindow,textvariable=v2)
        e2.place(x=85, y=70)
        
        w = Label(newWindow, text = "")
        w.pack()

        w = Label(newWindow, text="asyn_port")
        w.pack()
        w.place(x=30,y=100)

        e3 = Entry(newWindow,textvariable=v3)
        e3.place(x=85, y=100)

        w = Label(newWindow, text = "")
        w.pack()

        w = Label(newWindow, text="ioc_port")
        w.pack()
        w.place(x=30,y=130)

        e4 = Entry(newWindow,textvariable=v4)
        e4.place(x=95,y=130)

        w = Label(newWindow, text = "")
        w.pack()


        w = Label(newWindow, text="connection")
        w.pack()
        w.place(x=30,y=160)

        e5 = Entry(newWindow,textvariable=v5)
        e5.place(x=95,y=160)

        w = Label(newWindow, text = "")
        w.pack()

        submitButton = Button(newWindow,text="Submit", command=lambda: iocActions2.append(self.submit(configfile, v1, v2, v3, v4, v5, newWindow,iocActions2)))
        submitButton.pack()
        submitButton.place(x=0, y=0)
        ##init_iocs()
        if len(iocActions2) > 0:
            return iocActions2.pop(0)
        else:
            return print("Error")




    def submit(self, configfile, v1,v2,v3,v4,v5,newWindow,iocActions2s):
        camera_info = v1.get() + "   " + v2.get() + "         " + v3.get() + "         " + v4.get() + "         " + v5.get()

        if v1.get() ==  "" and v2.get() == "" and v3.get() == "" and v4.get() == "" and v5.get() == "":
            
            
            popup = Tk()
            popup.wm_title("Error")
            new_display = Label(popup, text = "You have to fill everything in!!")
            new_display.pack()
            okay = Button(popup, text = "Okay", command = popup.destroy)
            okay.pack()
            popup.mainloop()
            new_display.pack()
            return print("Error")
        elif v1.get() !=  "" and v2.get() != "" and v3.get() != "" and v4.get() != "" and v5.get() != "":

            ##configfile.delete("1.0", END)
            ##configfile.update()
            configfile.insert(INSERT, "\n")
            configfile.insert(INSERT, camera_info)
            newWindow2 = Toplevel(self)
            l1 = Label(newWindow2, text="Would you like to add a new IOC again?")
            l1.pack()
            action = self.iocActionMaker(camera_info)

            yesButton = Button(newWindow2, text = "Yes")
            yesButton.pack()
            noButton = Button(newWindow2, text = "No", command=lambda: self.delete(newWindow,newWindow2))
            noButton.pack()
            return action
        else:
            popup = Tk()
            popup.wm_title("Error")
            new_display = Label(popup, text = "You have to fill everything in!!")
            new_display.pack()
            okay = Button(popup, text = "Okay", command = popup.destroy)
            okay.pack()
            popup.mainloop()
            new_display.pack()
            return print("Error")

            
        
    def reAdd(self, newWindow2):
        newWindow2.destroy()

    
    def delete(self, newWindow, newWindow2):
        newWindow.destroy()
        newWindow2.destroy()   

def parse_args():
    parser = argparse.ArgumentParser(description='A script for auto-initializing areaDetector IOCs. Edit the CONFIGURE file and run without arguments for default operation.')

    parser.add_argument('-i', '--individual', action='store_true', help='Add this flag to go through a guided process for generating a single IOC at a time.')
    parser.add_argument('-g', '--gui', action='store_true', help='Add this flag to enable the GUI version of initIOC.')
    arguments = vars(parser.parse_args())
    if arguments['individual']:
        guided_init()
    elif arguments['gui']:
        root = Tk()

        root.geometry("1080x1080")

        app = Window(root)
        root.mainloop()

        print('The initIOC gui is not yet supported in version {} - Exiting'.format(version))
        exit()
    else:
        init_iocs()



# Run the script
parse_args()



