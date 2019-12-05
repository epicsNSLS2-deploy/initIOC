#!./test_bundle_standard/support/areaDetector/ADSimDetector/iocs/simDetectorIOC/bin/linux-x86_64/simDetectorApp

< envPaths

< unique.cmd

errlogInit(20000)

dbLoadDatabase($(ADSIMDETECTOR)/iocs/simDetectorIOC/dbd/simDetectorApp.dbd)


simDetectorApp_registerRecordDeviceDriver(pdbbase) 


asynSetMinTimerPeriod(0.001)


simDetectorConfig("$(PORT)", $(XSIZE), $(YSIZE), 1, 0, 0)
dbLoadRecords("$(ADSIMDETECTOR)/db/simDetector.template","P=$(PREFIX),R=cam1:,PORT=$(PORT),ADDR=0,TIMEOUT=1")

simDetectorConfig("SIM2", 300, 200, 1, 50, 50000000)
dbLoadRecords("$(ADSIMDETECTOR)/db/simDetector.template","P=$(PREFIX),R=cam2:,PORT=SIM2,ADDR=0,TIMEOUT=1")


NDStdArraysConfigure("Image1", 20, 0, "$(PORT)", 0, 0, 0, 0, 0, 5)

dbLoadRecords("NDStdArrays.template", "P=$(PREFIX),R=image1:,PORT=Image1,ADDR=0,TIMEOUT=1,NDARRAY_PORT=$(PORT),TYPE=Int8,FTVL=UCHAR,NELEMENTS=12000000")

< $(ADCORE)/iocBoot/commonPlugins.cmd

NDStdArraysConfigure("Image2", 3, 0, "FFT1", 0)
dbLoadRecords("NDStdArrays.template", "P=$(PREFIX),R=image2:,PORT=Image2,ADDR=0,TIMEOUT=1,NDARRAY_PORT=FFT1,TYPE=Float64,FTVL=DOUBLE,NELEMENTS=12000000")

set_requestfile_path("$(ADSIMDETECTOR)/simDetectorApp/Db")

asynSetTraceIOMask("$(PORT)",0,2)

iocInit()

create_monitor_set("auto_settings.req", 30, "P=$(PREFIX)")
