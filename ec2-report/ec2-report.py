# Include standard modules
import argparse
import boto3
import csv
import time
from datetime import datetime, timedelta, timezone


# Define the program description
text = 'This program will generated EC2 instance report with all tags; you must pass aws profile(s); will run in us-east-1 region by default'

# Defaults, can be modified
AWS_REGIONS = ['us-east-1']

now=datetime.now(timezone.utc)
timestr = time.strftime("%Y%m%d-%H%M%S")


def get_ec2():
    """
        List all EC2 instances.
        :return: list of rows to be added in CVS
    """
    # Create EC2 client
    #client = boto_ec2_client(region)
    paginator = ec2.get_paginator('describe_instances')
    response_iterator = paginator.paginate()
    result = list()
    row = {}
    
    # get all tag keys
    tag_set = []
    for page in response_iterator:
        for obj in page['Reservations']:
            for Instance in obj['Instances']:
                for tag in Instance.get('Tags', []):
                    if tag.get('Key'):
                        tag_set.append(tag.get('Key'))
    
    # get all unique tag keys                   
    tag_set = list(set(tag_set))
    
    for page in response_iterator:
        for obj in page['Reservations']:
            for Instance in obj['Instances']:
                # set instancename from tag, "" if none exist
                InstanceName=None
                if Instance['State']['Name'] != 'terminated':
                    try:
                        for tag in Instance['Tags']:
                            if tag["Key"] == 'Name':InstanceName = tag["Value"]
                            
                    except:
                        InstanceName = ""
                        
                print("running for instance %s" % InstanceName)   
                
                # add tag key/value pair to dict; adding "tag:" to tag keys
                for tag in Instance.get('Tags',[]):
                    row['tag:'+tag.get('Key')] = tag.get('Value')
                    
                # add instance info to dict; can append other instance info as needed, make sure to add colume header.
                row['AccountName'] = accountAlias
                row['Region'] = region 
                row['InstanceId'] = Instance['InstanceId']
                row['InstanceName'] = InstanceName
                row['InstanceType'] = Instance['InstanceType']
                row['InstancePrivateIP'] = Instance.get('PrivateIpAddress', '')
                row['InstancePublicIP'] = Instance.get('PublicIpAddress', '')
                row['InstanceState'] = Instance['State'].get('Name', '')
                row['InstanceSubnet'] = Instance.get('SubnetId', '')
                row['InstanceVPC'] = Instance.get('VpcId', '')
                            
                # append dict to list
                result.append(dict(row))
     
    # return result and unique tag keys                                 
    return result, tag_set

if __name__ == '__main__':

    # Initiate the parser
    parser = argparse.ArgumentParser(description = text)
    parser.add_argument("--profile", "-p", nargs = '+', help = "set AWS Profile, this is required")
    parser.add_argument("--region", "-r", nargs = '+', default = AWS_REGIONS, help = "set AWS region, will default to us-east-1")

    # Read arguments from the command line
    args = parser.parse_args()
    
    # report headers
    fieldnames = ['AccountName','Region','InstanceId','InstanceName','InstanceType','InstancePrivateIP','InstancePublicIP','InstanceState','InstanceSubnet', 'InstanceVPC']
    
    # initialize report, all resulfs from each profile/region will append to this
    report = list()
    
    # looping thru each profile
    for arg in args.profile:
        
        # set boto3 session to use profile
        session = boto3.Session(profile_name = arg)
               
        # get AWS account ID and Alias(Name)
        accountId = session.client('sts').get_caller_identity().get('Account')
        accountAlias = session.client('iam').list_account_aliases()['AccountAliases'][0]
        
        print("running for profile %s" % arg)
        print("accountID %s" % accountId)
        print("accountAlias %s" % accountAlias)
        
        # looping thru regions for each profile
        for region in args.region:
            print("running in %s region" % region)
            
            # set up boto3 client for region
            ec2 = session.client('ec2', region_name = region)
           
            # get report, tag keys 
            results, tags = get_ec2()
            
            # append tags to fieldnames; adding "tag:" to tag keys
            for tag in tags:
                fieldnames.append('tag:'+tag)
            
            report.extend(results)
             
    # write report to csv
    # adding field headers first
    with open('ec2-report-'+timestr+'.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in report:
            writer.writerow(item)
            