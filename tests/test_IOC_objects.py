import os
import shutil
import initIOCs
from sys import platform

import tests.helper_functions as HELPER



def test_update_mod_paths():
    os.chdir('tests')
    manager_flat_temp = initIOCs.IOCActionManager('./testiocs', './test_bundle_standard', False, False, False, True)
    assert manager_flat_temp.base_path == './test_bundle_standard/base'
    assert manager_flat_temp.support_path == './test_bundle_standard/support'
    assert manager_flat_temp.areaDetector_path == './test_bundle_standard/support/areaDetector'    
    manager_flat_temp.binary_location = './test_bundle_flat'
    manager_flat_temp.update_mod_paths()
    assert manager_flat_temp.base_path == './test_bundle_flat/base'
    assert manager_flat_temp.support_path == './test_bundle_flat'
    assert manager_flat_temp.areaDetector_path == './test_bundle_flat/areaDetector'   
    os.chdir('..')


def test_get_lib_path_for_module():
    os.chdir('tests')
    manager = initIOCs.IOCActionManager('./testiocs', './test_bundle_standard', False, False, False, True)
    path = manager.get_lib_path_for_module(initIOCs.initIOC_path_join(manager.binary_location, 'support/testModule'), 'linux-x86_64', ':')
    assert path == './test_bundle_standard/support/testModule/bin/linux-x86_64:./test_bundle_standard/support/testModule/lib/linux-x86_64:'
    os.chdir('..')


def test_get_lib_path_str():
    if platform == 'win32':
        pass
    else:
        os.chdir('tests')
        manager = initIOCs.IOCActionManager('./testiocs', './test_bundle_standard', False, False, False, True)
        action = initIOCs.IOCAction('ADSimDetector', '', '', 'sim1:', '', '', '', '')
        lib_path = manager.get_lib_path_str(action)
        print(lib_path)
        assert lib_path == 'export LD_LIBRARY_PATH=./test_bundle_standard/base/bin/linux-x86_64:./test_bundle_standard/base/lib/linux-x86_64:./test_bundle_standard/support/testModule/bin/linux-x86_64:./test_bundle_standard/support/testModule/lib/linux-x86_64:./test_bundle_standard/support/areaDetector/ADSupport/bin/linux-x86_64:./test_bundle_standard/support/areaDetector/ADSupport/lib/linux-x86_64:./test_bundle_standard/support/areaDetector/ADCore/bin/linux-x86_64:./test_bundle_standard/support/areaDetector/ADCore/lib/linux-x86_64:./test_bundle_standard/support/areaDetector/ADSimDetector/bin/linux-x86_64:./test_bundle_standard/support/areaDetector/ADSimDetector/lib/linux-x86_64:$LD_LIBRARY_PATH'
        os.chdir('..')


def test_get_env_paths_name():
    manager = initIOCs.IOCActionManager('./testiocs', './test_bundle_standard', False, False, False, True)
    assert manager.get_env_paths_name('seq') == 'SNCSEQ'
    assert manager.get_env_paths_name('iocStats') == 'DEVIOCSTATS'
    assert manager.get_env_paths_name('areaDetector') == 'AREA_DETECTOR'
    assert manager.get_env_paths_name('testModule') == 'TESTMODULE'


def test_add_to_environment():
    action = initIOCs.IOCAction('ADSimDetector', '', '', '', '', '', '')
    action.add_to_environment('epicsEnvSet("TEST_ENV_SET", "TEST_VALUE")')
    assert 'TEST_ENV_SET' in action.epics_environment.keys()
    assert action.epics_environment['TEST_ENV_SET'] == 'TEST_VALUE'


def test_create_config_file():
    os.chdir('tests')
    manager = initIOCs.IOCActionManager('./testiocs', './test_bundle_standard', False, False, False, True)
    action = initIOCs.IOCAction('ADSimDetector', 'test-sim1', '', 'sim1:', '', '4040', '', '')
    action.epics_environment['HOSTNAME'] = 'localhost'
    manager.initialize_ioc_directory()
    os.mkdir('testiocs/test-sim1')
    manager.create_config_file(action)
    fp1 = open('testiocs/test-sim1/config', 'r')
    fp2 = open('expected_files/expected_config', 'r')
    assert HELPER.compare_files(fp1, fp2)
    fp1.close()
    fp2.close()
    shutil.rmtree('testiocs')
    os.chdir('..')


