from itertools import chain

from ansible.module_utils.basic import AnsibleModule
import boto3

def main():
  module = AnsibleModule(
    argument_spec={
      "logGroupName": {"type": "str", "required": True},
      "filterName": {"type": "str", "required": True},
      "filterPattern": {"type": "str", "required": True},
      "destinationArn": {"type": "str", "required": True},
      #"roleArn": {"type": "str", "required": True},
    }
  )

  log_group_name = module.params["logGroupName"]
  filter_name = module.params["filterName"]
  filter_pattern = module.params["filterPattern"]
  destination_arn = module.params["destinationArn"]
  #role_arn = module.params["roleArn"]

  client = boto3.client("logs")

  pages = client.get_paginator("describe_subscription_filters").paginate(logGroupName=log_group_name, filterNamePrefix=filter_name)
  existing_subscriptions = flat_map(field("subscriptionFilters"), pages)
  existing = head(filter(lambda f: f["filterName"] == filter_name, existing_subscriptions))
  if existing is None:
    new_state = client.put_subscription_filter(
      logGroupName=log_group_name,
      filterName=filter_name,
      filterPattern=filter_pattern,
      destinationArn=destination_arn
    )
    module.exit_json(changed=True, result=new_state)
    return
  else:
    changed = False
    if existing["filterPattern"] != filter_pattern:
      changed = True
    if existing["destinationArn"] != destination_arn:
      changed = True
    #if existing["roleArn"] != role_arn:
    #  changed = True

    if changed:
      new_state = client.put_subscription_filter(
        logGroupName=log_group_name,
        filterName=filter_name,
        filterPattern=filter_pattern,
        destionationArn=destination_arn
      )
      module.exit_json(changed=True, result=new_state)
    else:
      module.exit_json(changed=False, result=existing)

def head(values):
  return next(iter(values), None)

def flat_map(func, values):
  return list(chain.from_iterable(map(func, values)))

def field(name):
  return lambda x: x[name]

if __name__ == "__main__":
  main()
