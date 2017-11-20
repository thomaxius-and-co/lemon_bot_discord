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
            "role": {"type": "str", "required": True},
            "env": {"type": "dict", "required": True},
        }
    )

    client = boto3.client("lambda")

    func = get_function(client, module.params["name"])
    zip_file = build_lambda(module.params["path"])
    if func is None:
        func = client.create_function(
            FunctionName=module.params["name"],
            Runtime="nodejs6.10",
            Role=module.params["role"],
            Handler=module.params["handler"],
            Code={"ZipFile": zip_file},
            Timeout=15,
            MemorySize=128,
            Environment={"Variables": module.params["env"]},
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
            Environment={"Variables": module.params["env"]}
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
        shutil.rmtree(tmp_dir)
    except:
        pass

if __name__ == "__main__":
    main()
