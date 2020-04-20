# initIOC

Script for generating camera IOC configurations from areaDetector bundles, or from the [ioc-template](https://github.com/epicsNSLS2-deploy/ioc-template).

### Usage

This script is intended for rapidly initializing IOCs for new detectors en-mass. To use the script, simply clone this repository, enter the `initIOC` directory, and run:

```
./initIOCs.py
```

Then follow along with the instructions printed to the terminal by the script. You may want to decide on a binary bundle to use, and have its location ready prior to executing the script.

**(Note that python3 is required for the script to run)**

You may also utilize certain optional command line flags with initIOC:

```
E:\BNL\epics\utils\initIOC>py initIOCs.py -h
usage: initIOCs.py [-h] [-c CONFIGURE] [-p] [-t] [-l] [-m] [-s SEARCHBUNDLE]

A script for auto-initializing areaDetector IOCs. Edit the CONFIGURE file and
run without arguments for default operation.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIGURE, --configure CONFIGURE
                        Add this flag and path to install script to use a run
                        initIOCs given a configure file.
  -p, --setlibrarypath  This flag should be added to set library path before
                        startup script is run.
  -t, --template        This flag will tell initIOC to use an st.cmd template.
                        These are more likely to process without error, but
                        may be somewhat out of date.
  -l, --links           Add this flag if you would like initIOC to create
                        links of required helper files instead of copies.
  -m, --minimal         This flag specifies if initIOC should attempt to
                        generate a minimal IOC. May result in some missing
                        files that will need manual tweaks.
  -s SEARCHBUNDLE, --searchbundle SEARCHBUNDLE
                        Add this flag, followed by a path to a binary bundle
                        to get a list of driver executables that are included.

```

### GUI Usage

The `initIOC` GUI is still in development, and should not be used until further notice.

### Currently supported drivers

There are two primary ways that `initIOC` can be used to generate IOCs. By default, it attempts to convert the `iocBoot` directory of the given driver into a structured IOC. When using this mode, any driver ioc can be generated provided the `iocBoot` directory can be found.

Alternatively, when using the `-t` flag, `initIOCs.py` relies on [ioc-template](https://github.com/epicsNSLS2-deploy/ioc-template) to deploy its IOCs, and as a result, IOC support is limited to those drivers that have startup scripts located in `ioc-template`. Currently this includes:
* ADAndor3
* ADLambda
* ADUVC
* ADProsilica
* ADPilatus
* ADPerkinElmer
* ADMerlin
* ADSpinnaker
* ADPointGrey
* ADSimDetector
* ADURL
* ADPSL
* ADEiger
