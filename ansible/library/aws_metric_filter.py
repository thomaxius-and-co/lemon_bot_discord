from ansible.module_utils.basic import *
import boto3

def head(xs):
    return next(iter(xs), None)

def main():
    module = AnsibleModule(
        argument_spec={
            "filterName": {"type": "str", "required": True},
            "logGroupName": {"type": "str", "required": True},
            "filterPattern": {"type": "str", "required": True},
            "metricName": {"type": "str", "required": True},
            "metricNamespace": {"type": "str", "required": True},
            "metricValue": {"type": "str", "required": True}
        }
    )

    logGroupName = module.params["logGroupName"]
    filterPattern = module.params["filterPattern"]
    filterName = module.params["filterName"]
    metricName = module.params["metricName"]
    metricNamespace = module.params["metricNamespace"]
    metricValue = module.params["metricValue"]

    client = boto3.client("logs")

    existing_filters = client.describe_metric_filters(filterNamePrefix=filterName)["metricFilters"]
    existing = head(filter(lambda f: f["filterName"] == filterName, existing_filters))
    if existing is None:
        new_state = client.put_metric_filter(
            logGroupName=logGroupName,
            filterName=filterName,
            filterPattern=filterPattern,
            metricTransformations=[{
                "metricName": metricName,
                "metricNamespace": metricNamespace,
                "metricValue": metricValue
            }]
        )
        module.exit_json(changed=True, result=new_state)
        return
    else:
        # LOL
        changed = False
        if existing["logGroupName"] != logGroupName:
            changed = True
        if existing["filterPattern"] != filterPattern:
            changed = True
        if existing["metricTransformations"][0]["metricNamespace"] != metricNamespace:
            changed = True
        if existing["metricTransformations"][0]["metricName"] != metricName:
            changed = True
        if existing["metricTransformations"][0]["metricValue"] != metricValue:
            changed = True

        if changed:
            new_state = client.put_metric_filter(
                logGroupName=logGroupName,
                filterName=filterName,
                filterPattern=filterPattern,
                metricTransformations=[{
                    "metricName": metricName,
                    "metricNamespace": metricNamespace,
                    "metricValue": metricValue
                }]
            )
            module.exit_json(changed=True, result=new_state)
        else:
            module.exit_json(changed=False, result=existing)

if __name__ == "__main__":
    main()
