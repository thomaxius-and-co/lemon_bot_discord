from ansible.module_utils.basic import AnsibleModule
import boto3

def main():
    module = AnsibleModule(
        argument_spec={
            "name": {"type": "str", "required": True},
        }
    )

    name = module.params["name"]
    client = boto3.client("logs")

    log_group = find_log_group(client, name)
    if log_group is not None:
        module.exit_json(changed=False, log_group=log_group)
    else:
        client.create_log_group(logGroupName=name)
        log_group = find_log_group(client, name)
        module.exit_json(changed=True, log_group=log_group)

def find_log_group(client, name):
    response = client.describe_log_groups(logGroupNamePrefix=name)
    return head([g for g in response["logGroups"] if g["logGroupName"] == name])

def head(xs):
    return next(iter(xs), None)
