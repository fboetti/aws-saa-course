# Lab — Network ACLs

Hands-on lab for the [NACL notes](../../nacl/README.md). Everything is done with the AWS CLI
from bash.

## Step 1 — Create a VPC with 1 AZ, 1 public subnet, 0 private subnets, no VPC endpoints

This is the CLI equivalent of the console wizard **VPC and more** with:

| Wizard option | Value |
|---|---|
| Number of Availability Zones | **1** |
| Public subnets | 1 |
| Private subnets | **0** |
| NAT gateways | None |
| VPC endpoints | **None** |

Cost: a VPC, subnet, route table, IGW and NACL are free. Nothing in this step creates a
NAT gateway, endpoint or instance.

### 1.1 Variables

```bash
export AWS_REGION=us-east-1          # change if needed
export AWS_DEFAULT_REGION=$AWS_REGION
export AZ=${AWS_REGION}a             # the single AZ
export VPC_CIDR=10.0.0.0/16
export SUBNET_CIDR=10.0.1.0/24
```

### 1.2 Create the VPC

```bash
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block $VPC_CIDR \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=my-nacl-lab-vpc-fboetti}]' \
  --query 'Vpc.VpcId' --output text)
echo $VPC_ID

# Instances get DNS hostnames (off by default in a custom VPC)
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames '{"Value":true}'
```

### Create the NACL

aws ec2 create-network-acl --vpc-id $VPC_ID

### 1.5 Verify

```bash
# One subnet, in one AZ
aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC_ID \
  --query 'Subnets[].{Id:SubnetId,Cidr:CidrBlock,AZ:AvailabilityZone,PublicIP:MapPublicIpOnLaunch}' \
  --output table

# Default route goes to the IGW
aws ec2 describe-route-tables --route-table-ids $RTB_ID \
  --query 'RouteTables[0].Routes' --output table

# No VPC endpoints (expect an empty list)
aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=$VPC_ID \
  --query 'VpcEndpoints[].VpcEndpointId'

# The default NACL created with the VPC (allow all) already covers the subnet
aws ec2 describe-network-acls --filters Name=vpc-id,Values=$VPC_ID \
  --query 'NetworkAcls[].{Id:NetworkAclId,Default:IsDefault,Subnets:Associations[].SubnetId}' \
  --output table
```

Expected: 1 subnet in `$AZ` with `PublicIP: True`, a `0.0.0.0/0 → igw-…` route, an empty
endpoint list, and the default NACL associated with the subnet.

### 1.6 Save the IDs for the next steps

```bash
cat > ~/nacl-lab.env <<EOF
export AWS_REGION=$AWS_REGION
export VPC_ID=$VPC_ID
export SUBNET_ID=$SUBNET_ID
export IGW_ID=$IGW_ID
export RTB_ID=$RTB_ID
EOF
# later: source ~/nacl-lab.env
```

## Clean up (when the whole lab is finished)

```bash
source ~/nacl-lab.env
aws ec2 disassociate-route-table --association-id $(aws ec2 describe-route-tables \
  --route-table-ids $RTB_ID \
  --query 'RouteTables[0].Associations[?SubnetId==`'$SUBNET_ID'`].RouteTableAssociationId' --output text)
aws ec2 delete-route-table --route-table-id $RTB_ID
aws ec2 detach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID
aws ec2 delete-subnet --subnet-id $SUBNET_ID
aws ec2 delete-vpc --vpc-id $VPC_ID      # default NACL and default SG go with it
```
