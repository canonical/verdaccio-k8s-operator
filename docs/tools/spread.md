### Setting up LXD environment

Source: https://github.com/canonical/spread/blob/master/README.md

Commands to install and initialize the LXD hypervisor on Ubuntu.

```bash
sudo apt update
sudo apt install lxd
sudo lxd init
```

--------------------------------

### Install Spread via Go

Source: https://github.com/canonical/spread/blob/master/README.md

Use the Go toolchain to install the latest version of the Spread command-line utility.

```shell
go install github.com/canonical/spread/cmd/spread@latest
```

--------------------------------

### Install and build QEMU image

Source: https://github.com/canonical/spread/blob/master/README.md

Commands to install necessary QEMU packages and build an Ubuntu cloud image for use with the backend.

```bash
sudo apt install qemu-kvm autopkgtest
adt-buildvm-ubuntu-cloud
```

--------------------------------

### Define Project Configuration

Source: https://github.com/canonical/spread/blob/master/README.md

Configure the project and backends in spread.yaml. This example uses the LXD backend.

```yaml
project: hello-world

backends:
    lxd:
        systems: [ubuntu-16.04]

suites:
    examples/:
        summary: Simple examples

path: /remote/path
```

--------------------------------

### Configure Linode Backend

Source: https://github.com/canonical/spread/blob/master/README.md

Example of configuring the Linode backend in spread.yaml using an environment variable for the API key.

```yaml
backends:
    linode:
        key: $(HOST:echo $LINODE_API_KEY)
        systems: [ubuntu-16.04]
```

--------------------------------

### Define Task Execution

Source: https://github.com/canonical/spread/blob/master/README.md

Create a task.yaml file to specify commands to execute. This example prints a message and exits with an error code.

```yaml
summary: Greet the planet
execute: |
    echo "Hello world!"
    exit 1
```

--------------------------------

### Configure QEMU backend in spread.yaml

Source: https://github.com/canonical/spread/blob/master/README.md

Define the QEMU backend systems and credentials within the spread.yaml configuration file.

```yaml
backends:
    qemu:
        systems:
            - ubuntu-16.04:
                username: ubuntu
                password: ubuntu
```

--------------------------------

### Authenticate with User Credentials

Source: https://github.com/canonical/spread/blob/master/README.md

Log in using personal credentials to set up application-default authentication.

```bash
$ gcloud auth application-default login
```

--------------------------------

### Configuring LXD backend

Source: https://github.com/canonical/spread/blob/master/README.md

Define the LXD backend and supported systems in the project file.

```yaml
backends:
    lxd:
        systems:
            - ubuntu-16.04
```

--------------------------------

### Authenticate with Service Account

Source: https://github.com/canonical/spread/blob/master/README.md

Activate a service account for application-default credentials using a JSON key file.

```bash
$ gcloud auth application-default activate-service-account --key-file=$GOOGLE_JSON_FILENAME
```

--------------------------------

### Configure Google Backend in spread.yaml

Source: https://github.com/canonical/spread/blob/master/README.md

Define the Google backend settings, including credentials and system images, within the spread.yaml file.

```yaml
backends:
    google:
        key: $(HOST:echo $GOOGLE_JSON_FILENAME)
	location: yourproject/southamerica-east1-a
        systems:
            - ubuntu-16.04

	    # Extended syntax:
	    - another-system:
	        image: some-other-image
		workers: 3
```

--------------------------------

### Configure a pass-through repack script

Source: https://github.com/canonical/spread/blob/master/README.md

A basic configuration that reads from file descriptor 3 and writes to file descriptor 4 without modifying the content.

```yaml
repack: |
    cat <&3 >&4
```

--------------------------------

### Select tasks via command line

Source: https://github.com/canonical/spread/blob/master/README.md

Pass task names as arguments to the spread command to execute specific jobs.

```bash
$ spread my-suite/task-one my-suite/task-two
```

--------------------------------

### Basic Linode Backend Configuration

Source: https://github.com/canonical/spread/blob/master/README.md

