import {App, RemovalPolicy, Stack} from 'aws-cdk-lib'
import {
  InstanceClass,
  InstanceSize,
  InstanceType,
  IpAddresses,
  Peer,
  Port,
  SecurityGroup,
  SubnetType,
  Vpc
} from "aws-cdk-lib/aws-ec2";
import {Credentials, DatabaseInstance, DatabaseInstanceEngine, PostgresEngineVersion, PerformanceInsightRetention} from "aws-cdk-lib/aws-rds";
import {Repository} from "aws-cdk-lib/aws-ecr";
import {Code, Function, Runtime} from "aws-cdk-lib/aws-lambda";
import {
  AwsLogDriver,
  Cluster,
  ContainerImage,
  FargatePlatformVersion,
  FargateService,
  FargateTaskDefinition,
  Secret as EcsSecret
} from "aws-cdk-lib/aws-ecs";
import {FilterPattern, LogGroup, RetentionDays, SubscriptionFilter} from "aws-cdk-lib/aws-logs";
import {Secret} from "aws-cdk-lib/aws-secretsmanager";
import {join} from "path";
import {LambdaDestination} from "aws-cdk-lib/aws-logs-destinations";

async function main() {
  const app = new App()
  const { repository } = new ImageRepository(app)
  new Application(app, { repository, versionTag: process.env.VERSION_TAG! })
  app.synth()
}

class ImageRepository extends Stack {
  readonly repository: Repository
  constructor(scope: App) {
    super(scope, "ImageRepository")
    this.repository = new Repository(this, "Repository", {
      repositoryName: "lemon",
      lifecycleRules: [{
        maxImageCount: 2,
      }]
    })
  }
}

