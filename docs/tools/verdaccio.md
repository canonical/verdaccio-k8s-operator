### Install and run local package

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Commands to install the locally published package and start the Verdaccio server.

```shell
npm i -g verdaccio --registry=http://localhost:4873
verdaccio
```

--------------------------------

### Start SSL deployment

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/reverse_proxy/nginx/relative_path/README.md

Builds and starts the containers using the SSL-enabled configuration.

```bash
docker compose -f docker-compose_ssl.yml up --build --force-recreate
```

--------------------------------

### Setup Plugin Development Environment

Source: https://github.com/verdaccio/verdaccio/blob/master/README.md

Commands to install Yeoman and the Verdaccio plugin generator for creating custom plugins.

```bash
npm install -g yo
npm install -g generator-verdaccio-plugin
```

--------------------------------

### Install @verdaccio/ui-components

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/ui-components/README.md

Install the ui-components package as a development dependency.

```bash
npm i -D @verdaccio/ui-components@7-next
```

--------------------------------

### Install dependencies

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Install all project dependencies using pnpm.

```shell
pnpm install
```

--------------------------------

### Start HTTP deployment

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/reverse_proxy/nginx/relative_path/README.md

Builds and starts the containers for the HTTP-based Verdaccio instances.

```bash
docker compose up --build --force-recreate
```

--------------------------------

### Full Package Filter Configuration Example

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/package-filter/README.md

A comprehensive example demonstrating 'minAgeDays', 'dateThreshold', 'block' rules with version constraints and strategies, and 'allow' rules for exceptions.

```yaml
filters:
  '@verdaccio/package-filter':
    minAgeDays: 7
    dateThreshold: '2025-01-01'
    block:
      - scope: '@malicious'
      - package: 'typosquat-pkg'
      - package: 'compromised-lib'
        versions: '>=3.0.0'
      - package: 'legacy-lib'
        versions: '>=2.0.0'
        strategy: replace
    allow:
      - scope: '@my-org'
      - package: 'compromised-lib'
        versions: '3.0.1'
```

--------------------------------

### Install @verdaccio/plugin-verifier

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

Install the plugin verifier as a development dependency.

```bash
npm install --save-dev @verdaccio/plugin-verifier
```

--------------------------------

### Configure local hosts file

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/reverse_proxy/https-portal/README.md

Map the example domain to localhost for local testing.

```text
127.0.0.1       localhost
127.0.0.1       example.com
```

--------------------------------

### Start the Apache reverse proxy environment

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/reverse_proxy/apache/README.md

Builds and starts the containers in detached mode.

```bash
docker compose up -d --build
```

--------------------------------

### Run Verdaccio Programmatically

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/verdaccio/README.md

Starts a Verdaccio server programmatically using its API. This example demonstrates building a configuration with storage, uplinks, package access, authentication, and logging.

```typescript
import { runServer } from 'verdaccio';

import { ConfigBuilder } from '@verdaccio/config';

const config = ConfigBuilder.build()
  .addStorage('./storage')
  .addUplink('npmjs', { url: 'https://registry.npmjs.org/' })
  .addPackageAccess('**', { access: '$all', publish: '$authenticated', proxy: 'npmjs' })
  .addAuth({ htpasswd: { file: './htpasswd' } })
  .addLogger({ level: 'info', type: 'stdout', format: 'pretty' })
  .getConfig();

const app = await runServer(config);
app.listen(4873, () => {
  console.log('Verdaccio is running on http://localhost:4873');
});
```

--------------------------------

### Changeset summary input prompt

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Example output showing the summary input phase of the changeset creation process.

```text
🦋  Which packages would you like to include? · @verdaccio/config
🦋  Which packages should have a major bump? · No items were selected
🦋  Which packages should have a minor bump? · No items were selected
🦋  The following packages will be patch bumped:
🦋  @verdaccio/config@5.0.0-alpha.0
🦋  Please enter a summary for this change (this will be in the changelogs). Submit empty line to open external editor
🦋  Summary ›
```

--------------------------------

### Start Root Path Deployment

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/reverse_proxy/nginx/README.md

Commands to navigate to the root path directory and launch the services.

```bash
cd root_path
docker compose up -d --build
```

--------------------------------

### Changeset package selection output

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Example output showing the selection of packages for a changeset.

```text
🦋  Which packages would you like to include? …
✔ changed packages
 changed packages
  ✔ @verdaccio/api
  ✔ @verdaccio/auth
  ✔ @verdaccio/cli
  ✔ @verdaccio/config
  ✔ @verdaccio/commons-api
```

--------------------------------

### Install verdaccio-htpasswd Plugin

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/htpasswd/README.md

Install the verdaccio-htpasswd plugin globally using npm.

```bash
$ npm install -g verdaccio-htpasswd
```

--------------------------------

### Initialize development environment

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Commands to install the required Node.js version and enable corepack for pnpm management.

```shell
nvm install
corepack enable
```

--------------------------------

### Start Verdaccio Server

Source: https://github.com/verdaccio/verdaccio/blob/master/README.md

Execute this command in the terminal to launch the Verdaccio server instance.

```bash
verdaccio
```

--------------------------------

### Install verdaccio-audit Plugin

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/audit/README.md

Install the verdaccio-audit plugin globally using npm.

```bash
npm install --global verdaccio-audit
```

--------------------------------

### Start Verdaccio 5.x with Babel-Node

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Starts the Verdaccio development server using babel-node for transpilation.

```bash
yarn start
```

--------------------------------

### Install Local Storage Plugin

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/local-storage/README.md

Install the @verdaccio/local-storage package using npm. This plugin is built-in with Verdaccio.

```bash
npm install @verdaccio/local-storage
```

--------------------------------

### Basic Unit Test Structure (Jest)

Source: https://github.com/verdaccio/verdaccio/wiki/Developing-new-tests

Example of a basic unit test structure using Jest. It includes setup and teardown hooks and a simple test case.

```javascript
const verdaccio = require('../../src/api/index');
const config = require('./partials/config');

describe('basic system test', () => {

  beforeAll(function(done) {
    // something important
  });

  afterAll((done) => {
    // undo something important
  });

  test('server should respond on /', done => {
    // your test
    done();
  });
});
```

--------------------------------

### Multi-stage Dockerfile for plugin installation

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/plugins/docker-build-install-plugin/README.md

Uses a builder stage to install the plugin and copies it into the final Verdaccio image with appropriate permissions.

```dockerfile
# Docker multi-stage build - https://docs.docker.com/develop/develop-images/multistage-build/
# Use an alpine node image to install the plugin
FROM node:lts-alpine as builder

RUN mkdir -p /verdaccio/plugins \
  && cd /verdaccio/plugins \
  && npm install --global-style --no-bin-links --omit=optional verdaccio-auth-memory@next-7

FROM verdaccio/verdaccio:7.x-next

# copy your modified config.yaml into the image
ADD docker.yaml /verdaccio/conf/config.yaml

COPY --chown=$VERDACCIO_USER_UID:root --from=builder \
  /verdaccio/plugins/node_modules/verdaccio-auth-memory \
  /verdaccio/plugins/verdaccio-auth-memory
```

