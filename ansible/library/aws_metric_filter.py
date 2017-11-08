from ansible.module_utils.basic import *
import boto3

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

    existingFilters = client.describe_metric_filters(filterNamePrefix=filterName)["metricFilters"]
    if len(existingFilters) == 0:
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
        module.fail_json(msg="Not implemented")

if __name__ == "__main__":
    main()
