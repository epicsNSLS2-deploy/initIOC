#!/usr/bin/env python3

import initIOCs

#-------------------------------------------------
#---------------- MAIN GUI CLASSES ---------------
#-------------------------------------------------


# Include guard in case user doesn't have tkinter installed but still wants to use the CLI version
WITH_GUI=True
try:
    from tkinter import *
    from tkinter import messagebox
    from tkinter import simpledialog
    import tkinter.scrolledtext as ScrolledText
    from tkinter import font as tkFont
    from tkinter import ttk
    import threading
    import webbrowser
except ImportError:
    WITH_GUI=False




class ToolTip:
    """
    Class for handling tool tips in the initIOC GUI.

    Attributes
    ----------
    widget : tkinter widget
        target widget for which to display tooltip
    tipwindow : window
        tooltip window
    id : int
        id number
    x, y : int
        coordinates of the tooltip
    """

    # Written by Michael Posada

    def __init__(self, widget):
        """Constructor for ToolTip class
        """

        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = 0
        self.y = 0


    def showtip(self, text):
        """Function that actually displays the tooltip
        """

        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, _, cy = self.widget.bbox("insert")
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
        """Function that destroys the tooltip
        """

        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


def CreateToolTip(widget, text):
    """Function that binds the tooltip to a widget

    Parameters
    ----------
    widget : tkinter widget
        widget to bind to
    text : str
        tooltip text
    """

    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