--------------------------------

### Install Verdaccio and Auth Memory Plugin

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/auth-memory/README.md

Install Verdaccio and the auth-memory plugin globally using npm.

```sh
npm install -g verdaccio
npm install -g verdaccio-auth-memory
```

--------------------------------

### Start Verdaccio with Docker Compose

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/docker-local-storage-volume/README.md

Initializes the Verdaccio container with local volume mounts for configuration and storage.

```bash
docker compose up
```

--------------------------------

### Install Verdaccio Globally

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Installs the latest version of Verdaccio globally using npm.

```bash
npm install -g verdaccio@latest
```

--------------------------------

### Install Verdaccio via Helm

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/kubernetes/helm/README.md

Add the official Verdaccio repository and install the chart using the provided values.yaml file.

```bash
# 1. Add the Verdaccio chart repository
helm repo add verdaccio https://charts.verdaccio.org
helm repo update

# 2. Install the chart with the values from this example
helm install my-registry verdaccio/verdaccio -f values.yaml
```

--------------------------------

### Changeset confirmation output

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Example output confirming the successful creation of a changeset file.

```text
🦋  Is this your desired changeset? (Y/n) · true
🦋  Changeset added! - you can now commit it
🦋
🦋  If you want to modify or expand on the changeset summary, you can find it here
🦋  info /Users/user/verdaccio.clone/.changeset/light-scissors-smell.md
```

--------------------------------

### Install Verdaccio 9.x (Experimental)

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/verdaccio/README.md

Installs the experimental Verdaccio 9.x pre-release version using npm. This version is not recommended for production and may have breaking changes.

```bash
npm install verdaccio@next-9
```

--------------------------------

### Locate Verdaccio Installation

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Finds the installation path of the globally installed Verdaccio executable.

```bash
which verdaccio
/home/xxxx/.nvm/versions/node/v14.17.4/bin/verdaccio
```

--------------------------------

### Start Verdaccio 5.x with Debug and Babel-Register

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Starts Verdaccio with debug logging enabled, using @babel/register for transpilation.

```bash
DEBUG=verdaccio* yarn start:debug
```

--------------------------------

### Install Dependencies for Verdaccio 6.x

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Installs project dependencies for Verdaccio version 6.x using pnpm.

```bash
pnpm install
```

--------------------------------

### Install Verdaccio

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/memory/README.md

Ensure Verdaccio is installed globally. This is a prerequisite for using Verdaccio storage plugins.

```bash
npm install -g verdaccio
```

--------------------------------

### CI Integration: GitHub Actions example

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

Integrate plugin verification into your CI pipeline using npx to run the verifier.

```yaml
# GitHub Actions example
- name: Verify plugin
  run: npx verdaccio-plugin-verifier my-auth --category authentication --plugins-folder ./build
```

--------------------------------

### Install Verdaccio via Package Managers

Source: https://github.com/verdaccio/verdaccio/blob/master/README.md

Commands to install the next-9 version of Verdaccio globally using common Node.js package managers.

```bash
npm install -g verdaccio@next-9
```

```bash
yarn global add verdaccio@next-9
```

```bash
pnpm i -g verdaccio@next-9
```

--------------------------------

### Initialize ConfigBuilder with Partial Configuration

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/config/README.md

Start building a configuration by providing an initial partial configuration object to the ConfigBuilder. This allows pre-setting specific properties.

```typescript
const config = ConfigBuilder.build({ security: { api: { legacy: false } } });
```

--------------------------------

### Install Dependencies for Verdaccio 5.x

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Installs project dependencies for Verdaccio version 5.x using yarn.

```bash
yarn install
```

--------------------------------

### Manage Docker containers

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/reverse_proxy/https-portal/README.md

Commands to start, rebuild, and stop the Verdaccio and https-portal containers.

```bash
docker compose up -d --build
```

```bash
docker compose up -d --build --force-recreate
```

```bash
docker compose down
```

--------------------------------

### Require and Initialize Auth Memory Plugin

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/auth-memory/README.md

Example of how to require and initialize the verdaccio-auth-memory plugin within a Node.js environment.

```js
const plugin = require('verdaccio-auth-memory');

plugin(config, appConfig);
```

--------------------------------

### Install verdaccio-memory Plugin

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/memory/README.md

Install the verdaccio-memory plugin globally using npm. This command is used to add the plugin to your system's package manager.

```bash
npm install --global verdaccio-memory
```

--------------------------------

### Start Verdaccio for Chrome DevTools Debugging

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Run this command in your terminal to start Verdaccio in a way that allows Chrome DevTools to connect to it. Ensure you replace 'xxxx' with the correct port if it's not the default.

```bash
node --inspect-brk=xxxx server.js --config ~./config.yaml
```

--------------------------------

### Build and Run Verdaccio Server Programmatically

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/config/README.md

Use ConfigBuilder to construct a custom configuration and then run the Verdaccio server programmatically. This example demonstrates setting storage, authentication, uplinks, package access rules, web UI, middleware, logging, security settings, and internationalization.

```typescript
import { runServer } from 'verdaccio';

import { ConfigBuilder } from '@verdaccio/config';
import { constants } from '@verdaccio/core';

const config = ConfigBuilder.build()
  .addStorage('./storage')
  .addAuth({ htpasswd: { file: '.htpasswd' } })
  .addUplink('npmjs', { url: 'https://registry.npmjs.org/' })
  .addPackageAccess(constants.PACKAGE_ACCESS.SCOPE, {
    access: constants.ROLES.$AUTH,
    publish: constants.ROLES.$AUTH,
    proxy: 'npmjs',
  })
  .addPackageAccess(constants.PACKAGE_ACCESS.ALL, {
    access: constants.ROLES.$ALL,
    publish: constants.ROLES.$AUTH,
    proxy: 'npmjs',
  })
  .addWeb({ title: 'My Registry', darkMode: true })
  .addMiddlewares({ audit: { enabled: true } })
  .addLogger({ type: 'stdout', format: 'pretty', level: 'info' })
  .addSecurity({
    api: { jwt: { sign: { expiresIn: '7d' }, verify: {} }, legacy: false },
    web: { sign: { expiresIn: '1h' }, verify: {} },
  })
  .addI18n({ web: 'en-US' });

runServer(config.getConfig())
  .then((app) => {
    app.listen(4873, () => {
      console.log('verdaccio running on port 4873');
    });
  })
  .catch((err) => {
    console.error(err);
  });
```

--------------------------------

### Build and Run Verdaccio Docker with Custom Config

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Builds a Docker image with a custom config.yaml and runs it. This example shows how to use a local plugin configuration.

```dockerfile
FROM verdaccio/verdaccio:5

ADD docker.yaml /verdaccio/conf/config.yaml
```

