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
# v0.4 - avoid not recognized types by protobuf
# v0.5 - allow resume downloads of logs.
# v0.6 - page_size set at 1000 to avoid rate limit in projects with huge logs
# v0.7 - adding option select_project

import os
import glob
from googleapiclient import discovery
from google.oauth2 import service_account
import google.cloud.logging_v2
import argparse
import json
from dateparser import parse

def get_project_list(credentials):
    project_name={}
    project_id={}
    i = 0
    service = discovery.build('cloudresourcemanager', 'v1', credentials=credentials)
    request = service.projects().list()
    while request is not None:
        response = request.execute()
        for project in response.get('projects', []):
            project_name[i] = project["name"]
            project_id[i] = project["projectId"]
            i += 1
        request = service.projects().list_next(previous_request=request, previous_response=response)
    return project_name, project_id,i


def argprocessor() :
    parser = argparse.ArgumentParser (prog='gcp_mass_downloader', description='Insert log type you wanna download:',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument ('--log_type', help='Type of log to download ', choices=['audit', 'flow', 'all'], required=True)
    parser.add_argument ('--start', default='1 Month ago', help='start date to download')
    parser.add_argument ('--end', default='now', help='End date to download.')
    parser.add_argument ('--resume', default='no', choices=['yes', 'no'],help='resume download.')
    parser.add_argument ('--select_project', default='no', choices=['yes', 'no'], help='select project to download')
    args = parser.parse_args ()
    return args

def get_logging_list(project_id, log_type, credentials, start_date, end_date) :
    if log_type.upper() == 'AUDIT':
        filter_str = f' timestamp<=\"{end_date}\" AND timestamp>=\"{start_date}\" AND logName:\"cloudaudit.googleapis.com\" AND NOT protoPayload.serviceData.@type: \"type.googleapis.com/google.cloud.bigquery.logging.v1.AuditData\"'
    elif log_type.upper() == 'FLOW':
        filter_str = f' timestamp<=\"{end_date}\" AND timestamp>=\"{start_date}\" AND resource.type=\"gce_subnetwork\" AND log_id(\"compute.googleapis.com/vpc_flows\")'
    elif log_type.upper() == 'ALL':
        filter_str = f' timestamp<=\"{end_date}\" AND timestamp>=\"{start_date}\" AND NOT protoPayload.serviceData.@type: \"type.googleapis.com/google.cloud.bigquery.logging.v1.AuditData\"'
    client = google.cloud.logging_v2.Client(project=project_id, credentials=credentials)
    return client.list_entries(filter_=filter_str, page_size=1000)


def select_dates(start, end) :
    start_date_input = start
    start_date = parse (start_date_input, settings={'TIMEZONE' : 'UTC'})
    end_date_input = end
    end_date = parse (end_date_input, settings={'TIMEZONE' : 'UTC'})
    if (not start_date_input or not end_date_input) :
        print ('You must introduce a date')
    if start_date > end_date :
        print ('start date needs to be before than end date')
    else :
        return start_date.isoformat () + 'Z', end_date.isoformat () + 'Z'


def save_log(log,filename, format):
    with open("data/" + filename, "a") as file:
        if format == 'json':
            file.write(json.dumps(log))
        elif format == 'text':
            file.write(log)


def resume_operations(project_id):
    current_path = os.getcwd()
    resdown = glob.glob(current_path + '/data/*.json')
    for file in resdown:
        downfilename = os.path.basename(file).split('.', 1)[0]
        key_del = [new_key for new_key in project_id.items() if new_key[1] == downfilename][0][0]
        del project_id[key_del]
    return project_id

def resume_file(project_id):
    with open('data/projects.txt', 'r') as proj:
        lines = proj.readlines()
        for line in lines:
            key_del = [new_key for new_key in project_id.items() if new_key[1] == line.strip()][0][0]
            del project_id[key_del]
    return project_id

        
def main():
    print("Authenticating")
    args = argprocessor()
    credentials = service_account.Credentials.from_service_account_file('service-account.json')
    print("Obtaining project list")
    project_name, project_id,number = get_project_list(credentials)
    print("There is",number,"project/s")
    start,end = select_dates(args.start, args.end)
    filename =[]
    if args.resume.upper() == 'YES':
       project_id = resume_file(project_id)
       print('Resuming download of', len(project_id), 'projects')
    if args.select_project.upper() == 'YES':
        project_value = {}
        for key, value in project_name.items():
            print(key,value)
        project_sel = int(input('Select a project by its number: '))
        project_value[project_sel] = project_id[project_sel]
        project_id = project_value
    for key , value in project_id.items():
        print("Checking logs for",project_name[key], "/ project_id:", value )
        log = get_logging_list(value,args.log_type, credentials, start, end)
        data = list(log)
        if len(data) == 0:
            print('No', args.log_type, 'logs for project:', project_name[key])
            save_log(value +'\n', "projects.txt", 'text')
        else:
            print("Saving logs from project", project_name[key], "in data/" + value + ".json")
            save_log(value +'\n', "projects.txt", 'text')
            for entries in data:
                save_log(entries.to_api_repr(),value + ".json", 'json')


if __name__ == '__main__' :
    main ()
