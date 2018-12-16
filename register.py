import boto3
import logging
import jmespath
import time
import os


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handle(event, context):
    try:
        logger.info(event)
        _DOMAIN = os.environ['DOMAIN']
        _HOSTED_ZONE_ID = os.environ['HOSTED_ZONE_ID']
        instance_id = event['detail']['instance-id']
        if event['detail']['state'] != 'running':
            exit(1)

        c_ec2 = boto3.client('ec2')

        while True:
            res = c_ec2.describe_instances(InstanceIds=[instance_id])
            (tag_name, ip_addr) = jmespath.search(
                'Reservations[0].Instances[0].[Tags[?Key==`Name`].Value | [0],  PrivateIpAddress ]',
                res
            )
            logger.info(tag_name)
            logger.info(ip_addr)
            time.sleep(1)
            if None not in (tag_name, ip_addr):
                break

        c_r53 = boto3.client('route53')
        change_batch = {
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': "%s.%s" % (tag_name, _DOMAIN),
                        'Type': 'A',
                        'TTL': 300,
                        'ResourceRecords': [
                            {'Value': ip_addr}
                            ]
                    }
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