```bash
docker build -t verdaccio/verdaccio:local .
docker run -it --rm --name verdaccio -p 4873:4873 verdaccio/verdaccio:local
```

--------------------------------

### Changeset major bump selection output

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Example output showing the selection of packages for a major version bump.

```text
🦋  Which packages should have a major bump? …
✔ all packages
  ✔ @verdaccio/config@5.0.0-alpha.0
```

--------------------------------

### Functional Test Server Interaction Example

Source: https://github.com/verdaccio/verdaccio/wiki/Developing-new-tests

Example of interacting with a Verdaccio server instance within a functional test. This snippet demonstrates making a request to add a tag to a package and checking for a 404 error.

```javascript
export default function(server) {
  // we recieve any server instance via arguments
  test('add tag - 404', () => {
    // we interact with the server instance.
    return server.addTag('testpkg-tag', 'tagtagtag', '0.0.1').status(404).body_error(/no such package/);
  });
});
```

--------------------------------

### Run Verdaccio with Inspect (Dynamic Path)

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Starts Verdaccio with the Node.js inspector enabled, dynamically locating the executable path.

```bash
node --inspect $(which verdaccio)
```

--------------------------------

### CLI: Verify npm-installed storage plugin

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

Use the CLI to verify a storage plugin installed via npm. Only the plugin name and category are required.

```bash
verdaccio-plugin-verifier my-storage --category storage
```

--------------------------------

### Enable Debug Logging for Verdaccio

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Starts Verdaccio with the DEBUG environment variable set to 'verdaccio*' for verbose logging.

```bash
DEBUG=verdaccio* node /home/xxxx/.nvm/versions/node/v14.17.4/bin/verdaccio
```

```bash
DEBUG=verdaccio* verdaccio
```

--------------------------------

### Dockerfile configuration for local plugins

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/plugins/docker-local-plugin/README.md

Dockerfile setup to copy the local plugin directory into the Verdaccio container with appropriate permissions.

```dockerfile
FROM verdaccio/verdaccio:7.x-next
USER root
COPY docker.yaml /verdaccio/conf/config.yaml
COPY --chown=$VERDACCIO_USER_UID:root \
  plugins/verdaccio-docker-dummy \
  /verdaccio/plugins/verdaccio-docker-dummy
USER $VERDACCIO_USER_UID
```

--------------------------------

### Configure htpasswd Authentication

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/htpasswd/README.md

Configure the htpasswd plugin in Verdaccio's config.yaml file. This example shows basic configuration with file path and optional settings for max users, hash algorithm, bcrypt rounds, and slow verify duration.

```yaml
auth:
    htpasswd:
        file: ./htpasswd
        # Maximum amount of users allowed to register, defaults to "+infinity".
        # You can set this to -1 to disable registration.
        #max_users: 1000
        # Hash algorithm, possible options are: "bcrypt", "md5", "sha1", "crypt".
        #algorithm: bcrypt
        # Rounds number for "bcrypt", will be ignored for other algorithms.
        # Setting this value higher will result in password verification taking longer.
        #rounds: 10
        # Log a warning if the password takes more then this duration in milliseconds to verify.
        #slow_verify_ms: 200
```

--------------------------------

### Functional Test Server Initialization

Source: https://github.com/verdaccio/verdaccio/wiki/Developing-new-tests

Example of initializing multiple Verdaccio server instances and an Express server for functional testing. This code sets up the necessary server processes before running tests.

```javascript
// we create 3 server instances
 const config1 = new VerdaccioConfig(
    './store/test-storage',
    './store/config-1.yaml',
    'http://localhost:55551/');
  const config2 = new VerdaccioConfig(
      './store/test-storage2',
      './store/config-2.yaml',
      'http://localhost:55552/');
  const config3 = new VerdaccioConfig(
        './store/test-storage3',
        './store/config-3.yaml',
        'http://localhost:55553/');
  const server1: IServerBridge = new Server(config1.domainPath);
  const server2: IServerBridge = new Server(config2.domainPath);
  const server3: IServerBridge = new Server(config3.domainPath);
  const process1: IServerProcess = new VerdaccioProcess(config1, server1, SILENCE_LOG);
  const process2: IServerProcess = new VerdaccioProcess(config2, server2, SILENCE_LOG);
  const process3: IServerProcess = new VerdaccioProcess(config3, server3, SILENCE_LOG);
  const express: any = new ExpressServer();
  ...

    // we check whether all instances has been started, since run in independent processes
    beforeAll((done) => {
      Promise.all([
        process1.init(),
        process2.init(),
        process3.init()]).then((forks) => {
          _.map(forks, (fork) => {
            processRunning.push(fork[0]);
          });
          express.start(EXPRESS_PORT).then((app) =>{
            done();
          }, (err) => {
            done(err);
          });
      }).catch((error) => {
        done(error);
      });
    });

    // after finish all, we ensure are been stoped
    afterAll(() => {
      _.map(processRunning, (fork) => {
        fork.stop();
      });
      express.server.close();
    });
```

--------------------------------

### Run Verdaccio with Node Inspector

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Starts Verdaccio with the Node.js inspector enabled to allow debugging.

```bash
node --inspect /home/xxxx/.nvm/versions/node/v14.17.4/bin/verdaccio
```

--------------------------------

### Run Verdaccio with Inspect-brk

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Starts Verdaccio with the Node.js inspector enabled, pausing execution at the first line. Useful for debugging startup issues.

```bash
node --inspect-brk /home/xxxx/.nvm/versions/node/v14.17.4/bin/verdaccio
```

--------------------------------

### Verdaccio Configuration with Memory Storage and Auth

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/memory/README.md

A complete Verdaccio configuration example showing the use of memory storage alongside htpasswd authentication. The 'store:' configuration overrides any 'storage:' fallback.

```yaml
storage: /Users/user/.local/share/verdaccio/storage
auth:
  htpasswd:
    file: ./htpasswd
store:
  memory:
    limit: 1000
```

--------------------------------

### Debug Verdaccio 6.x

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Starts Verdaccio 6.x in debug mode, typically using babel-node with inspector enabled.

```bash
pnpm debug
```

--------------------------------

### Programmatic API: Verify scoped npm-installed plugin

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

Verify a scoped plugin installed via npm using the programmatic API. The plugin path should be the full scoped name.

```typescript
// Scoped: looks for `@myorg/my-auth` as-is
const result = await verifyPlugin({
  pluginPath: '@myorg/my-auth',
  category: PLUGIN_CATEGORY.AUTHENTICATION,
});
```

--------------------------------

### Programmatic API: Verify unscoped npm-installed plugin

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

Verify an unscoped plugin installed via npm using the programmatic API. When pluginsFolder is omitted, the loader checks node_modules.

```typescript
// Unscoped: looks for `verdaccio-my-auth` in node_modules
const result = await verifyPlugin({
  pluginPath: 'my-auth',
  category: PLUGIN_CATEGORY.AUTHENTICATION,
});
```

