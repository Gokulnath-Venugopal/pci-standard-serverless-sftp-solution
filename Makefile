SHELL := /bin/bash -e
CODE := "pssit"
ENVIRONMENT := "dev"
STACK := "cfn-serverless-sftp"

.PHONY: all test env-vars \
		test-validate-shell test-validate-cfn

#test: test-cfn-lint-yaml test-validate-shell test-validate-cfn
test: test-validate-cfn


test-lint-yaml:
	@echo "--- Test Lint YAML"
	@docker-compose run --rm yamllint .

test-cfn-lint-yaml:
	@echo "--- Test CFN Lint YAML"
	@docker-compose run --rm cfnlint cfn-lint -t cloudformation/**/template.yml

test-validate-shell:
	@echo "--- Test Validate Shell Scripts"
	@docker-compose run --rm shellcheck scripts/validate_shell_scripts.sh

test-validate-cfn:
	@echo "--- Test Validate CloudFormation"
	@docker-compose run --rm awscli scripts/validate_cloudformation.sh

shell-in:
	@docker pull realestate/shush:latest
	@docker-compose run -T --rm shush encrypt shush $(CODE)

deploy: env-vars
	@echo "--- Deploy $(STACK) cloudformation stack"
	@docker-compose run --rm stackup $(STACK) up \
		--template cloudformation/network/template.yml \
		--parameters cloudformation/network/parameters/$(ENVIRONMENT).yml
	@echo "--- Deploy SAM components of $(STACK) stack"
	@docker-compose run --rm samcli sam validate --template-file cloudformation/sam/template.yml --lint
	@docker-compose run --rm samcli sam package --template-file cloudformation/sam/template.yml --output-template-file package.yml \
		--s3-bucket $$( aws cloudformation list-stack-resources --stack-name $(STACK) --query 'StackResourceSummaries[?LogicalResourceId==`SAMdeploymentS3Bucket`].PhysicalResourceId' --output text )
	@docker-compose run --rm samcli sam deploy --template-file package.yml --stack-name sam-$(STACK) --capabilities CAPABILITY_IAM --no-fail-on-empty-changeset
	
all: test deploy

env-vars:
ifndef AWS_DEFAULT_REGION
	$(error AWS_DEFAULT_REGION is undefined)
endif
