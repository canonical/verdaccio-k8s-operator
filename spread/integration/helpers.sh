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

read_verdaccio_pid() {
  sudo -H -u ubuntu juju ssh \
    --model "${MODEL}" \
    --container verdaccio \
    verdaccio-k8s/0 \
    'for process in /proc/[0-9]*; do command="$(tr "\0" " " < "${process}/cmdline" 2>/dev/null || true)"; case "${command}" in *"verdaccio --config /verdaccio/conf/config.yaml"*) printf "%s\n" "${process##*/}"; exit 0 ;; esac; done; exit 1'
}

read_charm_revision() {
  sudo -H -u ubuntu juju status \
    --model "${MODEL}" \
    --format json |
    python3 -c 'import json, sys; print(json.load(sys.stdin)["applications"]["verdaccio-k8s"]["charm-rev"])'
}

read_pod_uid() {
  sudo -H -u workshop kubectl \
    --namespace "${MODEL}" \
    get pod verdaccio-k8s-0 \
    --output=jsonpath='{.metadata.uid}'
}

deploy_ingress() {
  routing_mode="${1}"
  sudo -H -u ubuntu juju deploy \
    --model "${MODEL}" \
    traefik-k8s \
    --channel latest/stable \
    --trust \
    --config external_hostname=traefik.local \
    --config "routing_mode=${routing_mode}"
  sudo -H -u ubuntu env JUJU_MODEL="${MODEL}" juju wait-for \
    application traefik-k8s \
    --query='status=="active"' \
    --timeout 10m
  sudo -H -u ubuntu juju integrate \
    --model "${MODEL}" \
    verdaccio-k8s:ingress \
    traefik-k8s:ingress
}

deploy_loki() {
  sudo -H -u ubuntu juju deploy \
    --model "${MODEL}" \
    loki-k8s \
    --channel 2/stable \
    --trust
  sudo -H -u ubuntu env JUJU_MODEL="${MODEL}" juju wait-for \
    application loki-k8s \
    --query='status=="active"' \
    --timeout 10m
  sudo -H -u ubuntu juju integrate \
    --model "${MODEL}" \
    verdaccio-k8s:logging \
    loki-k8s:logging
}

deploy_prometheus() {
  sudo -H -u ubuntu juju deploy \
    --model "${MODEL}" \
    prometheus-k8s \
    --channel 2/stable \
    --trust
  sudo -H -u ubuntu env JUJU_MODEL="${MODEL}" juju wait-for \
    application prometheus-k8s \
    --query='status=="active"' \
    --timeout 10m
  sudo -H -u ubuntu juju integrate \
    --model "${MODEL}" \
    verdaccio-k8s:metrics-endpoint \
    prometheus-k8s:metrics-endpoint
}

deploy_tempo() {
  sudo -H -u ubuntu juju deploy \
    --model "${MODEL}" \
    tempo-k8s \
    --channel latest/beta \
    --trust
  sudo -H -u ubuntu env JUJU_MODEL="${MODEL}" juju wait-for \
    application tempo-k8s \
    --query='status=="active"' \
    --timeout 10m
  sudo -H -u ubuntu juju integrate \
    --model "${MODEL}" \
    verdaccio-k8s:tracing \
    tempo-k8s:tracing
}

read_plan() {
  sudo -H -u ubuntu juju ssh \
    --model "${MODEL}" \
    --container verdaccio \
    verdaccio-k8s/0 \
    /charm/bin/pebble plan
}

read_checks() {
  sudo -H -u ubuntu juju ssh \
    --model "${MODEL}" \
    --container verdaccio \
    verdaccio-k8s/0 \
    /charm/bin/pebble checks
}

read_ingress_relation() {
  sudo -H -u ubuntu juju show-unit \
    --model "${MODEL}" \
    traefik-k8s/0 \
    --format yaml
}

