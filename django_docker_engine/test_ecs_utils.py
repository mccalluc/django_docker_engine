import unittest
import boto3

class EcsTests(unittest.TestCase):
    def setUp(self):
        self.ecs_client = boto3.client('ecs')
        self.ec2_client = boto3.client('ec2')
        self.key_pair_name = 'test_django_docker'
        self.instance_id = None

    def tearDown(self):
        self.ec2_client.delete_key_pair(KeyName=self.key_pair_name)
        self.instance.terminate()

    def test_create_cluster(self):
        CLUSTER_NAME = 'test_cluster'
        response = self.ecs_client.create_cluster(clusterName=CLUSTER_NAME)
        self.assertEqual(response['cluster']['status'], 'ACTIVE')

        TASK_NAME = 'test_task'
        response = self.ecs_client.register_task_definition(
            family=TASK_NAME,
            containerDefinitions=[{
                'name': 'my_container',
                'image': 'nginx:1.11-alpine',
                'portMappings': [
                    {
                        'containerPort': 80,
                        'protocol': 'tcp'
                        # host port will be assigned
                    },
                ],
                # At least one required:
                'memory': 100,  # Hard limit
                'memoryReservation': 50, # Soft limit
            }]
        )
        self.assertEqual(response['taskDefinition']['status'], 'ACTIVE')

        response = self.ec2_client.create_key_pair(KeyName=self.key_pair_name)
        self.assertEqual(response['KeyName'], self.key_pair_name)

        response = self.ec2_client.run_instances(
            ImageId='ami-275ffe31',
            # us-east-1: amzn-ami-2016.09.g-amazon-ecs-optimized
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.nano',
            KeyName=self.key_pair_name
        )
        self.assertEqual(response['Instances'][0]['State']['Name'], 'pending')
        instance_id = response['Instances'][0]['InstanceId']
        self.instance = self.ec2_client.Instance(instance_id)
        self.instance.wait_until_running()

        #
        # # TODO: register instance with cluster
        #
        # response = self.ecs_client.run_task(
        #     cluster=CLUSTER_NAME,
        #     taskDefinition=TASK_NAME
        # )
        # print response
        # # TODO: assert
        #
        # # Requires revision
        # #response = self.ecs_client.deregister_task_definition()
        #
        #
        # response = self.ecs_client.delete_cluster(cluster=CLUSTER_NAME)
        # self.assertEqual(response['cluster']['status'], 'INACTIVE')