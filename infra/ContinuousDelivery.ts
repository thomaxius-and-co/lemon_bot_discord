import { App, Stack, StackProps } from 'aws-cdk-lib'
import { Role, ManagedPolicy, FederatedPrincipal, OpenIdConnectProvider } from 'aws-cdk-lib/aws-iam'

async function main() {
  const app = new App()
  new ContinuousDeliveryStack(app)
  app.synth()
}

class ContinuousDeliveryStack extends Stack {
  constructor(scope: App) {
    super(scope, "ContinuousDelivery", {
      env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION,
      }
    })

    const githubRepositories = [{
      repo: "thomaxius-and-co/lemon_bot_discord",
      branch: "github-actions-test"
    }, {
      repo: "thomaxius-and-co/lemon_bot_discord",
      branch: "master"
    }]

    const githubConnectProvider = new OpenIdConnectProvider(this, "OpenIdConnectProvider", {
      url: "https://token.actions.githubusercontent.com",
      clientIds: ["sts.amazonaws.com"],
      thumbprints: ["6938fd4d98bab03faadb97b34396831e3780aea1"],
    })

    const condition = {
      "ForAnyValue:StringLike": {
        "token.actions.githubusercontent.com:sub": githubRepositories
          .map(_ => `repo:${_.repo}:ref:refs/heads/${_.branch}`)
      }
    }
    const deployRole = new Role(this, "DeployRole", {
      roleName: "GithubActionsAccessRole",
      assumedBy: new FederatedPrincipal(githubConnectProvider.openIdConnectProviderArn, condition, "sts:AssumeRoleWithWebIdentity"),
    })


    deployRole.addManagedPolicy(ManagedPolicy.fromAwsManagedPolicyName("AdministratorAccess"))
  }
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
