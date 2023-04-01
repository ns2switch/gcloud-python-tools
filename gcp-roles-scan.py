#!/usr/bin/env python3
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
# v0.8 - modifying roles search

import argparse
import json

from google.cloud import resourcemanager_v3
from google.iam.v1 import iam_policy_pb2
from google.oauth2 import service_account
from google.protobuf.json_format import MessageToDict
from googleapiclient import discovery


def get_project_list(credentials):
	project_name = {}
	project_id = {}
	i = 0
	service = discovery.build('cloudresourcemanager', 'v1', credentials = credentials)
	request = service.projects().list()
	while request is not None:
		response = request.execute()
		for project in response.get('projects', []):
			project_name[i] = project["name"]
			project_id[i] = project["projectId"]
			i += 1
		request = service.projects().list_next(previous_request = request, previous_response = response)
	return project_name, project_id, i


def argprocessor():
	parser = argparse.ArgumentParser(prog = 'gcp_mass_downloader', description = 'Search users in GCP:',
	                                 formatter_class = argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('--resume', default = 'no', choices = ['yes', 'no'], help = 'resume download.')
	parser.add_argument('--select_project', default = 'no', choices = ['yes', 'no'],
	                    help = 'select project to download')
	args = parser.parse_args()
	return args


def save_log(log, filename, format):
	with open("data/" + filename, "a", encoding = 'utf-8') as file:
		if format == 'json':
			file.write(json.dumps(log, indent = 2))
		elif format == 'text':
			file.write(log)


def save_file(data):
	with open('data/user_report.csv', 'a') as f:
		f.write(data)


def resume_file(project_id):
	with open('data/projects.txt', 'r') as proj:
		lines = proj.readlines()
		for line in lines:
			key_del = [new_key for new_key in project_id.items() if new_key[1] == line.strip()][0][0]
			del project_id[key_del]
	return project_id


def get_user_list(project_id, credentials):
	roles = ['roles/owner', 'roles/editor', 'roles/viewer','roles/iam.ServiceAccountUser', 'roles/iam.serviceAccountAdmin','roles/iam.serviceAccountTokenCreator','roles/dataflow.developer','roles/dataflow.admin','oles/composer.admin','roles/dataproc.admin','roles/dataproc.editor']
	# this roles are susceptible to be used to escalate privileges or to be used in lateral movement
    # I have included all the basic roles , because is a bad practice to assign it , and roles/viewer can be used to enumerate resources.
	user_match = {}
	client = resourcemanager_v3.ProjectsClient(credentials = credentials)
	request = iam_policy_pb2.GetIamPolicyRequest(
		resource = 'projects/{}'.format(project_id)
	)
	response: Policy = client.get_iam_policy(request = request)
	jsonwner = MessageToDict(response)
	if 'bindings' in jsonwner:
		for i in jsonwner['bindings']:
			if any([x in i['role'] for x in roles]):
				members = (i['role'], i['members'])
				for k in members[1]:
					user_match[k] = i['role']
		return user_match
	
	else:
		pass


def main():
	print("Authenticating")
	args = argprocessor()
	credentials = service_account.Credentials.from_service_account_file('security-iam-serviceaccount.json')
	print("Obtaining project list")
	project_name, project_id, number = get_project_list(credentials)
	print("There is", number, "project/s")
	if args.resume.upper() == 'YES':
		project_id = resume_file(project_id)
		print('Resuming download of', len(project_id), 'projects')
	if args.select_project.upper() == 'YES':
		project_value = {}
		for key, value in project_name.items():
			print(key, value)
		project_sel = int(input('Select a project by its number: '))
		project_value[project_sel] = project_id[project_sel]
		project_id = project_value
		print("Selecting users from project", project_id[project_sel]);
		header = 'project_name,' + 'project_id,' + 'user email,' + 'role' + '\n'
		save_log(header, 'user_report.csv', 'text')
		userList = get_user_list(project_id[project_sel], credentials)
		if userList:
			for k in userList:
				data = project_id[project_sel] + ',' + k + ',' + userList[k] + '\n'
				save_log(data, 'user_report.csv', 'text')
		print('Saved in data/user_report.csv')
	
	else:
		header = 'project_name,' + 'project_id,' + 'user email,' + 'role' + '\n'
		if args.resume.upper() == 'NO':
			save_log(header, 'user_report.csv', 'text')
		for key, value in project_id.items():
			print("Checking user for", project_name[key], "/ project_id:", value)
			userList = get_user_list(value, credentials)
			if userList:
				for k in userList:
					data = project_name[key] + ',' + value + ',' + k + ',' + userList[k] + '\n'
					save_log(data, 'user_report.csv', 'text')
			save_log(value + '\n', 'projects.txt', 'text')
			print('Saved in data/user_report.csv')


if __name__ == '__main__':
	main()
