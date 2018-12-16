aws-lambda-internaldns
===

# 目的
EC2が起動したら、route53 DNS Aレコード登録
Terminateしたら、route53 DNS Aレコード削除

# Deploy

## 前提 = 依存
- docker
- docker-compose
- aws account & credentials

## 手順
1. .envrc や `export` でaws credential の環境変数を通す
2. route53のHostedzoneは先づくりしておく
3. serverless.yml 必須: 環境変数の `DOMAIN` と `HOSTED_ZONE_ID`を弄る
4. 分かる人は serverless.yml の `iamRoleStatements:` 特に `route53:*` はリソース名で絞ったほうがより安全 e.g. Resource を `arn:aws:route53:::hostedzone/XXXXXX` へ
5. `docker-compose run --rm bld sls deploy` でデプロイ

# 機能
## register
Running状態になったら、上記で指定したHostedZoneに対して Tag:Name + `DOMAIN` 値は ローカルIPアドレスでレコード登録する。

## unregister
Terminated状態になったら、上記で指定したHostedZoneに対して Tag:Name + `DOMAIN` 値は ローカルIPアドレスでレコード削除する。ただし、CFnやTerraformでre-createしたときに、先に作ってあとに(同じ名前で)
Terminateすると消しちゃうから、そこは制御している。

# test run
ec2-running.json をいじる
```
{
    "version": "0",
    "id": "xxxx-xxxxxx-xxxxx-xxxxx-xxxxx",
    "detail-type": "EC2 Instance State-change Notification",
    "source": "aws.ec2",
    "account": "xxxxxxxxx",
    "time": "2016-08-18T02:38:57Z",
    "region": "ap-northeast-1",
    "resources": [
        "arn:aws:ec2:ap-northeast-1:xxxxxx:instance/i-xxxxxxxx"
    ],
    "detail": {
        "instance-id": "i-xxxxxxx",
        "state": "running"
    }
}
```

実際使うのは detail.instance-id だけ、機能的に実際に動いているインスタンスがないと、Tag:Nameをひらえないので、ここだけ合わせる必要あり。

```
docker-compose run --rm bld sls invoke -f register -p lambda-events/ec2-running.json
```
