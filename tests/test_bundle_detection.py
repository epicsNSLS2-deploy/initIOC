import pytest
import os
import initIOCs


manager_flat = initIOCs.IOCActionManager('tests/testiocs', 'tests/test_bundle_flat', False, False, False, True)
manager_standard = initIOCs.IOCActionManager('tests/testiocs', 'tests/test_bundle_standard', False, False, False, True)


def test_detect_flat_bundle():
    assert manager_flat.binaries_flat == True

def test_detect_standard_bundle():
    assert manager_standard.binaries_flat == False


def test_find_files_flat():
    pwd = os.getcwd()
    sim_exe = 'tests/test_bundle_flat/areaDetector/ADSimDetector/iocs/simDetectorIOC/bin/linux-x86_64/simDetectorApp'
    sim_dbd = 'iocs/simDetectorIOC/dbd/simDetectorApp.dbd'
    sim_iocBoot = 'tests/test_bundle_flat/areaDetector/ADSimDetector/iocs/simDetectorIOC/iocBoot/iocSimDetector'
    # We only care about the IOC type here.
    action = initIOCs.IOCAction('ADSimDetector', '', '', '', '', '', '')
    det_exe, det_dbd, det_iocBoot = manager_flat.find_paths_for_action(action)
    assert sim_exe == det_exe
    assert sim_dbd == det_dbd
    assert sim_iocBoot == det_iocBoot


def test_find_files_standard():
    pwd = os.getcwd()
    sim_exe = 'tests/test_bundle_standard/support/areaDetector/ADSimDetector/iocs/simDetectorIOC/bin/linux-x86_64/simDetectorApp'
    sim_dbd = 'iocs/simDetectorIOC/dbd/simDetectorApp.dbd'
    sim_iocBoot = 'tests/test_bundle_standard/support/areaDetector/ADSimDetector/iocs/simDetectorIOC/iocBoot/iocSimDetector'
    # We only care about the IOC type here.
    action = initIOCs.IOCAction('ADSimDetector', '', '', '', '', '', '')
    det_exe, det_dbd, det_iocBoot = manager_standard.find_paths_for_action(action)
    assert sim_exe == det_exe
    assert sim_dbd == det_dbd
    assert sim_iocBoot == det_iocBoot

