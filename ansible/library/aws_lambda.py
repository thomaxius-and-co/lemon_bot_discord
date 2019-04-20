from ansible.module_utils.basic import AnsibleModule
from botocore.exceptions import ClientError
import boto3

from contextlib import contextmanager
import shutil
import subprocess
import tempfile
import contextlib

def main():
    module = AnsibleModule(
        argument_spec={
            "name": {"type": "str", "required": True},
            "path": {"type": "str", "required": True},
            "handler": {"type": "str", "required": True},
            "runtime": {"type": "str", "required": True, "choices": ["nodejs6.10", "nodejs8.10"]},
            "role": {"type": "str", "required": True},
            "env": {"type": "dict"},
        }
    )

    # TODO: Run npm install with proper version of nodejs

    client = boto3.client("lambda")

    func = get_function(client, module.params["name"])
    zip_file = build_lambda(module.params["path"])

    lambda_environment = {"Variables": module.params["env"] or {}}

    if func is None:
        func = client.create_function(
            FunctionName=module.params["name"],
            Runtime=module.params["runtime"],
            Role=module.params["role"],
            Handler=module.params["handler"],
            Code={"ZipFile": zip_file},
            Timeout=15,
            MemorySize=128,
            Environment=lambda_environment,
            Publish=False
        )

        func = get_function(client, module.params["name"])
        module.exit_json(changed=True, **func)
    else:
        changed = True # TODO: Check if update is needed

        client.update_function_configuration(
            FunctionName=module.params["name"],
            Role=module.params["role"],
            Handler=module.params["handler"],
            Environment=lambda_environment
        )
        client.update_function_code(
            FunctionName=module.params["name"],
            ZipFile=zip_file,
            Publish=False
        )

        func = get_function(client, module.params["name"])
        module.exit_json(changed=changed, **func)

def build_lambda(path):
    with mkdtemp() as tmp_dir:
        src_dir = tmp_dir + "/src"
        shutil.copytree(path, src_dir)
        subprocess.check_call(["npm", "install"], cwd=src_dir)
        subprocess.check_call(["zip", "-r",  "../lambda.zip", "."], cwd=src_dir)

        with open(tmp_dir + "/lambda.zip", "rb") as zip_file:
            return zip_file.read()

def get_function(client, function_name):
    try:
        return client.get_function(FunctionName=function_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return None
        else:
            raise e

@contextmanager
def mkdtemp():
    tmp_dir = tempfile.mkdtemp()
    try:
        yield tmp_dir
    finally:
        rmtree(tmp_dir)

def rmtree(path):
    try:
        shutil.rmtree(path)
    except:
        pass

if __name__ == "__main__":
    main()
