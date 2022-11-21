#
#  Copyright (c) 2022 - Anibal Canada Ruiz - <anibal@n2h4.es>
#
#  Distributed under BSD2.
#  BSD 2-Clause License
#
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#  1. Redistributions of source code must retain the above copyright notice, this
#     list of conditions and the following disclaimer.
#
#  2. Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
#  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#  SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#  OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
import subprocess
import os
import json
from dateparser import parse


def execute_command(command) :
    process = subprocess.run (command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if process.returncode == 0 :
        pass
    else :
        print ('An error ocurred')
    return process


def auth_gcloud() :
    command = 'gcloud auth activate-service-account --key-file=service-account.json'
    if os.path.exists ('service-account.json') :
        authg = execute_command (command)
        if authg.returncode == 0 :
            print (authg.stdout.decode ('utf-8'))
        else :
            print (authg.stdout.decode ('utf-8'))
    else :
        print ('Need account json file saved in service-account.json')



def projects_list() :
    try:
        project_name = {}
        project_id = {}
        print ('Obtaining projects...')
        command = 'gcloud projects list --format=json'
        plist = execute_command (command)
        if plist.returncode == 0 :
            projects = plist.stdout
            projectst = json.loads (projects.decode ('utf-8'))
            savedlist = input ('Do you want to save projects list to a file(Y/N)?')
            if savedlist.upper () == "Y" :
                with open ('data/project-list.csv', "w+") as savedp :
                    projectstxt = 'name' + ',' + 'id' + 'created time' + ',' + 'status' + ',' + 'owner' + '\n'
                    savedp.write (projectstxt)
                    for project in projectst :
                        if 'labels' in project :
                            if 'owner' in project['labels'] :
                                projectstxt = project['name'] + ',' + project['projectId'] + ', ' + project['createTime'] + ',' + project[
                                    'lifecycleState'] + ',' + project['labels']['owner'] + '\n'
                                savedp.write (projectstxt)
                        else :
                            projectstxt = project['name'] + ',' + project['projectId'] + ', ' + project['createTime'] + ',' + project[
                                'lifecycleState'] + '\n'
                            savedp.write (projectstxt)
                    print ('file saved as project-list.txt')
            i = 0
            print ('Projects list:')
            for project in projectst :
                project_name[i] = project["name"]
                project_id[i] = project["projectId"]
                i += 1
            try :
                return project_name, project_id
            except :
                print ("select valid value for project")
    except:
        print('An error ocurred or you dont has permission for this account')

def get_logging_list(project_id, log_type) :
    command = f'gcloud config set project "{project_id}"'
    proj = execute_command (command)
    log_list ={}
    command = "gcloud logging logs list"
    loglist = execute_command (command)
    audit = 'cloudaudit'
    flow = 'vpc_flow'
    if loglist.returncode == 0 :
        loglisting = loglist.stdout.decode ('utf-8').split ('\n')
        i = 0
        for log in loglisting :
            log_list[i] = log
            i += 1
        del log_list[0]
        del log_list[(len (log_list))]
        if log_type == 'AUDIT':
            audit_keys = [key for key, val in log_list.items() if audit in val]
            audit_logs = {}
            for key in audit_keys:
                audit_logs[key] = log_list[key]
            return audit_logs
        elif log_type == 'FLOW':
            flow_keys =  [key for key, val in log_list.items() if flow in val]        
            flow_logs = {}
            for key in flow_keys:
                flow_logs[key] = log_list[key]
            return flow_logs
        elif log_type =='ALL':
            return log_list
        else:
            flow_keys =  [key for key, val in log_list.items() if flow in val]
            audit_keys = [key for key, val in log_list.items() if audit in val]
            for key in flow_keys:
                log_list.pop(key)
            for key in audit_keys:
                log_list.pop(key)
            return log_list
    else:
        print("An error ocurred while listing logs.")


def select_dates(start , end):
    start_date_input = start
    start_date = parse(start_date_input, settings={'TIMEZONE': 'UTC'})
    end_date_input = end
    end_date = parse(end_date_input, settings={'TIMEZONE': 'UTC'})
    if (not start_date_input or not end_date_input):
        print('You must introduce a date')
    if start_date > end_date:
        print('start date needs to be before than end date')
        select_dates()
    else:
        return start_date.isoformat()+'Z', end_date.isoformat()+'Z'


def log_processor(option, project_name, project_id, start_date, end_date, format):
    print('start date: ', start_date)
    print('end_date :', end_date)
    log_type = option.upper()
    for k, v in project_id.items():
        print(project_name[k], f'{option}', 'logs :')
        result = get_logging_list(v, log_type)
        for key, value in result.items():
            print(value)
            command = f"gcloud logging read '{value} AND timestamp<=\"{end_date}\" AND timestamp>=\"{start_date}\"' --format=\"{format}\""
            log_output = execute_command(command)
            filename_log = f'data/{project_name[k]}-{option}.{format}'
            print(filename_log)
            with open(filename_log , 'ab+') as log_file:
                log_file.write(log_output.stdout)


def argprocessor():
    parser = argparse.ArgumentParser(prog='gcp_mass_downloader', description='Insert log type you wanna download:', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--log_type', help='Type of log to download ', choices=['audit',
        'flow', 'all', 'other'], required=True)
    parser.add_argument('--start', default='1 Month ago', help='start date to download')
    parser.add_argument('--end', default='now', help='End date to download.')
    parser.add_argument('--format', default='json', help='format to output logs', choices=['json','list', 'yaml',
        'none', 'text', 'object', 'default'])
    args = parser.parse_args()
    return args


def main() :
    args = argprocessor()
    #print(args.log_type, args.start, args.end)
    print ('Authenticating...')
    auth_gcloud ()
    project_name , project_id = projects_list ()
    start_date, end_date = select_dates(args.start, args.end)
    log_processor(args.log_type, project_name, project_id, start_date, end_date, args.format)
    
    
if __name__ == '__main__' :
    main ()