--------------------------------

### Get Default Verdaccio Configuration

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/config/README.md

Retrieve the default configuration object for Verdaccio using the getDefaultConfig method. This provides a baseline configuration that can be further customized.

```typescript
import { getDefaultConfig } from '@verdaccio/config';

const defaultConfig = getDefaultConfig();
```

--------------------------------

### Verdaccio Memory Storage Configuration

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/memory/README.md

Configure Verdaccio to use the memory storage plugin by specifying the 'memory' store in the config.yaml file. This example sets a limit for the memory storage.

```yaml
store:
  memory:
    limit: 1000
```

--------------------------------

### Build the project

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Build all packages in the monorepo.

```shell
pnpm build
```

--------------------------------

### Initialize a changeset

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Execute this command to begin the process of adding a changeset for your changes.

```shell
pnpm changeset
```

--------------------------------

### Build and publish to local registry

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Commands to build the project and launch a temporary local registry for testing changes.

```shell
pnpm build
pnpm local:publish:release
```

--------------------------------

### Authenticate and publish with the dummy plugin

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/plugins/docker-local-plugin/README.md

Commands to test the dummy authentication plugin by logging in and publishing a package.

```bash
npm adduser --registry http://localhost:4873
```

```bash
npm publish --registry http://localhost:4873
```

--------------------------------

### Build and run the Docker image

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/plugins/docker-build-install-plugin/README.md

Commands to build the local Docker image and execute the container.

```bash
docker build -t verdaccio/verdaccio:local .
```

```bash
docker run -it --rm --name verdaccio -p 4873:4873 verdaccio/verdaccio:local
```

--------------------------------

### Publishing Packages

Source: https://github.com/verdaccio/verdaccio/blob/master/README.md

Commands for creating a user, configuring CA settings, and publishing packages to the local registry.

```bash
npm adduser --registry http://localhost:4873
```

```bash
npm set ca null
```

```bash
npm publish --registry http://localhost:4873
```

--------------------------------

### Log in using npm

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/htpasswd/README.md

Log in to your Verdaccio registry using the npm CLI with the specified registry URL.

```bash
npm adduser --registry  https://your.registry.local
```

--------------------------------

### Ruby Hello World

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/web/test/partials/readme/ascii.adoc

A simple 'Hello, World!' program written in Ruby.

```ruby
puts "Hello, World!"
```

--------------------------------

### CLI: Use custom plugin prefix

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

Use the CLI with a custom plugin prefix to resolve plugins that do not follow the default 'verdaccio-' naming convention.

```bash
verdaccio-plugin-verifier auth --category authentication --prefix mycompany
# resolves to "mycompany-auth"
```

--------------------------------

### LocalFS Constructor

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/local-storage/README.md

Instantiate the LocalFS class for handling package instances in the file system. Requires the package storage path and a logger instance.

```javascript
new LocalFS(packageStoragePath, logger);
```

--------------------------------

### CLI: Verify local auth plugin

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

Use the CLI to verify a local authentication plugin. Specify the plugin name, category, and the folder containing the plugin.

```bash
verdaccio-plugin-verifier my-auth --category authentication --plugins-folder /path/to/plugins
```

--------------------------------

### Run tests

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Execute the test suite for the project or specific packages.

```shell
pnpm test
```

```shell
cd packages/store
pnpm test
```

```shell
pnpm test test/merge.dist.tags.spec.ts
```

```shell
pnpm test test/merge.dist.tags.spec.ts -- -t 'simple'
```

```shell
pnpm test test/merge.dist.tags.spec.ts -- -t 'simple' --coverage=false
```

```shell
DEBUG=verdaccio:* pnpm test
```

--------------------------------

### Verify code quality before push

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Run these commands to ensure linting, formatting, and tests pass before submitting a pull request.

```bash
pnpm lint
pnpm format
pnpm build
pnpm test
```

--------------------------------

### Configure npm Registry

Source: https://github.com/verdaccio/verdaccio/blob/master/README.md

Set the npm registry to point to the local Verdaccio instance.

```bash
npm set registry http://localhost:4873/
```

```bash
NPM_CONFIG_REGISTRY=http://localhost:4873 npm i
```

--------------------------------

### Run Unit Tests

Source: https://github.com/verdaccio/verdaccio/wiki/Developing-new-tests

Execute unit tests using yarn.

```bash
yarn run test
```

--------------------------------

### Manage the Docker Compose environment

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/reverse_proxy/apache/README.md

Common commands for monitoring and stopping the proxy and registry services.

```bash
docker compose logs -f        # follow logs (Apache logs to stdout/stderr)
docker compose ps             # list running containers
docker compose down           # stop and remove the containers
```

--------------------------------

### CLI: Verify scoped plugin

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

Use the CLI to verify a scoped plugin. Provide the full scoped name and the plugin category.

```bash
verdaccio-plugin-verifier @myorg/my-plugin --category middleware
```

--------------------------------

### Deploy Verdaccio on Dokku

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/docker-local-storage-volume/README.md

Commands to configure and deploy a Verdaccio instance on a Dokku environment.

```bash
dokku apps:create verdaccio
docker pull verdaccio/verdaccio:7.x-next
docker tag verdaccio/verdaccio:7.x-next dokku/verdaccio:v1
mkdir -p /var/lib/dokku/data/storage/verdaccio/storage
mkdir -p /var/lib/dokku/data/storage/verdaccio/storage
dokku storage:mount verdaccio /var/lib/dokku/data/storage/verdaccio/storage:/verdaccio/storage
dokku storage:mount verdaccio /var/lib/dokku/data/storage/verdaccio/conf:/verdaccio/conf
dokku tags:deploy verdaccio v1
```

--------------------------------

### Using useVersion Hook

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/ui-components/src/providers/ManifestsProvider/README.md

Demonstrates how to consume the useVersion hook within a custom component to access package metadata, name, and version. The provider must be wrapped around the component that needs access to this information.

```jsx
function CustomComponent() {
  const { packageMeta, packageName, packageVersion } = useVersion();
  return <div />;
}

<Route path={Routes.PACKAGE}>
  <VersionProvider>
    <CustomComponent />
  </VersionProvider>
</Route>
```

--------------------------------

### Publish to registry

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/reverse_proxy/https-portal/README.md

Publish a package to the local registry via the HTTPS proxy.

```bash
npm publish --registry https://example.com
```

--------------------------------

### Basic Usage of @verdaccio/ui-components

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/ui-components/README.md

Demonstrates how to integrate Verdaccio UI components into a React application, including routing, theming, and internationalization.