def test_generate_env_paths():
    os.chdir('tests')
    pwd = os.getcwd()
    manager = initIOCs.IOCActionManager('./testiocs', './test_bundle_standard', False, False, False, True)
    action = initIOCs.IOCAction('ADSimDetector', 'test-sim1', '', 'sim1:', '', '4040', '', '')
    manager.initialize_ioc_directory()
    os.mkdir('testiocs/test-sim1')
    manager.generate_env_paths(action)
    fp1 = open('testiocs/test-sim1/envPaths', 'r')
    fp2 = open('expected_files/expected_envPaths', 'r')
    assert HELPER.compare_files(fp1, fp2)
    fp1.close()
    fp2.close()
    shutil.rmtree('testiocs')
    os.chdir('..')


def test_grab_additionl_env():
    manager = initIOCs.IOCActionManager('./testiocs', './test_bundle_standard', False, False, False, True)
    action = initIOCs.IOCAction('ADSimDetector', 'test-sim1', '', 'sim1:', '', '4040', '', '')
    st_base_path = 'tests/test_bundle_standard/support/areaDetector/ADSimDetector/iocs/simDetectorIOC/iocBoot/iocSimDetector/Makefile'
    manager.grab_additional_env(action, st_base_path)
    assert action.epics_environment['MAX_THREADS'] == '8'
    assert action.epics_environment['EPICS_DB_INCLUDE_PATH'] == '$(ADCORE)/db'


def test_generate_unique_cmd():
    os.chdir('tests')
    pwd = os.getcwd()
    manager = initIOCs.IOCActionManager('./testiocs', initIOCs.initIOC_path_join(pwd, 'test_bundle_standard'), False, False, False, True)
    action = initIOCs.IOCAction('ADSimDetector', 'test-sim1', 'TEST1:', 'sim1:', 'TS1', '4040', 'NA', 3)
    action.epics_environment['HOSTNAME'] = 'localhost'
    action.epics_environment['EPICS_CA_ADDR_LIST'] = '127.0.0.255'
    action.epics_environment['ENGINEER'] = 'J. Wlodek'
    manager.initialize_ioc_directory()
    os.mkdir('testiocs/test-sim1')
    st_base_path = 'test_bundle_standard/support/areaDetector/ADSimDetector/iocs/simDetectorIOC/iocBoot/iocSimDetector/Makefile'
    manager.grab_additional_env(action, st_base_path)
    manager.generate_unique_cmd(action)
    fp1 = open('testiocs/test-sim1/unique.cmd', 'r')
    fp2 = open('expected_files/expected_unique.cmd', 'r')
    assert HELPER.compare_files(fp1, fp2)
    fp1.close()
    fp2.close()
    shutil.rmtree('testiocs')
    os.chdir('..')


def test_generate_st_cmd():
    os.chdir('tests')
    pwd = os.getcwd()
    manager = initIOCs.IOCActionManager('./testiocs', './test_bundle_standard', False, False, False, True)
    action = initIOCs.IOCAction('ADSimDetector', 'test-sim1', 'TEST1:', 'sim1:', 'TS1', '4040', 'NA', 3)
    action.epics_environment['HOSTNAME'] = 'localhost'
    action.epics_environment['EPICS_CA_ADDR_LIST'] = '127.0.0.255'
    action.epics_environment['ENGINEER'] = 'J. Wlodek'
    manager.initialize_ioc_directory()
    os.mkdir('testiocs/test-sim1')
    st_base_path = 'test_bundle_standard/support/areaDetector/ADSimDetector/iocs/simDetectorIOC/iocBoot/iocSimDetector/st_base.cmd'
    manager.grab_additional_env(action, st_base_path)
    exe_path, dbd_path, iocBoot_path = manager.find_paths_for_action(action)
    manager.genertate_st_cmd(action, exe_path, st_base_path, dbd_path=dbd_path)
    fp1 = open('testiocs/test-sim1/st.cmd', 'r')
    fp2 = open('expected_files/expected_st.cmd', 'r')
    assert HELPER.compare_files(fp1, fp2)
    fp1.close()
    fp2.close()
    shutil.rmtree('testiocs')
    os.chdir('..')