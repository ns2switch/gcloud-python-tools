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

#still not fully usable
#in dev.


import subprocess
import os
import json
import sys
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


def menu_select(input_text, option_dict, all_value) :
    for order, elem in option_dict.items () :
        print (order, elem)
    print('there is', len(option_dict), 'items')    
    sel_menu = input (input_text)
    if sel_menu.upper() == 'A':
        sel_menu = sel_menu.upper()
    else:
        sel_menu = int(sel_menu)
    if all_value == 1:
        if isinstance (sel_menu, int) :
            selected_menu = option_dict[sel_menu]
            return selected_menu
        elif sel_menu == 'A' :
            print ("You selected all.")
    else :
        if isinstance (sel_menu, int) :
            selected_menu = option_dict[sel_menu]
            return selected_menu,  sel_menu
        else :
            print ("You need to input a valid value.")
            sys.exit(1)


def sele_proj(project_name, project_id) :
    command = 'gcloud config unset project'
    execute_command (command)
    selected_project, proj_id = menu_select ("Select project(Insert number): ", project_name, 0)
    print ("You have selected: ", selected_project)
    project_sel_id = project_id[proj_id]
    try:    
        command = f'gcloud config set project "{project_sel_id}"'
        proj = execute_command (command)
        print (proj.stdout.decode ('utf-8'))
    except :
        print ("An error ocurred")
        sys.exit (1)


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
                    projectstxt = 'name' + ',' + 'created time' + ',' + 'status' + ',' + 'owner' + '\n'
                    savedp.write (projectstxt)
                    for project in projectst :
                        if 'labels' in project :
                            if 'owner' in project['labels'] :
                                projectstxt = project['name'] + ',' + project['createTime'] + ',' + project[
                                    'lifecycleState'] + ',' + project['labels']['owner'] + '\n'
                                savedp.write (projectstxt)
                        else :
                            projectstxt = project['name'] + ',' + project['createTime'] + ',' + project[
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
                sele_proj (project_name, project_id)
            except :
                print ("select valid value for project")
    except:
        print('An error ocurred or you dont has permission for this account')

def get_logging_list() :
    log_list = {}
    command = "gcloud logging logs list"
    loglist = execute_command (command)
    if loglist.returncode == 0 :
        loglisting = loglist.stdout.decode ('utf-8').split ('\n')
        i = 0
        for log in loglisting :
            log_list[i] = log
            i += 1
        del log_list[0]
        del log_list[(len (log_list))]
        audit = 'cloudaudit'
        flow = 'flow'
        audit_logs = {}
        flow_logs = {}
        audit_keys = [key for key, val in log_list.items() if audit in val]
        flow_keys =  [key for key, val in log_list.items() if flow in val]
        for key in audit_keys:
            audit_logs[key] = log_list[key]
            log_list.pop(key)
        for key in flow_keys:
            flow_logs[key] = log_list[key]
            log_list.pop(key)
        return audit_logs , flow_logs, log_list
    else:
        print("undef command")


def select_dates(start , end):
    start_date_input = start
    start_date = parse(start_date_input, settings={'TIMEZONE': 'UTC'})
    end_date_input = end
    end_date = parse(end_date_input, settings={'TIMEZONE': 'UTC'})
    if (not start_date_input or not end_date_input):
        print('You must introduce a date')
    if start_date > end_date:
        print('start date needs to be before than end date')
    else:
        return start_date.isoformat()+'Z', end_date.isoformat()+'Z'

def men_save(audit=None, flow=None, other=None):
    print('Logs: ', '\n')
    if audit:
        print('Audit logs:(to select all ,press A) ')
        for key, val in audit.items():
            print(key, val)
    else:
        print('No Audit logs found')
         
    print('\n')
    if flow:
        print('Flow logs: to select all, press F')
        for key, val in flow.items():
            print(key, val)
    else:
        print('No VPC flows logs found')
    print('\n')
    if other:
        print('other logs: ')
        for key, val in other.items():
            print(key, val)
    else:
        print('No logs found')
    print('\n')
    if audit or flow or other:
        sel_logs = input('Select logs to save: ')
        return sel_logs
    else:
        sys.exit('No logs found in this account')

def log_processor(option, project_name, project_id, start_date, end_date, format):
    print('start date: ', start_date)
    print('end_date :', end_date)
    log_type = option.upper()
    for k, v in project_id.items():
        print(project_name[k], f'{option}', 'logs :')
        result = get_logging_list()
        for key, value in result.items():
            print(value)
            command = f"gcloud logging read '{value} AND timestamp<=\"{end_date}\" AND timestamp>=\"{start_date}\"' --format=\"{format}\""
            print(command)
            log_output = execute_command(command)
            filename_log = f'data/{project_name[k]}-{option}.{format}'
            print(filename_log)
            with open(filename_log , 'ab+') as log_file:
                log_file.write(log_output.stdout)


def main() :
    auth_gcloud ()
    projects_list ()
    try:
        audit_logs, flow_logs, other_logs = get_logging_list ()
    except:
        sys.exit('An error ocurred , Do you have permisssions in this account?')
    sel_logs = men_save(audit=audit_logs, flow=flow_logs, other=other_logs)
    start_date, end_date = select_dates()
    log_processor(sel_logs, start_date, end_date, 'json')
    
if __name__ == '__main__' :
    print ('Authenticating...')
    main ()