Defines the Linode backend with an API key sourced from an environment variable and a list of target systems.

```yaml
(...)

backends:
    linode:
        key: $(HOST:echo $LINODE_API_KEY)
        systems:
            - ubuntu-16.04
```

--------------------------------

### Executing tasks with artifacts

Source: https://github.com/canonical/spread/blob/master/README.md

Use the -artifacts flag to specify the destination directory for downloaded task content.

```bash
$ spread -artifacts=./artifacts lxd:ubuntu-16.04:mysuite/task-one:variant-a
```

--------------------------------

### Configure delta-based repository uploads

Source: https://github.com/canonical/spread/blob/master/README.md

A complex configuration using xdelta3 to compute and ship repository deltas, including environment variables and preparation steps.

```yaml
environment:
    DELTA_REF: v1.23

rename:
    - s,^,$DELTA_REF,S

exclude:
    - .git

repack: |
    trap "rm -f delta-ref.tar current.delta" EXIT
    git archive -o delta-ref.tar --format=tar --prefix=$DELTA_PREFIX $DELTA_REF
    xdelta3 -s delta-ref.tar <&3 > current.delta
    tar c current.delta >&4

prepare: |
    apt-get install xdelta3
    curl -s -o - https://codeload.github.com/myrepo/myproject/tar.gz/$DELTA_REF | gunzip > delta-ref.tar
    xdelta3 -d -s delta-ref.tar current.delta | tar x --strip-components=1
    rm -f delta-ref.tar current.delta
```

--------------------------------

### Spread Execution Output

Source: https://github.com/canonical/spread/blob/master/README.md

Sample console output showing the execution process and failure report for a task.

```text
2016/06/06 09:59:34 Allocating server lxd:ubuntu-16.04...
2016/06/06 09:59:55 Waiting for LXD container spread-1-ubuntu-16-04 to have an address...
2016/06/06 09:59:59 Allocated lxd:ubuntu-16.04 (spread-1-ubuntu-16-04).
2016/06/06 09:59:59 Connecting to lxd:ubuntu-16.04 (spread-1-ubuntu-16-04)...
2016/06/06 10:00:04 Connected to lxd:ubuntu-16.04 (spread-1-ubuntu-16-04).
2016/06/06 10:00:04 Sending data to lxd:ubuntu-16.04 (spread-1-ubuntu-16-04)...
2016/06/06 10:00:05 Error executing lxd:ubuntu-16.04:examples/hello:
-----
+ echo Hello world!
Hello world!
+ exit 1
-----
2016/06/06 10:00:05 Discarding lxd:ubuntu-16.04 (spread-1-ubuntu-16-04)...
2016/06/06 10:00:06 Successful tasks: 0
2016/06/06 10:00:06 Aborted tasks: 0
2016/06/06 10:00:06 Failed tasks: 1
    - lxd:ubuntu-16.04:examples/hello
```

--------------------------------

### Define prepare and restore scripts in spread.yaml

Source: https://github.com/canonical/spread/blob/master/README.md

Configure suite-level prepare and restore scripts within the spread.yaml file.

```yaml
suites:
    examples/:
        summary: Simple examples
        prepare: |
            echo Preparing...
        restore: |
            echo Restoring...
```

--------------------------------

### Execution order of prepare and restore scripts

Source: https://github.com/canonical/spread/blob/master/README.md

Visual representation of the hierarchical execution order for prepare and restore hooks across projects, backends, suites, and tasks.

```text
project prepare
    backend1 prepare
        suite1 prepare
            project prepare-each
                backend1 prepare-each
                    suite1 prepare-each
                        task1 prepare; task1 execute; task1 restore
                    suite1 restore-each
                backend1 restore-each
            project restore-each
            project prepare-each
                backend1 prepare-each
                    suite1 prepare-each
                        task2 prepare; task2 execute; task2 restore
                    suite restore-each
                backend1 restore-each
            project restore-each
        suite1 restore
        suite2 prepare
            project prepare-each
                backend1 prepare-each
                    suite2 prepare-each
                        task3 prepare; task3 execute; task3 restore
                    suite2 restore-each
                backend2 restore-each
            project restore-each
        suite2 restore
    backend1 restore
project restore
```

