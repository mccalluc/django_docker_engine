#!/usr/bin/env bash
set -o errexit

start() { echo travis_fold':'start:$1; echo $1; }
end() { echo travis_fold':'end:$1; }
die() { set +v; echo "$*" 1>&2 ; sleep 1; exit 1; }
# Race condition truncates logs on Travis: "sleep" might help.
# https://github.com/travis-ci/travis-ci/issues/6018

ping -c1 container-name.docker.localhost > /dev/null  # Prereq for hostname-based dispatch.
docker info | grep 'Operating System'  # Are we able to connect to Docker, and what OS is it?

start test
# Travis logs were truncated, so always use "die" to avoid race condition.
coverage run manage.py test --verbosity=2 \
  && coverage report --include=django_docker_engine/* --skip-covered --show-missing --fail-under 30 \
  || die
end test

start doctest
# Add "--append" if you want to have a single coverage.
coverage run -m doctest *.md \
  && coverage report --include=django_docker_engine/* --skip-covered --show-missing --fail-under 60 \
  || die
end doctest

start docker
docker system df
# TODO: Make assertions about the disk usage we would expect to see.
end docker

start format
flake8 --exclude build . || die "Run 'autopep8 --in-place -r .'"
end format

start isort
isort --recursive . --verbose --check-only || die "See ERRORs: Run 'isort --recursive .'"
end isort

start wheel
python setup.py sdist bdist_wheel
end wheel