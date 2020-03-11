SHELL = /usr/bin/env bash -xeuo pipefail

stack_name:=fukuoka-de-longi-bot-cloud
template_path:=dist/packaged.yml

isort:
	poetry run isort -rc src tests

black:
	poetry run black src tests

format: isort black

lint:
	poetry run flake8 src tests

update-submodule:
	git submodule foreach git pull origin master

test-unit:
	@for test_dir in $$(find tests/unit -type d -name test_unit); do \
		handler=src/$$(echo $$test_dir | sed -e "s/^tests\/unit\///" -e "s/\/test_unit//"); \
		PYTHONPATH=submodules/fukuoka-de-longi-bot-layer/src/logger/python:$$handler \
		AWS_DEFAULT_REGION=ap-northeast-1 \
		AWS_ACCESS_KEY_ID=dummy \
		AWS_SECRET_ACCESS_KEY=dummy \
			poetry run pytest -c setup.cfg --cov=$$handler $$test_dir; \
	done

package:
	rm -rf dist/
	mkdir dist/
	poetry run sam package --s3-bucket $$SAM_ARTIFACT_BUCKET --output-template-file $(template_path) --template-file template.yml

deploy: package
	poetry run sam deploy \
		--stack-name $(stack_name) \
		--template-file $(template_path) \
		--capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
		--role-arn $$CLOUDFORMATION_DEPLOY_ROLE_ARN \
		--no-fail-on-empty-changeset
	poetry run aws cloudformation describe-stacks \
		--stack-name $(stack_name) \
		--query Stacks[0].Outputs

localstack-up:
	docker rm -f localstack
	docker-compose up -d

localstack-stop:
	docker-compose stop

localstack-down:
	docker-compose down