```jsx
import React from 'react';
import { Route, Router, Switch } from 'react-router-dom';

import {
  Home,
  Loading,
  NotFound,
  Route as Routes,
  TranslatorProvider,
  VersionProvider,
  loadable,
} from '@verdaccio/ui-components';

// to enable webpack code splitting
const VersionPage = loadable(() => import('../pages/Version'));

const App: React.FC = () => {
  // configuration from config.yaml
  const { configOptions } = useConfig();
  const listLanguages = [{lng: 'en-US', icon: <someSVGIcon>, menuKey: 'lng.english'}];
  return (
    <AppConfigurationProvider>
      <ThemeProvider>
        <TranslatorProvider i18n={i18n} listLanguages={listLanguages} onMount={() => {}}>
          <Suspense fallback={<Loading />}>
            <Router history={history}>
              <Header HeaderInfoDialog={CustomInfoDialog} />
                <Switch>
                  <Route exact={true} path={Routes.ROOT}>
                    <Home />
                  </Route>
                  <Route exact={true} path={Routes.SCOPE_PACKAGE}>
                    <VersionProvider>
                      <VersionPage />
                    </VersionProvider>
                  </Route>
                </Switch>
            </Router>
            {configOptions.showFooter && <Footer />}
          </Suspense>
        </TranslatorProvider>
      </ThemeProvider>
    </AppConfigurationProvider>
  );
};

```

--------------------------------

### Minimal Configuration (no-op)

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/package-filter/README.md

Enables the package filter plugin without any specific rules, acting as a passthrough.

```yaml
filters:
  '@verdaccio/package-filter':
```

--------------------------------

### LocalDatabase Constructor

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/local-storage/README.md

Instantiate the LocalDatabase class, which manages a JSON database for private packages. Requires a Verdaccio configuration and logger instance.

```javascript
new LocalDatabase(config, logger);
```

--------------------------------

### Configure Whitelisting with Allow Clause

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/package-filter/README.md

Use the 'allow' clause to bypass blocking rules for specific scopes, packages, or versions. 'allow' rules take precedence over all blocking rules.

```yaml
filters:
  '@verdaccio/package-filter':
    minAgeDays: 30 # Block versions younger than 30 days
    allow:
      - scope: '@my-company-scope' # Don't block the scope that belongs to you
      - package: '@coolauthor/not-stolen' # Don't block package you really trust
      - package: semver
        versions: '7.7.3' # Don't block specific package version that you know is not malicious
```

--------------------------------

### Prepare pnpm version

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Use corepack to prepare the pnpm version defined in the package.json file.

```shell
corepack prepare
```

--------------------------------

### Access the Registry

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/kubernetes/helm/README.md

Port-forward the service to access the registry locally or configure npm to use the registry.

```bash
kubectl port-forward svc/my-registry 4873:4873
```

```bash
npm publish --registry http://localhost:4873
```

--------------------------------

### Build Verdaccio 6.x

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Builds the project for Verdaccio version 6.x, which is required before debugging.

```bash
pnpm build
```

--------------------------------

### Enable Inspect with NODE_OPTIONS in Docker

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Runs a Verdaccio Docker container with Node.js inspector enabled on specified ports.

```bash
docker run -p 4873:4873 -p 9229:9229 -e NODE_OPTIONS='--inspect-brk=0.0.0.0' verdaccio/verdaccio
```

--------------------------------

### Combine Allow and Block Rules

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/package-filter/README.md

Create fine-grained exceptions by combining 'allow' and 'block' rules. Allow rules are checked before block rules.

```yaml
filters:
  '@verdaccio/package-filter':
    block:
      - scope: '@untrusted'
    allow:
      - package: '@untrusted/but-verified'
      - package: 'some-pkg'
        versions: '2.1.0'
```

--------------------------------

### Multiple Version Ranges for a Package

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/package-filter/README.md

Blocks versions of 'some-pkg' that are greater than '2.0.0' or less than '1.3.0', effectively serving only versions in the range [1.3.0, 2.0.0].

```yaml
filters:
  '@verdaccio/package-filter':
    block:
      - package: 'some-pkg'
        versions: '>2.0.0'
      - package: 'some-pkg'
        versions: '<1.3.0'
```

--------------------------------

### Configure language menu key

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Define the menu key for the new language in the enabled languages configuration file.

```typescript
menuKey: 'lng.korean'
```

--------------------------------

### Configure Verdaccio UI Options

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/ui-theme/index.html

Defines the global configuration object for the Verdaccio UI, including theme settings and environment variables.

```javascript
window.__VERDACCIO_BASENAME_UI_OPTIONS = { base: 'http://localhost:4873/', protocol: 'http', host: 'localhost', primaryColor: '#4b5e40', url_prefix: '', darkMode: false, language: 'en-US', uri: 'http://localhost:4873/', pkgManagers: ['pnpm', 'yarn', 'npm'], title: 'Verdaccio Dev UI', scope: '', version: 'dev', };
```

--------------------------------

### Upgrade or Uninstall the Deployment

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/kubernetes/helm/README.md

Commands to update the existing release or remove it from the cluster.

```bash
helm upgrade my-registry verdaccio/verdaccio -f values.yaml
helm uninstall my-registry
```

--------------------------------

### Run All Tests

Source: https://github.com/verdaccio/verdaccio/wiki/Developing-new-tests

Execute all available tests (unit and functional) using yarn.

```bash
yarn run test:all
```

--------------------------------

### Manage Docker Compose Services

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/reverse_proxy/nginx/README.md

Common commands for monitoring and managing the lifecycle of the Docker containers.

```bash
docker compose logs -f     # follow logs
docker compose ps          # list containers
docker compose down        # stop and remove containers
```

--------------------------------

### Development Workaround for New Languages

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/ui-theme/src/i18n/ABOUT_TRANSLATIONS.md

In development mode, manually create a folder and JSON file for your translations to test them locally. This bypasses the need for admin credentials to download official translations.

```json
/packages/plugins/ui-theme/src/i18n/download_translations/fr-FR/ui.json
```

--------------------------------

### Configure npm SSL settings

Source: https://github.com/verdaccio/verdaccio/blob/master/docker-examples/v7/reverse_proxy/https-portal/README.md

Disable strict SSL for local testing with self-signed certificates.

```bash
npm config set strict-ssl false
```

--------------------------------

### Run Verdaccio Docker with Debug and Custom Config

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Runs a Verdaccio Docker container with debug logging enabled and a custom configuration.

```bash
docker run -it --rm --name verdaccio -e DEBUG='verdaccio*' -p 4873:4873 verdaccio/verdaccio:local
```

--------------------------------

### Pass Plugin Configuration to Verifier

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

If your plugin requires specific configuration during instantiation, provide it using the `pluginConfig` option. This ensures the plugin is tested with its intended settings.

```typescript
const result = await verifyPlugin({
  pluginPath: 'my-storage',
  category: PLUGIN_CATEGORY.STORAGE,
  pluginsFolder: '/path/to/plugins',
  pluginConfig: {
    dataDir: '/tmp/verdaccio-storage',
    maxSize: 1024,
  },
});
```

--------------------------------

### Run End-to-End Tests

Source: https://github.com/verdaccio/verdaccio/wiki/Developing-new-tests

Execute end-to-end tests using yarn.

```bash
yarn run test:e2e
```

--------------------------------

