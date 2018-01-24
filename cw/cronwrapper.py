#!/usr/bin/env python

import os
import time
import datetime
from gmailer import senderror
import sys
import runprocess
import optparse

import vmtools

vm_root_path = vmtools.vm_root_grabber()
sys.path.append(vm_root_path)
from local_settings import *

# make sure cw dir exists
cw_dir = '/var/log/cw'
if not os.path.isdir(cw_dir):
    os.makedirs(cw_dir)

# basic variables
hostname_output = runprocess.runprocess('hostname')
local_hostname =  hostname_output['output'][0].strip()

# get today's date
def get_time():
    """Get the current time and return a dictionary with the current time available in various formats
    """
    today_raw = datetime.datetime.now()
    today = today_raw.strftime("%Y%m%d")
    today_extended = today_raw.strftime("%Y%m%d%H%M%S")
    todaymonth = today_raw.strftime("%Y%m")
    right_now_dict = {'today_raw':today_raw, 'today':today, 'today_extended': today_extended, 'todaymonth': todaymonth }
    return right_now_dict

if __name__ == '__main__':
    # make paser object
    parser = optparse.OptionParser(description="A tool to wrap cron jobs and send an email if the exit status is non-zero or stderr output is detected.")
    # add the command and log_name
    parser.add_option('-c', '--command', help="The command that cronwrapper should run. If the command contains spaces, enclose in single quotes", dest='command', action='store')
    parser.add_option('-l', '--log_name', help="The name that cronwrapper will use to store stdout and sterr logs in /var/log/cw (stdout: /var/log/cw/<log_name> stderr: /var/log/cw/<log_name>.err).", dest='log_name', action='store')
    # parse our options
    (opts, args) = parser.parse_args()
    # if any of the arguments are missing print help and exit
    if opts.command is None:
        parser.print_help()
        sys.exit(-1)
    if opts.log_name is None:
        parser.print_help()
        sys.exit(-1)
    # make easier variables
    log_name = opts.log_name
    command = opts.command
    stdout_log_file = '/var/log/cw/'+log_name
    stderr_log_file = '/var/log/cw/'+log_name+'.err'
    # open stdout log file
    stdout_log_file_object = open(stdout_log_file, 'a')
    # write start stamp
    get_time_dict = get_time()
    start_stdout_message = '\n\nStart stdout from %s %s\n\n' % (log_name, get_time_dict['today_extended'])
    stdout_log_file_object.write(start_stdout_message)
    # close file while process is running
    stdout_log_file_object.close()
    # run process and create our output dictionary
    output_dict = runprocess.runprocess_full(command,singlestring=True)
    # open stdout log file
    stdout_log_file_object = open(stdout_log_file, 'a')
    # write the stdout
    for line in output_dict['stdout']:
        stdout_log_file_object.write("%s" % line)
    # write end stamp
    get_time_dict = get_time()
    end_stdout_message = '\nEnd stdout from %s %s' % (log_name, get_time_dict['today_extended'])
    stdout_log_file_object.write(end_stdout_message)
    # close file
    stdout_log_file_object.close()

    # non-zero exit status and stderr
    if (output_dict['exit_status'] != 0) and output_dict['stderr']:
        stderr_log_file_object = open(stderr_log_file, 'a')
        # write stderr start stamp
        get_time_dict = get_time()
        start_stderr_message = '\n\nStart stderr from %s %s\n\n' % (log_name, get_time_dict['today_extended'])
        stderr_log_file_object.write(start_stderr_message)
        # write stderr
        for line in output_dict['stderr']:
            stderr_log_file_object.write("%s\n" % line)
        subject_text= '{}{}{}'.format(str(log_name), ' failed and produced stderr on server: ', str(local_hostname))
        # write stderr end stamp
        get_time_dict = get_time()
        end_stderr_message = '\nEnd stderr from %s %s' % (log_name, get_time_dict['today_extended'])
        stderr_log_file_object.write(end_stderr_message)
        stderr_log_file_object.close()
        stderr_string = '\n'.join(output_dict['stderr'])
        # if stderr is longer that 2000 character attach it to the email
        if len(stderr_string) > 2000:
            body_text = '%s failed and produced stderr on server: %s\n\nThe stderr is longer than 2000 characters and therefore has been attached. below are the first 3 lines of the stderr output:\n\n%s' % (log_name, local_hostname, '\n'.join(output_dict['stderr'][:3]))
            temp_attachment_file = vm_root_path+'/stderr.txt'
            temp_attachment_file_object = open(temp_attachment_file, 'w')
            for line in output_dict['stderr']:
                temp_attachment_file_object.write("%s" % line)
            temp_attachment_file_object.close()
            senderror(subject_text=subject_text, body_text=body_text, username=GMAIL_USER, password=GMAIL_PASS, recipients=ERROR_RECIPIENTS, attachment_files_path=[temp_attachment_file])
        else: 
            body_text = '%s failed and produced stderr on server: %s\n\nThe stderr is below:\n\n%s' % (log_name, local_hostname, '\n'.join(output_dict['stderr']))
            senderror(subject_text=subject_text, body_text=body_text, username=GMAIL_USER, password=GMAIL_PASS, recipients=ERROR_RECIPIENTS)


    # exit status zero with stderr
    if (output_dict['exit_status'] == 0) and output_dict['stderr']:
        stderr_log_file_object = open(stderr_log_file, 'a')
        # write stderr start stamp
        get_time_dict = get_time()
        start_stderr_message = '\n\nStart stderr from %s %s\n\n' % (log_name, get_time_dict['today_extended'])
        stderr_log_file_object.write(start_stderr_message)
        # write stderr
        for line in output_dict['stderr']:
            stderr_log_file_object.write("%s" % line)
        subject_text=log_name+' succeded and produced stderr on server: '+local_hostname
        # write stderr end stamp
        get_time_dict = get_time()
        end_stderr_message = '\nEnd stderr from %s %s' % (log_name, get_time_dict['today_extended'])
        stderr_log_file_object.write(end_stderr_message)
        # close file
        stderr_log_file_object.close()
        stderr_string = '\n'.join(output_dict['stderr'])

        # if stderr is longer that 2000 character attach it to the email
        if len(stderr_string) > 2000:
            body_text = '%s succeded and produced stderr on server: %s\n\nThe stderr is longer than 2000 characters and therefore has been attached. below are the first 3 lines of the stderr output:\n\n%s' % (log_name, local_hostname, '\n'.join(output_dict['stderr'][:3]))
            temp_attachment_file = vm_root_path+'/stderr.txt'
            temp_attachment_file_object = open(temp_attachment_file, 'w')
            for line in output_dict['stderr']:
                temp_attachment_file_object.write("%s" % line)
            temp_attachment_file_object.close()
            senderror(subject_text=subject_text, body_text=body_text, username=GMAIL_USER, password=GMAIL_PASS, recipients=ERROR_RECIPIENTS, attachment_files_path=[temp_attachment_file])
        else: 
            body_text = '%s succeded and produced stderr on server: %s\n\nThe stderr is below:\n\n%s' % (log_name, local_hostname, '\n'.join(output_dict['stderr']))
            senderror(subject_text=subject_text, body_text=body_text, username=GMAIL_USER, password=GMAIL_PASS, recipients=ERROR_RECIPIENTS)


    # non-zero exit status and no stderr
    if (output_dict['exit_status'] != 0) and (not output_dict['stderr']):
        # send email
        subject_text= log_name+' failed with no stderr on server: '+local_hostname
        body_text = '%s failed and unfortunately did not produce any stderr on server: %s. Remeber stdout logs are located here: %s' % (log_name, local_hostname, stdout_log_file)
        senderror(subject_text=subject_text, body_text=body_text, username=GMAIL_USER, password=GMAIL_PASS, recipients=ERROR_RECIPIENTS)
    # exit status zero and no stderr
    if (output_dict['exit_status'] == 0) and (not output_dict['stderr']):
        # if everything goes well pass cuz stdout logs were already written
        pass
