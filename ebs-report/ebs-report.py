# Include standard modules
import argparse
import csv
import getopt
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from operator import itemgetter

import boto3
from botocore.exceptions import ClientError

# Define the program description
text = 'This program will generated EBS volume report; you must pass aws profile(s); will run in us-east-1 region by default'

# Defaults, can be modified
AWS_REGIONS = ['us-east-1']

now = datetime.now(timezone.utc)
timestr = time.strftime("%Y%m%d-%H%M%S")


def get_snapshots():
    """
        List all EC2 snapshots owned by account in region.
        It is faster than querying aws each time.
        :return: json dictionary list
    """
    #client = boto_ec2_client(region)
    paginator = ec2.get_paginator('describe_snapshots')
    response_iterator = paginator.paginate(OwnerIds=[accountId])
    snapshots = list()
    for page in response_iterator:
        for obj in page['Snapshots']:
            snapshots.append(obj)

    return(snapshots)


def latest_snapshot(snapshots):
    """
        Return latest snapshot from a list of snapshots.

    """
    # new list for sorting
    snaps = list()

    # update list with data and snapshotId
    for snapshot in snapshots:
        snaps.append({'date': snapshot['StartTime'], 'snap_id': snapshot['SnapshotId']})

    # sort new list by date
    sorted_snapshots = sorted(snaps, key=lambda k: k['date'], reverse=True)

    # get latest snapshot id
    latest_snap_id = sorted_snapshots[0]['snap_id']

    # get latest snapshot date
    latest_snap_date = sorted_snapshots[0]['date']

    return(latest_snap_date, latest_snap_id)


def get_volumes(InstanceId, VolumeID):
    """
        List all volumes from transmitted instance id // Counting Snapshots by Description
        :return: number of snaps and volume age in days
    """

    paginator = ec2.get_paginator('describe_volumes')
    response_iterator = paginator.paginate(VolumeIds=[VolumeID])
    for page in response_iterator:
        for volume in page['Volumes']:
            # calculating volume age
            voldate = volume['CreateTime']
        VolumeAge = now-voldate
        VolumeSize = volume['Size']
        # filtering snapshots by VolumeID
        FilteredSnapshots = [x for x in snapshots if x['VolumeId'] == volume['VolumeId']]

        # if FilteredSnapshots is empty, volume have no snapshot
        if len(FilteredSnapshots) == 0:
            #print('no snapshot')
            latestSnap = u''
            latestSnapId = "No Snapshot"
        else:
            # print(FilteredSnapshots)
            latestSnap, latestSnapId = latest_snapshot(FilteredSnapshots)

        print("latest snapshot %s" % latestSnapId)

        return VolumeAge, len(FilteredSnapshots), VolumeSize, latestSnap, latestSnapId


def get_ec2():
    """
        List all EC2 instances.
        :return: list of rows to be added in CVS
    """

    paginator = ec2.get_paginator('describe_instances')
    response_iterator = paginator.paginate()

    row = list()
    for page in response_iterator:
        for obj in page['Reservations']:
            for Instance in obj['Instances']:
                InstanceName = None
                if Instance['State']['Name'] != 'terminated':
                    try:
                        for tag in Instance['Tags']:
                            if tag["Key"] == 'Name':
                                InstanceName = tag["Value"]
                    except:
                        InstanceName = ""

                print("running for instance %s" % InstanceName)
                for Volume in Instance['BlockDeviceMappings']:
                    # print(Instance['BlockDeviceMappings'])
                    VolumeAge, SnapshotsCount, VolumeSize, latestSnapDate, latestSnapId = get_volumes(Instance['InstanceId'], Volume['Ebs']['VolumeId'])

                    row.append({
                        'AccountName': accountAlias,
                        'Region': region,
                        'InstanceId': Instance['InstanceId'],
                        'InstanceName': InstanceName,
                        'VolumeID': Volume['Ebs']['VolumeId'],
                        'VolumeSize': VolumeSize,
                        'VolAge': str(VolumeAge).split(".")[0],
                        'LatestSnapDate': latestSnapDate,
                        'LatestSnapId': latestSnapId,
                        'SnapshotCount': SnapshotsCount
                    })
    return row


if __name__ == '__main__':

    # Initiate the parser
    parser = argparse.ArgumentParser(description=text)
    parser.add_argument("--profile", "-p", nargs='+', help="set AWS Profile, this is required")
    parser.add_argument("--region", "-r", nargs='+', default=AWS_REGIONS,
                        help="set AWS region, will default to us-east-1")

    # Read arguments from the command line
    args = parser.parse_args()

    # report headers
    fieldnames = ['AccountName', 'Region', 'InstanceId', 'InstanceName', 'VolumeSize',
                  'VolumeID', 'VolAge', 'LatestSnapDate', 'LatestSnapId', 'SnapshotCount']

    # initialize report, all resulfs from each profile/region will append to this
    report = list()

    # looping thru each profile
    for arg in args.profile:

        # set boto3 session to use profile
        session = boto3.Session(profile_name=arg)

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
            ec2 = session.client('ec2', region_name=region)

            # get list of snapshots for profile
            snapshots = get_snapshots()

            # get result and append
            report.extend(get_ec2())

    # write report to csv
    # adding field headers first
    with open('ebs-report-'+timestr+'.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in report:
            writer.writerow(item)
