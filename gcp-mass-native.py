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
# v0.04 - avoid not recognized types by protobuf
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
    return client.list_entries(filter_=filter_str)


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


def save_log(log,filename):
    with open(filename, "a") as file:
        file.write(json.dumps(log))


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
        current_path = os.getcwd()
        resdown = glob.glob(current_path + '/data/*.json')
        for items in resdown:
            file = items.split(current_path + '/data/',1)
            filename += file
        print(filename)
        exit(2)
    for key , value in project_id.items():
        print("Checking logs for",project_name[key])
        log = get_logging_list(value,args.log_type, credentials, start, end)
        data = list(log)
        if len(data) == 0:
            print('No', args.log_type, 'logs for project:', project_name[key], "/ project id:", value)
        else:
            print("Saving logs from project", project_name[key], "in data/" + value + ".json")
            for entries in data:
                save_log(entries.to_api_repr(),"data/" + value + ".json")


if __name__ == '__main__' :
    main ()