--------------------------------

### View Job Matrix Format

Source: https://github.com/canonical/spread/blob/master/README.md

Displays the format used by the -list option to show all jobs that would run in the matrix.

```text
backend:system:suite/task:variant
```

--------------------------------

### Define multiple backends of the same type

Source: https://github.com/canonical/spread/blob/master/README.md

Explicitly specifies the backend type when using multiple instances of the same provider.

```yaml
backends:
    linode-a:
        type: linode
        (...)
    linode-b:
        type: linode
        (...)
```

--------------------------------

### Configure AdHoc backend in spread.yaml

Source: https://github.com/canonical/spread/blob/master/README.md

Define allocation and discard scripts for the AdHoc backend to manage system lifecycle.

```yaml
backends:
    adhoc:
        allocate: |
            echo "Allocating $SPREAD_SYSTEM..."
            ADDRESS disposable.machine.address:22
        discard:
            echo "Discarding $SPREAD_SYSTEM..."
        systems:
            - ubuntu-16.04
```

--------------------------------

### Configure OpenStack backend in spread.yaml

Source: https://github.com/canonical/spread/blob/master/README.md

Defines the OpenStack backend settings including endpoint, credentials, and system definitions. Requires OpenStack identity API v3 and default domain.

```yaml
backends:
    openstack:
        endpoint: https://my-keystone-server:5000/v3
        account: my-account
        key: '$(HOST: echo "$OS_PASSWORD")'
        location: my-project/my-region
        plan: cpu2-ram4-disk10
        halt-timeout: 2h
        systems:
            - ubuntu-20.04:
                  image: ubuntu-focal-daily-amd64
                  workers: 2

            # Extended syntax:
            - another-system:
                image: some-other-image
                networks:
                    - network_external
                    - network_pvn
                groups:
                    - group_external
```

--------------------------------

### Registering artifacts in task.yaml

Source: https://github.com/canonical/spread/blob/master/README.md

Define files or directories to be retrieved after a task completes by adding them to the artifacts list.

```yaml
summary: Generate some useful content.

artifacts:
    - some/file
    - some/dir/

...
```

--------------------------------

### Dynamic System Allocation

Source: https://github.com/canonical/spread/blob/master/README.md

Configures the plan and datacenter location for dynamic machine allocation in Linode.

```yaml
backends:
    linode:
        key: (...)
	plan: 4GB
	location: newark
```

--------------------------------

### Configuring Halt Timeout

Source: https://github.com/canonical/spread/blob/master/README.md

Sets a halt-timeout to automatically shut down reused systems after a specified duration.

```yaml
backends:
    linode:
        key: (...)
	halt-timeout: 6h
	systems:
	    - ubuntu-16.04
```

--------------------------------

### Rebooting a system in a task

Source: https://github.com/canonical/spread/blob/master/README.md

Demonstrates using the REBOOT function to trigger a system reboot and re-execute the script based on the SPREAD_REBOOT environment variable.

```yaml
execute: |
    if [ $SPREAD_REBOOT = 0 ]; then
        echo "Before reboot"
        REBOOT
    fi
    echo "After reboot"
```

--------------------------------

### Configure systems for concurrent task execution

Source: https://github.com/canonical/spread/blob/master/README.md

Defines systems and worker counts within a backend to enable parallel task processing.

```yaml
(...)

backends:
    linode:
        systems:
            - ubuntu-14.04
            - ubuntu-16.04:
                workers: 2
```

--------------------------------

### Extended System Configuration

Source: https://github.com/canonical/spread/blob/master/README.md

Specifies custom image and kernel settings for a system within the Linode backend.

```yaml
(...)

backends:
    linode:
        key: (...)
	systems:
	    - ubuntu-16.04:
	        image: Ubuntu 16.04
	        kernel: GRUB 2
```

--------------------------------

### Configure file synchronization in spread.yaml

Source: https://github.com/canonical/spread/blob/master/README.md