### Test Plugin Loading with Vitest

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

Use this snippet in your plugin's test suite (e.g., Vitest or Jest) to verify that Verdaccio can load your plugin. It checks for successful loading and the number of plugins loaded.

```typescript
import { describe, expect, it } from 'vitest';

import { PLUGIN_CATEGORY } from '@verdaccio/core';
import { verifyPlugin } from '@verdaccio/plugin-verifier';

describe('my verdaccio plugin', () => {
  it('should be loadable by verdaccio', async () => {
    const result = await verifyPlugin({
      pluginPath: 'my-auth',
      category: PLUGIN_CATEGORY.AUTHENTICATION,
      pluginsFolder: '/path/to/build/output',
    });

    expect(result.success).toBe(true);
    expect(result.pluginsLoaded).toBe(1);
  });
});
```

--------------------------------

### Visual Studio Code Debug Attach Configuration

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

A sample VS Code debug configuration to attach to a running Node.js process, typically used for debugging Verdaccio.

```json
{
  "name": "Attach",
  "port": 9229,
  "request": "attach",
  "skipFiles": [
    "<node_internals>/**"
  ],
  "type": "pwa-node"
}
```

--------------------------------

### Configure New Hashing Algorithms

Source: https://github.com/verdaccio/verdaccio/blob/master/docs/migrations-guide.md

Configure the `auth` section to specify password hashing algorithms like `bcrypt`, `md5`, or `sha1`, and set `bcrypt` complexity with `rounds`.

```yaml
auth:
htpasswd:
  file: ./htpasswd
  max_users: 1000
  # Hash algorithm, possible options are: "bcrypt", "md5", "sha1", "crypt".
  algorithm: bcrypt
  # Rounds number for "bcrypt", will be ignored for other algorithms.
  rounds: 10
```

--------------------------------

### Configure Auth Memory Plugin in Verdaccio

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/auth-memory/README.md

Add the auth-memory plugin configuration to your Verdaccio config.yaml file, defining users and their passwords.

```yaml
auth:
  auth-memory:
    users:
      foo:
        name: foo
        password: s3cret
      bar:
        name: bar
        password: s3cret
```

--------------------------------

### Block by Package Name

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/package-filter/README.md

Blocks all versions of specific packages, 'malicious-pkg' and '@coolauthor/stolen'.

```yaml
filters:
  '@verdaccio/package-filter':
    block:
      - package: 'malicious-pkg'
      - package: '@coolauthor/stolen'
```

--------------------------------

### Docker Operations

Source: https://github.com/verdaccio/verdaccio/blob/master/README.md

Commands for pulling the Verdaccio Docker image and running the container.

```bash
docker pull verdaccio/verdaccio:nightly-master
```

```bash
docker run -it --rm --name verdaccio -p 4873:4873 verdaccio/verdaccio
```

--------------------------------

### Build Verdaccio Configuration Programmatically

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/config/README.md

Use ConfigBuilder to construct a comprehensive Verdaccio configuration object with various settings. This is useful for testing or dynamic configuration generation.

```typescript
import { ConfigBuilder } from '@verdaccio/config';
import { constants } from '@verdaccio/core';

const config = ConfigBuilder.build()
  .addStorage('./storage')
  .addSecurity({
    api: { 
      jwt: { sign: { expiresIn: '7d' }, verify: {} }, 
      legacy: false,
    },
    web: {
      sign: { expiresIn: '1h' },
      verify: {},
    },
  })
  .addAuth({ 
    htpasswd: { file: '.htpasswd' }, 
  })
  .addUplink('npmjs', { url: 'https://registry.npmjs.org/' })
  .addPackageAccess('@scope/*', {
    access: constants.ROLES.$AUTH,
    publish: constants.ROLES.$AUTH,
    proxy: 'npmjs',
  })
  .addWeb({ title: 'My Registry', darkMode: true, primaryColor: '#4b5e40' })
  .addLogger({ type: 'stdout', format: 'pretty', level: 'info' })
  .addMiddlewares({ audit: { enabled: true } })
  .addFlags({ changePassword: true })
  .addI18n({ web: 'en-US' });

// Get the configuration object
const configObj = config.getConfig();

// Get the configuration as YAML text
const configYaml = config.getAsYaml();
```

--------------------------------

### verifyPlugin Function

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

The `verifyPlugin` function is the primary interface for testing Verdaccio plugins. It takes an options object and returns a promise that resolves to a verification result. This function checks if a plugin can be loaded by Verdaccio and performs a default sanity check based on its category, or a custom check if provided.

```APIDOC
## `verifyPlugin(options: VerifyPluginOptions): Promise<VerifyResult>`

### Description
Verifies if a Verdaccio plugin can be loaded and instantiated correctly. It performs a sanity check based on the plugin's category or a custom check function.

### Parameters
#### Path Parameters
None

#### Query Parameters
None

#### Request Body
##### `VerifyPluginOptions`
- **pluginPath** (string) - Required - Plugin identifier as it would appear in `config.yaml` (e.g. `my-auth`, `@scope/my-plugin`).
- **category** (PluginCategory) - Required - Plugin category: `authentication`, `storage`, `middleware`, or `filter`.
- **pluginConfig** (Record<string, unknown>) - Optional - Configuration passed to the plugin constructor. Defaults to `{}`.
- **sanityCheck** ((plugin: any) => boolean) - Optional - Custom validation function; overrides the built-in check. Defaults to a category-specific check.
- **prefix** (string) - Optional - Plugin name prefix (maps to `server.pluginPrefix`). Defaults to `'verdaccio'`.
- **pluginsFolder** (string) - Optional - Absolute path to plugins directory (maps to `config.plugins`); when omitted, resolves from `node_modules`. Defaults to `undefined`.

### Response
#### Success Response (200)
##### `VerifyResult`
- **success** (boolean) - Whether the plugin loaded and passed all checks.
- **pluginName** (string) - The plugin identifier used.
- **category** (PluginCategory) - The category verified against.
- **pluginsLoaded** (number) - Number of plugin instances successfully loaded.
- **error** (string?) - Error message if verification failed.

### Request Example
```typescript
import { verifyPlugin } from '@verdaccio/plugin-verifier';

const result = await verifyPlugin({
  pluginPath: 'my-auth',
  category: 'authentication',
  pluginsFolder: '/path/to/build/output',
  pluginConfig: {
    dataDir: '/tmp/verdaccio-storage',
  },
  sanityCheck: (plugin) => typeof plugin.authenticate === 'function',
  prefix: 'mycompany'
});
```

### Response Example
```json
{
  "success": true,
  "pluginName": "my-auth",
  "category": "authentication",
  "pluginsLoaded": 1,
  "error": null
}
```
```

--------------------------------

### Run Functional Tests

Source: https://github.com/verdaccio/verdaccio/wiki/Developing-new-tests

Execute functional tests using yarn.

```bash
yarn run test:functional
```

--------------------------------

### Block Versions by Date

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/package-filter/README.md