class InitIOCGui:
    """Class representing the main GUI for initIOCs.

    Attributes
    ----------
    master : Tk window
        the containing window
    frame : tk frame
        the main frame
    ioc_num_counter : int
        counter for number of IOCs deployed.
    actions, configuration, bin_flat : list of IOCAction, dict of {str,str}, bool
        configuration of IOCs to generate

    Methods
    -------
    initWindow()
        initializes the window
    writeToIOCPanel()
        writes to the ioc panel
    readGUIConfig()
        parses gui data into actions, configuration, binflat
    execute()
        executes the ioc actions
    save()
        saves the IOC configuration
    openAddIOCWindow()
        opens window to add new IOC
    """

    def __init__(self, master, configuration, actions, manager):
        """ Constructor for InitIOCGui """

        self.master = master
        self.configuration = configuration
        self.manager = manager

        self.master.protocol('WM_DELETE_WINDOW', self.thread_cleanup)
        self.frame = Frame(self.master)
        self.frame.pack()

        self.largeFont = tkFont.Font(size = 12)
        self.largeFontU = tkFont.Font(size = 12)
        self.largeFontU.configure(underline = True)

        self.showPopups = BooleanVar()
        self.showPopups.set(True)
        self.askAnother = BooleanVar()
        self.askAnother.set(False)

        self.executionThread = threading.Thread()

        menubar = Menu(self.master)

        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label='Save Configuration',    command=self.save)
        filemenu.add_command(label='Save Log',              command=self.saveLog)
        filemenu.add_command(label='Clear Log',             command=self.clearLog)
        filemenu.add_command(label='Exit',                  command=self.thread_cleanup)
        menubar.add_cascade(label='File', menu=filemenu)

        editmenu = Menu(menubar, tearoff=0)
        editmenu.add_command(label='Add IOC',           command=self.openAddIOCWindow)
        editmenu.add_command(label='Clear IOC table',   command=self.initIOCPanel)
        editmenu.add_checkbutton(label='Toggle Popups',             onvalue=True, offvalue=False, variable=self.showPopups)
        editmenu.add_checkbutton(label='Ask to Add Multiple IOCs',  onvalue=True, offvalue=False, variable=self.askAnother)
        menubar.add_cascade(label='Edit', menu=editmenu)

        runmenu = Menu(menubar, tearoff=0)
        runmenu.add_command(label='Generate IOCs', command=self.execute)
        menubar.add_cascade(label='Run', menu=runmenu)

        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label='Online Docs',       command=lambda: webbrowser.open('https://epicsnsls2-deploy.github.io/Deploy-Docs/#initIOC-step-by-step-example', new=2))
        helpmenu.add_command(label='initIOC on Github', command = lambda: webbrowser.open('https://github.com/epicsNSLS2-deploy/initIOC', new=2))
        helpmenu.add_command(label='Report an Issue',   command = lambda: webbrowser.open('https://github.com/epicsNSLS2-deploy/initIOC/issues', new=2))
        helpmenu.add_command(label='Supported Drivers', command=print_supported_drivers)
        helpmenu.add_command(label='About',             command=print_start_message)
        menubar.add_cascade(label='Help', menu=helpmenu)

        self.master.config(menu=menubar)

        # Read initial configuration from save file
        self.actions = actions

        # User inputs for all configuration options
        self.text_inputs = {}
        row_counter = 0

        for elem in self.configuration.keys():
            self.text_inputs[elem] = StringVar()
            Label(self.frame, text=elem).grid(row=row_counter, column=0, padx = 10, pady = 10)
            elem_entry = Entry(self.frame, textvariable=self.text_inputs[elem], width=30)
            elem_entry.grid(row=row_counter, column=1, columnspan = 2, padx=10, pady=10)
            elem_entry.insert(0, self.configuration[elem])
            CreateToolTip(elem_entry, config_tooltips[elem])
            row_counter = row_counter + 1

        self.master.title('initIOC GUI')

        ttk.Separator(self.frame, orient=HORIZONTAL).grid(row=row_counter, columnspan=3, padx = 5, sticky = 'ew')

        Label(self.frame, text='IOC Generation Table - You may edit this table manually, or add new IOCs with the Add Button').grid(row = 0, column = 3, columnspan = 5, padx = 10, pady = 10)
        self.iocPanel = ScrolledText.ScrolledText(self.frame, width = '75', height = '15')
        self.iocPanel.grid(row = 1, column = 3, padx = 15, pady = 15, columnspan = 5, rowspan = row_counter + 1)
        self.initIOCPanel()
        for action in self.actions:
            self.writeToIOCPanel(action.ioc_type, action.ioc_name, action.dev_prefix, action.asyn_port, action.ioc_port, action.connection)

        Label(self.frame, text='Log', font=self.largeFontU).grid(row = row_counter + 1, column = 0, padx = 5, pady = 0)
        self.logPanel = ScrolledText.ScrolledText(self.frame, width='100', height = '15')
        self.logPanel.grid(row = row_counter + 2, column = 0, rowspan = 5, columnspan = 4, padx = 10, pady = 10)

        saveButton  = Button(self.frame, text="Save",     font=self.largeFont, command=self.save,                height='3', width='20')
        runButton   = Button(self.frame, text="Run",      font=self.largeFont, command=self.execute,             height='3', width='20')
        addButton   = Button(self.frame, text="Add IOC",  font=self.largeFont, command=self.openAddIOCWindow,    height='3', width='20')
        saveButton.grid(row=row_counter+3, column=5, columnspan=2, padx=5, pady=5)
        runButton.grid( row=row_counter+4, column=5, columnspan=2, padx=5, pady=5)
        addButton.grid( row=row_counter+5, column=5, columnspan=2, padx=5, pady=5)


    def initIOCPanel(self):
        """ Function that resets the IOC panel """

        self.iocPanel.delete('1.0', END)
        self.iocPanel.insert(INSERT, '# IOC Type        IOC Name    Device Prefix   Asyn Port      IOC Port      Cam Connection\n')
        self.iocPanel.insert(INSERT, '#-----------------------------------------------------------------------------------------\n')


    def writeToIOCPanel(self, ioc_type, name, dev_prefix, asyn, port, connect):
        """ Function that writes to the iocPanel """

        self.iocPanel.insert(INSERT, '{:<18}{:<15}{:<15}{:<15}{:<12}{}\n'.format(ioc_type, name, dev_prefix, asyn, port, connect))


    def writeToLog(self, text):
        """Function that writes text to the GUI log
        """

        self.logPanel.insert(INSERT, text)
        self.logPanel.see(END)


    def showError(self, text):

        if self.showPopups.get():
            messagebox.showerror('ERROR', text)
        self.writeToLog('ERROR - ' + text + '\n')


    def showWarning(self, text):

        if self.showPopups.get():
            messagebox.showerror('WARNING', text)
        self.writeToLog('WARNING - ' + text + '\n')


    def showMessage(self, text):

        if self.showPopups.get():
            messagebox.showerror('Info', text)
        self.writeToLog(text + '\n')


    def read_gui_config(self):
        """Function that reads values entered into gui into actions, configuration, and bin_flat 
        """

        for elem in self.text_inputs.keys():
            if self.text_inputs[elem].get() != self.configuration[elem]:
                self.configuration[elem] = self.text_inputs[elem].get()
        
        self.manager.ioc_top = self.configuration['IOC_DIR']
        self.manager.binary_location = self.configuration['TOP_BINARY_DIR']

        self.manager.binaries_flat = self.manager.check_binaries_flat()

        self.manager.update_mod_paths()

        del self.actions[:]
        for line in self.iocPanel.get('1.0', END).splitlines():
            if not line.startswith('#') and len(line) > 1:
                action = parse_line_into_action(line, self.configuration['PREFIX'])
                action.epics_environment['HOSTNAME'] = self.configuration['HOSTNAME']
                action.epics_environment['ENGINEER'] = self.configuration['ENGINEER']
                action.epics_environment['EPICS_CA_ADDR_LIST'] = self.configuration['CA_ADDRESS']
                if action is not None:
                    self.actions.append(action)
                    self.ioc_num_counter = self.ioc_num_counter + 1
                else:
                    self.showWarning('Could not parse one of the IOC lines entered into the table.')


    def execute(self):
        """Reads gui info, and runs init_iocs
        """

        if self.executionThread.is_alive():
            self.showError('Process thread is already active!')
        else:
           self.read_gui_config()
           self.executionThread = threading.Thread(target=lambda : init_iocs_cli(self.actions, self.manager))
           self.executionThread.start()


    def save(self):
        """Saves the current IOC configuration
        """

        self.read_gui_config()
        if os.path.exists('CONFIGURE'):
            os.remove('CONFIGURE')
        file = open('CONFIGURE', 'w')
        file.write('#\n# initIOCs CONFIGURE file autogenerated on {}\n#\n\n'.format(datetime.datetime.now()))
        for elem in self.configuration.keys():
            file.write('# {}\n'.format(config_tooltips[elem]))
            file.write('{}={}\n\n'.format(elem, self.configuration[elem]))

        file.write(self.iocPanel.get('1.0', END))
        initIOC_print('Saved configuration to CONFIGURE file.')


    def saveLog(self):
        """Function that saves the current log into a log file
        """

        if not os.path.exists('logs'):
            os.mkdir('logs')
        elif not os.path.isdir('logs'):
            self.showError('logs directory could not be created, logs file exists')
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        log = open('logs/initIOC-{}.log'.format(stamp), 'w')
        log.write(self.logPanel.get('1.0', END))
        log.close()
        self.writeToLog('Wrote log file.\n')


    def clearLog(self):
        """Reinitializes the log
        """

        self.logPanel.delete('1.0', END)
        print_start_message()


    def openAddIOCWindow(self):
        """Opens an addIOC window
        """

        AddIOCWindow(self)


    def thread_cleanup(self):
        if self.executionThread.is_alive():
            self.executionThread.join()
        self.master.destroy()