Defines the remote base path and rules for including, excluding, and renaming files during synchronization.

```yaml
(...)

path: /remote/path

include:
    - src/*
exclude:
    - src/*.o

rename:
    - s,path/one,path/two,
```

--------------------------------

### Configuring explicit LXD images

Source: https://github.com/canonical/spread/blob/master/README.md

Override default image mapping by providing an explicit image name for a system.

```yaml
backends:
    lxd:
        systems:
            - ubuntu-16.04:
                image: ubuntu:16.04.1
```

--------------------------------

### Configure manual task execution

Source: https://github.com/canonical/spread/blob/master/README.md

Set manual: true in a task definition to prevent it from running unless explicitly selected.

```yaml
summary: This task only runs manually.

manual: true

...
```

--------------------------------

### Whitelist variants

Source: https://github.com/canonical/spread/blob/master/README.md

Explicitly list the variants to include without using prefixes.

```yaml
variants:
    - foo
    - baz
```

--------------------------------

### Define task environment variables

Source: https://github.com/canonical/spread/blob/master/README.md

Configures environment variables for a task, supporting shell syntax for remote evaluation.

```yaml
summary: Greet the planet
environment:
    SUBJECT: world
    GREETING: Hello $SUBJECT!
execute: |
    echo "$GREETING"
    exit 1
```

--------------------------------

### Define debug scripts in task.yaml

Source: https://github.com/canonical/spread/blob/master/README.md

Specifies scripts to run in trace mode upon task failure, providing diagnostic output.

```yaml
execute: |
    echo "Something went wrong."
    exit 1
debug: |
    dmesg | tail
```

--------------------------------

### Exclude a system

Source: https://github.com/canonical/spread/blob/master/README.md

Use the minus prefix to prevent a task or suite from running on a specific system.

```yaml
systems: [-ubuntu-14.04]
```

--------------------------------

### Define suite-level environment variables

Source: https://github.com/canonical/spread/blob/master/README.md

Sets common environment variables at the suite level to be inherited by tasks.

```yaml
(...)

suites:
    examples/:
        summary: Simple examples
        environment:
            SUBJECT: sanity
```

--------------------------------

### Updating user group for LXD

Source: https://github.com/canonical/spread/blob/master/README.md

Apply group changes to the current shell session to access the lxc client tool.

```bash
$ newgrp lxd
```

--------------------------------

### Append a variant

Source: https://github.com/canonical/spread/blob/master/README.md

Use the plus prefix to add a variant to the existing set.

```yaml
variants:
    - +buz
```

--------------------------------

### Define SSH credentials in spread.yaml

Source: https://github.com/canonical/spread/blob/master/README.md

Specifies system-specific usernames and passwords for SSH connections within the backends configuration.

```yaml
backends:
    qemu:
        systems:
            - debian-sid:
                password: mypassword
            - ubuntu-16.04:
                username: ubuntu
                password: ubuntu
```

--------------------------------

### Define suite-level variants

Source: https://github.com/canonical/spread/blob/master/README.md

Configures variants for a suite, causing tasks to execute multiple times based on variant keys.

```yaml
(...)

suites:
    examples/:
        summary: Simple examples
        environment:
            SUBJECT/foo: sanity
            SUBJECT/bar: lunacy
```

--------------------------------

### Blacklist a variant

Source: https://github.com/canonical/spread/blob/master/README.md

Use the minus prefix to exclude a specific variant from a task.

```yaml
variants:
    - -bar
```

--------------------------------

### Define task-level variants

Source: https://github.com/canonical/spread/blob/master/README.md

Configures task-specific variants, allowing for conditional variable overrides per job.

```yaml
summary: Greet the planet
environment:
    GREETING: Hello
    GREETING/bar: Goodbye
    SUBJECT/baz: world
execute: |
    echo "$GREETING $SUBJECT!"
    exit 1
```

--------------------------------

### Define task priority

Source: https://github.com/canonical/spread/blob/master/README.md

Set the priority field to influence scheduling order, where higher values are scheduled earlier.

```yaml
priority: 100
```