Restricts visibility to package versions published before January 1, 2024. When combined with minAgeDays, the earlier cutoff date is used.

```yaml
filters:
  '@verdaccio/package-filter':
    dateThreshold: '2024-01-01'
```

--------------------------------

### Register a new language in the UI configuration

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Add the new language entry to the language definition file to make it available for translation in Crowdin.

```javascript
{ lng: {korean:"Korean"}}
```

--------------------------------

### Configure verdaccio-audit Middleware

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/audit/README.md

Enable and configure the audit middleware in your Verdaccio configuration file. The 'strict_ssl' option is optional and defaults to true.

```yaml
middlewares:
  audit:
    enabled: true
    strict_ssl: true # optional, defaults to true
    timeout: 1000
```

--------------------------------

### Enable Debug Logging in Dockerfile

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Sets the DEBUG environment variable within a Dockerfile to enable verbose logging for Verdaccio.

```dockerfile
FROM verdaccio/verdaccio:5
ENV DEBUG=verdaccio*
ADD docker.yaml /verdaccio/conf/config.yaml
```

--------------------------------

### Specify Custom Plugin Prefix

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

If your Verdaccio instance uses a custom plugin prefix (e.g., `mycompany-` instead of `verdaccio-`), specify it using the `prefix` option. This ensures the verifier looks for the correctly named plugin.

```typescript
const result = await verifyPlugin({
  pluginPath: 'auth',
  category: PLUGIN_CATEGORY.AUTHENTICATION,
  pluginsFolder: '/path/to/plugins',
  prefix: 'mycompany', // looks for "mycompany-auth" instead of "verdaccio-auth"
});
```

--------------------------------

### Programmatic API: Verify file-based plugin

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

Verify a plugin located in a specific folder using the programmatic API. This requires specifying the plugin path, category, and the absolute path to the plugins folder.

```typescript
import { PLUGIN_CATEGORY } from '@verdaccio/core';
import { verifyPlugin } from '@verdaccio/plugin-verifier';

const result = await verifyPlugin({
  pluginPath: 'my-auth',
  category: PLUGIN_CATEGORY.AUTHENTICATION,
  pluginsFolder: '/absolute/path/to/plugins',
});

if (result.success) {
  console.log(`Plugin loaded successfully (${result.pluginsLoaded} instance(s))`);
} else {
  console.error('Plugin verification failed:', result.error);
}
```

--------------------------------

### Block by Version Range

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/package-filter/README.md

Blocks versions of '@coolauthor/stolen' that are greater than '2.0.1'.

```yaml
filters:
  '@verdaccio/package-filter':
    block:
      - package: '@coolauthor/stolen'
        versions: '>2.0.1'
```

--------------------------------

### Enable Debug Output for Package Filter

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/package-filter/README.md

Use the DEBUG environment variable to control the verbosity of plugin debug output. Specify namespaces to filter the output.

```bash
# See all plugin debug output
DEBUG=verdaccio:plugin:package-filter* verdaccio

# See only config parsing
DEBUG=verdaccio:plugin:package-filter:config verdaccio

# See only filtering decisions
DEBUG=verdaccio:plugin:package-filter:filter verdaccio

# See manifest cleanup details
DEBUG=verdaccio:plugin:package-filter:manifest verdaccio

# Combine with other verdaccio debug namespaces
DEBUG=verdaccio:plugin:package-filter*,verdaccio:storage verdaccio
```

--------------------------------

### Block Versions by Age

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/package-filter/README.md

Hides package versions published less than 30 days ago. This is a global rule applicable to all packages.

```yaml
filters:
  '@verdaccio/package-filter':
    minAgeDays: 30
```

--------------------------------

### Debug a Verdaccio Unit Test

Source: https://github.com/verdaccio/verdaccio/wiki/Debugging-Verdaccio

Runs a specific Verdaccio unit test with the Node.js inspector enabled, allowing for step-by-step debugging.

```bash
node --inspect-brk ../../node_modules/jest/bin/jest.js packages/store/test/storage.spec.ts
```

--------------------------------

### Pull Verdaccio Docker Image

Source: https://github.com/verdaccio/verdaccio/blob/master/README.md

Command to pull the nightly master Docker image for Verdaccio.

```bash
docker pull verdaccio/verdaccio:nightly-master
```

--------------------------------

### Import Sanity Check Helpers

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

Import individual sanity check functions or a general helper to use directly in your code. These functions are designed to perform specific checks for different plugin categories.

```typescript
import {
  authSanityCheck,
  filterSanityCheck,
  getSanityCheck,
  // returns the right check for a given category
  middlewareSanityCheck,
  storageSanityCheck,
} from '@verdaccio/plugin-verifier';
```

--------------------------------

### Update Node-API Usage

Source: https://github.com/verdaccio/verdaccio/blob/master/docs/migrations-guide.md

The node-api interface has been updated to be Promise-based with fewer arguments. Use `runServer` from `@verdaccio/node-api` or `verdaccio`.

```javascript
import { runServer } from '@verdaccio/node-api';
// or
import { runServer } from 'verdaccio';
const app = await runServer(); // default configuration
const app = await runServer('./config/config.yaml');
const app = await runServer({ configuration });
app.listen(4000, (event) => {
  // do something
});
```

--------------------------------

### Debug compiled code with environment variables

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Use the DEBUG environment variable to enable verbose output for specific Verdaccio namespaces.

```shell
DEBUG=verdaccio:* node packages/verdaccio/debug/bootstrap.js
```

```shell
DEBUG=verdaccio:plugin:* node packages/verdaccio/debug/bootstrap.js
```

--------------------------------

### Rename Experiments to Flags

Source: https://github.com/verdaccio/verdaccio/blob/master/docs/migrations-guide.md

The `experiments` configuration property has been renamed to `flags`. This change does not affect functionality.

```yaml
flags:
  token: false;
  search: false;
```

--------------------------------

### Block by Scope

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/package-filter/README.md

Blocks all packages belonging to the '@evilscope' scope.

```yaml
filters:
  '@verdaccio/package-filter':
    block:
      - scope: '@evilscope'
```

--------------------------------

### Replace Strategy for Blocked Versions

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/package-filter/README.md

When versions of '@coolauthor/stolen' greater than '2.0.1' are blocked, they are replaced with the nearest older safe version (e.g., 2.0.1) instead of being removed. This is useful for transitive dependencies.

```yaml
filters:
  '@verdaccio/package-filter':
    block:
      - package: '@coolauthor/stolen'
        versions: '>2.0.1'
        strategy: replace
```

--------------------------------

### Sanity Check Helpers

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

Individual sanity check functions are exported for direct use, allowing for more granular control or integration into custom testing workflows.

