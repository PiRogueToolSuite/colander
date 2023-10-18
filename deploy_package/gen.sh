#!/bin/bash

ENV_TPL_FILES=./.envs/.tpl/
ENV_OUT_DIR=./.envs/.production/

mkdir -p $ENV_OUT_DIR

source $ENV_TPL_FILES/.base

for f in `find $ENV_TPL_FILES -type f`
do
  filename=$(basename $f)
  eval "cat <<EOF
$(<$f)
EOF" > $ENV_OUT_DIR/$filename
  source $ENV_OUT_DIR/$filename
done

eval "cat <<EOF
$(<./compose/production/traefik/traefik.yml.tpl)
EOF" > ./compose/production/traefik/traefik.yml