fetch_ingress() {
  host="${1}"
  path="${2}"
  sudo -H -u ubuntu juju ssh \
    --model "${MODEL}" \
    --container verdaccio \
    verdaccio-k8s/0 \
    wget -qO- \
    --header="Host:${host}" \
    "http://traefik-k8s-lb.${MODEL}.svc.cluster.local${path}"
}

fetch_registry() {
  port="${1}"
  path="${2}"
  sudo -H -u ubuntu juju ssh \
    --model "${MODEL}" \
    --container verdaccio \
    verdaccio-k8s/0 \
    wget -qO- "http://127.0.0.1:${port}${path}"
}

read_metrics() {
  fetch_registry 9464 /metrics
}

query_prometheus() {
  sudo -H -u ubuntu juju ssh \
    --model "${MODEL}" \
    --container verdaccio \
    verdaccio-k8s/0 \
    wget -qO- \
    "http://prometheus-k8s.${MODEL}.svc.cluster.local:9090/api/v1/query?query=verdaccio_http_requests_total%7Bjuju_application%3D%22verdaccio-k8s%22%7D"
}

query_tempo_traces() {
  sudo -H -u ubuntu juju ssh \
    --model "${MODEL}" \
    --container verdaccio \
    verdaccio-k8s/0 \
    wget -qO- \
    "http://tempo-k8s.${MODEL}.svc.cluster.local:3200/api/search?tags=service.name%3Dverdaccio-k8s"
}

query_loki() {
  sudo -H -u ubuntu juju ssh \
    --model "${MODEL}" \
    --container verdaccio \
    verdaccio-k8s/0 \
    wget -qO- \
    "http://loki-k8s.${MODEL}.svc.cluster.local:3100/loki/api/v1/query_range?query=%7Bjuju_application%3D%22verdaccio-k8s%22%7D&limit=20"
}

publish_package() {
  create_user_script=$(cat <<'EOF'
const payload = {
  name: "spread-user",
  password: "spread-password",
  email: "spread@example.test",
  type: "user",
  roles: [],
};
(async () => {
  let lastError;
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      const response = await fetch(
        "http://verdaccio-k8s:4873/-/user/org.couchdb.user:spread-user",
        {
          method: "PUT",
          headers: {"content-type": "application/json"},
          body: JSON.stringify(payload),
        },
      );
      const body = await response.json();
      if (!response.ok || !body.token) {
        throw new Error(`user creation failed: ${response.status}`);
      }
      console.log(body.token);
      return;
    } catch (error) {
      lastError = error;
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }
  throw lastError;
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
EOF
  )
  sudo -H -u workshop kubectl \
    --namespace "${MODEL}" \
    run npm-publisher \
    --image=node:24-bookworm-slim \
    --restart=Never \
    --attach \
    --rm \
    --quiet \
    --env="CREATE_USER_SCRIPT=${create_user_script}" \
    --command -- \
    sh -euxc '
      mkdir /tmp/package
      cd /tmp/package
      printf "%s\n" \
        "{\"name\":\"spread-published-package\",\"version\":\"1.0.0\"}" \
        > package.json
      printf "%s\n" "published by Spread" > README.md
      token="$(node -e "${CREATE_USER_SCRIPT}")"
      npm config set //verdaccio-k8s:4873/:_authToken "${token}"
      npm config set email spread@example.test
      npm publish --registry=http://verdaccio-k8s:4873
      test "$(npm view spread-published-package version --registry=http://verdaccio-k8s:4873)" = 1.0.0
    '
}

verify_published_package() {
  verify_package_script=$(cat <<'EOF'
(async () => {
  const response = await fetch(
    "http://verdaccio-k8s:4873/spread-published-package",
  );
  const metadata = await response.json();
  if (!response.ok || !metadata.versions?.["1.0.0"]) {
    throw new Error(`published package unavailable: ${response.status}`);
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
EOF
  )
  sudo -H -u workshop kubectl \
    --namespace "${MODEL}" \
    run registry-verifier \
    --image=node:24-bookworm-slim \
    --restart=Never \
    --attach \
    --rm \
    --quiet \
    --command -- \
    node -e "${verify_package_script}"
}
