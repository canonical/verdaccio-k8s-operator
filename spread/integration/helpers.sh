read_config() {
  sudo -H -u ubuntu juju ssh \
    --model "${MODEL}" \
    --container verdaccio \
    verdaccio-k8s/0 \
    cat /verdaccio/conf/config.yaml
}

ping_registry() {
  sudo -H -u ubuntu juju ssh \
    --model "${MODEL}" \
    --container verdaccio \
    verdaccio-k8s/0 \
    wget -qO- "http://127.0.0.1:${1}/-/ping"
}