type ApplicationStackProps = {
  repository: Repository
  versionTag: string
}
class Application extends Stack {
  constructor(scope: App, props: ApplicationStackProps) {
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
        mapPublicIpOnLaunch: true,
      }]
    })

    const dbSecurityGroup = new SecurityGroup(this, "DatabaseSecurityGroup", { vpc })
    const engine = DatabaseInstanceEngine.postgres({ version: PostgresEngineVersion.VER_14 })
    const credentials = Credentials.fromGeneratedSecret("postgres")
    const db = new DatabaseInstance(this, "Database", {
      engine,
      vpc,
      instanceType: InstanceType.of(InstanceClass.T4G, InstanceSize.MICRO),
      securityGroups: [ dbSecurityGroup ],
      vpcSubnets: { subnetType: SubnetType.PUBLIC },
      credentials,
      allowMajorVersionUpgrade: true,
      autoMinorVersionUpgrade: true,
      allocatedStorage: 20,
      maxAllocatedStorage: 20,
      enablePerformanceInsights: true,
      performanceInsightRetention: PerformanceInsightRetention.DEFAULT,
    })

    const cluster = new Cluster(this, "Cluster", { vpc })
    const image = ContainerImage.fromEcrRepository(props.repository, props.versionTag)
    const logGroup = new LogGroup(this, "LogGroup", {
      logGroupName: "lemon",
      retention: RetentionDays.INFINITE,
      removalPolicy: RemovalPolicy.RETAIN,
    })

    const taskDefinition = new FargateTaskDefinition(this, "AppTaskDefinition", {
      cpu: 256,
      memoryLimitMiB: 512,
    })
    const appSecrets = Secret.fromSecretNameV2(this, "ApplicationSecrets", "ApplicationSecrets")
    taskDefinition.addContainer("AppContainer", {
      image,
      logging: new AwsLogDriver({ logGroup, streamPrefix: "lemon" }),
      environment: {
        "DATABASE_NAME": "postgres",
        "LOG_JSON": "true",
      },
      secrets: {
        "ADMIN_USER_IDS": EcsSecret.fromSecretsManager(appSecrets, "ADMIN_USER_IDS"),
        "LEMONBOT_TOKEN": EcsSecret.fromSecretsManager(appSecrets, "LEMONBOT_TOKEN"),
        "DISCORD_BOT_ID": EcsSecret.fromSecretsManager(appSecrets, "DISCORD_BOT_ID"),
        "DISCORD_CLIENT_ID": EcsSecret.fromSecretsManager(appSecrets, "DISCORD_CLIENT_ID"),
        "DISCORD_CLIENT_SECRET": EcsSecret.fromSecretsManager(appSecrets, "DISCORD_CLIENT_SECRET"),
        "DISCORD_CALLBACK_URL": EcsSecret.fromSecretsManager(appSecrets, "DISCORD_CALLBACK_URL"),
        "WOLFRAM_ALPHA_APPID": EcsSecret.fromSecretsManager(appSecrets, "WOLFRAM_ALPHA_APPID"),
        "OPEN_WEATHER_APPID": EcsSecret.fromSecretsManager(appSecrets, "OPEN_WEATHER_APPID"),
        "BING_CLIENTID": EcsSecret.fromSecretsManager(appSecrets, "BING_CLIENTID"),
        "BING_SECRET": EcsSecret.fromSecretsManager(appSecrets, "BING_SECRET"),
        "OSU_API_KEY": EcsSecret.fromSecretsManager(appSecrets, "OSU_API_KEY"),
        "STEAM_API_KEY": EcsSecret.fromSecretsManager(appSecrets, "STEAM_API_KEY"),
        "FACEIT_API_KEY": EcsSecret.fromSecretsManager(appSecrets, "FACEIT_API_KEY"),
        "REDIS_HOST": EcsSecret.fromSecretsManager(appSecrets, "REDIS_HOST"),
        "REDIS_PORT": EcsSecret.fromSecretsManager(appSecrets, "REDIS_PORT"),
        "WEB_SESSION_SECRET": EcsSecret.fromSecretsManager(appSecrets, "WEB_SESSION_SECRET"),
        "WITHINGS_CLIENT_ID": EcsSecret.fromSecretsManager(appSecrets, "WITHINGS_CLIENT_ID"),
        "WITHINGS_CLIENT_SECRET": EcsSecret.fromSecretsManager(appSecrets, "WITHINGS_CLIENT_SECRET"),
        "WITHINGS_CALLBACK_URL": EcsSecret.fromSecretsManager(appSecrets, "WITHINGS_CALLBACK_URL"),
        "OPENAI_KEY": EcsSecret.fromSecretsManager(appSecrets, "OPENAI_KEY"),
        "KANSALLISGALLERIA_API_KEY": EcsSecret.fromSecretsManager(appSecrets, "KANSALLISGALLERIA_API_KEY"),
        "DATABASE_USERNAME": EcsSecret.fromSecretsManager(db.secret!, "username"),
        "DATABASE_PASSWORD": EcsSecret.fromSecretsManager(db.secret!, "password"),
        "DATABASE_HOST": EcsSecret.fromSecretsManager(db.secret!, "host"),
        "DATABASE_PORT": EcsSecret.fromSecretsManager(db.secret!, "port"),
      }
    })
    appSecrets.grantRead(taskDefinition.executionRole!)
    appSecrets.grantRead(taskDefinition.taskRole)
    db.secret!.grantRead(taskDefinition.executionRole!)
    db.secret!.grantRead(taskDefinition.taskRole)

    const appSecurityGroup = new SecurityGroup(this, "AppSecurityGroup", { vpc })
    const service = new FargateService(this, "Service", {
      cluster,
      taskDefinition,
      assignPublicIp: true,
      desiredCount: 1,
      maxHealthyPercent: 100,
      minHealthyPercent: 0,
      vpcSubnets: { subnetType: SubnetType.PUBLIC },
      securityGroups: [appSecurityGroup],
      platformVersion: FargatePlatformVersion.VERSION1_4,
    })

    dbSecurityGroup.addIngressRule(appSecurityGroup, Port.tcp(5432))
    dbSecurityGroup.addIngressRule(Peer.ipv4("84.250.255.24/32"), Port.tcp(5432))


    const webhookUrlSecret = Secret.fromSecretNameV2(this, "DiscordWebhookSecret", "discord-alarm-webhook")
    const errorsToDiscordLambda = new Function(this, "ErrorsToDiscord", {
      runtime: Runtime.NODEJS_14_X,
      handler: "errors-to-discord.handler",
      code: Code.fromAsset(join(__dirname, "../errors-to-discord")),
    })
    webhookUrlSecret.grantRead(errorsToDiscordLambda)

    new SubscriptionFilter(this, "ErrorLogSubscription", {
      logGroup,
      destination: new LambdaDestination(errorsToDiscordLambda),
      filterPattern: FilterPattern.literal('{ $.level = "ERROR" }'),
    })
  }
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
