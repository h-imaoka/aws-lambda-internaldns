import boto3
import logging
import jmespath
import os


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handle(event, context):
    try:
        _DOMAIN = os.environ['DOMAIN']
        _HOSTED_ZONE_ID = os.environ['HOSTED_ZONE_ID']
        instance_id = event['detail']['instance-id']
        if event['detail']['state'] != 'terminated':
            exit(1)

        c_ec2 = boto3.client('ec2')
        res = c_ec2.describe_instances(InstanceIds=[instance_id])
        (tag_name,) = jmespath.search(
            'Reservations[0].Instances[0].Tags[?Key==`Name`].Value',
            res
            )
        logger.info(tag_name)

        # Cfn or Terraform ReCreation
        res = c_ec2.describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': [tag_name]},
                {'Name': 'instance-state-name', 'Values': ['running']}
                ]
            )
        if len(res['Reservations']) > 0:
            return 0

        c_r53 = boto3.client('route53')
        # get current_record
        res = c_r53.list_resource_record_sets(
            HostedZoneId=_HOSTED_ZONE_ID
            )
        jp = 'ResourceRecordSets[?(Name==`%s.%s`&&Type==`A`)]' % (tag_name, _DOMAIN)
        (rrs,) = jmespath.search(jp, res)

        change_batch = {
            'Changes': [
                {
                    'Action': 'DELETE',
                    'ResourceRecordSet': rrs
                }
                ]
            }
        c_r53.change_resource_record_sets(
            HostedZoneId=_HOSTED_ZONE_ID,
            ChangeBatch=change_batch
            )

    except Exception as e:
        logger.error(e)
        raise e