```APIDOC
## Sanity Check Helpers

### Description
Provides individual sanity check functions that can be imported and used directly for custom validation logic.

### Functions
- **authSanityCheck**: Performs sanity checks specific to authentication plugins.
- **filterSanityCheck**: Performs sanity checks specific to filter plugins.
- **middlewareSanityCheck**: Performs sanity checks specific to middleware plugins.
- **storageSanityCheck**: Performs sanity checks specific to storage plugins.
- **getSanityCheck**: Returns the appropriate sanity check function for a given plugin category.

### Usage Example
```typescript
import {
  authSanityCheck,
  filterSanityCheck,
  getSanityCheck,
  middlewareSanityCheck,
  storageSanityCheck,
} from '@verdaccio/plugin-verifier';

// Example: Get the storage sanity check
const storageCheck = getSanityCheck('storage');
// Example: Directly use a sanity check
const isAuthPluginValid = authSanityCheck(myAuthPluginInstance);
```
```

--------------------------------

### Avoid disabling package locks in .npmrc

Source: https://github.com/verdaccio/verdaccio/blob/master/CONTRIBUTING.md

Ensure the global .npmrc file does not contain this setting to prevent incorrect dependency versions.

```text
package-lock=false
```

--------------------------------

### Disable Package Filter Plugin

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/package-filter/README.md

To disable the package filter plugin, remove or comment out the 'filters' section related to '@verdaccio/package-filter' in your 'config.yaml' file.

```yaml
# filters:
#   '@verdaccio/package-filter':
```

--------------------------------

### Verdaccio PGP Public Key

Source: https://github.com/verdaccio/verdaccio/blob/master/SECURITY.md

This is the PGP public key for the Verdaccio project. Use it to encrypt sensitive information before sharing it over unsecured channels.

```text
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: OpenPGP.js v4.5.1
Comment: https://openpgpjs.org

xsBNBFzm3asBCACxnJDv1r6dxiM2e8iqS6B7fxY2I3X1Rc+3m8mhXOwVwRG4
AOrQ417oSzsVLf4iocg+DWrtxzY79odTLJEovVt79rxwqIIl4y96tH+29kLB
ao7eaYZacfstonVkBAmxBLaYv1x7cqWuukm6sBCOxapW1X9BcbR3vOghDziY
/1AwNjupAOPvKNMtghjrdh3w0iMfZS1hw28zjM1oCeezEil+CTjgQDN+69qS
UFG/BInJ7CVn9TvhU85inSwpxVa576fkhvFoNUrGvFvYRWtXRJndbRdBodVj
C9At/Gb2IeNf7xqXH2KloZ1yaVNVSzLX4jqrMWeF+9Z12SjUyL6G9TwDABEB
AAHNIXZlcmRhY2Npb0BwbS5tZSA8dmVyZGFjY2lvQHBtLm1lPsLAdQQQAQgA
HwUCXObdqwYLCQcIAwIEFQgKAgMWAgECGQECGwMCHgEACgkQpSvoGbwFJYhn
2wf+JF+yLQXh1EFMih6lpbx243hvglgOWmcigYVRh5mSfULcdW2pmkPQXqhE
DW73qqwN9G9piiPnGMw7sKoB7XJVuFKyvHOYKtem5UQVRvs2rTxnSc5qFcUJ
0w3Tw/pZ9B3fYAEYti2B/GsSOzaECfBKCFOg15xXGAdwfgff5FsorN1Gb6MG
eCO9c8faSF/+fQUCfokwMDVzxXQFZEMx3q/rHVJ/Fm+XelZ+00c9fdyiuPW5
dM9gATle7lz0iPtxaUDGLW8QZ/7b6O8IJ1kle0tL4AE++bXsVWxNdzhlNohH
Hn09sIdFnG4ySTz4YJjiDd70ZdQjOGEGvutymEIN1xcNq87ATQRc5t2rAQgA
yX2ZhUCtrz7lzK0992yveB+duVF//yo9Pei2ra9Z3GNmA+oWlRH1FTWpAmVH
uDdUchTnxAwaKntabt3Mb1AgEZwrdiG4LuHFbdx2ls93BJ5lXdp7vB6pVf3N
IrhHKyQ/Y5L5kMSj/GjrhO19zmj6mPPEgb3M3ZIZjQUF4pro0pExuAPA9Wxe
awn5+0BUYFs4mZQDtTdiVuz5tWA0fNtt1aBfOPA97tmn18y4b1b0iQIJQpep
BVVnFLeAZOevDcBJFbmQOdAjufWSSgpzX+FZ3rx6RVwwKxUiVQyUuwSQkKh5
RufZ5zE0y7Fe/YlWXbKoj4zNJqYtjPSPngQRWf7UpwARAQABwsBfBBgBCAAJ
BQJc5t2rAhsMAAoJEKUr6Bm8BSWIoYQH+QDw0Z84tZK4N1lh49hYyohs6vNU
9kG69nKLQA5NymPtTxh8YOJhdJL697FkvKI4OGEO2FXUmcJS3CBJ2nBVKMq2
1biDRKC4OhIU2RgFhS6bHy6VOn24EYs77T+zX8YXpz8ulYVln2b0QZCubN0Z
L50tEC8HnuVMVN+/pqITdD3FjzwGZgHdW8qkKgD6qhObHCl8/cW2buCsaIAY
eZWVPgPY1S1U0V608qYNtUCkrmUW5Sl6YLvz7JTvTsaym5mzyFXF3ErAURgI
/v4XaWmRgNGIxbIxsFGuEs+KIKBQDJmtvJCVpBNS5IYnFf5h/LA5cfkwMKJt
wXhyE0b/iDs60ZM=
=QWXs
-----END PGP PUBLIC KEY BLOCK-----
```

--------------------------------

### Custom Sanity Check for Plugin Methods

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/tools/plugin-verifier/README.md

Override the default sanity check by providing a custom `sanityCheck` function. This allows you to verify specific methods or behaviors unique to your plugin, ensuring it meets custom requirements.

```typescript
const result = await verifyPlugin({
  pluginPath: 'my-auth',
  category: PLUGIN_CATEGORY.AUTHENTICATION,
  pluginsFolder: '/path/to/plugins',
  sanityCheck: (plugin) => {
    return typeof plugin.authenticate === 'function' && typeof plugin.changePassword === 'function';
  },
});
```

--------------------------------

### Add New Language Translation

Source: https://github.com/verdaccio/verdaccio/blob/master/packages/plugins/ui-theme/README.md

To add a new language translation, create a JSON file in `i18n/translations/*`, update configuration files, and add an SVG flag.

```plaintext
1 - A json file in the folder `i18n/translations/*` with the translations. The file must be named according to the new added language

2 - The files `i18n/config.ts` and `LanguageSwitch.tsx` updated with the new language. Please see the current structure

3 - The other translations containing the new language in the language of the file. Example:

New language: `cs_CZ `

The file `pt-BR ` should contain:

```
"lng": {
    ...,
    "czech": "Tcheco"
}
```

4 - A SVG flag of the new translated language in the the folder `src/components/Icon/img/*`. You maybe want to compress the svg file using https://jakearchibald.github.io/svgomg/
```
