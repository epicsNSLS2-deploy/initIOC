import pytest
import os
import shutil
import initIOCs

import tests.helper_functions as HELPER


def test_initIOC_path_join():
    joined_A = initIOCs.initIOC_path_join('test_path/A', 'test')
    joined_B = initIOCs.initIOC_path_join('test_path/A/', 'test')
    joined_C = initIOCs.initIOC_path_join('test_path/A', '/test')
    joined_D = initIOCs.initIOC_path_join('test_path/A', 'test/')
    expected = 'test_path/A/test'
    assert joined_A == expected
    assert joined_B == expected
    assert joined_C == expected
    assert joined_D == expected



def test_read_ioc_config():
    pwd = os.getcwd()
    os.chdir('tests')
    ioc_actions, configuration = initIOCs.read_ioc_config(3)
    assert len(ioc_actions) == 1
    assert configuration['IOC_DIR'] == 'tests'
    assert configuration['TOP_BINARY_DIR'] == 'tests/test_bundle_standard'
    assert configuration['PREFIX'] == 'TEST1:'
    assert configuration['ENGINEER'] == 'J. Wlodek' 
    assert configuration['HOSTNAME'] == 'localhost'
    assert configuration['CA_ADDRESS'] == '127.0.0.255'
    assert ioc_actions[0].ioc_type == 'ADSimDetector'
    assert ioc_actions[0].ioc_name == 'test-sim1'
    assert ioc_actions[0].asyn_port == 'TS1'
    assert ioc_actions[0].ioc_num == 3
    assert ioc_actions[0].ioc_port == '4040'
    assert ioc_actions[0].connection == 'NA'
    assert ioc_actions[0].epics_environment['PREFIX'] == 'TEST1:{SimDetector-Cam:3}'
    os.chdir('..')



def test_parse_line_into_action():
    action = initIOCs.parse_line_into_action('ADSimDetector      test-sim1    TS1           4040          NA', 'TEST1:', 3)
    assert action.ioc_type == 'ADSimDetector'
    assert action.ioc_name == 'test-sim1'
    assert action.asyn_port == 'TS1'
    assert action.ioc_num == 3
    assert action.ioc_port == '4040'
    assert action.connection == 'NA'
    assert action.epics_environment['PREFIX'] == 'TEST1:{SimDetector-Cam:3}'


def test_write_config():
    if os.path.exists('temp'):
        shutil.rmtree('temp')
    os.mkdir('temp')
    pwd = os.getcwd()

    configuration = {}
    configuration['IOC_DIR'] = 'tests'
    configuration['TOP_BINARY_DIR'] = 'tests/test_bundle_standard'
    configuration['PREFIX'] = 'TEST1:'
    configuration['ENGINEER'] = 'J. Wlodek' 
    configuration['HOSTNAME'] = 'localhost'
    configuration['CA_ADDRESS'] = '127.0.0.255'
    os.chdir('temp')
    initIOCs.write_config(configuration)
    fp1 = open('CONFIGURE', 'r')
    fp2 = open('../tests/expected_files/expected_CONFIGURE', 'r')
    assert HELPER.compare_files(fp1, fp2)
    fp1.close()
    fp2.close()
    os.chdir(pwd)
    shutil.rmtree('temp')
