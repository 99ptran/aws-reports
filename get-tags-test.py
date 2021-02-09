import argparse
import boto3
import csv
import os


#output_file_path = "./tmp/tagged-resources.csv"
#field_names = ['ResourceArn', 'TagKey', 'TagValue']

def getTags(resourceType):
    """
        get all tags keys for Filters resource-type
    """
    
    # initializing lists
    allTags = []
    uniqueTags = []
    
    
    Filters =[{
    'Name': 'resource-type',
    'Values': [resourceType]
    }]
    
    # get tags for filtered resource
    response = client.describe_tags(Filters=Filters)
    
    # get Tags from response dictionary
    tags = response['Tags']
    
    # get a list of all Tag keys
    for tag in tags:
        #for key in tag.key():
        allTags.append(tag['Key'])
        
    # get unique tag keys
    for tag in allTags:
        if tag not in uniqueTags:
            uniqueTags.append(tag)
        
    #print("####unique tags####")
    #print(uniqueTags)
    return uniqueTags


    
    


client = boto3.client('ec2')

tags=getTags("instance")


print("####unique tags####")
print(tags)



