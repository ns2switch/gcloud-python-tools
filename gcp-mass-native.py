from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from google.oauth2 import service_account
from google.protobuf.json_format import MessageToDict
import google.cloud.logging
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
    return project_name, project_id

def argprocessor():
    parser = argparse.ArgumentParser(prog='gcp_mass_downloader', description='Insert log type you wanna download:', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--log_type', help='Type of log to download ', choices=['audit',
        'flow', 'all'], required=True)
    parser.add_argument('--start', default='1 Month ago', help='start date to download')
    parser.add_argument('--end', default='now', help='End date to download.')
    #parser.add_argument('--format', default='json', help='format to output logs', choices=['json','list', 'yaml','none', 'text', 'object', 'default'])
    args = parser.parse_args()
    return args

def get_logging_list(project_id, log_type, credentials, start_date, end_date) :
    if log_type.upper() == 'AUDIT':
        filter_str = f' timestamp<=\"{end_date}\" AND timestamp>=\"{start_date}\" AND logName:\"cloudaudit.googleapis.com\"'
    elif log_type.upper() == 'FLOW':
        filter_str = f' timestamp<=\"{end_date}\" AND timestamp>=\"{start_date}\" AND resource.type=\"gce_subnetwork\" AND log_id(\"compute.googleapis.com/vpc_flows\")'
    elif log_type.upper() == 'ALL':
        filter_str = f' timestamp<=\"{end_date}\" AND timestamp>=\"{start_date}\"'
    client = google.cloud.logging.Client(project=project_id, credentials=credentials)
    for entries in  client.list_entries(filter_=filter_str):
        return entries.to_api_repr()


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


def main():
    args = argprocessor()
    credentials = service_account.Credentials.from_service_account_file('service-account.json')
    project_name, project_id = get_project_list(credentials)
    start,  end = select_dates(args.start, args.end)
    for key , value in project_id.items():
        log = get_logging_list(value,args.log_type, credentials, start, end)
        if log == None:
            print('No ', args.log_type, ' logs for ', project_name[key])
        else:
            print(log)
if __name__ == '__main__' :
    main ()
