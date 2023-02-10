import {App, Stack} from 'aws-cdk-lib'
import {IpAddresses, SubnetType, Vpc} from "aws-cdk-lib/aws-ec2";

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
      maxAzs: 1,
      subnetConfiguration: [{
        name: "public",
        subnetType: SubnetType.PUBLIC,
        cidrMask: 24,
      }]
    })

  }
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
