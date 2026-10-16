#!/usr/bin/env bash

set -euo pipefail

# Simple AWS CLI smoke test used in the SAA course.
echo "Caller identity:"
aws sts get-caller-identity

echo
echo "Regions:"
aws ec2 describe-regions --query 'Regions[].RegionName' --output table
