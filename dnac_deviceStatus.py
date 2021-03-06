#!/usr/bin/env python
"""DNAv3 - DNAC Northbound API - Hands on exercise 02
In this exercise we create helper functions to get an auth token
from DNAC - get_auth_token() and also get_url(), create_url(),
dna_ip_to_id(), dna_get_modules() to get a list of all network modules attached
to a device represented by it's IP.

Copyright (c) 2018 Cisco and/or its affiliates.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import csv
import datetime
import json
import os
import platform
import pprint
import requests
import sys
import subprocess
from requests.auth import HTTPBasicAuth

requests.packages.urllib3.disable_warnings()

# Get the absolute path for the directory where this file is located "here"
here = os.path.abspath(os.path.dirname(__file__))

# Get the absolute path for the project / repository root
project_root = os.path.abspath(os.path.join(here, ""))


# Extend the system path to include the project root and import the env files
#sys.path.insert(0, project_root)
#import env_lab
#
#DNAC = env_lab.DNA_CENTER['host']
#DNAC_USER = env_lab.DNA_CENTER['username']
#DNAC_PASSWORD = env_lab.DNA_CENTER['password']
#DNAC_PORT = env_lab.DNA_CENTER['port']

# -------------------------------------------------------------------
# DNAC functions
# -------------------------------------------------------------------
def get_auth_token(controller_ip, username, password,port):
    """ Authenticates with controller and returns a token to be used in subsequent API invocations
    """

    login_url = "https://{0}:{1}/dna/system/api/v1/auth/token".format(controller_ip, port)
    result = requests.post(url=login_url, auth=HTTPBasicAuth(username, password), verify=False)
    result.raise_for_status()

    token = result.json()["Token"]
    return (token)
##

def create_url(path, controller_ip, port):
    """ Helper function to create a DNAC API endpoint URL
    """
    return "https://%s:%s/dna/intent/api/v1/%s" % (controller_ip, port, path)
##

def rest_get_url(url, token, ip, port):
    url = create_url(url, ip, port)
    headers = {'X-auth-token' : token}
    try:
        response = requests.get(url, headers=headers, verify=False)
    except requests.exceptions.RequestException as cerror:
        print("Error processing request", cerror)
        sys.exit(1)
    return response.json()
##

def dna_ip_to_id(dnac_info,ip):
    return rest_get_url("network-device/ip-address/%s" % ip,dnac_info['token'], dnac_info['host'] , dnac_info['https_port'])
##

def dna_get_modules(dnac_info,id) :
    return rest_get_url("network-device/module?deviceId=%s" % id,dnac_info['token'], dnac_info['host'] , dnac_info['https_port'])
##

def dna_get_device_list(dnac_info):
    return rest_get_url("network-device", dnac_info['token'], dnac_info['host'] , dnac_info['https_port'])
##

# -------------------------------------------------------------------
# General functions
# -------------------------------------------------------------------
def convert_list_to_dict(data_list):
    Keys_of_Column = data_list[0]
    del data_list[0]
    for idx_1, item_1 in enumerate(data_list):
        Temp_Json = '{'
        for idx_2, item_2 in enumerate(item_1):
            if idx_2 >= 1:
                Temp_Json += ','
            Temp_Json += '"' + Keys_of_Column[idx_2] + '":"' + item_2 + '"'
        Temp_Json += '}'
        data_list[idx_1] = json.loads(Temp_Json)
    return (data_list)
##

def csvFile_read(path, json_format = True):
    """ Read csv file
    input: [Path <str>]
    return: [Lines <list>]
    """
    # Read Text File
    Lines = []
    Keys_of_Column = []
    # Read  HostList as List
    with open(path, "r") as ins:
        for line in  csv.reader(ins, quotechar='"', delimiter=',',quoting=csv.QUOTE_ALL, skipinitialspace=True):
            Lines.append(line)
    
    if json_format == True:
        # cover list into of Dict (json form)
        Lines = convert_list_to_dict(Lines)
    #pprint.pprint (Lines)
    return (Lines)
##

def csvFile_write(data, path):
    # Write Confiuration into file
    with open(path, 'w', newline='') as ins:
        writer = csv.writer(ins, delimiter=',')
        for line in data:
            writer.writerow(line)
        ins.close
##

def convert_path(path):
    return os.path.abspath(os.path.expanduser(path))
##


def ping(ip_address, os_name):
    """
    input: [ip_address]
    return: [0] (failed), [1] (success)
    """

    # For each IP address in the subnet,
    # run the ping command with subprocess.popen interface

    # Use Windows OS ping
    if os_name == 'Windows':
        # Configure subprocess to hide the console window
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = subprocess.SW_HIDE

        output = subprocess.Popen(['ping', '-n', '1', ip_address], stdout=subprocess.PIPE, startupinfo=info).communicate()[0]
        # Classify output
        if "Destination host unreachable" in output.decode('utf-8'):
            return (0)
        elif "Request timed out" in output.decode('utf-8'):
            return (0)
        elif "TTL=" in output.decode('utf-8'):
            return (1)
        else:
            return (0)

    if os_name == 'Linux':
        # Configure subprocess to hide the console Linux

        output = subprocess.Popen(["/bin/ping", "-c1", "-w 5", ip_address], stdout=subprocess.PIPE).stdout.read()
        # Classify output
        if "Destination host unreachable" in output.decode('utf-8'):
            return (0)
        elif "Request timed out" in output.decode('utf-8'):
            return (0)
        elif "expired in transit" in output.decode('utf-8'):
            return (0)
        elif "ttl=" in output.decode('utf-8'):
            return (1)
        else:
            return (0)
##


# -------------------------------------------------------------------
# Program functions
# -------------------------------------------------------------------

def device_grouping(device_json):
    # input : device list (json)
    # grouping device
    # output : 
    #   switch device (list)
    #   wireless device (list)
    return_list = []
    for idx_1, item_1 in enumerate (device_json['response']):
        temp_01 = []
        # add table header
        if idx_1 == 0:
            temp_01.append('hostname')
            temp_01.append('id')
            temp_01.append('location')
            temp_01.append('family')
            temp_01.append('platformId')
            temp_01.append('role')
            temp_01.append('serialNumber')
            temp_01.append('upTime')
            temp_01.append('errorCode')
            return_list.append(temp_01)
            temp_01 = []
        
        # filter Switch device and add to list
        temp_01.append(item_1['hostname'])
        temp_01.append(item_1['id'])
        temp_01.append(item_1['location'])
        temp_01.append(item_1['family'])
        temp_01.append(item_1['platformId'])
        temp_01.append(item_1['role'])
        temp_01.append(item_1['serialNumber'])
        if (item_1['upTime']).find('day') < 0:
            item_1['upTime'] = '0day,' + item_1['upTime']
        temp_01.append(item_1['upTime'])
        temp_01.append(item_1['errorCode'])
        return_list.append(temp_01)
    return (return_list )
##

def cred_control ():
    """  
    1. Directory check
    2. read credencial file
    3. DNAC authen,

    return credencial
    """
    # check/create dir

    if not os.path.exists(os.path.abspath("_codeData")):
        os.makedirs(os.path.abspath("_codeData"))

    if not os.path.exists(os.path.abspath(os.path.join('_codeData','deviceList'))):
        os.makedirs(os.path.abspath(os.path.join("_codeData","deviceList")))
    
    # Check cache file
    # - get Credencial of DNAC
    # - Check token, timeout
    # -

    # read credencialgetToken_control
    if not os.path.exists(os.path.abspath(os.path.join("cred_list.csv"))):
        return  ("Not found credencial file")
    else:
        cred_list = csvFile_read(os.path.abspath("cred_list.csv"))
        # turn hostname as cred_control key of each credencial
        temp_cred = {}
        for idx_1, item_1 in enumerate (cred_list):
            temp_key = item_1['hostname']
            del item_1['hostname']
            temp_cred[temp_key] = item_1
        cred_list = temp_cred

        token_check = 0
        token = ""
        token_cache_list = []
        temp_list = []

        if not os.path.exists(os.path.abspath(os.path.join("_codeData","_init_cache.txt"))):
            token_check = 1
        else:
            # Read file
            init_cache = csvFile_read(os.path.abspath(os.path.join("_codeData","_init_cache.txt")))

            # 
            temp_init_cache = {}
            for idx_1, item_1 in enumerate (init_cache):
                temp_key = item_1['name']
                del item_1['name']
                temp_init_cache[temp_key] = item_1
            init_cache = temp_init_cache
            
            # Check Token timeout,
            time_now = (datetime.datetime.now()).strftime("%Y%m%d%H%M")
            time_token =  init_cache['token']['date']
            #pprint.pprint(time_token)
            if int(time_now) > (int(time_token)+30):
                #print ('Timeout auth')
                token_check = 1
            else:
                #print ('Old auth')
                token = init_cache['token']['value']
                cred_list['DNAC']['token'] = token
                return (cred_list)
        
        if token_check == 1:
            if (ping (cred_list['DNAC']['host'], platform.system())) == 1:
                #print ("New auth")
                
                ## Token file Format list of [token,(token_value),(date-time)]175.176.222.199175.176.222.199
                temp_list.append('token')
                
                token = (get_auth_token(cred_list['DNAC']['host'],cred_list['DNAC']['username'],cred_list['DNAC']['password'],cred_list['DNAC']['https_port']))
                temp_list.append(token)

                temp_list.append((datetime.datetime.now()).strftime("%Y%m%d%H%M"))

                token_cache_list.append(['name','value','date'])
                token_cache_list.append(temp_list)
                csvFile_write(token_cache_list, os.path.abspath(os.path.join("_codeData","_init_cache.txt")))

                cred_list['DNAC']['token'] = token
                return (cred_list)
            else:
                return ("Can not conncet to DNAC")
##

def switch_compare(new_switch_list):
    # read credencialgetToken_control  "_codeData","deviceList","device_switch_list.csv")
    old_switch_list = csvFile_read(os.path.abspath(os.path.join("_codeData","deviceList","device_switch_list.csv")), False)

    #pprint.pprint  (old_switch_list)
    new_switch = []
    notFound_switch =[]
    compare_switch_old = []
    for idx_1, item_1 in enumerate (old_switch_list):
        compare_switch_old.append(item_1[0])

    #pprint.pprint (new_switch_list)
    compare_switch_new = []
    for idx_1, item_1 in enumerate (new_switch_list):
        compare_switch_new.append(item_1[0])
    
    # compare, 
    if len(set(compare_switch_new) - set(compare_switch_old)) > 0:
        new_switch = list(set(compare_switch_new) - set(compare_switch_old))
        print ("\nSwitch NEW "+"("+ str(len(new_switch))+")")
        for idx_1, item_1 in enumerate (new_switch):
            text = item_1.replace('.pttgrp.corp', '')
            print (" ", str(idx_1+1)+")", text)
    if len(set(compare_switch_old) - set(compare_switch_new)) > 0:
        notFound_switch = list(set(compare_switch_old) - set(compare_switch_new))
        print ("\nSwitch NOT FOUND "+"("+ str(len(notFound_switch))+")")
        for idx_1, item_1 in enumerate (notFound_switch):
            text = item_1.replace('.pttgrp.corp', '')
            print (" ", str(idx_1+1)+")", text)
    if len(set(compare_switch_new) - set(compare_switch_old)) == 0 & len(compare_switch_new) == len(compare_switch_old):
        print ("\nSwitc Good")
        

##


def dna_get_switchDeviceList(dnac_info):
    return rest_get_url("network-device?family=Switches and Hubs", dnac_info['token'], dnac_info['host'] , dnac_info['https_port'])
##
def dna_get_wirelessDeviceList(dnac_info):
    return rest_get_url("network-device?family=Unified AP", dnac_info['token'], dnac_info['host'] , dnac_info['https_port'])
##

if __name__ == "__main__":
    ## initial
    ##  - get token
    ##  - Check connection
    line_msg = ""
    cred_list = cred_control()


    if type(cred_list) != str:
        ## Get device list
        dnac_info = cred_list['DNAC']

        #Get device and remove unused data
        device_switch_list      = device_grouping(dna_get_switchDeviceList(dnac_info))
        device_wireless_list    = device_grouping(dna_get_wirelessDeviceList(dnac_info))

        print ("Switch Device :", len(device_switch_list)-1)
        print ("Wireless Device :", len(device_wireless_list)-1)

        line_msg += "Switch Device :" + str(len(device_switch_list)-1) + "\n"
        line_msg += "Wireless Device :" + str(len(device_wireless_list)-1) + "\n"

        ## compare Device
        ##  - existing file?
        ##      - yes > compare, write, noti ### new device, SN change (check model),
        ##      - no > write
        if os.path.exists(os.path.abspath(os.path.join('_codeData','deviceList','device_switch_list'))) == 0:
            switch_compare(device_switch_list)  
            #csvFile_write(device_switch_list, os.path.abspath(os.path.join("_codeData","deviceList","device_switch_list.csv")))
        else:
            # sholde print something to report
            csvFile_write(device_switch_list, os.path.abspath(os.path.join("_codeData","deviceList","device_switch_list.csv")))

        ## check uptime
        ##  - uptime == 0day, down** > noti
        #(device_switch_list, os.path.abspath(os.path.join("_codeData","deviceList","device_switch_list.csv")))
        csvFile_write(device_wireless_list, os.path.abspath(os.path.join("_codeData","deviceList","device_wireless_list.csv")))

    else:
        ## Print error
        print (cred_list)
        