class AddIOCWindow:
    """Class representing a window for adding a new IOC into the config
    """

    def __init__(self, root):

        self.root = root
        self.master = Toplevel()
        self.master.title('Add New IOC')

        # Create the entry fields for all the paramters
        self.ioc_type_var       = StringVar()
        self.ioc_type_var.set(supported_drivers[0])

        self.ioc_name_var       = StringVar()
        self.dev_prefix_var     = StringVar()
        self.asyn_port_var      = StringVar()
        self.ioc_port_var       = StringVar()
        self.cam_connect_var    = StringVar()

        Label(self.master, text="IOC Type").grid(row = 0, column = 0, padx = 10, pady = 10)
        ioc_type_entry      = ttk.Combobox(self.master, textvariable=self.ioc_type_var, values=supported_drivers)
        ioc_type_entry.grid(row = 0, column = 1, columnspan=2, padx = 10, pady = 10)
        CreateToolTip(ioc_type_entry, 'The IOC type. Must be from list of supported drivers.')

        Label(self.master, text="IOC Name").grid(row = 1, column = 0, padx = 10, pady = 10)
        ioc_name_entry      = Entry(self.master, textvariable=self.ioc_name_var)
        ioc_name_entry.grid(row = 1, column = 1, columnspan=2, padx = 10, pady = 10)
        CreateToolTip(ioc_name_entry, 'The name of the IOC. Usually cam-$NAME')

        Label(self.master, text="Device Prefix").grid(row = 1, column = 0, padx = 10, pady = 10)
        dev_prefix_entry      = Entry(self.master, textvariable=self.dev_prefix_var)
        dev_prefix_entry.grid(row = 1, column = 1, columnspan=2, padx = 10, pady = 10)
        CreateToolTip(dev_prefix_entry, 'The device-specific prefix. ex. {{Sim-Cam:1}}')

        Label(self.master, text="Asyn Port").grid(row = 2, column = 0, padx = 10, pady = 10)
        asyn_port_entry     = Entry(self.master, textvariable=self.asyn_port_var)
        asyn_port_entry.grid(row = 2, column = 1, columnspan=2, padx = 10, pady = 10)
        CreateToolTip(asyn_port_entry, 'IOC Asyn port. Usually Shorthand of IOC type and number. ex. SIM1')

        Label(self.master, text="IOC Port").grid(row = 3, column = 0, padx = 10, pady = 10)
        ioc_port_entry      = Entry(self.master, textvariable=self.ioc_port_var)
        ioc_port_entry.grid(row = 3, column = 1, columnspan=2, padx = 10, pady = 10)
        CreateToolTip(ioc_port_entry, 'Telnet port used by softioc when running the IOC')

        Label(self.master, text="Cam Connection").grid(row = 4, column = 0, padx = 10, pady = 10)
        cam_connect_entry   = Entry(self.master, textvariable=self.cam_connect_var)
        cam_connect_entry.grid(row = 4, column = 1, columnspan=2, padx = 10, pady = 10)
        CreateToolTip(cam_connect_entry, 'A general parameter used to connect to camera. Typically IP, Serial #, config path, etc.')

        Button(self.master,text="Submit", command=self.submit).grid(row = 5, column = 0, padx = 10, pady = 10)
        Button(self.master,text="Cancel", command=self.master.destroy).grid(row = 5, column = 2, padx = 10, pady = 10)


    def submit(self):
        """Function that enters the filled IOC values into the configuration
        """

        if self.ioc_type_var.get() not in supported_drivers:
            self.root.showError('The selected IOC type is not supported.')
            self.master.destroy()
            return

        ioc_type = self.ioc_type_var.get()
        name = self.ioc_name_var.get()
        dev_prefix = self.dev_prefix_var.get()
        asyn = self.asyn_port_var.get()
        port = self.ioc_port_var.get()
        connect = self.cam_connect_var.get()
        if ioc_type == '' or name == '' or dev_prefix == '' or asyn == '' or port == '' or connect == '':
            self.root.showError('Please enter a valid value for all of the fields.')
            return

        self.root.writeToIOCPanel(ioc_type, name, dev_prefix, asyn, port, connect)
        self.root.writeToLog('Added IOC {} to configuration.\n'.format(name))

        if self.root.askAnother.get():
            res = messagebox.askyesno('Continue', 'Would you like to add another IOC?')
            if res is not None and not res:
                self.master.destroy()
            elif res is not None:
                self.ioc_name_var.set('')
                self.ioc_type_var.set('')
                self.ioc_port_var.set('')
                self.asyn_port_var.set('')
                self.cam_connect_var.set('')
        else:
            self.master.destroy()



def main():
                    if not WITH_GUI:
                    initIOC_print('ERROR - TKinter GUI package not installed. Please intall and rerun.')
                    exit()
                else:
                    root = Tk()
                    USING_GUI = True
                    app = InitIOCGui(root, configuration, actions, manager)
                    GUI_TOP_WINDOW = app
                    print_start_message()
                    root.mainloop()