from pathlib import Path

import yaml
from ops import pebble, testing

from charm import VerdaccioK8SCharm
from workload import CONFIG_PATH, SERVICE_NAME


def test_log_level_change_restarts_service(tmp_path: Path) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    config_dir = tmp_path / "conf"
    config_dir.mkdir()
    container = testing.Container(
        "verdaccio",
        can_connect=True,
        mounts={"config": testing.Mount(location="/verdaccio/conf", source=config_dir)},
    )
    initial = ctx.run(ctx.on.pebble_ready(container), testing.State(containers={container}))

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config={"log-config": "type: stdout\nformat: pretty\nlevel: debug\n"},
            containers=initial.containers,
            opened_ports=initial.opened_ports,
        ),
    )

    workload = output.get_container("verdaccio")
    config = (workload.get_filesystem(ctx) / CONFIG_PATH.lstrip("/")).read_text()
    assert "level: debug" in config
    assert workload.service_statuses[SERVICE_NAME] is pebble.ServiceStatus.ACTIVE
    assert output.unit_status == testing.ActiveStatus()


def test_listener_configuration_updates_service_and_port() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = testing.Container("verdaccio", can_connect=True)

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config={
                "https-config": "pfx: /verdaccio/storage/server.pfx\n",
                "listen-protocol": "https",
                "listen-address": "::",
                "listen-port": 8080,
            },
            containers={container},
        ),
    )

    service = output.get_container("verdaccio").plan.services[SERVICE_NAME]
    assert service.command.endswith("--listen https://[::]:8080")
    assert output.opened_ports == {testing.TCPPort(8080)}


def test_blank_uplinks_and_packages_clear_sections() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = testing.Container("verdaccio", can_connect=True)

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config={"uplinks-config": "", "packages-config": ""}, containers={container}
        ),
    )

    workload = output.get_container("verdaccio")
    rendered = yaml.safe_load((workload.get_filesystem(ctx) / CONFIG_PATH.lstrip("/")).read_text())
    assert "uplinks" not in rendered
    assert "packages" not in rendered
    assert output.unit_status == testing.ActiveStatus()


def test_store_plugin_can_replace_storage_path() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = testing.Container("verdaccio", can_connect=True)

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config={"storage-path": "", "store-config": "memory:\n  limit: 1000\n"},
            containers={container},
        ),
    )

    workload = output.get_container("verdaccio")
    rendered = yaml.safe_load((workload.get_filesystem(ctx) / CONFIG_PATH.lstrip("/")).read_text())
    assert "storage" not in rendered
    assert rendered["store"] == {"memory": {"limit": 1000}}
    assert output.unit_status == testing.ActiveStatus()


def test_numeric_uplink_intervals_and_boolean_trust_proxy_are_rendered() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = testing.Container("verdaccio", can_connect=True)

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config={
                "uplinks-config": (
                    "npmjs:\n"
                    "  url: https://registry.npmjs.org/\n"
                    "  timeout: 30000\n"
                    "  maxage: 2.5\n"
                    "  fail_timeout: 5\n"
                ),
                "server-config": "trustProxy: true\n",
            },
            containers={container},
        ),
    )

    workload = output.get_container("verdaccio")
    rendered = yaml.safe_load((workload.get_filesystem(ctx) / CONFIG_PATH.lstrip("/")).read_text())
    assert rendered["uplinks"]["npmjs"]["timeout"] == 30000
    assert rendered["uplinks"]["npmjs"]["maxage"] == 2.5
    assert rendered["uplinks"]["npmjs"]["fail_timeout"] == 5
    assert rendered["server"]["trustProxy"] is True
    assert output.unit_status == testing.ActiveStatus()


def test_trailing_dot_fqdn_is_accepted() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = testing.Container("verdaccio", can_connect=True)

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(config={"listen-address": "registry.example.test."}, containers={container}),
    )

    service = output.get_container("verdaccio").plan.services[SERVICE_NAME]
    assert service.command.endswith("--listen http://registry.example.test.:4873")
    assert output.unit_status == testing.ActiveStatus()


