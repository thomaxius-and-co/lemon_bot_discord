import {App, Stack} from 'aws-cdk-lib'
import {
  InstanceClass,
  InstanceSize,
  InstanceType,
  IpAddresses,
  SecurityGroup,
  SubnetType,
  Vpc
} from "aws-cdk-lib/aws-ec2";
import {Credentials, DatabaseInstance, DatabaseInstanceEngine, PostgresEngineVersion} from "aws-cdk-lib/aws-rds";

async function main() {
  const app = new App()
  new Application(app)
  app.synth()
}

class Application extends Stack {
  constructor(scope: App) {
    super(scope, "Application", {
      env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION,
      }
    })

    const vpc = new Vpc(this, "Vpc", {
      ipAddresses: IpAddresses.cidr('10.0.0.0/16'),
      maxAzs: 2,
      subnetConfiguration: [{
        name: "public",
        subnetType: SubnetType.PUBLIC,
        cidrMask: 24,
      }]
    })

    const dbSecurityGroup = new SecurityGroup(this, "DatabaseSecurityGroup", { vpc })
    const engine = DatabaseInstanceEngine.postgres({ version: PostgresEngineVersion.VER_12 })
    const db = new DatabaseInstance(this, "Database", {
      engine,
      vpc,
      instanceType: InstanceType.of(InstanceClass.T4G, InstanceSize.MICRO),
      securityGroups: [ dbSecurityGroup ],
      vpcSubnets: { subnetType: SubnetType.PUBLIC },
      credentials: Credentials.fromGeneratedSecret('postgres'),
      autoMinorVersionUpgrade: true,
      allocatedStorage: 20,
      maxAllocatedStorage: 20,
    })
  }
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