def test_complete_verdaccio_configuration_is_rendered(tmp_path: Path) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    config_dir = tmp_path / "conf"
    config_dir.mkdir()
    container = testing.Container(
        "verdaccio",
        can_connect=True,
        mounts={"config": testing.Mount(location="/verdaccio/conf", source=config_dir)},
    )
    source = """storage: /verdaccio/storage/data
plugins: /verdaccio/plugins
web:
  title: Private registry
  logo: /verdaccio/storage/logo.svg
  logoDark: /verdaccio/storage/logo-dark.svg
  favicon: /verdaccio/storage/favicon.ico
  gravatar: false
  sort_packages: desc
  darkMode: true
  url_prefix: /packages
  language: en-US
  login: true
  scope: '@example'
  pkgManagers: [npm, pnpm]
  showInfo: false
  showSettings: true
  showSearch: true
  showFooter: false
  showThemeSwitch: true
  showDownloadTarball: false
  showUplinks: true
  hideDeprecatedVersions: true
  primaryColor: '#123456'
  showRaw: false
  scriptsHead: ['<script src="/head.js"></script>']
  scriptsBodyAfter: ['<script src="/after.js"></script>']
  scriptsBodyBefore: ['<div>before</div>']
  metaScripts: ['<meta name="robots" content="noindex">']
  bodyBefore: ['<main>']
  bodyAfter: ['</main>']
  rateLimit: {windowMs: 1000, max: 50}
  html_cache: true
  enabled: true
auth:
  htpasswd:
    file: /verdaccio/storage/htpasswd
    max_users: 100
    algorithm: bcrypt
    rounds: 12
    slow_verify_ms: 200
  company-auth:
    endpoint: https://auth.example.test
uplinks:
  npmjs:
    url: https://registry.npmjs.org/
    ca: certificate
    cache: true
    timeout: 30s
    maxage: 2m
    max_fails: 3
    fail_timeout: 5m
    http_proxy: http://proxy.example.test
    https_proxy: https://proxy.example.test
    no_proxy: localhost,127.0.0.1
    headers: {X-Registry: primary}
    auth: {type: bearer, token: secret-token, token_env: false}
    strict_ssl: true
    agent_options: {keepAlive: true}
packages:
  '@example/*':
    storage: private
    access: team
    publish: maintainers
    unpublish: admins
    proxy: npmjs
server:
  rateLimit: {windowMs: 2000, max: 100}
  keepAliveTimeout: 30
  legacyAuthCache: {enabled: true, maxEntries: 500, ttlMs: 15000}
  pluginPrefix: company
  passwordValidationRegex: '/.{10}$/'
  trustProxy: 1
  searchRemote: true
publish:
  allow_offline: true
  keep_readmes: tagged
  check_owners: true
url_prefix: /registry
security:
  web:
    sign: {expiresIn: 1h}
    verify: {algorithms: [HS256]}
  api:
    legacy: false
    migrateToSecureLegacySignature: true
    jwt:
      sign: {expiresIn: 7d}
      verify: {}
userRateLimit: {windowMs: 50000, max: 1000}
max_body_size: 20mb
https:
  key: /verdaccio/storage/tls.key
  cert: /verdaccio/storage/tls.crt
  ca: /verdaccio/storage/ca.crt
user_agent: false
http_proxy: http://proxy.example.test
https_proxy: https://proxy.example.test
no_proxy: localhost,127.0.0.1
store:
  memory: {limit: 1000}
notifications:
  endpoint: https://hooks.example.test/packages
  content: 'published {{ name }}'
  packagePattern: '^@example/'
  packagePatternFlags: i
  method: POST
  headers: {Authorization: token}
notify:
  - endpoint: https://hooks.example.test/audit
    content: '{{ name }}'
    method: PUT
middlewares:
  audit: {enabled: true, strict_ssl: true, timeout: 1000}
filters:
  '@verdaccio/package-filter':
    minAgeDays: 7
    block: [{scope: '@untrusted'}]
    allow: [{scope: '@example'}]
log:
  type: file
  format: json
  path: /verdaccio/storage/verdaccio.log
  level: trace
  colors: false
  sync: true
  redact:
    paths: [req.header.authorization]
    censor: redacted
    remove: false
flags:
  searchRemote: true
  changePassword: true
  createUser: true
  webLogin: true
i18n: {web: en-US}
"""

    expected = yaml.safe_load(source)
    section_options = {
        "web": "web-config",
        "auth": "auth-config",
        "uplinks": "uplinks-config",
        "packages": "packages-config",
        "server": "server-config",
        "publish": "publish-config",
        "security": "security-config",
        "userRateLimit": "user-rate-limit-config",
        "https": "https-config",
        "store": "store-config",
        "notifications": "notifications-config",
        "notify": "notify-config",
        "middlewares": "middlewares-config",
        "filters": "filters-config",
        "log": "log-config",
        "flags": "flags-config",
        "i18n": "i18n-config",
    }
    config = {
        option: yaml.safe_dump(expected[key], sort_keys=False)
        for key, option in section_options.items()
    }
    config.update(
        {
            "storage-path": expected["storage"],
            "plugins-path": expected["plugins"],
            "url-prefix": expected["url_prefix"],
            "max-body-size": expected["max_body_size"],
            "user-agent": "false",
            "http-proxy": expected["http_proxy"],
            "https-proxy": expected["https_proxy"],
            "no-proxy": expected["no_proxy"],
        }
    )

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(config=config, containers={container}),
    )

    rendered = (config_dir / "config.yaml").read_text()
    assert yaml.safe_load(rendered) == expected
    assert output.unit_status == testing.ActiveStatus()


def test_pfx_passphrase_is_serialized_to_workload() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = testing.Container("verdaccio", can_connect=True)
    source = "pfx: /verdaccio/storage/server.pfx\npassphrase: secret\n"

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(config={"https-config": source}, containers={container}),
    )

    workload = output.get_container("verdaccio")
    rendered = (workload.get_filesystem(ctx) / CONFIG_PATH.lstrip("/")).read_text()
    assert yaml.safe_load(rendered)["https"] == yaml.safe_load(source)
