### Example of tutorial installation steps

Source: https://github.com/canonical/workshop/blob/main/docs/doc-style-guide.md

A sample of how to structure installation steps using clear, imperative language.

```restructuredtext
Install Workshop,
upgrading the prerequisites if needed,
then ensure it runs.

Authenticate to the Snap Store and install the snap
using the `--classic <...>`_ option:
```

--------------------------------

### Install and start LXD

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/fix-workshops/fix-installation.md

Install and start the LXD snap, a prerequisite for Workshop. Add yourself to the lxd group for access.

```console
$ sudo snap install --channel=6/stable lxd
$ sudo snap start --enable lxd.daemon
$ sudo snap services lxd
```

```console
$ sudo usermod -a -G lxd $USER
```

--------------------------------

### SDK Setup and Task Management

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Functions for retrieving SDK setup configurations and managing SDK download and installation tasks.

```go
func SdkSetup(task *state.Task) (sdk.Setup, error) {
        st := task.State()
        st.Lock()
        defer st.Unlock()

        var retrieveId string
        var sdkSetup sdk.Setup

        err := task.Get("sdk-retrieve-task", &retrieveId)

        if err != nil {
                return sdk.Setup{}, err
        }

        retrieve := task.State().Task(retrieveId)
        if retrieve == nil {
                return sdk.Setup{}, fmt.Errorf("internal error: no corresponding retrieve-sdk task found")
        }

        if err = retrieve.Get("sdk-setup", &sdkSetup); err != nil {
                return sdk.Setup{}, err
        }
        return sdkSetup, nil
}
```

```go
func (m *SdkManager) doRetrieveSdk(task *state.Task, tomb *tomb.Tomb) error {
        user, project, _, err := UserProjectWorkshop(task)
        if err != nil {
                return err
        }

        st := task.State()
        var rec sdk.Setup

        st.Lock()
        err = task.Get("sdk-setup", &rec)
        st.Unlock()
        if err != nil {
                return err
        }

        ctx, cancel := BackendContext(tomb, user, project.ProjectId)
        defer cancel()

        st.Lock()
        store := sdk.StoreService(st)
        st.Unlock()

        reporter := &progress.Reporter{
                Name: task.ID(),
                Report: func(label string, done, total int) {
                        st.Lock()
                        task.SetProgress(label, done, total)
                        st.Unlock()
                },
        }

        return store.DownloadSdk(ctx, rec, reporter)
}
```

```go
func (m *SdkManager) doInstallLocalSdk(task *state.Task, tomb *tomb.Tomb) error {
        user, project, w, err := UserProjectWorkshop(task)
        if err != nil {
                return err
        }

        sdkSetup, err := SdkSetup(task)
        if err != nil {
                return err
        }

        ctx, cancel := BackendContext(tomb, user, project.ProjectId)
        defer cancel()

        wp, err := m.backend.Workshop(ctx, w)
        if err != nil {
                return err
        }
```

--------------------------------

### Preferred imperative installation instruction

Source: https://github.com/canonical/workshop/blob/main/docs/doc-style-guide.md

An example of the preferred imperative style for providing installation instructions.

```default
Install Workshop using the --classic option:
```

--------------------------------

### Define SDK Setup and Type Structures

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the Setup structure for SDK installations and associated types for SDK configuration.

```go
package sdk

import (
        "bytes"
        "fmt"
        "path/filepath"
        "sort"
        "strings"
        "time"

        "gopkg.in/check.v1"
        "gopkg.in/yaml.v3"

        "github.com/canonical/workshop/internal/dirs"
        "github.com/canonical/workshop/internal/metautil"
)

type Setup struct {
        Name             string     `json:"name"`
        Channel          string     `json:"channel"`
        Revision         Revision   `json:"revision"`
        RevisionSequence []Revision `json:"revision-sequence,omitempty"`
        InstallTime      *time.Time `json:"install-time"`
}

func (s *Setup) Filename() string {
        return filepath.Join(dirs.SdkDir, fmt.Sprintf("%s_%s.sdk", s.Name, s.Revision.String()))
}

type sdkYaml struct {
        Name      string                 `yaml:"name"`
        Base      string                 `yaml:"base"`
        Version   string                 `yaml:"version,omitempty"`
        Type      string                 `yaml:"type"`
        BuildTime *time.Time             `yaml:"sdkcraft-started-at,omitempty"`
        Plugs     map[string]interface{} `yaml:"plugs,omitempty"`
        Slots     map[string]interface{} `yaml:"slots,omitempty"`
}

type Type string

const Sketch = "sketch"

const (
        Regular Type = "regular"
        System  Type = "system"
)

func (t Type) String() string {
        return string(t)
}
```

--------------------------------

### Connect plug to slot examples

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Examples demonstrating shorthand and full syntax for connecting plugs to slots.

```console
$ workshop connect nimble/go:mod-cache :mount
```

```console
$ workshop connect nimble/go:mod-cache nimble/system:mount
```

--------------------------------

### Configure setup-project Hook

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-3-sketch-sdks.md

Example of adding a setup-project hook to install dependencies within an existing virtual environment.

```yaml
name: sketch

hooks:
  setup-project: |
    source /var/lib/workshop/sdk/jupyter/venv/bin/activate
    pip install jupyter-console
```

--------------------------------

### Install Workshop via Snap

Source: https://github.com/canonical/workshop/blob/main/docs/doc-style-guide.md

Use this command to install the Workshop tool. The example omits the shell prompt to facilitate easy copying.

```restructuredtext
.. code-block:: console

   sudo snap install --classic workshop
```

--------------------------------

### Install SDKs

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Orchestrates the sequential installation of SDKs, setup hooks, and auto-connection tasks to ensure dependency safety.

```go
func installSdks(st *state.State, w string, sdks []sdk.Setup, retrieveSet *state.TaskSet) *state.TaskSet {
        var prevInstall = sdkstate.InstallSystemSdk(st)
        install := state.NewTaskSet(prevInstall.Tasks()...)

        var prevSetup *state.Task
        setupHook := state.NewTaskSet()

        var prevAuto = st.NewTask("auto-connect", fmt.Sprintf(`Auto-connect interfaces of %q SDK`, sdk.System.String()))
        prevAuto.Set("sdk", sdk.System.String())
        autoConnect := state.NewTaskSet(prevAuto)

        for idx, setup := range sdks {
                // The install task sets must not run concurrently as exec ops are not
                // allowed by LXD to be run concurrently and in general case we cannot
                // guarantee safety of concurrent installations.
                var installTs *state.TaskSet
                if setup.Channel != "" {
                        installTs = sdkstate.Install(st, setup.Name, retrieveSet.Tasks()[idx].ID())
                } else {
                        installTs = sdkstate.InstallLocalSdk(st, setup)
                }

                if prevInstall != nil {
                        installTs.WaitAll(prevInstall)
                }
                prevInstall = installTs
                install.AddAll(installTs)

                // Make sure that the hook tasks are not concurrent
                setupHookTask := hookstate.Hook(st, w, setup.Name, hookstate.SetupBase)
                if prevSetup != nil {
                        setupHookTask.WaitFor(prevSetup)
                }
                prevSetup = setupHookTask
                setupHook.AddTask(setupHookTask)

                autoconnect := st.NewTask("auto-connect", fmt.Sprintf("Auto-connect interfaces of %q SDK", setup.Name))
                autoconnect.Set("sdk", setup.Name)
                autoConnect.AddTask(autoconnect)
                if prevAuto != nil {
                        autoconnect.WaitFor(prevAuto)
                }
                prevAuto = autoconnect
        }
        setupHook.WaitAll(install)
        autoConnect.WaitAll(setupHook)
        autoConnect.WaitAll(install)

        all := state.NewTaskSet(install.Tasks()...)
        all.AddAll(setupHook)
        all.AddAll(autoConnect)
        return all
}
```

--------------------------------

### Daemon Start Sequence

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Performs startup initialization, including overlord setup and listener serving.

```go
func (d *Daemon) Start() error {
        if d.rebootIsMissing {
                // we need to schedule and wait for a system restart
                d.tomb.Kill(nil)
                // avoid systemd killing us again while we wait
                systemdSdNotify("READY=1")
                return nil
        }
        if d.overlord == nil {
                panic("internal error: no Overlord")
        }

        d.StartTime = time.Now()

        // now perform expensive overlord/manages initialization
        if err := d.overlord.StartUp(); err != nil {
                return err
        }
        d.connTracker = &connTracker{conns: make(map[net.Conn]struct{})}
        d.serve = &http.Server{
                Handler:   logit(d.router),
                ConnState: d.connTracker.trackConn,
        }

        d.initStandbyHandling()

        d.overlord.Loop()

        d.tomb.Go(func() error {
                if d.untrustedListener != nil {
                        d.tomb.Go(func() error {
                                if err := d.serve.Serve(d.untrustedListener); err != http.ErrServerClosed && d.tomb.Err() == tomb.ErrStillAlive {
                                        return err
                                }
                                return nil
                        })
                }
                if err := d.serve.Serve(d.generalListener); err != http.ErrServerClosed && d.tomb.Err() == tomb.ErrStillAlive {
                        return err
                }
                return nil
        })
```

--------------------------------

### Start Workshop Instance

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Starts a workshop instance by enabling autostart, updating the instance state, and executing a startup command.

```go
func (s *Backend) StartWorkshop(ctx context.Context, name string) error {
        conn, err := s.LxdClient(ctx)
        if err != nil {
                return err
        }
        defer conn.Disconnect()

        // Workshop started, enable autostart
        if err = s.addWorkshopConfig(conn, ctx, name, &workshop.WorkshopConfigValue{Name: "boot.autostart", Value: "true"}); err != nil {
                return err
        }

        if err = s.updateInstanceState(conn, ctx, name, "start", false); err != nil {
                return err
        }

        args := workshop.Execution{
                ExecArgs: workshop.ExecArgs{
                        UserId:  0,
                        GroupId: 0,
                        Command: []string{
                                "bash", "-euc", startCommand,
                        },
                        WorkDir: "/",
                },
        }

        exectx, err := s.execCommand(conn, ctx, name, &args)
        if err != nil {
                return err
        }

        return exectx.WaitExecution(ctx)
}
```

--------------------------------

### Install Local SDK Logic

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles the installation of local SDKs by switching between system and sketch-based SDK directories.

```go
        switch sdkSetup.Name {
        case sdk.System.String():
                return wp.InstallLocalSdk(ctx, sdkSetup.Name, sdkSetup.Revision.String(), system.SystemSdkFs)
        case sdk.Sketch:
                usr, err := workshop.LookupUsername(user)
                if err != nil {
                        return err
                }
                sketchdir := sdk.WorkshopSketchSdkCurrent(usr.HomeDir, project.ProjectId, w)
                return wp.InstallLocalSdk(ctx, sdkSetup.Name, sdkSetup.Revision.String(), os.DirFS(sketchdir))
        default:
                return fmt.Errorf("unknown type of the local SDK")
        }
}
```

--------------------------------

### Install system packages in setup-base

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/build-an-sdk.md

Installs necessary build dependencies using apt-get, which is preconfigured to skip recommendations and auto-confirm.

```shell
apt-get update
apt-get install build-essential cmake ninja-build
```

--------------------------------

### Install Snapcraft and LXD

Source: https://github.com/canonical/workshop/blob/main/docs/contributing/maintenance.md

Install the necessary tools for building and packaging snaps locally.

```console
$ sudo snap install --classic snapcraft
$ sudo snap install --channel=6/stable lxd
```

--------------------------------

### Install Local SDK

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Installs a local SDK by copying metadata and hooks into the workshop filesystem. Uses a reverter to ensure cleanup on failure.

```go
func (w *Workshop) InstallLocalSdk(ctx context.Context, name string, rev string, src fs.FS) error {
        wfs, err := w.Backend.WorkshopFs(ctx, w.Name)
        if err != nil {
                return err
        }
        defer wfs.Close()

        reverter := revert.New()
        defer reverter.Fail()

        // meta: /var/lib/workshop/sdk/<name>/<rev>/meta
        metasrc := filepath.Join("meta", "sdk.yaml")
        metadst := filepath.Join(sdk.SdkRevPath(name, rev), "meta", "sdk.yaml")
        reverter.Add(func() { _ = wfs.RemoveAll(filepath.Dir(metadst)) })

        if err = install(wfs, src, metasrc, metadst, 0644); err != nil {
                return err
        }

        // hooks: /var/lib/workshop/sdk/<name>/<rev>/sdk/hooks
        hooksdir := filepath.Join(sdk.SdkRevPath(name, rev), "sdk", "hooks")
        reverter.Add(func() { _ = wfs.RemoveAll(hooksdir) })

        for _, hook := range []string{"setup-base", "save-state", "restore-state", "check-health"} {
                hooksrc := filepath.Join("hooks", hook)
                hookdst := filepath.Join(hooksdir, hook)

                // Hooks are optional.
                if _, err := src.Open(hooksrc); err != nil {
                        if !osutil.IsDirNotExist(err) {
                                return err
                        }
                        continue
                }

                if err = install(wfs, src, hooksrc, hookdst, 0755); err != nil {
                        return err
                }
        }

        reverter.Success()
        return nil
}
```

--------------------------------

### Initialize SDKs with Versioning

Source: https://github.com/canonical/workshop/blob/main/docs/readme.rst

Examples of initializing projects with default or pinned SDK channels.

```console
workshop init web --sdks node            # latest/stable, the default
workshop init web --sdks node/24/stable  # pinned to the Node.js 24 LTS line
workshop init api --sdks go/1.25/stable  # pinned to the Go 1.25 release line
```

--------------------------------

### Install SDK via Backend Execution

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Installs an SDK by mounting the file and extracting it using tar within the workshop environment.

```go
func (m *SdkManager) doInstallSdk(task *state.Task, tomb *tomb.Tomb) error {
        user, project, w, err := UserProjectWorkshop(task)
        if err != nil {
                return err
        }

        sdkSetup, err := SdkSetup(task)
        if err != nil {
                return err
        }

        ctx, cancel := BackendContext(tomb, user, project.ProjectId)
        defer cancel()

        // The install tasks should hold the lock until the SDK is unpacked in the
        // workshop. There are could be multiple of them reading the file
        // concurrently and, hence, TryLock, so a writer (e.g. DownloadSdk) would
        // not corrupt the file before it is installed.
        fl, err := sdk.OpenLock(sdkSetup.Name)
        if err != nil {
                return err
        }
        if err = fl.TryLock(); err != nil && !errors.Is(err, osutil.ErrAlreadyLocked) {
                return err
        }
        defer fl.Close()

        target := filepath.Join("/root", filepath.Base(sdkSetup.Filename()))
        sdkMount := workshop.Mount{Name: sdkSetup.Name, What: sdkSetup.Filename(), Where: target}
        if err = m.backend.AddWorkshopMount(ctx, w, sdkMount); err != nil {
                return err
        }
        umount := func() {
                // Make sure the SDK file will be unmounted once installed into the workshop
                if err := m.backend.RemoveWorkshopMount(ctx, w, sdkMount.Name); err != nil {
                        logger.Debugf("cannot unmount SDK %q from workshop %q: %v", sdkMount.Name, w, err)
                }
        }
        defer umount()

        // example: /var/lib/workshop/sdk/cuda/712/
        sdkPath := filepath.Join(dirs.WorkshopSdksDir, sdkSetup.Name, sdkSetup.Revision.String())

        // create a memory out/err to log the hook output into the task's log
        var out bytes.Buffer

        // Unpack the SDK to the desired location in the workshop
        //   Note: the following command requires ~ tar >= 1.29 due to --one-top-level
        args := workshop.Execution{
                ExecArgs: workshop.ExecArgs{
                        UserId:  0,
                        GroupId: 0,
                        Command: []string{
                                "tar",
                                "--extract",
                                "--file",
                                target,
                                "--one-top-level=" + sdkPath,
                                "--no-same-owner",
                        },
                        WorkDir: "/",
                },
                ExecControls: workshop.ExecControls{
                        Stdin:  nil,
                        Stdout: nil,
                        Stderr: &out,
                },
        }

        exectx, err := m.backend.Exec(ctx, w, &args)
        if err != nil {
                return err
        }

        if err = exectx.WaitExecution(ctx); err != nil {
                return fmt.Errorf("%w: %v", err, out.String())
        }

        return err
}
```

--------------------------------

### Build and install an SDK

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/build-an-sdk.md

Use this command to pack the SDK and copy it into the try area for testing.

```console
$ sdkcraft try
```

--------------------------------

### Launch Documentation Preview

Source: https://github.com/canonical/workshop/blob/main/docs/contributing/documentation.md

Commands to start the development environment and serve the documentation locally at 127.0.0.1:8000.

```console
$ workshop launch dev
$ workshop run dev docs-run
```

--------------------------------

### Install Workshop

Source: https://github.com/canonical/workshop/blob/main/docs/readme.rst

Install the required LXD dependency and the Workshop snap package.

```console
sudo snap install --channel=6/stable lxd  # skip if LXD is already installed
sudo snap install --classic workshop
```

--------------------------------

### Launch Store SDK Information

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initiates SDK installation actions via the store service, excluding system SDKs.

```go
func launchStoreInfo(st *state.State, ctx context.Context, projectid string, file *workshop.File) ([]sdk.SdkResult, error) {
        sto := sdk.StoreService(st)
        acts := []sdk.SdkAction{}
        for _, sd := range file.Sdks {
                // "system" SDK is bootstrapped and installed by Workshop locally in a
                // separate task.
                if sd.Name == sdk.System.String() {
                        continue
                }
                act := sdk.SdkAction{ProjectId: projectid, Workshop: file.Name, Name: sd.Name, Channel: sd.Channel, Action: sdk.Install}
                acts = append(acts, act)
        }
        res, err := sto.SdkAction(ctx, acts)
        if err != nil {
                return nil, err
        }
        return res, nil
}
```

--------------------------------

### Workshop Start Command Implementation

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the 'start' command using the Cobra framework to activate specified workshops.

```go
package main

import (
        "fmt"

        "github.com/canonical/x-go/strutil"
        "github.com/spf13/cobra"
)

type CmdStart struct {
        waitMixin
        root *CmdRoot
}

func (c *CmdStart) Command() *cobra.Command {
        var cmd = &cobra.Command{
                Use:   "start <WORKSHOP>...",
                Short: "Start one or many workshops",
                Long: `
This command activates the workshops listed as arguments. For each one, it:

- Makes sure the workshop was actually launched

- Activates the workshop for use and sets it to 'Ready'


If multiple workshops are listed and an error occurs,
the operation is aborted and no workshops are started.


Notes:

- If a workshop is already started or wasn't yet launched, an error occurs.

- When interrupted, the command attempts to gracefully revert its actions.

- To stop a started workshop, use 'workshop stop'.
`,
                Example: `
Start the 'nimble' and 'jazzy' workshops in the current project directory:
$ workshop start nimble jazzy

The name is optional if the project has only one workshop:
$ workshop start`,
                RunE: c.Run,
        }

        return cmd
}

func (c *CmdStart) Run(cmd *cobra.Command, av []string) error {
        av = strutil.Deduplicate(av)

        cli, err := c.root.client()
        if err != nil {
                return err
        }

        c.skipAbort = true

        project, err := cli.Project(c.root.project)
        if err != nil {
                return err
        }

        if len(av) == 0 {
                name, err := cli.SingleWorkshopName(project)
                if err != nil {
                        return err
                }
                av = []string{name}
        }

        changeId, err := cli.Start(project.Id, av)
        if err != nil {
                return err
        }

        if _, err := c.wait(cli, changeId); err != nil {
                if err == errNoWait {
                        return nil
                }
                return err
        }

        for _, name := range av {
                fmt.Fprintf(Stdout, "%q started\n", name)
        }

        return nil
}
```

--------------------------------

### Avoided non-imperative installation instruction

Source: https://github.com/canonical/workshop/blob/main/docs/doc-style-guide.md

An example of phrasing to avoid when providing installation instructions.

```default
You can install Workshop with:
```

--------------------------------

### Interface Installation Check

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Validates plugs and slots during installation.

```go
// CheckInterfaces checks whether plugs and slots of sdk are allowed for installation.
func CheckInterfaces(sdkInfo *sdk.Info) error {
	baseDecl := asserts.BuiltinBaseDeclaration()
	if baseDecl == nil {
		return fmt.Errorf("internal error: cannot find base declaration")
	}
```

--------------------------------

### Workshop Start Command Usage

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-start.rst

Displays the general usage syntax for the 'workshop start' command. Use this to understand the expected arguments and flags.

```console
$ workshop start <WORKSHOP>... [flags]
```

--------------------------------

### Start Workshop Operation

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes a workshop by setting a force flag and invoking the backend start method.

```go
func (m *WorkshopManager) doStart(task *state.Task, tomb *tomb.Tomb) error {
        user, project, w, err := UserProjectWorkshop(task)
        if err != nil {
                return err
        }

        ctx, cancel := BackendContext(tomb, user, project.ProjectId)
        defer cancel()

        st := task.State()
        st.Lock()
        task.Set("force", true)
        st.Unlock()

        return m.backend.StartWorkshop(ctx, w)
}
```

--------------------------------

### Mount Installation Logic

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles the installation of workshop mounts, including profile updates and directory creation for host-based mounts.

```go
func installMount(user *user.User, fs workshop.WorkshopFs, dev workshop.Mount) (reload bool, err error) {
        if dev.Type == workshop.WorkshopWorkshop {
                if _, err = fs.Stat(dev.What); err != nil {
                        return false, fmt.Errorf(`stat workshop-source %q: %v`, dev.What, err)
                }

                if _, err = fs.Stat(dev.Where); err != nil {
                        return false, fmt.Errorf(`stat workshop-target %q: %v`, dev.Where, err)
                }

                mounts, err := readMountProfile(fs)
                if err != nil {
                        return false, err
                }

                check := func(me osutil.MountEntry) bool { return me.Name == dev.What && me.Dir == dev.Where }
                if slices.ContainsFunc(mounts.Entries, check) {
                        return false, nil
                }

                entry := osutil.MountEntry{Name: dev.What, Dir: dev.Where, Type: "none", Options: []string{"bind", "x-systemd.requires=/project"}}
                mounts.Entries = append(mounts.Entries, entry)
                if err = writeMountProfile(fs, mounts); err != nil {
                        return false, err
                }
                return true, nil
        }

        if dev.Type == workshop.HostWorkshop {
                // Ensure that the source path exists here. LXD allows to
                // require the source attribute when updating an instance
                // configuration but it would fail and still save changes to the
                // instace profile even if the source does not exist. For
                // Workshop that would mean that the interface connection would
                // fail but there will still be changes made to the instance
                // configuration which is not acceptable.
                // The dir is being dynamically created (no source attribute
                // provided by the slot).
                sourceExists, sourceIsDir, err := osutil.ExistsIsDir(dev.What)
                if err != nil {
                        return false, err
                }

                // We cannot infer what the user intended to mount if the source doesn't
                // exist. In this case - inline with the above - we create a directory.
                if !sourceExists {
                        uid, gid, err := osutil.UidGid(user)
                        if err != nil {
                                return false, err
                        }

                        if err = osutil.MkdirAllChown(dev.What, 0755, uid, gid); err != nil {
                                return false, err
                        }
                }

                if !sourceIsDir {
                        return false, nil
                }
```

--------------------------------

### Install SDKcraft

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-4-craft-sdks.md

Install the SDKcraft snap package using the classic confinement mode.

```console
$ sudo snap install --classic sdkcraft
```

--------------------------------

### Install and enable a systemd service

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/sdks/best-practices.md

Use shell commands to install the service file and manage the systemd unit during the setup-project phase.

```shell
install -D --mode=644 --target-directory ~/.config/systemd/user "$SDK/ollama.service"

systemctl --user daemon-reload
systemctl --user enable --now ollama
```

--------------------------------

### Define Plug Installation Constraints

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Structure and feature checking for plug installation constraints.

```go
// PlugInstallationConstraints specifies a set of constraints on an interface plug relevant to the installation of snap.
type PlugInstallationConstraints struct {
        PlugSdkTypes []string

        PlugNames *NameConstraints

        PlugAttributes *AttributeConstraints
}

func (c *PlugInstallationConstraints) feature(flabel string) bool {
        if flabel == nameConstraintsFeature {
                return c.PlugNames != nil
        }
        return c.PlugAttributes.feature(flabel)
}
```

--------------------------------

### Create Workshop with Go and UV SDKs

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-init.rst

Example of creating a new workshop named 'dev' and including the Go and UV SDKs.

```console
$ workshop init dev --sdks go,uv
```

--------------------------------

### Install dependencies based on detected hardware

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/sdks/best-practices.md

Perform dynamic configuration in setup-project based on variables determined after the workshop has launched.

```shell
case "$GPU_TYPE" in
    nvidia)
        pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu129
        ;;
    amd)
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.4
        ;;
    *)
        pip install torch torchvision torchaudio
        ;;
esac
```

--------------------------------

### Connect Plug to Slot with Target SDK Example

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-connect.rst

Connects the 'mod-cache' plug from the 'nimble/go' SDK to the 'mount' slot within the 'nimble/system' SDK. This example explicitly specifies both the source plug and the target SDK/slot.

```console
$ workshop connect nimble/go:mod-cache nimble/system:mount
```

--------------------------------

### Remount Example: Go SDK Mod-Cache

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-remount.rst

Example of remounting the 'mod-cache' plug for the 'go' SDK in the 'nimble' workshop to a new host path.

```console
$ workshop remount nimble/go:mod-cache ~/new-cache-mount
```

--------------------------------

### Open workshop shell

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Examples for launching the default login shell in a workshop.

```console
$ workshop shell nimble
```

```console
$ workshop shell
```

--------------------------------

### Manage test setup and constants

Source: https://github.com/canonical/workshop/blob/main/docs/coding-style-guide.md

Extract common setup into helper functions while avoiding excessive coupling through shared constants across unrelated tests.

```go
const readyWorkshopJSON = `{
    "name": "dev",
    "status": "Ready"
}`

func (s *testSuite) setupReadyWorkshop(c *check.C) Workshop {
    return Workshop{Name: "dev", Status: "Ready"}
}
```

```go
// Reusing status across unrelated tests
const sharedStatus = "Ready" // Used for both success and error cases
```

--------------------------------

### Configure SDK Lifecycle Tasks

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the sequence of tasks for saving state, installing SDKs, and managing health checks during workshop setup.

```go
                saveStateHook := hookstate.Hook(st, wp.Name, setup.Name, hookstate.SaveState)
                saveStateHook.WaitFor(createStateStorage)

                disconnect := st.NewTask("auto-disconnect", fmt.Sprintf(`Disconnect interfaces of %q SDK`, setup.Name))
                disconnect.Set("sdk", setup.Name)
                disconnect.WaitFor(saveStateHook)
                ts.AddTask(saveStateHook)
                ts.AddTask(disconnect)
        }

        install := sdkstate.InstallLocalSdk(st, setup)
        install.WaitAll(ts)
        ts.AddAll(install)

        setupHook := hookstate.Hook(st, wp.Name, setup.Name, hookstate.SetupBase)
        setupHook.WaitAll(install)
        ts.AddTask(setupHook)

        autoconnect := st.NewTask("auto-connect", fmt.Sprintf("Auto-connect interfaces of %q SDK", setup.Name))
        autoconnect.Set("sdk", setup.Name)
        autoconnect.WaitFor(setupHook)
        ts.AddTask(autoconnect)

        if installed {
                restoreState := hookstate.Hook(st, wp.Name, setup.Name, hookstate.RestoreState)
                restoreState.WaitFor(autoconnect)
                ts.AddTask(restoreState)
        }

        checkHealth := hookstate.Hook(st, wp.Name, setup.Name, hookstate.CheckHealth)
        checkHealth.WaitAll(ts)
        ts.AddTask(checkHealth)

        if installed {
                removeStateStorage := st.NewTask("remove-state-storage", "Remove SDK state storage")
                removeStateStorage.WaitFor(checkHealth)
                ts.AddTask(removeStateStorage)
        }

        for _, task := range ts.Tasks() {
                task.Set("workshop", wp.Name)
                task.Set("project", wp.Project)
        }

        return ts, nil
}
```

--------------------------------

### Install Workshop Script

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Prepares and writes a script to the workshop filesystem, updating execution arguments for the task.

```go
func (m *CommandManager) doInstallScript(task *state.Task, tomb *tomb.Tomb) error {
        user, prj, w, err := UserProjectWorkshop(task)
        if err != nil {
                return err
        }

        ctx, cancel := BackendContext(tomb, user, prj.ProjectId)
        defer cancel()

        var execTask string
        st := task.State()
        st.Lock()
        err = task.Get("exec-task", &execTask)
        st.Unlock()
        if err != nil {
                return fmt.Errorf("cannot get exec task for task %q: %w", task.ID(), err)
        }
        st.Lock()
        argsObj := st.Cached(ExecArgsKey(task.ID()))
        st.Unlock()
        argsOld, ok := argsObj.(*workshop.ExecArgs)
        if !ok || argsOld == nil {
                return fmt.Errorf("cannot get exec args for task %q: task was probably interrupted", task.ID())
        }
        // Shallow copy to avoid modifying original object.
        args := *argsOld

        name := args.Command[0]
        file, err := prj.Workshop(w)
        if err != nil {
                return err
        }

        script, ok := file.Scripts[name]
        if !ok {
                return errors.New("script not found")
        }

        path := filepath.Join(dirs.WorkshopScriptsDir, name)
        command := []string{"bash", "-ue", "-o", "pipefail", path}
        args.Command = append(command, args.Command[1:]...)

        wfs, err := m.backend.WorkshopFs(ctx, w)
        if err != nil {
                return err
        }
        defer wfs.Close()

        if err := wfs.MkdirAll(dirs.WorkshopScriptsDir, 0755); err != nil {
                return err
        }

        err = workshop.AtomicWrite(wfs, path, strings.NewReader(string(script)), 0644)
        if err != nil {
                return err
        }

        st.Lock()
        st.Cache(ExecArgsKey(execTask), &args)
        st.Unlock()

        return nil
}
```

--------------------------------

### Install Workshop CLI

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-1-get-started.md

Installs the Workshop CLI tool using the classic confinement mode.

```console
$ sudo snap install --classic workshop
```

--------------------------------

### Install or Refresh LXD

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-4-craft-sdks.md

Commands to install a fresh instance of LXD or update an existing installation to the required version.

```console
$ sudo snap install --channel=6/stable lxd
```

```console
$ sudo snap refresh --channel=6/stable lxd
```

--------------------------------

### Install Spread testing tool

Source: https://github.com/canonical/workshop/blob/main/docs/contributing/development.md

Commands to clone and install the Spread tool from its repository.

```console
$ git clone https://github.com/canonical/spread
$ cd spread
$ go install ./...
```

--------------------------------

### Define Docker build and user setup

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/sdks/sdk-vs-dockerfile.md

A standard Dockerfile pattern using RUN instructions for system setup and USER for switching to a non-root user for project-specific tasks.

```docker
# System setup as root (≈ setup-base)
RUN apt-get update && apt-get install -y ...

# Switch to non-root user and set up the project (≈ setup-project)
USER appuser
WORKDIR /home/appuser
RUN pip install --user ...
```

--------------------------------

### Install Files to Workshop

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Copies a file from a source filesystem to a destination within the workshop filesystem.

```go
func install(wfs WorkshopFs, srcfs fs.FS, src, dst string, perm fs.FileMode) error {
	dstdir := filepath.Dir(dst)
	if err := wfs.MkdirAll(dstdir, 0755); err != nil {
		return err
	}

	filesrc, err := srcfs.Open(src)
	if err != nil {
		return err
	}
	defer filesrc.Close()

	filedst, err := wfs.OpenFile(dst, os.O_RDWR|os.O_CREATE|os.O_EXCL, perm)
	if err != nil {
		return err
	}
	defer filedst.Close()

	if _, err = io.Copy(filedst, filesrc); err != nil {
		return err
	}
	return nil
}
```

--------------------------------

### Run the daemon using go tool try

Source: https://github.com/canonical/workshop/blob/main/docs/contributing/development.md

Starts the daemon in a temporary session directory with pre-configured environment variables.

```console
$ go tool try
```

--------------------------------

### Agent Interaction Example

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/use-workshops-with-ai-agents.md

Example of an interactive prompt session during the synthesis phase.

```text
Q: Implementation A keeps everything in :file:`app.py`,
   while Implementation B splits out helpers.
   Which layout do you prefer?

A: option B
```

--------------------------------

### Execution Environment Setup

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Manages the execution flow, including environment variable injection and terminal state handling.

```go
func exec(root *CmdRoot, flags *ExecFlags, args *ExecArgs) error {
        if flags.Interactive && flags.NonInteractive {
                return errors.New("'-i' incompatible with '-I'")
        }

        cli, err := root.client()
        if err != nil {
                return err
        }

        project, err := cli.Project(root.project)
        if err != nil {
                return err
        }

        workshop := args.workshop
        if args.implicit {
                workshop, err = cli.SingleWorkshopName(project)
                if err != nil {
                        return err
                }
        }

        if args.script {
                logger.Debugf("Running script %q", args.command)
        } else {
                logger.Debugf("Running %q", args.command)
        }

        // Set up environment variables.
        env := make(map[string]string)
        term, ok := os.LookupEnv("TERM")
        if ok {
                env["TERM"] = term
        }

        for _, kv := range flags.Env {
                parts := strings.SplitN(kv, "=", 2)
                key := parts[0]

                var value string
                if len(parts) == 2 {
                        value = parts[1]
                } else {
                        value, ok = os.LookupEnv(key)
                        if !ok {
                                continue
                        }
                }

                env[key] = value
        }

        stdoutIsTerminal := ptyutil.IsTerminal(unix.Stdout)

        // Specify Interactive=true if -i is given, or if stdin and stdout are TTYs.
        stdinIsTerminal := ptyutil.IsTerminal(unix.Stdin)
        var interactive bool
        if flags.Interactive {
                interactive = true
        } else if flags.NonInteractive {
                interactive = false
        } else {
                interactive = stdinIsTerminal && stdoutIsTerminal
        }

        // Record terminal state (and restore it before we exit).
        if interactive && stdinIsTerminal {
                oldState, err := ptyutil.MakeRaw(unix.Stdin)
                if err != nil {
                        return fmt.Errorf("cannot switch terminal to raw mode: %v", err)
                }
                defer ptyutil.Restore(unix.Stdin, oldState)
        }
```

--------------------------------

### Implement setup-project hook

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/write-runtime-hooks.md

Executes as the workshop user within the project directory for per-project initialization.

```shell
id -u >"$HOME/.dotfiles-uid"
install -m 0644 -t "$HOME" "$SDK/skel/.bash_aliases"
```

--------------------------------

### Package Imports

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Standard imports for the handler setup package.

```go
package handlersetup

import (
	"context"
	"fmt"

	"gopkg.in/tomb.v2"
```

--------------------------------

### Access persistent completion installation help

Source: https://github.com/canonical/workshop/blob/main/cmd/internal/doctemplates/sdk.rst

Command to view instructions for setting up persistent shell completion.

```console
$ sdk completion bash --help
```

--------------------------------

### Implement setup-base hook

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/write-runtime-hooks.md

Executes as root before project mounting to perform system-wide preparation.

```shell
cat <<PROFILE >/etc/profile.d/dotfiles.sh
export DOTFILES_SDK="$SDK"
PROFILE
```

--------------------------------

### Define InstallCandidate and Policy Checks

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Structures for evaluating SDK installation candidates against base declarations and specific slot/plug rules.

```go
type InstallCandidate struct {
        Sdk             *sdk.Info
        BaseDeclaration *asserts.BaseDeclaration
}
```

```go
func (ic *InstallCandidate) checkSlotRule(slot *sdk.SlotInfo, rule *asserts.SlotRule) error {
        if checkSlotInstallationAltConstraints(ic, slot, rule.DenyInstallation) == nil {
                return fmt.Errorf("installation denied by %q slot rule of interface %q", slot.Name, slot.Interface)
        }
        if checkSlotInstallationAltConstraints(ic, slot, rule.AllowInstallation) != nil {
                return fmt.Errorf("installation not allowed by %q slot rule of interface %q", slot.Name, slot.Interface)
        }
        return nil
}
```

```go
func (ic *InstallCandidate) checkPlugRule(plug *sdk.PlugInfo, rule *asserts.PlugRule) error {
        context := ""
        if checkPlugInstallationAltConstraints(ic, plug, rule.DenyInstallation) == nil {
                return fmt.Errorf("installation denied by %q plug rule of interface %q%s", plug.Name, plug.Interface, context)
        }
        if checkPlugInstallationAltConstraints(ic, plug, rule.AllowInstallation) != nil {
                return fmt.Errorf("installation not allowed by %q plug rule of interface %q%s", plug.Name, plug.Interface, context)
        }
        return nil
}
```

```go
func (ic *InstallCandidate) checkSlot(slot *sdk.SlotInfo) error {
        iface := slot.Interface
        if rule := ic.BaseDeclaration.SlotRule(iface); rule != nil {
                return ic.checkSlotRule(slot, rule)
        }
        return nil
}
```

```go
func (ic *InstallCandidate) checkPlug(plug *sdk.PlugInfo) error {
        iface := plug.Interface
        if rule := ic.BaseDeclaration.PlugRule(iface); rule != nil {
                return ic.checkPlugRule(plug, rule)
        }
        return nil
}
```

```go
func (ic *InstallCandidate) Check() error {
        if ic.BaseDeclaration == nil {
                return fmt.Errorf("internal error: improperly initialized InstallCandidate")
        }

        for _, slot := range ic.Sdk.Slots {
                err := ic.checkSlot(slot)
                if err != nil {
                        return err
                }
        }
```

--------------------------------

### Start Services

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Starts services in blocking or non-blocking modes. Note that GlobalUserMode is not supported for these operations.

```go
// Start the given service or services
func (s *systemd) Start(serviceNames ...string) error {
        if s.mode == GlobalUserMode {
                panic("cannot call start with GlobalUserMode")
        }
        _, err := s.systemctl(append([]string{"start"}, serviceNames...)...)
        return err
}

// StartNoBlock starts the given service or services non-blocking
func (s *systemd) StartNoBlock(serviceNames ...string) error {
        if s.mode == GlobalUserMode {
                panic("cannot call start with GlobalUserMode")
        }
        _, err := s.systemctl(append([]string{"start", "--no-block"}, serviceNames...)...)
        return err
}
```

--------------------------------

### Install LXD via snap

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-1-get-started.md

Installs the required LXD dependency using the stable channel.

```console
$ sudo snap install --channel=6/stable lxd
```

--------------------------------

### Define spread test scenario

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/build-an-sdk.md

Example configuration for a spread test suite that verifies successful SDK installation.

```yaml
summary: SDK installs and reports healthy
execute: |
  workshop launch --verbose --wait-on-error
  workshop info | grep -E 'status:\s+okay'
```

--------------------------------

### Daemon Initialization and Listener Setup

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Configures untrusted and HTTP listeners for the daemon and initializes routing.

```go
        if listener, err := netutil.GetListener(d.untrustedSocketPath, listenerMap); err == nil {
                // This listener may also be nil if that socket wasn't among
                // the listeners, so check it before using it.
                d.untrustedListener = &ucrednetListener{Listener: listener}
        } else {
                logger.Debugf("cannot get listener for %q: %v", d.untrustedSocketPath, err)
        }

        d.addRoutes()

        if d.httpAddress != "" {
                listener, err := net.Listen("tcp", d.httpAddress)
                if err != nil {
                        return fmt.Errorf("cannot listen on %q: %w", d.httpAddress, err)
                }
                d.httpListener = listener
                logger.Noticef("HTTP API server listening on %q.", d.httpAddress)
        }

        logger.Noticef("Started daemon.")
        return nil
}
```

--------------------------------

### Command Usage Example

Source: https://github.com/canonical/workshop/blob/main/cmd/internal/doctemplates/command.rst

This snippet shows the basic usage syntax for a command.

```console
$ {{ .Synopsis }}
```

--------------------------------

### Verify Spread installation

Source: https://github.com/canonical/workshop/blob/main/docs/contributing/development.md

Command to display the help message for the installed Spread tool.

```console
$ spread -h
```

--------------------------------

### PlugInstallationConstraints Methods

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for setting constraints on plug installation fields.

```go
func (c *PlugInstallationConstraints) setNameConstraints(field string, cstrs *NameConstraints) {
        switch field {
        case "plug-names":
                c.PlugNames = cstrs
        default:
                panic("unknown PlugInstallationConstraints field " + field)
        }
}

func (c *PlugInstallationConstraints) setAttributeConstraints(field string, cstrs *AttributeConstraints) {
        switch field {
        case "plug-attributes":
                c.PlugAttributes = cstrs
        default:
                panic("unknown PlugInstallationConstraints field " + field)
        }
}

func (c *PlugInstallationConstraints) setIDConstraints(field string, cstrs []string) {
        switch field {
        case "plug-sdk-type":
                c.PlugSdkTypes = cstrs
        default:
                panic("unknown PlugInstallationConstraints field " + field)
        }
}
```

--------------------------------

### Command syntax examples

Source: https://github.com/canonical/workshop/blob/main/docs/doc-style-guide.md

Use these exact command strings when referencing CLI operations.

```default
workshop launch
workshop connect
workshopctl
sdkcraft build
```

--------------------------------

### YAML endpoint configuration

Source: https://github.com/canonical/workshop/blob/main/docs/reference/definition-files/_interfaces/tunnel.md

Examples of quoting endpoints that start with special characters like '[' or '@' in YAML.

```yaml
endpoint: '[::1]:8080/tcp'
endpoint: '@abstract.sock'
```

--------------------------------

### Install Python Dependencies

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-3-sketch-sdks.md

Installing packages inside the interactive Jupyter console.

```console
In [1]: %pip install requests
```

--------------------------------

### Hook Handler Interface and Setup

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the core interface for hook handlers and the configuration structure for hook setups.

```go
package hookstate

import (
	"fmt"
	"regexp"
	"sync"
	"time"

	"github.com/canonical/workshop/internal/overlord/handlersetup"
	"github.com/canonical/workshop/internal/overlord/state"
	"github.com/canonical/workshop/internal/workshop"
)

// Handler is the interface a client must satify to handle hooks.
type Handler interface {
	// Before is called right before the hook is to be run.
	Before() error

	// Done is called right after the hook has finished successfully.
	Done() error

	// Error is called if the hook encounters an error while running.
	// The returned bool flag indicates if the original hook error should be
	// ignored by hook manager.
	Error(hookErr error) (ignoreHookErr bool, err error)
}

// HandlerGenerator is the function signature required to register for hooks.
type HandlerGenerator func(*Context) Handler

type HookSetup struct {
	Workshop    string            `json:"workshop"`
	Sdk         string            `json:"sdk"`
	HookType    WorkshopHookType  `json:"type"`
	Environment map[string]string `json:"environment"`
	Timeout     time.Duration     `json:"timeout"`
	IgnoreError bool              `json:"bool"`
}

type WorkshopHookType int
```

--------------------------------

### Detect hardware for project-specific setup

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/sdks/best-practices.md

Use setup-project for initialization that depends on runtime state, such as auto-connected hardware interfaces.

```shell
GPU_TYPE="none"

if command -v lspci >/dev/null 2>&1; then
    if lspci | grep -i 'NVIDIA' >/dev/null 2>&1; then
        GPU_TYPE="nvidia"
    elif lspci | grep -i 'AMD/ATI' >/dev/null 2>&1; then
        GPU_TYPE="amd"
    elif lspci | grep -i 'Intel.*Graphics' >/dev/null 2>&1; then
        GPU_TYPE="intel"
    fi
fi

echo "Detected GPU: $GPU_TYPE"
```

--------------------------------

### Mounting directories with Docker

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/sdks/sdk-vs-dockerfile.md

Example of manual directory mounting using the standard Docker CLI.

```console
$ docker run --name share-example --entrypoint bash -it \
  -v ~/docker/kit/cache/Kit:/kit/cache:rw \
  -v ~/docker/cache/ov:/root/.cache/ov:rw \
  ...
```

--------------------------------

### Validate Slot Installation Constraints

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Validates slot installation against specific or alternative constraints.

```go
func checkSlotInstallationConstraints(ic *InstallCandidate, slot *sdk.SlotInfo, constraints *asserts.SlotInstallationConstraints) error {
        if err := checkNameConstraints(constraints.SlotNames, slot.Interface, "slot name", slot.Name); err != nil {
                return err
        }

        if err := constraints.SlotAttributes.Check(slot, nil); err != nil {
                return err
        }

        if err := checkSdkType(slot.Sdk, constraints.SlotSdkTypes); err != nil {
                return err
        }
        return nil
}
```

```go
func checkSlotInstallationAltConstraints(ic *InstallCandidate, slot *sdk.SlotInfo, altConstraints []*asserts.SlotInstallationConstraints) error {
        var firstErr error
        // OR of constraints
        for _, constraints := range altConstraints {
                err := checkSlotInstallationConstraints(ic, slot, constraints)
                if err == nil {
                        return nil
                }
                if firstErr == nil {
                        firstErr = err
                }
        }
        return firstErr
}
```

--------------------------------

### Configure system-wide settings with setup-base

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/sdks/best-practices.md

Use setup-base for global environment configuration and system package integration that should be included in workshop snapshots.

```shell
sudo -u workshop mkdir -p /home/workshop/uv-venv

cat <<EOF >> /etc/profile.d/uv.sh
PATH="$SDK/bin:\$PATH"
EOF

"$SDK"/bin/uv generate-shell-completion bash > /etc/bash_completion.d/uv.sh
"$SDK"/bin/uvx --generate-shell-completion bash > /etc/bash_completion.d/uvx.sh

mkdir -p /usr/local/libexec/alternatives

cat << 'EOF' > /usr/local/libexec/alternatives/uv-pip
#!/bin/bash
exec uv pip "$@"
EOF

chmod +x /usr/local/libexec/alternatives/uv-pip
update-alternatives --install /usr/bin/pip pip /usr/local/libexec/alternatives/uv-pip 50
```

--------------------------------

### Get Unix Domain Socket Listener

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Retrieves a listener for a socket path from a map or initializes a new one if necessary. It handles socket cleanup and thread locking during setup.

```go
// GetListener tries to get a listener for the given socket path from
// the listener map, and if it fails it tries to set it up directly.
func GetListener(socketPath string, listenerMap map[string]net.Listener) (net.Listener, error) {
        if listener, ok := listenerMap[socketPath]; ok {
                return listener, nil
        }

        if c, err := net.Dial("unix", socketPath); err == nil {
                c.Close()
                return nil, fmt.Errorf("socket %q already in use", socketPath)
        }

        if err := os.Remove(socketPath); err != nil && !os.IsNotExist(err) {
                return nil, err
        }

        address, err := net.ResolveUnixAddr("unix", socketPath)
        if err != nil {
                return nil, err
        }

        runtime.LockOSThread()
        oldmask := unix.Umask(0111)
        listener, err := net.ListenUnix("unix", address)
        unix.Umask(oldmask)
        runtime.UnlockOSThread()
        if err != nil {
                return nil, err
        }

        logger.Debugf("socket %q was not activated; listening", socketPath)

        return listener, nil
}
```

--------------------------------

### List Revisions for a Specific SDK (Console)

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-revisions.rst

This example demonstrates how to list the available revisions for a particular SDK, such as 'my-sdk', from the store.

```console
$ sdkcraft revisions my-sdk
```

--------------------------------

### Undo SDK Installation

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Cleans up the workshop file system context after an SDK installation task.

```go
func (m *SdkManager) undoInstallSdk(task *state.Task, tomb *tomb.Tomb) error {
        user, project, w, err := UserProjectWorkshop(task)
        if err != nil {
                return err
        }

        ctx, cancel := BackendContext(tomb, user, project.ProjectId)
        defer cancel()

        sdkSetup, err := SdkSetup(task)
        if err != nil {
                return err
        }

        fs, err := m.backend.WorkshopFs(ctx, w)
        if err != nil {
                return err
        }
        defer fs.Close()
```

--------------------------------

### Validate Plug Installation Constraints

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Validates plug installation against specific constraints or a set of alternative constraints.

```go
func checkPlugInstallationConstraints1(ic *InstallCandidate, plug *sdk.PlugInfo, constraints *asserts.PlugInstallationConstraints) error {
        if err := checkNameConstraints(constraints.PlugNames, plug.Interface, "plug name", plug.Name); err != nil {
                return err
        }

        // TODO: allow evaluated attr constraints here too?
        if err := constraints.PlugAttributes.Check(plug, nil); err != nil {
                return err
        }
        if err := checkSdkType(plug.Sdk, constraints.PlugSdkTypes); err != nil {
                return err
        }
        return nil
}
```

```go
func checkPlugInstallationAltConstraints(ic *InstallCandidate, plug *sdk.PlugInfo, altConstraints []*asserts.PlugInstallationConstraints) error {
        var firstErr error
        // OR of constraints
        for _, constraints := range altConstraints {
                err := checkPlugInstallationConstraints1(ic, plug, constraints)
                if err == nil {
                        return nil
                }
                if firstErr == nil {
                        firstErr = err
                }
        }
        return firstErr
}
```

--------------------------------

### Client.Exec

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Starts a command with the given options, returning an ExecProcess representing the running process.

```APIDOC
## Exec(opts *ExecOptions, workshop, projectId string)

### Description
Starts a command or script within a specified workshop and project. Returns an ExecProcess object that can be used to monitor the process.

### Parameters
- **opts** (*ExecOptions) - Required - Configuration options for the execution including command, environment, and timeouts.
- **workshop** (string) - Required - The name of the workshop to run the command in.
- **projectId** (string) - Required - The ID of the project context.

### ExecOptions Fields
- **Workshop** (string) - Required - Name of the workshop.
- **Command** ([]string) - Required - Command and arguments to execute.
- **Script** (bool) - Optional - Treat command as a workshop script.
- **Environment** (map[string]string) - Optional - Environment variables.
- **WorkingDir** (string) - Optional - Working directory (default: /project).
- **UserId** (*int) - Optional - User ID for the process.
- **GroupId** (*int) - Optional - Group ID for the process.
- **Timeout** (time.Duration) - Optional - Execution timeout.
- **Interactive** (bool) - Optional - Use pseudo-terminal for stdin.
- **Width** (int) - Optional - Terminal width.
- **Height** (int) - Optional - Terminal height.
- **Stdin** (io.Reader) - Optional - Input stream.
- **Stdout** (io.Writer) - Optional - Output stream.
- **Stderr** (io.Writer) - Optional - Error stream.
```

--------------------------------

### Create or Load Project Backend Method

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Retrieves a user's project from LXD configuration, tracks the project path, and updates mounts or configuration if the project has moved or is new.

```go
func (s *Backend) CreateOrLoadProject(ctx context.Context, path string) (*workshop.Project, bool, error) {
        client, err := s.LxdClient(ctx)
        if err != nil {
                return nil, false, err
        }
        defer client.Disconnect()

        user, ok := ctx.Value(workshop.ContextUser).(string)
        if !ok {
                return nil, false, fmt.Errorf("context key %s not found", workshop.ContextUser)
        }

        lxdPrj, etag, err := client.GetProject(LxdProjectName(user))
        if err != nil {
                return nil, false, err
        }

        projects, err := readProjects([]byte(lxdPrj.Config["user.workshop.projects"]))
        if err != nil {
                return nil, false, err
        }

        tracker := workshop.ProjectTracker{Projects: projects}
        project, result, err := tracker.Track(path)
        if err != nil {
                return nil, false, err
        }

        if result == workshop.ProjectMoved {
                if err = s.updateProjectMounts(client, ctx, *project); err != nil {
                        return nil, false, err
                }
        }

        if result != workshop.ProjectFound {
                projectsJson, err := saveProjects(tracker.Projects)
                if err != nil {
                        return nil, false, err
                }
                lxdPrj.Config["user.workshop.projects"] = projectsJson
                if err = client.UpdateProject(lxdPrj.Name, lxdPrj.Writable(), etag); err != nil {
                        return nil, false, err
                }
        }

        return project, result == workshop.ProjectAdded, nil
}
```

--------------------------------

### Compile PlugInstallationConstraints

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Compiles plug installation constraints from a definition.

```go
func compilePlugInstallationConstraints(context *subruleContext, cDef constraintsDef) (constraintsHolder, error) {
        plugInstCstrs := &PlugInstallationConstraints{}
        // plug-snap-id is supported here mainly for symmetry with the slot case
        // see discussion there
        err := baseCompileConstraints(context, cDef, plugInstCstrs, []string{"plug-names"}, []string{"plug-attributes"}, []string{"plug-sdk-type"})
        if err != nil {
                return nil, err
        }
        return plugInstCstrs, nil
}
```

--------------------------------

### Define how-to file naming pattern

Source: https://github.com/canonical/workshop/blob/main/docs/doc-style-guide.md

Verb-first naming convention for task-oriented guides.

```default
add-actions.rst
connect-vscode.rst
forward-ports.rst
debug-issues.rst
resolve-plug-conflicts.rst
```

--------------------------------

### Define Workshop Configuration

Source: https://github.com/canonical/workshop/blob/main/docs/readme.rst

Example of a .workshop/dev.yaml file defining the base image, SDKs, and custom actions.

```yaml
# .workshop/dev.yaml
name: dev
base: ubuntu@24.04
sdks:
  - name: opencode
  - name: go
    channel: 1.26/stable
actions:                # add your own
  analyzer: |
    go vet ./...
```

--------------------------------

### Enable user-level systemd service in setup-project

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/build-an-sdk.md

Installs a service unit file and enables it for the current user session without requiring root privileges.

```shell
install -D --mode=644 --target-directory ~/.config/systemd/user \
    "$SDK/<NAME>.service"

systemctl --user daemon-reload
systemctl --user enable --now <NAME>
```

--------------------------------

### Create Workshop with Specific Base Image

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-init.rst

Example of creating a workshop using a specific base image (ubuntu@22.04) for the Go SDK.

```console
$ workshop init dev --sdks go --base ubuntu@22.04
```

--------------------------------

### Backend workshop definition

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/use-multiple-workshops.md

Example configuration for a backend workshop using the go SDK.

```yaml
name: backend
base: ubuntu@22.04
sdks:
  - name: go
    channel: 1.26
actions:
  test: |
    go test ./...
```

--------------------------------

### Undo Local SDK Installation

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Removes a previously installed local SDK from the workshop file system.

```go
func (m *SdkManager) undoInstallLocalSdk(task *state.Task, tomb *tomb.Tomb) error {
        user, project, w, err := UserProjectWorkshop(task)
        if err != nil {
                return err
        }

        sdkSetup, err := SdkSetup(task)
        if err != nil {
                return err
        }

        ctx, cancel := BackendContext(tomb, user, project.ProjectId)
        defer cancel()

        wfs, err := m.backend.WorkshopFs(ctx, w)
        if err != nil {
                return err
        }
        defer wfs.Close()

        return wfs.RemoveAll(sdk.SdkRevPath(sdkSetup.Name, sdkSetup.Revision.String()))
}
```

--------------------------------

### Create Workshop with Specific SDK Channel

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-init.rst

Example of creating a workshop with a specific channel for the Go SDK (1.26/stable).

```console
$ workshop init dev --sdks go/1.26/stable
```

--------------------------------

### Start Single Workshop (Implicit Name)

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-start.rst

Starts the only workshop available in the current project directory when the workshop name is omitted. This is a shortcut for projects with a single workshop.

```console
$ workshop start
```

--------------------------------

### Pack artifacts with sdkcraft

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft.md

Command syntax and examples for creating the final project artifact.

```console
$ sdkcraft pack [--destructive-mode] [--shell | --shell-after] [--debug]
                  [--platform name | --build-for arch] [--output OUTPUT]
```

```console
$ sdkcraft pack
```

```console
$ sdkcraft pack --output dist/
```

--------------------------------

### Initialize a New SDKcraft Project

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-init.rst

Demonstrates the basic command to initialize a new SDKcraft project in the current directory.

```console
$ sdkcraft init
```

--------------------------------

### Setup Workshop SDK Profile

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Configures an LXD profile for a specific SDK, including mounts, SSH agents, and desktop settings.

```go
// Setup creates mount profile specific to a given sdk.
func (b *Backend) Setup(ctx context.Context, sdkInfo sdk.Ref, repo *interfaces.Repository) error {
        s, err := repo.SdkSpecification(ctx, b.Name(), sdkInfo)
        if err != nil {
                return fmt.Errorf("cannot obtain device snippets for workshop %q: %w", sdkInfo.Workshop, err)
        }
        spec := s.(*Specification)

        name := lxdbackend.ProfileName(sdkInfo.ProjectId, sdkInfo.Workshop, sdkInfo.Sdk)
        newp := api.ProfilePut{
                Devices:     spec.devices,
                Config:      spec.config,
                Description: fmt.Sprintf("%q SDK profile for %q workshop", sdkInfo.Sdk, sdkInfo.Workshop),
        }

        conn, err := lxdClient(ctx)
        if err != nil {
                return err
        }
        defer conn.Disconnect()

        fs, err := workshopFs(conn, sdkInfo.ProjectId, sdkInfo.Workshop)
        if err != nil {
                return err
        }
        defer fs.Close()

        uname, ok := ctx.Value(workshop.ContextUser).(string)
        if !ok {
                return fmt.Errorf("context key user not found")
        }
        user, err := workshop.LookupUsername(uname)
        if err != nil {
                return err
        }

        reload := false
        for _, mnt := range spec.Profile.Mounts {
                if reload, err = installMount(user, fs, mnt); err != nil {
                        return err
                }
        }
        if reload {
                err = reloadMounts(conn, sdkInfo.ProjectId, sdkInfo.Workshop)
                if err != nil {
                        return err
                }
        }

        if spec.Profile.Agent != nil {
                err = installSshAgent(fs, *spec.Profile.Agent, sdkInfo.Workshop)
                if err != nil {
                        return err
                }
        }

        if spec.Profile.Desktop != nil {
                err = installDesktop(fs, *spec.Profile.Desktop, spec.User, sdkInfo.Workshop)
                if err != nil {
                        return err
                }
        }
```

--------------------------------

### Manage Operation Start Time

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Retrieves or initializes the operation start time within the state manager.

```go
var err error
	st := se.State()
	st.Lock()
	se.startOfOperationTime, err = se.StartOfOperationTime()
	st.Unlock()
	if err != nil {
		return fmt.Errorf("cannot get start of operation time: %w", err)
	}
	return se.stateEng.StartUp()
}

var timeNow = time.Now

// StartOfOperationTime returns the time when workshop started operating,
// and sets it in the state when called for the first time.
func (m *Overlord) StartOfOperationTime() (time.Time, error) {
	var opTime time.Time
	err := m.State().Get("start-of-operation-time", &opTime)
	if err == nil {
		return opTime, nil
	}
	if err != nil && !errors.Is(err, state.ErrNoState) {
		return opTime, err
	}

	opTime = timeNow()
	m.State().Set("start-of-operation-time", opTime)
	return opTime, nil
}
```

--------------------------------

### Initialize InterfaceManager

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Performs startup operations including security backend initialization, repository setup, and workshop project loading.

```go
func (m *InterfaceManager) StartUp() error {
        m.state.Lock()
        defer m.state.Unlock()
        for _, backend := range allSecurityBackends() {
                if err := backend.Initialize(); err != nil {
                        return err
                }
                if err := m.repo.AddBackend(backend);
                        return err
                }
        }

        for _, iface := range builtin.Interfaces() {
                if err := m.repo.AddInterface(iface); err != nil {
                        return err
                }
        }

        allprojects, err := m.backend.Projects(context.Background())
        if err != nil {
                return err
        }

        for user, projects := range allprojects {

                ctx := context.WithValue(context.Background(), workshop.ContextUser, user)
                for _, project := range projects {
                        pctx := context.WithValue(ctx, workshop.ContextProjectId, project.ProjectId)
                        workshops, err := m.backend.ProjectWorkshops(pctx)
                        if err != nil {
                                logger.Noticef("Cannot load workshops from %q: %v", project.Path, err)
                                continue
                        }
                        for _, workshop := range workshops {
                                // recreate the socket device for every workshop to ensure
                                // workshopctl can function (if the daemon was stopped the
                                // socket will render /deleted)
                                if err := m.recreateInternalMounts(pctx, workshop.Name); err != nil {
                                        logger.Noticef("Cannot create internal mounts for %q workshop: %v", workshop.Name, err)
                                }

                                system, err := workshop.SdkInfo(pctx, sdk.System.String())
                                if err != nil {
                                        continue
                                }
                                if err = m.repo.AddSdk(system); err != nil {
                                        continue
                                }

                                infos, err := workshop.SdkInfos(pctx)
                                if err != nil {
                                        logger.Noticef("Cannot obtain the installed SDKs for %q workshop: %v", workshop.Name, err)
                                        continue
                                }
```

--------------------------------

### Initialize SDK Directory

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-4-craft-sdks.md

Create the project directory and initialize the SDK structure.

```console
$ mkdir ollama/
```

```console
$ cd ollama/
$ sdkcraft init
```

--------------------------------

### sdk info

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdk.md

Retrieve metadata and installation details for a specific SDK.

```APIDOC
## sdk info

### Description
Prints the SDK’s metadata, shows the revisions currently available in the SDK Store, and lists workshops where the SDK is installed.

### Usage
`sdk info <SDK> [flags]`

### Parameters
- **SDK** (string) - Required - The name of the SDK to query.
- **--base** (string) - Optional - Restrict the Store channels to a specific base (e.g., ubuntu@24.04).
- **--arch** (string) - Optional - Show the channels for a specific architecture (e.g., all).
```

--------------------------------

### Launch and inspect workshop

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/connect-vscode.md

Commands to start the workshop and retrieve the hostname required for the VS Code connection.

```console
$ workshop launch
```

```console
$ workshop info

name:      dev
base:      ubuntu@24.04
project:   ~/my-project
hostname:  dev.my-project.wp
...
```

--------------------------------

### Create multiple tracks for an SDK

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-create-track.rst

Example showing how to create two distinct tracks for the 'go' SDK by repeating the --track flag.

```console
$ sdkcraft create-track --track 1.26 --track 1.25 go
```

--------------------------------

### Start workshops

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Activate one or more workshops by name. If only one workshop exists in the project, the name argument is optional.

```console
$ workshop start <WORKSHOP>... [flags]
```

```console
$ workshop start nimble jazzy
```

```console
$ workshop start
```

--------------------------------

### TestSecurityBackend Methods

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for recording setup, removal, and sandbox feature calls using optional callbacks.

```go
// Setup records information about the call and calls the setup callback if one is defined.
func (b *TestSecurityBackend) Setup(context context.Context, sdkInfo sdk.Ref, repo *interfaces.Repository) error {
        b.SetupCalls = append(b.SetupCalls, TestSetupCall{SdkInfo: sdkInfo})
        if b.SetupCallback == nil {
                return nil
        }
        return b.SetupCallback(context, sdkInfo, repo)
}

// Remove records information about the call and calls the remove callback if one is defined
func (b *TestSecurityBackend) Remove(context context.Context, workshop, sdkName string) error {
        b.RemoveCalls = append(b.RemoveCalls, sdkName)
        if b.RemoveCallback == nil {
                return nil
        }
        return b.RemoveCallback(sdkName)
}

func (b *TestSecurityBackend) NewSpecification(user *user.User, pid, sdk string) interfaces.Specification {
        return &Specification{user: user, pid: pid, sdk: sdk}
}

func (b *TestSecurityBackend) SandboxFeatures() []string {
        if b.SandboxFeaturesCallback == nil {
                return nil
        }
        return b.SandboxFeaturesCallback()
}
```

--------------------------------

### Manage sketch SDK

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Examples for editing, ejecting, and stashing sketch SDK definitions.

```console
$ workshop sketch-sdk nimble
```

```console
$ workshop sketch-sdk nimble --eject --name tools
```

```console
$ workshop sketch-sdk nimble --stash
```

--------------------------------

### Retrieve Multiple SDK Infos

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Iterates through installed SDKs to collect their metadata into a map.

```go
func (w *Workshop) SdkInfos(ctx context.Context) (map[string]*sdk.Info, error) {
	var infos = make(map[string]*sdk.Info, len(w.Sdks))
	for _, sdk := range w.Sdks {
		info, err := w.SdkInfo(ctx, sdk.Name)
		if err != nil {
			return nil, err
		}
		infos[info.Name] = info
	}
	return infos, nil
}
```

--------------------------------

### Setup Profiles in InterfaceManager

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Configures SDK backends for a given task and registers cleanup functions using a revert object.

```go
func (m *InterfaceManager) doSetupProfiles(task *state.Task, tomb *tomb.Tomb) error {
        st := task.State()
        st.Lock()
        user, err := handlersetup.User(task.Change())
        st.Unlock()
        if err != nil {
                return err
        }

        var sdks []sdk.Ref
        st.Lock()
        err = task.Get("sdks", &sdks)
        st.Unlock()
        if err != nil {
                return err
        }

        rev := revert.New()
        defer rev.Fail()

        for _, ref := range sdks {
                ctx, cancel := handlersetup.BackendContext(tomb, user, ref.ProjectId)
                defer cancel()
                for _, backend := range m.repo.Backends() {
                        if err := backend.Setup(ctx, ref, m.repo); err != nil {
                                return err
                        }

                        ref := ref
                        backend := backend
                        rev.Add(func() {
                                if err1 := backend.Remove(ctx, ref.Workshop, ref.Sdk); err1 != nil {
                                        logger.Noticef(`On doSetupProfiles: Failed to clean up %q SDK backend setup`, ref.ShortRef())
                                }
                        })
                }
        }
        rev.Success()
        return nil
}
```

--------------------------------

### Verify workshop connections

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/forward-ports.md

List all connections to confirm the manual tunnel setup.

```console
$ workshop connections --all

  INTERFACE  PLUG              SLOT          NOTES
  ...
  tunnel     web/system:caddy  web/go:caddy  manual
```

--------------------------------

### Configure Workshop Client and Process UID

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Sets up the workshop client configuration and demonstrates changing the process UID.

```go
var clientConfig = client.Config{
        // we need the less privileged workshop socket in workshopctl
        Socket: filepath.Join(dirs.WorkshopRunDir, filepath.Base(dirs.SocketPath)+".untrusted"),
}

func main() {
        // Set the user and group IDs to the workshop user
        uid := uint32(1000) // Change this to the workshop UID

        // Change the user IDs for this process
        if err := syscall.Setuid(int(uid)); err != nil {
                fmt.Println("Error setting UID:", err)
                return
        }
```

--------------------------------

### Initialize SDK Sketch

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-3-sketch-sdks.md

Opens the SDK definition file for editing.

```console
$ workshop sketch-sdk
```

--------------------------------

### Undo Setup Profiles in InterfaceManager

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Reverts profile setup by either removing specific SDK backends or setting them up depending on the current state.

```go
func (m *InterfaceManager) undoSetupProfiles(task *state.Task, tomb *tomb.Tomb) error {
        st := task.State()
        user, p, w, err := handlersetup.UserProjectWorkshop(task)
        if err != nil {
                return err
        }

        st.Lock()
        s, err := handlersetup.Sdk(task)
        st.Unlock()
        if err != nil {
                return err
        }

        sdkRef := sdk.Ref{ProjectId: p.ProjectId, Workshop: w, Sdk: s}

        var sdks []sdk.Ref
        st.Lock()
        err = task.Get("sdks", &sdks)
        st.Unlock()
        if err != nil {
                return err
        }

        for _, ref := range sdks {
                ctx, cancel := handlersetup.BackendContext(tomb, user, ref.ProjectId)
                defer cancel()
                for _, backend := range m.repo.Backends() {
                        if ref != sdkRef {
                                if err := backend.Setup(ctx, ref, m.repo); err != nil {
                                        return err
                                }
                        } else {
                                if err := backend.Remove(ctx, w, sdkRef.Sdk); err != nil {
                                        return err
                                }
                        }
                }
        }
        return nil
}
```

--------------------------------

### Get binary directory

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Returns the path to the directory containing the overridden commands.

```go
func (cmd *FakeCmd) BinDir() string {
        return cmd.binDir
}
```

--------------------------------

### Launch and connect cross-workshop tunnels

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/use-multiple-workshops.md

Start the workshops and manually connect the frontend tunnel to the system slot.

```console
$ workshop launch frontend backend
$ workshop connect frontend/node:api
```

--------------------------------

### Configure system PATH in setup-base

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/build-an-sdk.md

Adds the SDK binary directory to the system PATH by creating a profile script in /etc/profile.d/.

```shell
cat <<EOF > /etc/profile.d/<NAME>.sh
export PATH="$SDK/bin:\$PATH"
EOF
```

--------------------------------

### Define a workshop configuration with SDKs

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-3-sketch-sdks.md

Example YAML configuration for a workshop utilizing ollama, jupyter, and system SDKs.

```yaml
name: dev
base: ubuntu@24.04
sdks:
  - name: ollama
    channel: vulkan/stable
  - name: jupyter
  - name: system
    plugs:
      jupyter:
        interface: tunnel
        endpoint: 127.0.0.1:8989
```

--------------------------------

### Workshop shell usage

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Syntax for starting an interactive terminal session.

```console
$ workshop shell [<WORKSHOP>] [flags]
```

--------------------------------

### Frontend workshop definition

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/use-multiple-workshops.md

Example configuration for a frontend workshop using the node SDK.

```yaml
name: frontend
base: ubuntu@24.04
sdks:
  - name: node
    channel: 24
actions:
  build: |
    npm run build
```

--------------------------------

### Start the GitHub runner

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/run-github-actions-locally.md

Initiates the runner client within the workshop environment. Replace the repository placeholder with your specific target.

```console
$ workshop exec ci github-runner --label=workshop <OWNER>[/<REPO>]
```

--------------------------------

### Run the daemon directly

Source: https://github.com/canonical/workshop/blob/main/docs/contributing/development.md

Manually installs and executes the daemon with custom environment variables and directory creation.

```console
$ go install ./cmd/...
$ export WORKSHOP=~/workshop
$ export WORKSHOP_CACHE=~/workshop-cache
$ export WORKSHOP_DEBUG=1
$ workshopd run --create-dirs
```

--------------------------------

### PlugRule Definition

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Structure defining installation and connection rules for a plug.

```go
type PlugRule struct {
        Interface string

        AllowInstallation []*PlugInstallationConstraints
        DenyInstallation  []*PlugInstallationConstraints

        AllowConnection []*PlugConnectionConstraints
        DenyConnection  []*PlugConnectionConstraints

        AllowAutoConnection []*PlugConnectionConstraints
        DenyAutoConnection  []*PlugConnectionConstraints
}
```

--------------------------------

### Launch and execute code within a workshop

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/use-git.md

Start the workshop environment and run commands inside it.

```console
$ workshop launch
```

```go
package main

import "fmt"

func main() {
    fmt.Println("hello, Workshop")
}
```

```console
$ git add . && git commit -m "initial commit"
$ workshop exec dev go build -x main.go
```

--------------------------------

### Launch Jupyter Console

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-3-sketch-sdks.md

Commands to activate the environment and start the Jupyter console.

```console
$ workshop shell
workshop@dev:/project$ source /var/lib/workshop/sdk/jupyter/venv/bin/activate
(jupyter-venv) workshop@dev:/project$ jupyter console

  Jupyter console 6.6.3
  ...
```

--------------------------------

### GET /v1/projects

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Retrieves a list of all available projects.

```APIDOC
## GET /v1/projects

### Description
Retrieves a list of all projects currently available in the system.

### Method
GET

### Endpoint
/v1/projects

### Response
#### Success Response (200)
- **projects** (array) - A list of project objects containing ID and path information.
```

--------------------------------

### Manage Workshop Lifecycle and Configuration

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for creating, removing, starting, and stopping workshops, as well as managing their mounts and configuration settings.

```go
if f.Workshops[projectId] == nil {
			f.Workshops[projectId] = make(map[string]*FakeWorkshop)
		}
		if _, ok := f.Workshops[projectId][file.Name]; ok {
			return errors.New("workshop exists")
		}

		ws := &FakeWorkshop{}
		ws.WorkshopFilesystem, err = NewWorkshopFs(f.BaseDir)
		if err != nil {
			return err
		}
		ws.Workshop = &workshop.Workshop{Backend: f,
			Name:    file.Name,
			Running: false,
			Project: *prj,
			Base:    file.Base,
			File:    file,
		}

		ws.Config = make(map[string]string)
		ws.Config[workshop.ConfigWorkshopSdks] = `{}`
		ws.Devices = make(map[string]map[string]string)

		ws.Sdks = make(map[string]sdk.Setup)
		ws.Profiles = make(map[string]workshop.SdkProfile, 0)

		f.Workshops[projectId][file.Name] = ws
		return nil
}
```

```go
func (f *FakeWorkshopBackend) RemoveWorkshop(ctx context.Context, name string) error {
		user, projectId, err := f.userProject(ctx)
		if err != nil {
			return err
		}

		prj := f.project(user, projectId)

		if _, ok := f.Workshops[prj.ProjectId][name]; !ok {
			return workshop.ErrWorkshopNotLaunched
		}

		delete(f.Workshops[prj.ProjectId], name)
		return nil
}
```

```go
func (s *FakeWorkshopBackend) StartWorkshop(ctx context.Context, name string) error {
		w, err := s.Workshop(ctx, name)
		if err != nil {
			return err
		}
		if w.Running {
			return api.StatusErrorf(http.StatusConflict, "workshop already running")
		}
		w.Running = true
		return nil
}
```

```go
func (s *FakeWorkshopBackend) StopWorkshop(ctx context.Context, name string, force bool) error {
		w, err := s.Workshop(ctx, name)
		if err != nil {
			return err
		}
		w.Running = false
		return nil
}
```

```go
func (f *FakeWorkshopBackend) AddWorkshopMount(ctx context.Context, name string, props workshop.Mount) error {
		_, projectId, err := f.userProject(ctx)
		if err != nil {
			return err
		}
		f.Workshops[projectId][name].Devices[props.Name] = map[string]string{"type": "disk", "source": props.What,
			"path": props.Where}
		return nil
}
```

```go
func (f *FakeWorkshopBackend) RemoveWorkshopMount(ctx context.Context, name string, device string) error {
		_, projectId, err := f.userProject(ctx)
		if err != nil {
			return err
		}
		delete(f.Workshops[projectId][name].Devices, device)
		return nil
}
```

```go
func (f *FakeWorkshopBackend) AddWorkshopConfig(ctx context.Context, name string, item *workshop.WorkshopConfigValue) error {
		_, projectId, err := f.userProject(ctx)
		if err != nil {
			return err
		}
		f.Workshops[projectId][name].Config[item.Name] = item.Value
		return nil
}
```

```go
func (f *FakeWorkshopBackend) RemoveWorkshopConfig(ctx context.Context, name string, key string) error {
		_, projectId, err := f.userProject(ctx)
		if err != nil {
			return err
		}
		delete(f.Workshops[projectId][name].Config, key)
		return nil
}
```

```go
func (f *FakeWorkshopBackend) Workshop(ctx context.Context, name string) (*workshop.Workshop, error) {
		user, projectId, err := f.userProject(ctx)
		if err != nil {
			return nil, err
		}

		project := f.project(user, projectId)
		if project == nil {
			return nil, api.StatusErrorf(404, "project not found")
		}
		wp := f.Workshops[projectId][name]
		if wp == nil {
			return nil, workshop.ErrWorkshopNotLaunched
		}

		var c map[string]sdk.Setup
		if err := json.Unmarshal([]byte(f.Workshops[projectId][name].Config[workshop.ConfigWorkshopSdks]), &c); err != nil {
			return nil, err
		}
		wp.Sdks = c
		return wp.Workshop, nil
}
```

```go
func (f *FakeWorkshopBackend) ProjectWorkshops(ctx context.Context) ([]*workshop.Workshop, error) {
		_, projectId, err := f.userProject(ctx)
		if err != nil {
			return nil, err
		}

		var workshops = make([]*workshop.Workshop, 0)
		for _, i := range f.Workshops[projectId] {
			ws, _ := f.Workshop(ctx, i.Name)
			workshops = append(workshops, ws)
		}
		return workshops, nil
}
```

--------------------------------

### Configure Workshop with Local SDK

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-4-craft-sdks.md

Example YAML configuration to include a locally built SDK in a workshop definition using the try- prefix.

```yaml
name: dev
base: ubuntu@24.04
sdks:
  - name: try-ollama
```

--------------------------------

### Example patch implementation

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

A template for creating new patch functions. Ensure logic is idempotent as it may run multiple times upon failure.

```go
func patch1(s *state.State) error {

        // Here you can have any logic you want manipulating s and the
        // system itself when required to reflect such changes.

        // While working on the patch keep in mind that it may run partially
        // or fully again when a failure occurs, and this will happen until it
        // works completely.
```

--------------------------------

### Install pre-commit hooks

Source: https://github.com/canonical/workshop/blob/main/docs/contributing/development.md

Configure git to run linters automatically on every commit.

```console
$ pre-commit install
```

--------------------------------

### Initialize SFTP Filesystem

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Creates a new workshop filesystem interface using an SFTP connection to a specific LXD instance.

```go
func sftpFs(conn lxd.InstanceServer, pid, w string) (workshop.WorkshopFs, error) {
        sftp, err := conn.GetInstanceFileSFTP(lxdbackend.InstanceName(w, pid))
        if err != nil {
                return nil, err
        }
        return workshop.NewWorkshopFs(sftp), nil
}
```

--------------------------------

### Show SDK metadata

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdk.md

Commands to display SDK metadata, available store channels, and local installation details.

```console
$ sdk info <SDK> [flags]
```

```console
$ sdk info openvino
```

```console
$ sdk info openvino --base ubuntu@24.04
```

```console
$ sdk info openvino --arch all
```

--------------------------------

### Daemon Initialization

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes a new Daemon instance with the provided options.

```go
func New(opts *Options) (*Daemon, error) {
        d := &Daemon{
                workshopDir:         opts.Dir,
                normalSocketPath:    opts.SocketPath,
                untrustedSocketPath: opts.SocketPath + ".untrusted",
                httpAddress:         opts.HTTPAddress,
        }
```

--------------------------------

### Launch project workspace

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/sdks/sdk-vs-dockerfile.md

Demonstrates mounting a project directory into a container versus launching a workshop.

```console
$ docker run -it \
  --mount type=bind,source=/home/user/ros-project,target=/home/ws/src,consistency=cached \
  # ...
```

```console
$ workshop launch ros2jazzy  # must be run in the project directory
```

--------------------------------

### Manage workshop lifecycle

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/use-multiple-workshops.md

Stop, start, or remove workshops individually or in groups.

```console
$ workshop stop frontend
$ workshop start frontend
```

```console
$ workshop stop frontend backend
```

```console
$ workshop remove frontend backend
```

--------------------------------

### Configure Desktop Environment

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Sets up XDG and Qt environment variables for Wayland or X11 sessions.

```go
func installDesktop(fs workshop.WorkshopFs, dev workshop.Desktop, user *user.User, ws string) error {
        env, err := systemd.UserEnvironment(user)
        if err != nil {
                return err
        }

        backend := env["XDG_BACKEND"]

        var envVars map[string]string
        envFile, err := fs.Create(filepath.Join("/etc/profile.d", "desktop"+".sh"))
        if err != nil {
                return fmt.Errorf("cannot configure required environment for %q: %w", ws, err)
        }
        defer envFile.Close()

        // Use Wayland as the default backend in the case where it's unset
        if (backend == "wayland" || backend == "") && dev.Wayland != nil {
                envVars = map[string]string{
                        "QT_QPA_PLATFORM":  "wayland-egl",
                        "XDG_SESSION_TYPE": "wayland",
                        "XDG_BACKEND":      "wayland",
                }
        } else {
                envVars = map[string]string{
                        "QT_QPA_PLATFORM":  "xcb",
                        "XDG_SESSION_TYPE": "x11",
                        "XDG_BACKEND":      "x11",
                }
        }

        if dev.Wayland != nil {
                envVars["WAYLAND_DISPLAY"] = strings.TrimPrefix(dev.Wayland.Listen, "/run/user/1000/")
        }
```

--------------------------------

### Initialize Daemon Listener

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Sets up the daemon's network listener using socket activation.

```go
// Init sets up the Daemon's internal workings.
// Don't call more than once.
func (d *Daemon) Init() error {
	listenerMap, err := netutil.ActivationListeners()
	if err != nil {
		return err
	}

	if listener, err := netutil.GetListener(d.normalSocketPath, listenerMap); err == nil {
		d.generalListener = &ucrednetListener{Listener: listener}
	} else {
		return fmt.Errorf("when trying to listen on %s: %w", d.normalSocketPath, err)
	}
```

--------------------------------

### Execute Command and Handle Signals

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Configures execution options, starts the process, and manages lifecycle events including terminal resizing and signal handling.

```go
// Grab current terminal dimensions.
	var width, height int
	if stdoutIsTerminal {
		var err error
		width, height, err = ptyutil.GetSize(unix.Stdout)
		if err != nil {
			return err
		}
	}

	// TODO: the lack of separate output in LXD exec when executing a command in
	// an interactive mode begets quirky things. Consider this: workshop exec
	// empty -- ls -R / 2>/dev/null Given that the command will be executed in
	// the interactive mode (stdin, stdout both point to the terminal), even if
	// ls produces access errors, those will not be filtered out to null as LXD
	// combines stderr and stdout in the interactive mode.
	opts := &client.ExecOptions{
		Command:     args.command,
		Script:      args.script,
		Environment: env,
		WorkingDir:  flags.WorkingDir,
		UserId:      &flags.UserId,
		GroupId:     &flags.GroupId,
		Interactive: interactive,
		Timeout:     flags.Timeout,
		Width:       width,
		Height:      height,
		Stdin:       Stdin,
		Stdout:      Stdout,
		Stderr:      Stderr,
	}

	// Start the command.
	process, err := cli.Exec(opts, workshop, project.Id)
	if err != nil {
		return err
	}

	// Start the control goroutine to handle signals and window resizing.
	stopControl := make(chan struct{})
	defer close(stopControl)
	sighup := make(chan struct{})
	go execControlHandler(process, interactive, stopControl, sighup)

	finished := make(chan error)
	go func() {
		finished <- process.Wait()
	}()

	// Wait for either the command to finish, or SIGHUP to be received.
	select {
	case err = <-finished:
		switch e := err.(type) {
		case nil:
			return nil
		case *client.ExitError:
			logger.Debugf("Process exited with code %d", e.ExitCode())
			return err
		default:
			return err
		}
	case <-sighup:
		// The \r is because we might be in raw mode, and it moves the cursor
		// back to the start of the line.
		fmt.Fprintf(os.Stderr, "SIGHUP received, exiting\r\n")
		// Exit with exit code 0 in this case (same behaviour as ssh).
		return nil
	}
}
```

--------------------------------

### Define SDK interfaces and connections in workshop.yaml

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/workshops/concepts.md

Example of adding custom slots and plugs to SDKs and explicitly wiring them together within a workshop definition.

```yaml
name: dev
base: ubuntu@24.04
sdks:
  - name: uv
    slots:
      api:
        interface: tunnel
        endpoint: 8000
  - name: jupyter
  - name: system
    plugs:
      app:
        interface: tunnel
        endpoint: 127.0.0.1:8090
connections:
  - plug: jupyter:venv
    slot: uv:venv
  - plug: system:app
    slot: uv:api
```

--------------------------------

### Compile Slot Constraints

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Compiles slot installation and connection constraints from constraint definitions.

```go
func compileSlotInstallationConstraints(context *subruleContext, cDef constraintsDef) (constraintsHolder, error) {
        slotInstCstrs := &SlotInstallationConstraints{}
        err := baseCompileConstraints(context, cDef, slotInstCstrs, []string{"slot-names"}, []string{"slot-attributes"}, []string{"slot-sdk-type"})
        if err != nil {
                return nil, err
        }
        return slotInstCstrs, nil
}

func compileSlotConnectionConstraints(context *subruleContext, cDef constraintsDef) (constraintsHolder, error) {
        slotConnCstrs := &SlotConnectionConstraints{}
        err := baseCompileConstraints(context, cDef, slotConnCstrs, nameConstraints, attributeConstraints, slotIDConstraints)
        if err != nil {
                return nil, err
        }
        normalizeSideArityConstraints(context, slotConnCstrs)
        return slotConnCstrs, nil
}
```

--------------------------------

### Workshop Definition Example

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/move-projects.md

A sample YAML definition for a workshop named 'golang' based on Ubuntu 22.04 with Go 1.26 SDK.

```yaml
name: golang
base: ubuntu@22.04
sdks:
  - name: go
    channel: 1.26
```

--------------------------------

### Main Entry Point

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes the logger and executes the root command for the workshop CLI application.

```go
package main

import (
        "fmt"
        "os"

        "github.com/canonical/workshop/client"
        "github.com/canonical/workshop/internal/logger"
)

func main() {
        cwd, err := os.Getwd()
        if err != nil {
                panic(err)
        }
        l, err := logger.New(Stderr, 0)
        if err != nil {
                panic(err)
        }

        logger.SetLogger(l)

        rootCmd := (&CmdRoot{}).Command(cwd)

        if err = rootCmd.Execute(); err != nil {
                exitError, ok := err.(*client.ExitError)
                if ok {
                        os.Exit(exitError.ExitCode())
                }
                fmt.Fprintf(Stderr, "error: %v\n", err)
                os.Exit(1)
        }
}
```

--------------------------------

### Launch a workshop

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-1-get-started.md

Initializes and launches a workshop environment.

```console
$ workshop launch

  "dev" launched
```

--------------------------------

### Configure Workshop GitHub Action

Source: https://github.com/canonical/workshop/blob/main/docs/release-notes/v0.9.3.md

Example usage of the v1 Launch Workshop GitHub Action, replacing token/version inputs with channel/revision.

```yaml
- uses: canonical/launch-workshop@v1
  with:
    workshop: ${{ matrix.workshop }}
    cache: |
      uv:cache

- run: workshop run "$WS" unit-tests
  env:
    WS: ${{ matrix.workshop }}
```

--------------------------------

### Launch Workshop Tasks

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Orchestrates the creation of a workshop by managing SDK retrieval, apt cache creation, and health check hooks.

```go
func launch(st *state.State, file *workshop.File, sdks []sdk.Setup, project workshop.Project) *state.TaskSet {
        // check and download all the required SDKs
        retrieve := retrieveSdks(st, sdks)

        // create volume to store deb packages
        createAptCache := st.NewTask("create-apt-cache", fmt.Sprintf("Create apt cache for %q", file.Name))

        // create a basic workshop
        create := constructWorkshop(st, file, project)
        create.WaitAll(retrieve)
        create.WaitFor(createAptCache)

        // install the downloaded sdks
        launch := installSdks(st, file.Name, sdks, retrieve)
        launch.WaitAll(create)

        // run a quick check health script (for every SDK, if present)
        checkHealth := checkHealthHooks(st, file)
        checkHealth.WaitAll(launch)
        launch.AddAll(checkHealth)

        all := state.NewTaskSet(retrieve.Tasks()...)
        all.AddAll(retrieve)
        all.AddTask(createAptCache)
        all.AddAll(create)
        all.AddAll(launch)

        for _, task := range all.Tasks() {
                task.Set("workshop", file.Name)
                task.Set("project", project)
        }

        return all
}
```

--------------------------------

### Connect Plug to Slot Example

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-connect.rst

Connects the 'mod-cache' mount interface plug of the 'go' SDK under the 'nimble' workshop. The target slot is specified as ':mount', indicating a slot with the 'mount' interface.

```console
$ workshop connect nimble/go:mod-cache :mount
```

--------------------------------

### Example of Workshop project description

Source: https://github.com/canonical/workshop/blob/main/docs/doc-style-guide.md

A sample text block describing the core functionality of the Workshop tool.

```text
Workshop is a tool for defining and handling ephemeral development environments.

List your dependencies and components in YAML to define an environment. The key pieces of a definition are SDKs, independent but connectable units of functionality created by software publishers and available on the SDK Store. Workshop simplifies experiments with your environment layout.
```

--------------------------------

### Define Exec Command

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Configures the 'exec' command with flags and usage examples for running commands within a workshop.

```go
func (c *CmdExec) Command() *cobra.Command {
        var cmd = &cobra.Command{
                Use:   "exec [flags] [<WORKSHOP>] [--] <COMMAND>...",
                Args:  maybeNameAndCommand,
                Short: shortExecHelp,
                Long:  longExecHelp,
                Example: `
Run the 'go build main.go' command under the 'nimble' workshop
in the current project directory:
$ workshop exec nimble go build main.go

A similar command that sets an environment variable and the working directory:
$ workshop exec --env GO111MODULE=off -w /project nimble go build -x

Run a custom interactive shell:
$ workshop exec -I nimble sh

The name is optional if the project has only one workshop
and a separator is provided:
$ workshop exec -I -- sh

Run a command as root (the default is 'workshop'):
$ workshop exec --uid 0 nimble id`,
                RunE: c.Run,
        }

        cmd.Flags().SortFlags = false
        cmd.Flags().SetInterspersed(false)
        commonVars(cmd.Flags(), &c.flags)

        return cmd
}
```

--------------------------------

### Client Initialization and Lifecycle Hooks

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Manages client instantiation and handles pre-run path resolution and post-run warning summaries.

```go
func (c *CmdRoot) client() (*client.Client, error) {
        if c.cli != nil {
                return c.cli, nil
        }

        cli, err := client.New(&ClientConfig)
        if err == nil {
                c.cli = cli
        } else {
                err = fmt.Errorf("cannot create client: %v", err)
        }

        return cli, err
}

func (c *CmdRoot) preRun(cmd *cobra.Command, args []string) error {
        project, err := filepath.Abs(c.project)
        if err != nil {
                return err
        }
        c.project = project
        return nil
}

func (c *CmdRoot) postRun(cmd *cobra.Command, args []string) {
        if c.cli != nil {
                maybePresentWarnings(c.cli.WarningsSummary())
        }
}
```

--------------------------------

### Run an interactive shell

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Starts an interactive shell session within the specified workshop.

```console
$ workshop exec -I nimble sh
```

--------------------------------

### Launch Workshop

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/use-workshops-with-ai-agents.md

Initialize the workshop environment to allow agents to share resources.

```console
$ workshop launch
```

--------------------------------

### Initialize Project Directory

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/use-workshops-with-ai-agents.md

Create a new project directory and initialize a Git repository to serve as the base for worktrees.

```console
$ mkdir flask-project && cd flask-project
$ git init
```

--------------------------------

### Commit message format

Source: https://github.com/canonical/workshop/blob/main/docs/contributing/development.md

Example of the required commit message structure.

```none
Ensure correct permissions and ownership for the content mounts

 * Work around an LXD issue regarding empty dirs:
   https://github.com/canonical/lxd/issues/12648

 * Ensure the source directory is owned by the user running a workshop.

Links:
- ...
- ...
```

--------------------------------

### Connect Interface Implementation

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles the connection process between a plug and a slot, including attribute retrieval, connection validation, and backend setup.

```go
func (m *InterfaceManager) doConnect(task *state.Task, tomb *tomb.Tomb) error {
        st := task.State()
        st.Lock()
        defer st.Unlock()

        var user string
        err := task.Change().Get("user", &user)
        if err != nil {
                return err
        }

        plugRef, slotRef, err := getPlugAndSlotRefs(task)
        if err != nil {
                return err
        }

        conns, err := getConns(st)
        if err != nil {
                return err
        }

        plug := m.repo.Plug(plugRef.ProjectId, plugRef.Workshop, plugRef.Sdk, plugRef.Name)
        if plug == nil {
                return fmt.Errorf("SDK %q has no plug named %q", plugRef.SdkRef().ShortRef(), plugRef.Name)
        }

        slot := m.repo.Slot(slotRef.ProjectId, slotRef.Workshop, slotRef.Sdk, slotRef.Name)
        if slot == nil {
                return fmt.Errorf("SDK %q has no slot named %q", slotRef.SdkRef().ShortRef(), slotRef.Name)
        }

        var plugDynamicAttrs, slotDynamicAttrs map[string]interface{}
        if err = task.Get("plug-dynamic", &plugDynamicAttrs); err != nil && !errors.Is(err, state.ErrNoState) {
                return err
        }
        if err = task.Get("slot-dynamic", &slotDynamicAttrs); err != nil && !errors.Is(err, state.ErrNoState) {
                return err
        }

        var autoConnect bool
        if err := task.Get("auto", &autoConnect); err != nil && !errors.Is(err, state.ErrNoState) {
                return err
        }

        var delayedSetupProfile bool
        if err := task.Get("delayed-setup-profile", &delayedSetupProfile); err != nil && !errors.Is(err, state.ErrNoState) {
                return err
        }

        rev := revert.New()
        defer rev.Fail()

        cref := &interfaces.ConnRef{PlugRef: plugRef, SlotRef: slotRef}
        conn, err := m.repo.Connect(cref, plug.Attrs, plugDynamicAttrs,
                slot.Attrs, slotDynamicAttrs, connectCheck)
        if err != nil || conn == nil {
                return err
        }

        rev.Add(func() {
                err := m.repo.Disconnect(cref.PlugRef.ProjectId, cref.PlugRef.Workshop, cref.PlugRef.Sdk, cref.PlugRef.Name,
                        cref.SlotRef.ProjectId, cref.PlugRef.Workshop, cref.SlotRef.Sdk, cref.SlotRef.Name)
                if err != nil {
                        logger.Noticef("On doConnect: Cannot revert connection %q", cref.ID())
                }
        })

        if old, ok := conns[cref.ID()]; ok && old.Undesired {
                task.Set("old-conn", old)
        }

        // To setup a profile immediately it needs to be a master plug (i.e. bound
        // to or a completely unbound plug) AND the task must request the setup on
        // the spot and not as part of another task which usually happens with
        // auto-connections.
        if !delayedSetupProfile {
                for _, ref := range []sdk.Ref{conn.Plug.Sdk().Ref(), conn.Slot.Sdk().Ref()} {
                        ctx, cancel := handlersetup.BackendContext(tomb, user, ref.ProjectId)
                        defer cancel()
                        for _, backend := range m.repo.Backends() {
                                if err := backend.Setup(ctx, ref, m.repo); err != nil {
                                        return err
                                }
                        }
                }
        }

        conns[cref.ID()] = &schema.ConnState{
                Interface:        conn.Interface(),
                StaticPlugAttrs:  conn.Plug.StaticAttrs(),
                DynamicPlugAttrs: conn.Plug.DynamicAttrs(),
                StaticSlotAttrs:  conn.Slot.StaticAttrs(),
                DynamicSlotAttrs: conn.Slot.DynamicAttrs(),
                Auto:             autoConnect,
        }
        setConns(st, conns)

        rev.Success()

        return nil
}
```

--------------------------------

### Initialize HTTP Listener and Systemd Notification

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Starts an additional HTTP API listener within a tomb and notifies systemd of readiness.

```go
        if d.httpListener != nil {
                // Start additional HTTP API (currently only GuestOK endpoints are
                // available because the HTTP API has no authentication right now).
                d.tomb.Go(func() error {
                        err := d.serve.Serve(d.httpListener)
                        if err != http.ErrServerClosed && d.tomb.Err() == tomb.ErrStillAlive {
                                return err
                        }
                        return nil
                })
        }

        // notify systemd that we are ready
        systemdSdNotify("READY=1")
        return nil
}
```

--------------------------------

### Check feature availability in PlugRule

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Iterates through installation and connection constraints to determine if a specific feature label is supported.

```go
func (r *PlugRule) feature(flabel string) bool {
        for _, cs := range [][] *PlugInstallationConstraints{r.AllowInstallation, r.DenyInstallation} {
                for _, c := range cs {
                        if c.feature(flabel) {
                                return true
                        }
                }
        }

        for _, cs := range [][] *PlugConnectionConstraints{r.AllowConnection, r.DenyConnection, r.AllowAutoConnection, r.DenyAutoConnection} {
                for _, c := range cs {
                        if c.feature(flabel) {
                                return true
                        }
                }
        }

        return false
}
```

--------------------------------

### Manage workshop state

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-1-get-started.md

Commands to stop and start an existing workshop without destroying or rebuilding it.

```console
$ workshop stop
```

```console
$ workshop start
```

--------------------------------

### Define prerequisites section

Source: https://github.com/canonical/workshop/blob/main/docs/doc-style-guide.md

Use this format to list requirements before starting a procedure.

```restructuredtext
Prerequisites
-------------

Before starting, ensure you have these requirements satisfied:

- LXD 6.8 or later running on the host.

- An Ubuntu One account.
```

--------------------------------

### Initialize Overlord State and Restart Handler

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes the state and applies one-shot migrations before starting the restart handler.

```go
        err = initRestart(s, curBootID, restartHandler)
        if err != nil {
                return nil, err
        }

        // one-shot migrations
        err = patch.Apply(s)
        if err != nil {
                return nil, err
        }
        return s, nil
}

func initRestart(s *state.State, curBootID string, restartHandler restart.Handler) error {
        s.Lock()
        defer s.Unlock()
        return restart.Init(s, curBootID, restartHandler)
}
```

--------------------------------

### Manage SDK Symlinks

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Updates or removes the current SDK symlink based on the provided setup configuration.

```go
if setup, exist := w.Sdks[name]; exist {
		if err = fs.Remove(sdk.SdkCurrentPath(name)); err != nil {
			return err
		}
		if err = fs.Symlink(sdk.SdkRevPath(name, setup.Revision.String()), sdk.SdkCurrentPath(name)); err != nil {
			return err
		}
		return nil
	}

	// No revisions left in the sequence, remove the 'current' link.
	// This will be the case during a launch operation that fails, therefore it's
	// possible for there to be no current revision to remove.
	if err = fs.Remove(sdk.SdkCurrentPath(name)); errors.Is(err, os.ErrNotExist) {
		return nil
	}

	return err
}
```

--------------------------------

### Manage Workshop Actions

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods to start, stop, or remove workshop projects by interacting with the workshopd API.

```go
func (client *Client) Start(projectId string, names []string) (changeId string, err error) {
        return client.doWorkshopAction(projectId, &WorkshopActionSetup{
                Action: "start",
                Names:  names,
        })
}

func (client *Client) Stop(projectId string, names []string) (changeId string, err error) {
        return client.doWorkshopAction(projectId, &WorkshopActionSetup{
                Action: "stop",
                Names:  names,
        })
}

func (client *Client) Remove(projectId string, names []string) (changeId string, err error) {
        return client.doWorkshopAction(projectId, &WorkshopActionSetup{
                Action: "remove",
                Names:  names,
        })
}
```

--------------------------------

### Initialize AtomicFile

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Creates an AtomicFile instance backed by an os.File with specified permissions and ownership.

```go
func NewAtomicFile(filename string, perm os.FileMode, flags AtomicWriteFlags, uid sys.UserID, gid sys.GroupID) (aw *AtomicFile, err error) {
        if flags&AtomicWriteFollow != 0 {
                if fn, err := os.Readlink(filename); err == nil || (fn != "" && os.IsNotExist(err)) {
                        if filepath.IsAbs(fn) {
                                filename = fn
                        } else {
                                filename = filepath.Join(filepath.Dir(filename), fn)
                        }
                }
        }
        // The tilde is appended so that programs that inspect all files in some
        // directory are more likely to ignore this file as an editor backup file.
        //
        // This fixes an issue in apparmor-utils package, specifically in
        // aa-enforce. Tools from this package enumerate all profiles by loading
        // parsing any file found in /etc/apparmor.d/, skipping only very specific
        // suffixes, such as the one we selected below.
        tmp := filename + "." + randutil.RandomString(12) + "~"

        fd, err := os.OpenFile(tmp, os.O_WRONLY|os.O_CREATE|os.O_TRUNC|os.O_EXCL, perm)
        if err != nil {
                return nil, err
        }

        if flags&AtomicWriteChmod != 0 {
                err := fd.Chmod(perm)
                if err != nil {
                        return nil, err
                }
        }

        return &AtomicFile{
                File:    fd,
                target:  filename,
                tmpname: tmp,
                uid:     uid,
                gid:     gid,
        }, nil
}
```

--------------------------------

### SDK State Task Definitions

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Helper functions to create state tasks for SDK retrieval and installation workflows.

```go
package sdkstate

import (
        "fmt"

        "github.com/canonical/workshop/internal/overlord/state"
        "github.com/canonical/workshop/internal/sdk"
)

func Retrieve(st *state.State, s sdk.Setup) *state.Task {
        download := st.NewTask("retrieve-sdk", fmt.Sprintf("Retrieve %q SDK from channel %q", s.Name, s.Channel))
        download.Set("sdk-setup", s)
        return download
}

func InstallLocalSdk(st *state.State, setup sdk.Setup) *state.TaskSet {
        install := st.NewTask("install-local-sdk", fmt.Sprintf("Install %q SDK", setup.Name))
        install.Set("sdk-setup", setup)
        install.Set("sdk-retrieve-task", install.ID())

        link := st.NewTask("link-sdk", fmt.Sprintf("Link %q SDK", setup.Name))
        link.Set("sdk-retrieve-task", install.ID())
        link.WaitFor(install)

        return state.NewTaskSet(install, link)
}

func InstallSystemSdk(st *state.State) *state.TaskSet {
        return InstallLocalSdk(st, sdk.Setup{Name: sdk.System.String(), Revision: sdk.Revision{N: -1}})
}

func Install(st *state.State, sdk string, retrieveId string) *state.TaskSet {
        install := st.NewTask("install-sdk", fmt.Sprintf("Install %q SDK", sdk))
        install.Set("sdk-retrieve-task", retrieveId)

        link := st.NewTask("link-sdk", fmt.Sprintf("Link %q SDK", sdk))
        link.Set("sdk-retrieve-task", retrieveId)
        link.WaitFor(install)
```

--------------------------------

### Implement Test Security Backend

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

A mock security backend structure used for testing, providing callbacks for setup, removal, and sandbox features.

```go
type TestSecurityBackend struct {
        BackendName interfaces.SecuritySystem
        // SetupCalls stores information about all calls to Setup
        SetupCalls []TestSetupCall
        // RemoveCalls stores information about all calls to Remove
        RemoveCalls []string
        // SetupCallback is an callback that is optionally called in Setup
        SetupCallback func(context context.Context, sdkInfo sdk.Ref, repo *interfaces.Repository) error
        // RemoveCallback is a callback that is optionally called in Remove
        RemoveCallback func(sdkName string) error
        // SandboxFeaturesCallback is a callback that is optionally called in SandboxFeatures
        SandboxFeaturesCallback func() []string
}

// TestSetupCall stores details about calls to TestSecurityBackend.Setup
type TestSetupCall struct {
        // SdkInfo is a copy of the sdkInfo argument to a particular call to Setup
        SdkInfo sdk.Ref
}

// Initialize does nothing.
func (b *TestSecurityBackend) Initialize() error {
        return nil
}

// Name returns the name of the security backend.
func (b *TestSecurityBackend) Name() interfaces.SecuritySystem {
        return b.BackendName
}
```

--------------------------------

### Configure Workshop Backend

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Generates cloud-init configuration and LXD container settings, including X11 support via systemd units and NVIDIA runtime detection.

```go
func (s *Backend) workshopConfig(projectId string, userid, groupid string, file *workshop.File) (map[string]string, error) {
        cloudInitConfig := `#cloud-config
users:
  - default
  - name: workshop
    primary_group: workshop
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: adm,cdrom,sudo,dip,plugdev,audio,netdev,lxd,video,render
    shell: /bin/bash
write_files:
- content: |
    # Managed by workshop, do not remove
    [Unit]
    Description=Required for x11 support

    [Path]
    PathChanged=/var/lib/workshop/run/
    Unit=xauth-copy.service

    [Install]
    WantedBy=multi-user.target
  path: /etc/systemd/system/xauth-watch.path
- content: |
    # Managed by workshop, do not remove
    [Unit]
    Description=Required for x11 support; copies Xauthority to /tmp

    [Service]
    Type=simple
    ExecStart=/bin/bash -c 'if [ -f /var/lib/workshop/run/Xauthority/.Xauthority ]; then cp -f /var/lib/workshop/run/Xauthority/.Xauthority /tmp/.Xauthority && chown workshop:workshop /tmp/.Xauthority; fi'

    [Install]
    WantedBy=multi-user.target
  path: /etc/systemd/system/xauth-copy.service
runcmd:
  - systemctl daemon-reload
  - systemctl enable xauth-copy.service
  - systemctl enable --now xauth-watch.path
`

        f, err := yaml.Marshal(file)
        if err != nil {
                return map[string]string{}, err
        }

        cfg := map[string]string{
                "raw.idmap":                fmt.Sprint("uid ", userid, " 1000\ngid ", groupid, " 1000"),
                "security.nesting":         "true",
                "user.workshop.project-id": projectId,
                "user.user-data":           cloudInitConfig,
                "user.workshop.file":       string(f),
                // LXC appears to have a race condition wherein a proxy device mounted in
                // a dynamically created directory has the potential to be 'masked' by this
                // directory. We create an explicit mount for /tmp here (one such dymanic
                // directory) to allow us to mount X11 sockets reliably.
                // See: https://github.com/lxc/lxc/issues/434
                "raw.lxc": "lxc.mount.entry = tmpfs tmp tmpfs defaults",
        }

        nvidiaRuntime, err := checkNvidiaRuntime()
        if err != nil {
                return nil, err
        }

        if nvidiaRuntime {
                // nvidia.* properties must be set at launch as otherwise it requires a
                // container restart to take effect.
                cfg["nvidia.driver.capabilities"] = "all"
                cfg["nvidia.runtime"] = "true"
        }
        return cfg, nil
}
```

--------------------------------

### Check Workshop snap version

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/fix-workshops/fix-installation.md

Verify the currently installed version of the Workshop snap. If outdated, follow upgrade instructions.

```console
$ snap info workshop
```

--------------------------------

### Run Go Build with Environment and Working Directory

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-exec.rst

Executes 'go build -x' in the 'nimble' workshop, setting the 'GO111MODULE' environment variable to 'off' and specifying '/project' as the working directory.

```console
$ workshop exec --env GO111MODULE=off -w /project nimble -- go build -x
```

--------------------------------

### GET /v1/changes

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Fetches information for a list of changes based on provided options.

```APIDOC
## GET /v1/changes

### Description
Fetches information for the changes specified by the query parameters.

### Method
GET

### Endpoint
/v1/changes

### Parameters
#### Query Parameters
- **select** (string) - Optional - The selection criteria (e.g., "in-progress", "ready", "all").
- **workshops** (string) - Optional - Comma-separated list of service names to filter by.
- **project-id** (string) - Optional - The ID of the project to filter by.
```

--------------------------------

### Configure Health Reporting Command

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Setup for the set-health command, including help text and parameter requirements.

```go
var (
        shortHealthHelp = "Report the health status of an SDK"
        longHealthHelp  = `
 The set-health command is called from within a workshop to inform the system of the
 SDK's overall health.
 
 It can be called from any hook. An SDK can
 optionally provide a 'check-health' hook to manage these calls, which is
 then called periodically and with increased frequency while the SDK is
 "waiting". Any health regression will issue a warning to the user.
 
 - status: One of okay, waiting, error.
 
 - error-code: An optional note matching regex '[a-z](?:-?[a-z0-9])+', e.g. missing-cuda; up to 20 symbols.
 
 - message: A user-friendly message expanding the status, 7-70 lines long. Required if the status is 'waiting' or 'error'.
 `
)
```

--------------------------------

### Get SDK Specification

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Generates a specification for a specific SDK and security system, requiring user and project context.

```go
// SdkSpecification returns the specification of a given sdk in a given security system.
func (r *Repository) SdkSpecification(ctx context.Context, securitySystem SecuritySystem, sdkInfo sdk.Ref) (Specification, error) {
	r.m.Lock()
	defer r.m.Unlock()

	var backend SecurityBackend
	for _, b := range r.backends {
		if b.Name() == securitySystem {
			backend = b
			break
		}
	}
	if backend == nil {
		return nil, fmt.Errorf("cannot handle interfaces of %q workshop, security system %q is not known", sdkInfo.Workshop, securitySystem)
	}

	user, ok := ctx.Value(workshop.ContextUser).(string)
	if !ok {
		return nil, fmt.Errorf("internal error: context key %s not found", workshop.ContextUser)
	}

	usr, err := workshop.LookupUsername(user)
	if err != nil {
		return nil, err
	}

	projectId, ok := ctx.Value(workshop.ContextProjectId).(string)
	if !ok {
		return nil, fmt.Errorf("context key project-id not found")
	}

	spec := backend.NewSpecification(usr, projectId, sdkInfo.Sdk)

	key := plugOrSlotKey(sdkInfo.ProjectId, sdkInfo.Workshop, sdkInfo.Sdk)

	// XXX: If either of the AddConnected{Plug,Slot} methods for a connection
	// fail resiliently as-in they can never succeed (such as the case where a
	// bit of policy generated is unable to be used on this system), we may be
	// stuck never able to modify the policy without restarting daemon. This is
	// because the (broken) connection is still left inside the in-memory
	// repository so the next time we try to do any modification to this sdk's
	// plugs or slots, we will try to add that connection again and fail. It is
	// resolved by restarting daemon since we just store the repository in-memory
	// and don't persist new connections until after these bits are successful.
	// We may want to consider removing connections which fail when we try to
	// generate/add policy for them. This may just be a transitory failure
	// however, so maybe the right thing to do is try again, but we don't know
	// if the error is transient so we also don't want to infinitely loop trying
	// to add a connected plug that will never work.
```

--------------------------------

### Handle V1 Get Connections Request

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Processes HTTP requests to retrieve and return workshop connection information.

```go
func v1GetConnections(c *Command, r *http.Request, _ *userState) Response {
        query := r.URL.Query()
        projectId := query.Get("project-id")
        workshop := query.Get("workshop")
        ifaceName := query.Get("interface")
        qselect := query.Get("select")

        if projectId == "" {
                return statusBadRequest("project-id must not be empty")
        }

        if qselect != "all" && qselect != "" {
                return statusBadRequest("unsupported select qualifier")
        }
        onlyConnected := qselect == ""

        if workshop != "" {
                if err := checkWorkshopExists(r.Context(), c.d.overlord.WorkshopManager(), projectId, workshop); err != nil {
                        return statusNotFound("cannot access workshop %q: %w", workshop, err)
                }
        }

        connsjson, err := collectConnections(c.d.overlord.InterfaceManager(), collectFilter{
                projectId: projectId,
                workshop:  workshop,
                ifaceName: ifaceName,
                connected: onlyConnected,
        })
        if err != nil {
                return statusInternalError("collecting connection information failed: %w", err)
        }
        sort.Sort(byCrefConnJSON(connsjson.Established))
        sort.Sort(byCrefConnJSON(connsjson.Undesired))

        return SyncResponse(connsjson, http.StatusOK)
}
```

--------------------------------

### sdkcraft init Command Usage

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-init.rst

Displays the general usage syntax for the 'sdkcraft init' command, including optional flags and the project directory argument.

```console
$ sdkcraft init [--name NAME] [--profile {simple}] [project_dir]
```

--------------------------------

### GET /v1/changes/{id}

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Fetches information about a specific change given its ID.

```APIDOC
## GET /v1/changes/{id}

### Description
Fetches information about a Change given its ID.

### Method
GET

### Endpoint
/v1/changes/{id}

### Parameters
#### Path Parameters
- **id** (string) - Required - The unique identifier of the change.
```

--------------------------------

### Refresh LXD via snap

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-1-get-started.md

Updates an existing LXD installation to the stable channel.

```console
$ sudo snap refresh --channel=6/stable lxd
```

--------------------------------

### Initialize Client and Websocket

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Configures the client transport based on the base URL and sets up websocket dialing.

```go
if config.BaseURL == "" {
				// By default talk over a unix socket.
				transport = &http.Transport{DialContext: unixDialer(config.Socket), DisableKeepAlives: config.DisableKeepAlive}
				baseURL := url.URL{Scheme: "http", Host: "localhost"}
				client = &Client{baseURL: baseURL}
			} else {
				// Otherwise talk regular HTTP-over-TCP.
				baseURL, err := url.Parse(config.BaseURL)
				if err != nil {
					return nil, fmt.Errorf("cannot parse base URL: %v", err)
				}
				transport = &http.Transport{DisableKeepAlives: config.DisableKeepAlive}
				client = &Client{baseURL: *baseURL}
			}

			client.doer = &http.Client{
				Transport: transport,
				CheckRedirect: func(req *http.Request, via []*http.Request) error {
					return http.ErrUseLastResponse
				},
			}
			client.userAgent = config.UserAgent
			client.getWebsocket = func(url string) (clientWebsocket, error) {
				return getWebsocket(transport, url)
			}

			return client, nil
}

func (client *Client) getTaskWebsocket(taskID, websocketID string) (clientWebsocket, error) {
		url := fmt.Sprintf("ws://localhost/v1/tasks/%s/websocket/%s", taskID, websocketID)
		return client.getWebsocket(url)
}

func getWebsocket(transport *http.Transport, url string) (clientWebsocket, error) {
		dialer := websocket.Dialer{
			NetDialContext:   transport.DialContext,
			Proxy:            transport.Proxy,
			TLSClientConfig:  transport.TLSClientConfig,
			HandshakeTimeout: 5 * time.Second,
		}
		conn, resp, err := dialer.Dial(url, nil)
		if errors.Is(err, websocket.ErrBadHandshake) {
			// FIXME: gorilla truncates the response body to 1024 characters.
			// If parsing fails, the real error should appear in the server logs.
			return conn, parseError(resp)
		}
		logger.Debugf("response: %v", resp)
		return conn, err
}
```

--------------------------------

### Execute workshop remount commands

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/add-mounts.md

Commands to refresh, stop, remount, and start the workshop to apply host directory changes.

```console
$ workshop refresh
$ workshop stop dev
$ workshop remount dev/uv:shared ~/datasets
$ workshop start dev
```

--------------------------------

### Initialize a new workshop

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Creates a new workshop definition file in the .workshop/ directory.

```console
$ workshop init <NAME> --sdks <SDKs> [--base <BASE>] [flags]
```

```console
$ workshop init dev --sdks go,uv
```

```console
$ workshop init dev --sdks go/1.26/stable
```

```console
$ workshop init dev --sdks go --base ubuntu@22.04
```

--------------------------------

### Manage persistent state with Get and Set

Source: https://github.com/canonical/workshop/blob/main/docs/coding-style-guide.md

Use state.Get and state.Set for data that must persist across application restarts.

```go
import "github.com/canonical/workshop/internal/overlord/state"

// Store persistent data that survives restarts
func saveConnectionState(st *state.State) error {
    conns := map[string]any{
        "workshop/sdk:plug": "workshop/system:slot",
    }
    st.Set("conns", conns)
    return nil
}

// Retrieve persistent data
func loadConnectionState(st *state.State) (map[string]any, error) {
    var conns map[string]any
    err := st.Get("conns", &conns)
    if err != nil && err != state.ErrNoState {
        return nil, err
    }
    return conns, nil
}
```

--------------------------------

### Launch workshop

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/fix-workshops/resolve-plug-conflicts.md

Command to launch the workshop after configuring plug bindings.

```console
$ workshop launch digits
```

--------------------------------

### Workshop CLI help strings

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Help text definitions for the exec, shell, and run subcommands.

```go
var shortExecHelp = "Run a command and wait for it to complete"
var longExecHelp = `
The 'exec' subcommand runs an arbitrary command in the specified workshop,
waiting for it to complete. If a timeout elapses before that, it's terminated.

To accept an 'exec' command, the workshop must be 'Ready' or 'Pending'.
A command can run in two modes that determine how it handles standard streams:

- Interactively (for shell sessions)

- Non-interactively (for scripts)


To set the mode explicitly, use '-i' or '-I'. If neither is supplied,
'exec' deduces the mode based on the nature of its own streams:

- If stdin and stdout are terminals, the mode is interactive

- Otherwise, it's non-interactive


To separate the 'exec' subcommand from the command itself,
use shell syntax such as *--*:

  $ workshop exec nimble -- echo -n foo bar

This syntax is required if the workshop name is omitted.

Notes:

- To start a workshop before running commands in it, use 'workshop start'.

- You can set the working directory, environment variables, user and group ID
  for running the command in the workshop; reasonable defaults are provided.
`

var shortShellHelp = "Start an interactive terminal session for the workshop"
var longShellHelp = `
The 'shell' subcommand runs an interactive terminal session
in the specified workshop.

To accept a 'shell' command, the workshop must be 'Ready' or 'Pending'.


Notes:

- To start a workshop before running a terminal session, use 'workshop start'.

- The subcommand is a shorthand for 'workshop exec';
  it launches the login shell for 'workshop',
  the default non-privileged user in a workshop.
`

var shortRunHelp = "Run a workshop script and wait for it to complete"
var longRunHelp = `
The 'run' subcommand runs a script specified in the workshop definition file,
waiting for it to complete. If a timeout elapses before that, it's terminated.
`
```

--------------------------------

### Commit Message Format

Source: https://github.com/canonical/workshop/blob/main/docs/contributing/documentation.md

Example of the required commit message prefix for documentation-related changes.

```none
Doc[chore]: Align references
```

--------------------------------

### Initialize an SDKcraft project

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft.md

Creates an sdkcraft.yaml configuration file along with necessary hooks and tests in the specified directory.

```console
$ sdkcraft init [--name NAME] [--profile {simple}] [project_dir]
```

```console
$ sdkcraft init
```

--------------------------------

### Define workshop actions in YAML

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/workshops/concepts.md

Example configuration for a workshop definition including multiple utility actions for a Go development environment.

```yaml
name: dev
base: ubuntu@24.04
sdks:
  - name: go
    channel: 1.26
actions:
  lint: |
    golangci-lint run  --out-format=colored-line-number -c .golangci.yaml
  shellcheck: |
    git ls-files | file --mime-type -Nnf- | grep shellscript | cut -f1 -d: | xargs shellcheck --check-sourced --external-sources
  unit: |
    go test "$@" ./...
  cover: |
    go test ./... -coverprofile=coverage.out
    go tool cover -html=coverage.out
```

--------------------------------

### Acknowledge Global Warnings

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-okay.rst

This example demonstrates how to acknowledge globally registered warnings across all workshops. Ensure 'workshop warnings' has been run previously.

```console
$ workshop okay
```

--------------------------------

### Run Custom Interactive Shell

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-exec.rst

Starts an interactive shell ('sh') within the 'nimble' workshop, forcing interactive mode.

```console
$ workshop exec -I nimble sh
```

--------------------------------

### Get Plug and Slot References

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Retrieves plug and slot references from a task state.

```go
func getPlugAndSlotRefs(task *state.Task) (interfaces.PlugRef, interfaces.SlotRef, error) {
        var plugRef interfaces.PlugRef
        var slotRef interfaces.SlotRef
        if err := task.Get("plug", &plugRef); err != nil {
                return plugRef, slotRef, err
        }
        if err := task.Get("slot", &slotRef); err != nil {
                return plugRef, slotRef, err
        }
        return plugRef, slotRef, nil
}
```

--------------------------------

### Define CLI help strings

Source: https://github.com/canonical/workshop/blob/main/docs/coding-style-guide.md

Use concise, single-spaced strings for CLI help documentation.

```go
// Good: Single spaces, concise
Short: "Launch a new workshop",
Long: `Launch creates and starts a workshop. The workshop will be based on the configuration in workshop.yaml.`,

// Avoid: Multiple spaces or verbose explanations
Short: "Launch  a  new  workshop",
Long: `This command will launch a new workshop. It will create the workshop based on the configuration...`
```

--------------------------------

### Execute Debug Actions

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods to send POST or GET debug actions to the server.

```go
type debugAction struct {
        Action string      `json:"action"`
        Params interface{} `json:"params,omitempty"`
}

// DebugPost sends a POST debug action to the server with the provided parameters.
func (client *Client) DebugPost(action string, params interface{}, result interface{}) error {
        body, err := json.Marshal(debugAction{
                Action: action,
                Params: params,
        })
        if err != nil {
                return err
        }

        _, err = client.doSync("POST", "/v1/debug", nil, nil, bytes.NewReader(body), result)
        return err
}

// DebugGet sends a GET debug action to the server with the provided parameters.
func (client *Client) DebugGet(action string, result interface{}, params map[string]string) error {
        urlParams := url.Values{"action": []string{action}}
        for k, v := range params {
                urlParams.Set(k, v)
        }
        _, err := client.doSync("GET", "/v1/debug", urlParams, nil, nil, &result)
        return err
}
```

--------------------------------

### Install Debian packages via hooks

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/sdks/best-practices.md

Use this approach for system-level dependencies to ensure security updates and leverage local package caches.

```shell
apt-get update
apt-get install ros-dev-tools
apt-get install python3-colcon-argcomplete python3-colcon-alias python3-colcon-clean python3-colcon-mixin
# ...
```

--------------------------------

### Enable shell completion

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdk.md

Commands to enable shell completion for Bash, Zsh, and Fish, or view help for persistent installation.

```console
$ source <(sdk completion bash)
```

```console
$ source <(sdk completion zsh)
```

```console
$ sdk completion fish | source
```

```console
$ sdk completion bash --help
```

--------------------------------

### Check Workshop snap logs

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/fix-workshops/fix-installation.md

Review the snap's logs for troubleshooting before diving into individual workshop debugging guides.

```console
$ sudo snap logs workshop
```

--------------------------------

### Basic workshop launch command

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-launch.rst

Use this command to construct one or more workshops by listing their names as arguments. The command checks definitions, retrieves components, runs SDK hooks, and ties the workshop to the project.

```console
$ workshop launch <WORKSHOP>... [flags]
```

--------------------------------

### Initialize a Workshop Project

Source: https://github.com/canonical/workshop/blob/main/docs/readme.rst

Create a new workshop definition in the current directory using specified SDKs.

```console
workshop init dev --sdks opencode,go/1.26/stable
```

--------------------------------

### Manage Mount Unit Lifecycle

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Functions to add, enable, start, and remove systemd mount units, including daemon-reload synchronization.

```go
func (s *systemd) AddMountUnitFile(snapName, revision, what, where, fstype string) (string, error) {
        daemonReloadLock.Lock()
        defer daemonReloadLock.Unlock()

        options := []string{"nodev"}
        if fstype == "squashfs" {
                newFSType, newOptions, err := squashfs.FSType()
                if err != nil {
                        return "", err
                }
                options = append(options, newOptions...)
                fstype = newFSType
        }
        if osutil.IsDir(what) {
                options = append(options, "bind")
                fstype = "none"
        }

        c := fmt.Sprintf(`[Unit]
Description=Mount unit for %s, revision %s
Before=snapd.service

[Mount]
What=%s
Where=%s
Type=%s
Options=%s

[Install]
WantedBy=multi-user.target
`, snapName, revision, what, where, fstype, strings.Join(options, ","))

        mu := MountUnitPath(where)
        mountUnitName, err := filepath.Base(mu), osutil.AtomicWriteFile(mu, []byte(c), 0644, 0)
        if err != nil {
                return "", err
        }

        // we need to do a daemon-reload here to ensure that systemd really
        // knows about this new mount unit file
        if err := s.daemonReloadNoLock(); err != nil {
                return "", err
        }

        if err := s.Enable(mountUnitName); err != nil {
                return "", err
        }
        if err := s.Start(mountUnitName); err != nil {
                return "", err
        }

        return mountUnitName, nil
}

func (s *systemd) RemoveMountUnitFile(mountedDir string) error {
        daemonReloadLock.Lock()
        defer daemonReloadLock.Unlock()

        unitNamePath := mountedDir
        if s.rootDir != "" {
                rel, err := filepath.Rel(s.rootDir, mountedDir)
                if err != nil || strings.HasPrefix(rel, "..") {
                        return fmt.Errorf("mount unit file not inside root dir %q", mountedDir)
                }
                unitNamePath = "/" + rel
        }

        unit := MountUnitPath(unitNamePath)
        if !osutil.FileExists(unit) {
                return nil
        }

        // use umount -d (cleanup loopback devices) -l (lazy) to ensure that even busy mount points
        // can be unmounted.
        // note that the long option --lazy is not supported on trusty.
        // the explicit -d is only needed on trusty.
        isMounted, err := osutil.IsMounted(mountedDir)
        if err != nil {
                return err
        }
        if isMounted {
                if output, err := exec.Command("umount", "-d", "-l", mountedDir).CombinedOutput(); err != nil {
                        return osutil.OutputErr(output, err)
                }

                if err := s.Stop(filepath.Base(unit), time.Duration(1*time.Second)); err != nil {
                        return err
                }
        }
        if err := s.Disable(filepath.Base(unit)); err != nil {
                return err
        }
        if err := os.Remove(unit); err != nil {
                return err
        }
        // daemon-reload to ensure that systemd actually really
        // forgets about this mount unit
        if err := s.daemonReloadNoLock(); err != nil {
                return err
        }

        return nil
}
```

--------------------------------

### Define slot rule structure

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Data structure representing installation and connection rules for a slot.

```go
// SlotRule holds the rule of what is allowed, wrt installation and
// connection, for a slot of a specific interface for a SDK.
type SlotRule struct {
        Interface string

        AllowInstallation []*SlotInstallationConstraints
        DenyInstallation  []*SlotInstallationConstraints

        AllowConnection []*SlotConnectionConstraints
        DenyConnection  []*SlotConnectionConstraints

        AllowAutoConnection []*SlotConnectionConstraints
        DenyAutoConnection  []*SlotConnectionConstraints
}
```

--------------------------------

### Define a workshop with in-project SDK and plug binding

Source: https://github.com/canonical/workshop/blob/main/docs/reference/definition-files/workshop-definition.md

Configuration demonstrating an in-project SDK and a plug binding between SDKs.

```yaml
name: go-dev
base: ubuntu@22.04
sdks:
  - name: go
    channel: edge
  - name: project-cache
    plugs:
      data:
        bind: go:mod-cache
```

--------------------------------

### Initialize LXD Client

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Connects to the LXD Unix socket and initializes the project context for the authenticated user.

```go
func (s \*Backend) LxdClient(ctx context.Context) (lxd.InstanceServer, error) {
        user, ok := ctx.Value(workshop.ContextUser).(string)
        if !ok {
                return nil, fmt.Errorf("context key %s not found", workshop.ContextUser)
        }

        if srv, err := lxd.ConnectLXDUnixWithContext(ctx, LxdSock, nil); err != nil {
                return nil, err
        } else {
                if err = InitLxdProject(srv, user); err != nil {
                        return nil, err
                }
                return srv.UseProject(LxdProjectName(user)), nil
        }
}
```

--------------------------------

### Update state during patch application

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Example of checking and updating a state value during a patch process.

```go
var something string
        err := s.Get("something-in-test", &something)
        if err == nil && something == "old" {
                s.Set("something-in-test", "new")
        }

        return nil
```

--------------------------------

### En dash usage examples

Source: https://github.com/canonical/workshop/blob/main/docs/doc-style-guide.md

Use en dashes for ranges or connections between related items.

```default
pages 10–15
East–West traffic
Ubuntu 22.04–24.04
```

--------------------------------

### Define Custom Device Interface in Workshop

Source: https://github.com/canonical/workshop/blob/main/docs/release-notes/v0.9.1.md

Example of how to define a new 'custom-device' interface in a Workshop snap configuration. Specify the interface name and the subsystem it interacts with.

```yaml
plugs:
  <NAME>:
    interface: custom-device
    subsystem: <SUBSYSTEM>   # e.g. accel or input
```

--------------------------------

### Initialize a Git repository and workshop definition

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/use-git.md

Create a new Git repository and define the workshop configuration in a YAML file.

```console
$ git init original
$ cd original/
```

```yaml
name: dev
base: ubuntu@22.04
sdks:
  - name: go
    channel: 1.26
```

--------------------------------

### Configure workshop for GitHub Actions

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/run-github-actions-locally.md

Add the github-runner SDK to your workshop definition to install the necessary runner client and helper scripts.

```yaml
name: ci
base: ubuntu@24.04
sdks:
  - name: github-runner
```

--------------------------------

### Follow Godoc conventions

Source: https://github.com/canonical/workshop/blob/main/docs/coding-style-guide.md

Exported functions and types must have comments that start with the name of the element.

```go
// Workshop represents a development environment.
type Workshop struct { ... }

// Launch creates and starts a new workshop with the given configuration.
func Launch(cfg *Config) (*Workshop, error) { ... }
```

```go
// Represents a development environment.
type Workshop struct { ... }

// Creates and starts a workshop.
func Launch(cfg *Config) (*Workshop, error) { ... }
```

--------------------------------

### Create State Hooks

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Generates a set of tasks for executing state hooks, ensuring they only run for installed SDKs and execute sequentially.

```go
func createStateHooks(st \*state.State, w string, sdks \[\]sdk.Setup, newSdks \[\]workshop.SdkRecord, hooktype hookstate.WorkshopHookType) \*state.TaskSet {
        stateHooks := state.NewTaskSet(\[\]\*state.Task{}...)
        prevRestore := (\*state.Task)(nil)
        for \_, newsdk := range newSdks {
                // the state hooks will only be set for the SDKs that were installed AND
                // were not removed from the workshop file at the time of refresh
                if slices.IndexFunc(sdks, func(s sdk.Setup) bool { return s.Name == newsdk.Name }) == -1 {
                        continue
                }
                stateHook := hookstate.Hook(st, w, newsdk.Name, hooktype)
                stateHooks.AddTask(stateHook)
                if prevRestore != nil {
                        stateHook.WaitFor(prevRestore)
                }
                prevRestore = stateHook
        }
        return stateHooks
}
```

--------------------------------

### Start and Stop Multiple Workshops

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods to initiate or terminate multiple workshops by verifying their current status and creating corresponding task sets.

```go
func (w *WorkshopManager) StartMany(ctx context.Context, names []string, projectId string, opChangeId string) ([]*state.TaskSet, error) {
        // check if all the workshops are stopped
        for _, name := range names {
                err := w.CheckStatus(
                        ctx,
                        name,
                        projectId,
                        []healthstate.Status{healthstate.StoppedStatus})
                if err != nil {
                        return nil, fmt.Errorf("cannot start %q: %w", name, err)
                }
        }

        project, err := w.loadProject(ctx, projectId)
        if err != nil {
                return nil, err
        }
        taskset, err := startMany(w.state, names, *project)
        if err != nil {
                return nil, err
        }
        return taskset, nil
}

func startMany(st *state.State, names []string, project workshop.Project) ([]*state.TaskSet, error) {
        taskset := []*state.TaskSet{}

        for _, name := range names {
                start := st.NewTask("start-workshop", fmt.Sprintf("Start %q workshop", name))
                start.Set("workshop", name)
                start.Set("project", project)

                taskset = append(taskset, state.NewTaskSet(start))
        }

        return taskset, nil
}

func (w *WorkshopManager) StopMany(ctx context.Context, names []string, projectId string, opChangeId string) ([]*state.TaskSet, error) {
        for _, name := range names {
                err := w.CheckStatus(
                        ctx,
                        name,
                        projectId,
                        []healthstate.Status{healthstate.ReadyStatus, healthstate.StoppedStatus})
                if err != nil {
                        return nil, fmt.Errorf("cannot stop %q: %w", name, err)
                }
        }

        project, err := w.loadProject(ctx, projectId)
        if err != nil {
                return nil, err
        }
        taskset, err := stopMany(w.state, names, *project)
        if err != nil {
                return nil, err
        }
        return taskset, nil
}

func stopMany(st *state.State, names []string, project workshop.Project) ([]*state.TaskSet, error) {
        taskset := []*state.TaskSet{}

        for _, name := range names {
                stop := st.NewTask("stop-workshop", fmt.Sprintf("Stop %q workshop", name))
                stop.Set("force", false)
                stop.Set("workshop", name)
                stop.Set("project", project)

                taskset = append(taskset, state.NewTaskSet(stop))
        }

        return taskset, nil
}
```

--------------------------------

### Configure X11 Environment Variables

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Sets up DISPLAY and XAUTHORITY environment variables for X11 applications and writes them to an export file.

```go
        if dev.X11 != nil {
                envVars["DISPLAY"] = ":" + strings.TrimPrefix(filepath.Base(dev.X11.Listen), "X")
        }

        // The .Xauthority cookie contains a 128bit key used to authenticate consumers
        // of the X11 socket. It is generated on each boot with a random suffix,
        // because of this we need to ensure there exists a consistently-named copy
        // of the cookie for the LXC profile. There are two cases where we need to
        // copy the cookie, one is on workshopd startup as we iterate through the
        // list of projects, the other is on connect because this could be the first
        // workshop launched, in which case the user would not have had a project. We
        // handle it here for the connect, presence of the copied cookie after reboot
        // is the responsibility of the interface manager.
        xauth := env["XAUTHORITY"]
        if xauth != "" {
                envVars["XAUTHORITY"] = "/tmp/.Xauthority"
                if err := x11.MigrateXauthority(user, xauth); err != nil {
                        logger.Noticef("cannot migrate Xauthority file for user %s, X11 applications may not work: %v", user.Username, err)
                }
        }

        envVars["ELECTRON_OZONE_PLATFORM_HINT"] = "auto"

        for key, val := range envVars {
                _, err = envFile.WriteString("export " + key + "=" + val + "\n")
                if err != nil {
                        return fmt.Errorf("cannot set %s for %q: %w", key, ws, err)
                }
        }

        return nil
}
```

--------------------------------

### Workshop Init Command Usage

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-init.rst

Basic syntax for the 'workshop init' command, specifying the workshop name and SDKs.

```console
$ workshop init <NAME> --sdks <SDKs> [--base <BASE>] [flags]
```

--------------------------------

### Show OpenVINO SDK for All Architectures

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdk-info.rst

Displays the available SDK Store channels for every supported architecture. Use the '--arch all' flag to see compatibility across different system architectures.

```console
$ sdk info openvino --arch all
```

--------------------------------

### Handle startup errors

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Custom error type for capturing multiple startup failures.

```go
type startupError struct {
	errs []error
}

func (e *startupError) Error() string {
	return fmt.Sprintf("state startup errors: %v", e.errs)
}
```

--------------------------------

### GET /v1/connections

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Retrieves matching plugs, slots, and their connections based on provided filtering options.

```APIDOC
## GET /v1/connections

### Description
Returns matching plugs, slots, and their connections. Unless specified by matching options, returns established connections.

### Method
GET

### Endpoint
/v1/connections

### Parameters
#### Query Parameters
- **project-id** (string) - Optional - Filter by project ID
- **workshop** (string) - Optional - Filter by workshop
- **interface** (string) - Optional - Filter by interface
- **select** (string) - Optional - Set to 'all' to include established, undesired, and disconnected plugs and slots.
```

--------------------------------

### Configure workflow for local runner

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/run-github-actions-locally.md

Example YAML configuration for a workflow that allows selecting between a standard runner and the local workshop runner.

```yaml
on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      runner:
        description: Where to run the job
        type: choice
        required: true
        options: [ubuntu-latest, workshop]
        default: ubuntu-latest
jobs:
  test:
    runs-on: ["${{ inputs.runner || 'ubuntu-latest' }}"]
    steps:
      - uses: actions/checkout@v6
      - run: make test
```

--------------------------------

### Define SlotInstallationConstraints

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Structure for defining constraints on an interface slot during SDK installation, including methods for setting specific constraint fields.

```go
const (
        // feature label for plug-names/slot-names constraints
        nameConstraintsFeature = "name-constraints"
)

// SlotInstallationConstraints specifies a set of constraints on an
// interface slot relevant to the installation of SDK.
type SlotInstallationConstraints struct {
        SlotSdkTypes   []string
        SlotAttributes *AttributeConstraints
        SlotNames      *NameConstraints
}

func (c *SlotInstallationConstraints) feature(flabel string) bool {
        if flabel == nameConstraintsFeature {
                return c.SlotNames != nil
        }
        return c.SlotAttributes.feature(flabel)
}

func (c *SlotInstallationConstraints) setNameConstraints(field string, cstrs *NameConstraints) {
        switch field {
        case "slot-names":
                c.SlotNames = cstrs
        default:
                panic("unknown SlotInstallationConstraints field " + field)
        }
}

func (c *SlotInstallationConstraints) setIDConstraints(field string, cstrs []string) {
        switch field {
        case "slot-sdk-type":
                c.SlotSdkTypes = cstrs
        default:
                panic("unknown SlotInstallationConstraints field " + field)
        }
}

func (c *SlotInstallationConstraints) setAttributeConstraints(field string, cstrs *AttributeConstraints) {
        switch field {
        case "slot-attributes":
                c.SlotAttributes = cstrs
        default:
                panic("unknown SlotInstallationConstraints field " + field)
        }
}
```

--------------------------------

### View LXD container log entries

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/fix-workshops/fix-installation.md

If a container fails to start, use 'lxc info' to view its latest log entries.

```console
$ sudo lxc info --show-log nimble-ec275767 --project workshop.user
```

--------------------------------

### Typical usage patterns for Timings

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Demonstrates manual span management and the use of the Run helper for scoped measurements.

```go
        troot := timings.New(map[string]string{"task-id": task.ID(), "change-id": task.Change().ID()})
        t1 := troot.StartSpan("computation", "...")
        ....
        nestedTiming := t1.StartSpan("sub-computation", "...")
        ....
        nestedTiming.Stop()
        t1.Stop()
        troot.Save()

        troot := state.TimingsForTask(task) // tags set automatically from task
        t1 := troot.StartSpan("computation", "...")
        timings.Run(t1, "sub-computation", "...", func(nested *Span) {
               ... expensive computation
        })
        t1.Stop()
        troot.Save(task.State())
```

--------------------------------

### Configure SSH Agent Environment

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Functions to install and remove SSH_AUTH_SOCK environment variable exports in /etc/profile.d.

```go
func installSshAgent(fs workshop.WorkshopFs, dev workshop.SshAgent, workshop string) error {
        env, err := fs.Create(filepath.Join("/etc/profile.d", dev.Name+".sh"))
        if err != nil {
                return fmt.Errorf("cannot set SSH_AUTH_SOCK for %q: %w", workshop, err)
        }
        defer env.Close()

        varline := fmt.Sprintln("export SSH_AUTH_SOCK=" + strings.TrimPrefix(dev.Listen, "unix:"))
        _, err = env.Write([]byte(varline))
        if err != nil {
                return fmt.Errorf("cannot set SSH_AUTH_SOCK for %q: %w", workshop, err)
        }
        return nil
}
```

```go
func removeSshAgent(fs workshop.WorkshopFs, dev workshop.SshAgent) error {
        return fs.Remove(filepath.Join("/etc/profile.d", dev.Name+".sh"))
}
```

--------------------------------

### Refresh Workshop and SDKcraft snaps

Source: https://github.com/canonical/workshop/blob/main/docs/release-notes/index.md

Use these commands to update the installed snaps to the latest version using the classic confinement mode.

```console
$ sudo snap refresh --classic workshop
$ sudo snap refresh --classic sdkcraft
```

--------------------------------

### InstallCandidate Check

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes an InstallCandidate and performs a validation check.

```go
ic := InstallCandidate{
				Sdk:             sdkInfo,
				BaseDeclaration: baseDecl,
		}

		return ic.Check()
}
```

--------------------------------

### Disconnect with Explicit Target Slot

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-disconnect.rst

Example showing a full reference for disconnecting a plug, including the target SDK ('system') and slot ('mount').

```console
$ workshop disconnect nimble/go:mod-cache nimble/system:mount
```

--------------------------------

### Configure Proxy Devices

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods to set up SSH agent and desktop proxy configurations.

```go
func (s *Specification) SetSshAgent(agent workshop.SshAgent) error {
        s.Profile.Agent = &agent
        s.addProxyEntry(&agent.ProxyEntry, "ssh-agent")
        return nil
}

func (s *Specification) SetDesktop(desktop workshop.Desktop) error {
        s.Profile.Desktop = &desktop

        if desktop.Wayland != nil {
                s.addProxyEntry(desktop.Wayland, "desktop-wayland")
        }

        if desktop.X11 != nil {
                s.addProxyEntry(desktop.X11, "desktop-x11")
        }

        return nil
}
```

--------------------------------

### Define tutorial file naming sequence

Source: https://github.com/canonical/workshop/blob/main/docs/doc-style-guide.md

Sequential numbering pattern for tutorial files.

```default
part-1-get-started.rst
part-2-work-with-interfaces.rst
part-3-sketch-sdks.rst
part-4-craft-sdks.rst
```

--------------------------------

### Launch command syntax

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Basic usage pattern for the workshop launch command.

```console
$ workshop launch <WORKSHOP>... [flags]
```

--------------------------------

### Show SDK Info Usage

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdk-info.rst

Displays the general usage pattern for the 'sdk info' command. This command requires the SDK name as an argument and supports optional flags for filtering.

```console
$ sdk info <SDK> [flags]
```

--------------------------------

### Display OpenVINO SDK Metadata

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdk-info.rst

Retrieves and displays metadata, available Store channels, and local installation details for the 'openvino' SDK. This is the default behavior when no flags are specified.

```console
$ sdk info openvino
```

--------------------------------

### Launch the development workshop

Source: https://github.com/canonical/workshop/blob/main/docs/contributing/development.md

Initializes the development environment using the project's workshop definition.

```console
$ workshop launch dev
```

--------------------------------

### Set Slot Rule Constraints

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Updates slot rule fields based on provided installation or connection constraints.

```go
func (r *SlotRule) setConstraints(field string, cstrs []constraintsHolder) {
        if len(cstrs) == 0 {
                panic(fmt.Sprintf("cannot set SlotRule field %q to empty", field))
        }
        switch cstrs[0].(type) {
        case *SlotInstallationConstraints:
                switch field {
                case "allow-installation":
                        r.AllowInstallation = castSlotInstallationConstraints(cstrs)
                        return
                case "deny-installation":
                        r.DenyInstallation = castSlotInstallationConstraints(cstrs)
                        return
                }
        case *SlotConnectionConstraints:
                switch field {
                case "allow-connection":
                        r.AllowConnection = castSlotConnectionConstraints(cstrs)
                        return
                case "deny-connection":
                        r.DenyConnection = castSlotConnectionConstraints(cstrs)
                        return
                case "allow-auto-connection":
                        r.AllowAutoConnection = castSlotConnectionConstraints(cstrs)
                        return
                case "deny-auto-connection":
                        r.DenyAutoConnection = castSlotConnectionConstraints(cstrs)
                        return
                }
        }
        panic(fmt.Sprintf("cannot set SlotRule field %q with %T elements", field, cstrs[0]))
}
```

--------------------------------

### Configure GPU and Camera Devices

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Functions for setting up physical GPU devices and camera unix-char devices in an LXD profile.

```go
        // On another note, the render and video groups are not assigned to the
        // card*/render* dri devices by LXD properly. Both will be assigned to
        // the group provided in "gid"; there is no way to assign video to card*
        // and render to render* devices.
        s.devices[gpu.Name] = map[string]string{"type": "gpu", "gputype": "physical", "uid": "1000", "gid": "1000"}

        return nil
}

func (s *Specification) SetCamera(camera workshop.Camera) error {
        s.Profile.Camera = &camera

        s.devices[camera.Name] = map[string]string{"type": "none"}
        buf, err := json.Marshal(camera)
        if err != nil {
                return err
        }
        s.config[lxdbackend.DeviceConfigKey(s.Profile.Sdk, camera.Name)] = string(buf)
        s.config[lxdbackend.DeviceTypeConfigKey(s.Profile.Sdk, camera.Name)] = "camera"

        for i := 0; i < 10; i++ {
                // This name is unique because '/' is not permitted in plug names.
                name := fmt.Sprintf("%s/video%d", camera.Name, i)
                path := fmt.Sprintf("/dev/video%d", i)
                // The default workshop user must be able to acces the video devices.
                // Workshop assigns the devices to workshop.workshop. A more
                // traditional way here would be to add them device to the video
                // groups, but it requires an additional workshop exec to find out the
                // groups' ids at the LXD profile generation time. Given that we are
                // solving the problem of access in a confined environment and workshop
                // is a passwordless sudo user anyway, it was decided that it is OK if
                // the workshop user owns video devices.
                s.devices[name] = map[string]string{
                        "type":     "unix-char",
                        "source":   path,
                        "path":     path,
                        "required": "false",
                        "uid":      "1000",
                        "gid":      "1000",
                }
                s.config[lxdbackend.DeviceTypeConfigKey(s.Profile.Sdk, name)] = "camera"
        }

        return nil
}
```

--------------------------------

### Initialize Backend Context

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Creates a cancellable context enriched with project and user values for backend operations.

```go
func BackendContext(tomb *tomb.Tomb, user string, projectId string) (context.Context, context.CancelFunc) {
        ctx := tomb.Context(context.Background())
        ctxProject := context.WithValue(ctx, workshop.ContextProjectId, projectId)
        ctxUser := context.WithValue(ctxProject, workshop.ContextUser, user)
        ctxCancel, cancel := context.WithCancel(ctxUser)
        return ctxCancel, cancel
}
```

--------------------------------

### Report SDK error status

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshopctl.md

Example of reporting an error status with a specific error code and descriptive message.

```console
$ workshopctl set-health --code=missing-cuda error "CUDA libraries not found"
```

--------------------------------

### Load Workshop Configuration

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Parses workshop configuration files from LXD instance metadata.

```go
func workshopFile(lxdConfig map[string]string) (*workshop.File, error) {
        var f workshop.File
        if yml, ok := lxdConfig[workshop.ConfigWorkshopFile]; ok {
                if err := yaml.Unmarshal([]byte(yml), &f); err != nil {
                        return nil, err
                }
        }
        return &f, nil
}
```

--------------------------------

### Initialize Systemd Interface

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Creates a new systemd controller instance with a specified root directory, mode, and reporter.

```go
func New(rootDir string, mode InstanceMode, rep reporter) Systemd {
        return &systemd{rootDir: rootDir, mode: mode, reporter: rep}
}
```

--------------------------------

### Debug and Startup Timing

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Helper functions for managing debug state and logging startup stage timestamps.

```go
// used to force testing of the kernel command line parsing
var procCmdlineUseDefaultMockInTests = true

// The function returns false and left here for compatibility
// with snapd further merges. Workshopd does not use this
// functionality
func debugEnabledOnKernelCmdline() bool {
        return false
}

var timeNow = time.Now

// StartupStageTimestamp produce sdk startup timings message.
func StartupStageTimestamp(stage string) {
        now := timeNow()
        Debugf(`-- sdk startup {"stage":"%s", "time":"%v.%06d"}`,
                stage, now.Unix(), (now.UnixNano()/1e3)%1e6)
}
```

--------------------------------

### Format Go comments correctly

Source: https://github.com/canonical/workshop/blob/main/docs/coding-style-guide.md

Use complete sentences starting with a capital letter and ending with a period for all comments.

```go
// Workshop represents a development environment running in a container.
type Workshop struct {
    Name string
    Base string
}

// validateName checks that the workshop name is valid.
func validateName(name string) error {
    // Empty names are not allowed.
    if name == "" {
        return fmt.Errorf("name cannot be empty")
    }
    return nil
}
```

```go
// workshop struct
type Workshop struct { ... }

// check name
func validateName(name string) error { ... }
```

--------------------------------

### Disconnect Interface Logic

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles the disconnection of plugs and slots, including state validation and backend setup for SDKs.

```go
        plug := m.repo.Plug(plugRef.ProjectId, plugRef.Workshop, plugRef.Sdk, plugRef.Name)
        if plug == nil {
                return fmt.Errorf("SDK %q has no plug named %q", plugRef.SdkRef().ShortRef(), plugRef.Name)
        }

        slot := m.repo.Slot(slotRef.ProjectId, slotRef.Workshop, slotRef.Sdk, slotRef.Name)
        if slot == nil {
                return fmt.Errorf("SDK %q has no slot named %q", slotRef.SdkRef().ShortRef(), slotRef.Name)
        }

        if err = m.repo.Disconnect(plugRef.ProjectId, plugRef.Workshop,
                plugRef.Sdk, plugRef.Name, slotRef.ProjectId, slotRef.Workshop, slotRef.Sdk, slotRef.Name); err != nil {
                return err
        }

        var delayedSetupProfile bool
        if err := task.Get("delayed-setup-profile", &delayedSetupProfile); err != nil && !errors.Is(err, state.ErrNoState) {
                return err
        }
        if delayedSetupProfile {
                logger.Debugf("Connect undo handler: skipping setupSdkSecurity for SDKs %q and %q", connRef.PlugRef.Sdk, connRef.SlotRef.Sdk)
                return nil
        }

        for _, ref := range []sdk.Ref{plug.Sdk.Ref(), slot.Sdk.Ref()} {
                ctx, cancel := handlersetup.BackendContext(tomb, user, ref.ProjectId)
                defer cancel()
                for _, backend := range m.repo.Backends() {
                        if err := backend.Setup(ctx, ref, m.repo); err != nil {
                                return err
                        }
                }
        }

        return nil
}
```

--------------------------------

### Initialize Workshop Refresh

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Sets up the initial tasks for a workshop refresh, including state storage creation and SDK disconnection.

```go
func refresh(st *state.State, file *workshop.File, installed []sdk.Setup, toInstall []sdk.Setup, p workshop.Project) (*state.TaskSet, error) {
        // 1. Save previous state
        // 2. Stop previous workshop
        // 3. Put to stash
        // 4. Launch the new workshop
        // 5. Run restore state
        // 6. Delete the old workshop
        retrieve := retrieveSdks(st, toInstall)

        createStateStorage := st.NewTask("create-state-storage", "Create SDK state storage")
        createStateStorage.WaitAll(retrieve)

        // the saveStateHooks can be empty if the old SDKs were all removed in
        // the new version of the workshop
        saveStateHooks := saveStateHooks(st, file.Name, installed, file.Sdks)
        saveStateHooks.WaitFor(createStateStorage)

        // disconnect and remove SDKs plugs and slots
        disconnect := disconnectSdks(installed, st)
        disconnect.WaitAll(saveStateHooks)
        disconnect.WaitFor(createStateStorage)

        // put the workshop (old) away and disconnect its interfaces
        putToStash := st.NewTask("stash-workshop", fmt.Sprintf("Stash previous %q workshop", file.Name))
        putToStash.WaitAll(disconnect)
        putToStash.WaitAll(saveStateHooks)
        putToStash.WaitFor(createStateStorage)
```

--------------------------------

### Launch multiple workshops

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/use-multiple-workshops.md

Initiate multiple workshops simultaneously by listing their names.

```console
$ workshop launch frontend backend
```

--------------------------------

### Launch Workshop in Copied Project

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/move-projects.md

Command to launch a workshop in the newly copied project directory. This creates an independent workshop instance.

```console
$ workshop launch --project /home/user/new/
```

```console
$ workshop list --global

  PROJECT                 WORKSHOP  STATUS  NOTES
  /home/user/old          golang    Ready   -
  /home/user/new          golang    Ready   -
```

--------------------------------

### Specification and Mocking Utilities

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Helper methods for creating specifications and mocking the workshop filesystem.

```go
// NewSpecification returns a new mount specification.
func (b *Backend) NewSpecification(user *user.User, pid, sdk string) interfaces.Specification {
        return NewSpecification(user, sdk)
}

func MockWorkshopFs(f func(conn lxd.InstanceServer, pid, w string) (workshop.WorkshopFs, error)) func() {
        old := workshopFs
        workshopFs = f
        return func() {
                workshopFs = old
        }
}
```

--------------------------------

### Try SDKs with sdkcraft

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft.md

Packs the SDK and copies it to the Workshop try area for validation before publishing.

```console
$ sdkcraft try [--destructive-mode] [--shell | --shell-after] [--debug]
                 [--platform name | --build-for arch] [--output OUTPUT]
                 [SDKs ...]
```

```console
$ sdkcraft try
```

--------------------------------

### Cast constraint types

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Helper functions to cast generic constraint holders into specific installation or connection constraint types.

```go
func castPlugInstallationConstraints(cstrs []constraintsHolder) (res []*PlugInstallationConstraints) {
        res = make([]*PlugInstallationConstraints, len(cstrs))
        for i, cstr := range cstrs {
                res[i] = cstr.(*PlugInstallationConstraints)
        }
        return res
}

func castPlugConnectionConstraints(cstrs []constraintsHolder) (res []*PlugConnectionConstraints) {
        res = make([]*PlugConnectionConstraints, len(cstrs))
        for i, cstr := range cstrs {
                res[i] = cstr.(*PlugConnectionConstraints)
        }
        return res
}
```

--------------------------------

### Initialize TabWriter

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Creates a tabwriter instance configured for standard workshop list output.

```go
func tabWriter() *tabwriter.Writer {
        /* Tab writer uses the same formatting as snap list */
        return tabwriter.NewWriter(Stdout, 4, 3, 2, ' ', 0)
}
```

--------------------------------

### Client Project and Workshop Management

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Client methods for retrieving projects and performing workshop actions like launch and refresh.

```go
package client

import (
        "bytes"
        "encoding/json"
        "net/url"
)

type Project struct {
        Id   string `json:"id"`
        Path string `json:"path"`
}

type WorkshopActionOptions struct {
        Mode string `json:"mode,omitempty"`
}

type WorkshopActionSetup struct {
        Action  string
        Names   []string
        Options *WorkshopActionOptions
}

func (client *Client) Projects() ([]Project, error) {
        var projects []Project
        _, err := client.doSync("GET", "/v1/projects", nil, nil, nil, &projects)
        if err != nil {
                return nil, err
        }

        return projects, nil
}

func (client *Client) Project(path string) (*Project, error) {
        var project Project
        query := url.Values{}

        var postData struct {
                Path string `json:"path"`
        }
        postData.Path = path

        var body bytes.Buffer
        if err := json.NewEncoder(&body).Encode(postData); err != nil {
                return nil, err
        }

        _, err := client.doSync("POST", "/v1/projects", query, nil, &body, &project)
        if err != nil {
                return nil, err
        }

        return &project, nil
}

func (client *Client) doWorkshopAction(projectId string, action *WorkshopActionSetup) (changeId string, err error) {
        var postData struct {
                Names   []string               `json:"names"`
                Action  string                 `json:"action"`
                Options *WorkshopActionOptions `json:"options,omitempty"`
        }
        postData.Names = action.Names
        postData.Action = action.Action
        postData.Options = action.Options
        var body bytes.Buffer
        if err := json.NewEncoder(&body).Encode(postData); err != nil {
                return "", err
        }

        return client.doAsync("POST", "/v1/projects/"+projectId+"/workshops", nil, nil, &body)
}

func (client *Client) Launch(projectId string, names []string, mode string) (changeId string, err error) {
        return client.doWorkshopAction(projectId, &WorkshopActionSetup{
                Action: "launch",
                Names:  names,
                Options: &WorkshopActionOptions{
                        Mode: mode,
                },
        })
}

func (client *Client) Refresh(projectId string, names []string, mode string) (changeId string, err error) {
        return client.doWorkshopAction(projectId, &WorkshopActionSetup{
                Action: "refresh",
                Names:  names,
                Options: &WorkshopActionOptions{
                        Mode: mode,
                },
        })
}
```

--------------------------------

### Cast Constraint Types

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Helper functions to cast generic constraint holders into specific connection or installation constraint types.

```go
func castSlotConnectionConstraints(cstrs []constraintsHolder) (res []*SlotConnectionConstraints) {
        res = make([]*SlotConnectionConstraints, len(cstrs))
        for i, cstr := range cstrs {
                res[i] = cstr.(*SlotConnectionConstraints)
        }
        return res
}

func castSlotInstallationConstraints(cstrs []constraintsHolder) (res []*SlotInstallationConstraints) {
        res = make([]*SlotInstallationConstraints, len(cstrs))
        for i, cstr := range cstrs {
                res[i] = cstr.(*SlotInstallationConstraints)
        }
        return res
}
```

--------------------------------

### Launch Workshop

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/move-projects.md

Command to launch a workshop in a specified project directory.

```console
$ workshop launch --project /home/user/old/
```

--------------------------------

### Configure and Create Workshop Hooks

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Sets up environment variables for state-related hooks and creates tasks for execution with optional timeouts.

```go
func hookSetup(workshop, sdk string, hook WorkshopHookType) HookSetup {
        setup := HookSetup{HookType: hook, Workshop: workshop, Sdk: sdk, Environment: map[string]string{}}
        if hook == SaveState || hook == RestoreState {
                setup.Environment["SDK_STATE_DIR"] = filepath.Join(dirs.WorkshopStateDir, "sdk", sdk)
        }
        return setup
}

func Hook(st *state.State, workshop, sdk string, hook WorkshopHookType) *state.Task {
        setup_hook := st.NewTask("run-hook", fmt.Sprintf("Run hook %q for %q SDK", hook.String(), sdk))
        setup_hook.Set("hook-setup", hookSetup(workshop, sdk, hook))
        return setup_hook
}

func HookWithTimeout(st *state.State, workshop, sdk string, hook WorkshopHookType, timeout time.Duration) *state.Task {
        setup_hook := st.NewTask("run-hook", fmt.Sprintf("Run hook %q for %q SDK", hook.String(), sdk))
        setup := hookSetup(workshop, sdk, hook)
        setup.Timeout = timeout
        setup_hook.Set("hook-setup", &setup)
        return setup_hook
}
```

--------------------------------

### Retrieve System Information

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Fetches system version and boot ID from the remote API.

```go
type SysInfo struct {
        // Version is the server version.
        Version string `json:"version,omitempty"`

        // BootID is a unique string that represents this boot of the server.
        BootID string `json:"boot-id,omitempty"`
}

// SysInfo gets system information from the remote API.
func (client *Client) SysInfo() (*SysInfo, error) {
        var sysInfo SysInfo

        if _, err := client.doSync("GET", "/v1/system-info", nil, nil, nil, &sysInfo); err != nil {
                return nil, fmt.Errorf("cannot obtain system details: %w", err)
        }

        return &sysInfo, nil
}
```

--------------------------------

### Release SDK Revision to Stable Channel

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-release.rst

Example of releasing a specific SDK revision (revision 8) to the 'stable' channel.

```console
$ sdkcraft release my-sdk 8 stable
```

--------------------------------

### Ensure task execution in TaskRunner

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Starts new goroutines for tasks with no pending dependencies, ensuring state is locked during the process.

```go
// Ensure starts new goroutines for all known tasks with no pending
// dependencies.
// Note that Ensure will lock the state.
func (r *TaskRunner) Ensure() error {
        r.mu.Lock()
        defer r.mu.Unlock()

        if r.stopped {
                // we are stopping, don't run another ensure
                return nil
        }

        // Locks must be acquired in the same order everywhere.
        r.state.Lock()
        defer r.state.Unlock()

        r.someBlocked = false
        running := make([]*Task, 0, len(r.tombs))
        for tid := range r.tombs {
                t := r.state.Task(tid)
                if t != nil {
                        running = append(running, t)
                }
        }

        ensureTime := timeNow()
        nextTaskTime := time.Time{}
ConsiderTasks:
        for _, t := range r.state.Tasks() {
                handlers := r.handlerPair(t)
                if handlers.do == nil {
                        // Handled by a different runner instance.
                        continue
                }

                tb := r.tombs[t.ID()]

                if t.Status() == AbortStatus {
                        if tb != nil {
                                tb.Kill(nil)
                                continue
                        }
                        r.tryUndo(t)
                }

                if tb != nil {
                        // Already being handled.
                        continue
                }

                status := t.Status()
                if status.Ready() {
                        if !t.IsClean() {
                                r.clean(t)
                        }
                        continue
                }
                if status == WaitStatus {
                        // nothing more to run
                        continue
                }

                if mustWait(t) {
                        // Dependencies still unhandled.
                        continue
                }

                if status == UndoStatus && handlers.undo == nil {
                        // Although this has no dependencies itself, it must have waited
                        // above too since follow up tasks may have handlers again.
                        // Cannot undo. Revert to done status.
                        t.SetStatus(DoneStatus)
                        if len(t.WaitTasks()) > 0 {
                                r.state.EnsureBefore(0)
                        }
                        continue
                }

                // skip tasks scheduled for later and also track the earliest one
                tWhen := t.AtTime()
                if !tWhen.IsZero() && ensureTime.Before(tWhen) {
                        if nextTaskTime.IsZero() || nextTaskTime.After(tWhen) {
                                nextTaskTime = tWhen
                        }
                        continue
                }

                // check if any of the blocked predicates returns true
                // and skip the task if so
                for _, blocked := range r.blocked {
                        if blocked(t, running) {
                                r.someBlocked = true
                                continue ConsiderTasks
                        }
                }
```

--------------------------------

### Initialize Daemon Overlord

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles the creation of an overlord instance and manages system reboot states during daemon initialization.

```go
        ovld, err := overlord.New(opts.Dir, d)
        if err == errExpectedReboot {
                // we proceed without overlord until we reach Stop
                // where we will schedule and wait again for a system restart.
                // ATM we cannot do that in New because we need to satisfy
                // systemd notify mechanisms.
                d.rebootIsMissing = true
                return d, nil
        }
        if err != nil {
                return nil, err
        }
        d.overlord = ovld
        d.state = ovld.State()
        return d, nil
}

func (d *Daemon) Overlord() *overlord.Overlord {
        return d.overlord
}
```

--------------------------------

### Construct Workshop

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the sequence of tasks required to initialize a workshop environment, including image download, creation, and mounting.

```go
func constructWorkshop(st *state.State, file *workshop.File, project workshop.Project) *state.TaskSet {
        base := st.NewTask("download-base", fmt.Sprintf("Download %q base image", file.Base))
        base.Set("workshop-base", file.Base)

        create := st.NewTask("create-workshop", fmt.Sprintf("Create new %q workshop", file.Name))
        create.Set("workshop-file", file)
        create.WaitFor(base)

        mountProject := st.NewTask("mount-project", fmt.Sprintf("Mount project directory %q", project.Path))
        mountProject.WaitFor(create)

        mountAptCache := st.NewTask("mount-apt-cache", fmt.Sprintf("Mount apt cache directory %q", dirs.AptCachePath))
        mountAptCache.WaitFor(mountProject)

        start := st.NewTask("start-workshop", fmt.Sprintf("Start %q workshop", file.Name))
        start.WaitFor(mountAptCache)
        return state.NewTaskSet(base, create, mountProject, mountAptCache, start)
}
```

--------------------------------

### TestSecurityBackendSetupMany Implementation

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Extended security backend supporting SetupMany operations with callback functionality.

```go
// TestSecurityBackendSetupMany is a security backend that implements SetupMany on top of TestSecurityBackend.
type TestSecurityBackendSetupMany struct {
        TestSecurityBackend

        // SetupManyCalls stores information about all calls to Setup
        SetupManyCalls []TestSetupManyCall

        // SetupManyCallback is an callback that is optionally called in Setup
        SetupManyCallback func(context context.Context, sdkInfo []*sdk.Info, repo *interfaces.Repository) []error
}

// TestSetupManyCall stores details about calls to TestSecurityBackendMany.SetupMany
type TestSetupManyCall struct {
        // SdkInfos is a copy of the sdkInfo arguments to a particular call to SetupMany
        SdkInfos []*sdk.Info
}

func (b *TestSecurityBackendSetupMany) SetupMany(context context.Context, sdkInfo []*sdk.Info, repo *interfaces.Repository) []error {
        b.SetupManyCalls = append(b.SetupManyCalls, TestSetupManyCall{SdkInfos: sdkInfo})
        if b.SetupManyCallback == nil {
                return nil
        }
        return b.SetupManyCallback(context, sdkInfo, repo)
}
```

--------------------------------

### Initialize Specification

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Creates a new Specification instance with initialized maps for devices and configuration.

```go
func NewSpecification(user *user.User, sdk string) *Specification {
        return &Specification{
                devices: make(map[string]map[string]string),
                config:  make(map[string]string),
                Profile: workshop.NewSdkProfile(sdk),
                User:    user,
        }
}
```

--------------------------------

### List available video and media devices

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/interfaces/camera-interface.md

Verify that host cameras are accessible inside the workshop shell.

```console
$ workshop shell ws
workshop@ws:/project$ ls /dev/video*

  /dev/video0  /dev/video1

workshop@ws:/project$ ls /dev/media*

  /dev/media0
```

--------------------------------

### Initialize Workshop Daemon Paths

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines global variables and initialization logic for workshop daemon directory paths.

```go
var (
        // Base directory for workshopd
        BaseDir string
        // Work directory
        ExecDir string
        // The directory to store downloaded SDKs
        SdkDir string
        // Path to the daemon's unix socket
        SocketPath string
        // State lock file
        WorkshopStateLockFile string
        // Base for the XDG runtime directory of a host user
        XdgRuntimeDirBase string
        // Run directory
        WorkshopdRunDir string
        // Locks directory
        WorkshopdLocksDir string
        // Certificates
        WorkshopTlsDir string
)

func getEnvPaths() (workshopdDir string, socketPath string) {
        workshopdDir = os.Getenv("WORKSHOP")
        if workshopdDir == "" {
                workshopdDir = defaultBaseDir
        }
        socketPath = os.Getenv("WORKSHOP\_SOCKET")
        if socketPath == "" {
                socketPath = filepath.Join(workshopdDir, "workshop.socket")
        }
        return workshopdDir, socketPath
}

func init() {
        var err error
        var execPath string
        execPath, err = os.Executable()
        if err != nil {
                panic("cannot get working directory")
        }

        ExecDir = filepath.Dir(execPath)
        XdgRuntimeDirBase = "/run/user"
        BaseDir, SocketPath = getEnvPaths()
        SetRootDir(BaseDir)
}

func SetRootDir(rootdir string) {
        if !filepath.IsAbs(rootdir) {
                panic(fmt.Sprintf("cannot set root dir: path %q is not absolute", rootdir))
        }
        BaseDir = rootdir
        SdkDir = filepath.Join(BaseDir, "sdk")
        WorkshopStateLockFile = filepath.Join(BaseDir, "state.lock")
        WorkshopTlsDir = filepath.Join(BaseDir, "tls")
        WorkshopdRunDir = filepath.Join(BaseDir, "/run/workshopd")
        WorkshopdLocksDir = filepath.Join(WorkshopdRunDir, "locks")
}

func CreateDirs() error {
        if err := os.MkdirAll(BaseDir, 0755); err != nil {
                return err
        }
        if err := os.MkdirAll(SdkDir, 0755); err != nil {
                return err
        }
        if err := os.MkdirAll(WorkshopdRunDir, 0755); err != nil {
                return err
        }
        if err := os.MkdirAll(WorkshopdLocksDir, 0755); err != nil {
                return err
        }
        if err := os.MkdirAll(WorkshopTlsDir, 0755); err != nil {
                return err
        }
        return nil
}
```

--------------------------------

### Run SDK tests with sdkcraft

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft.md

Executes tests using the spread framework with automatic SDK packing and environment setup.

```console
$ sdkcraft test [--destructive-mode] [--shell | --shell-after] [--debug] [--platform name]
                  [--list]
                  [test_expressions ...]
```

```console
$ sdkcraft test
```

```console
$ sdkcraft test --list
```

```console
$ sdkcraft test my-suite/
```

--------------------------------

### Connect to LXD Image Server

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Establishes a connection to either a simplestreams or LXD image server based on the provided URL prefix.

```go
func connectImageServer(url string) (lxd.ImageServer, error) {
        if strings.HasPrefix(url, "simplestreams:") {
                server, _ := strings.CutPrefix(url, "simplestreams:")
                conn, err := ConnectSimpleStreams(server, nil)
                if err != nil {
                        return nil, fmt.Errorf("image server is not available: %w", err)
                }
                return conn, err
        }

        if strings.HasPrefix(url, "lxd:") {
                server, _ := strings.CutPrefix(url, "lxd:")
                args, err := lxdConnectionArgs()
                if err != nil {
                        return nil, err
                }
                conn, err := lxd.ConnectPublicLXD(server, args)
                if err != nil {
                        return nil, fmt.Errorf("image server is not available: %w", err)
                }
                return conn, err
        }

        return nil, fmt.Errorf("unknown image server URL prefix (supported: simplestreams, lxd)")
}
```

--------------------------------

### Context State Persistence

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for setting and getting persisted values within the context. Requires the context to be locked by the caller.

```go
func (c *Context) Set(key string, value interface{}) {
	c.writing()

	var data map[string]*json.RawMessage
	if c.IsEphemeral() {
		data, _ = c.cache["ephemeral-context"].(map[string]*json.RawMessage)
	} else {
		if err := c.task.Get("hook-context", &data); err != nil && !errors.Is(err, state.ErrNoState) {
			panic(fmt.Sprintf("internal error: cannot unmarshal context: %v", err))
		}
	}
	if data == nil {
		data = make(map[string]*json.RawMessage)
	}

	marshalledValue, err := json.Marshal(value)
	if err != nil {
		panic(fmt.Sprintf("internal error: cannot marshal context value for %q: %s", key, err))
	}
	raw := json.RawMessage(marshalledValue)
	data[key] = &raw

	if c.IsEphemeral() {
		c.cache["ephemeral-context"] = data
	} else {
		c.task.Set("hook-context", data)
	}
}

func (c *Context) Get(key string, value interface{}) error {
	c.reading()

	var data map[string]*json.RawMessage
	if c.IsEphemeral() {
		data, _ = c.cache["ephemeral-context"].(map[string]*json.RawMessage)
		if data == nil {
			return state.ErrNoState
		}
	} else {
		if err := c.task.Get("hook-context", &data); err != nil {
			return err
		}
	}

	raw, ok := data[key]
	if !ok {
		return state.ErrNoState
	}

	err := jsonutil.DecodeWithNumber(bytes.NewReader(*raw), &value)
	if err != nil {
		return fmt.Errorf("cannot unmarshal context value for %q: %w", key, err)
	}

	return nil
}
```

--------------------------------

### Sync project directory updates

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-1-get-started.md

Demonstrate bidirectional file synchronization between the host system and the mounted /project/ directory inside the workshop.

```console
$ touch created_outside.txt
$ workshop exec dev -- ls /project/

  ...  created_outside.txt  ...

$ workshop exec dev -- touch /project/created_inside.txt
$ ls

  ...  created_inside.txt  created_outside.txt  ...
```

--------------------------------

### Search for SDKs by Keyword

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdk-find.rst

Find SDKs matching a single keyword. This is the most basic way to search.

```console
$ sdk find openvino
```

--------------------------------

### Initialize System Loggers

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Functions for setting up default or boot-specific loggers using system flags and kernel command line options.

```go
// SimpleSetup creates the default (console) logger
func SimpleSetup() error {
        flags := buildFlags()
        l, err := New(os.Stderr, flags)
        if err == nil {
                SetLogger(l)
        }
        return err
}

// BootSetup creates a logger meant to be used when running from
// initramfs, where we want to consider the quiet kernel option.
func BootSetup() error {
        flags := buildFlags()
        m, _ := osutil.KernelCommandLineKeyValues("quiet")
        _, quiet := m["quiet"]
        logger := &Log{
                log:   log.New(os.Stderr, "", flags),
                debug: debugEnabledOnKernelCmdline(),
                quiet: quiet,
        }
        SetLogger(logger)

        return nil
}
```

--------------------------------

### Construct SDK and Project Paths

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Utility functions for generating consistent file paths for SDK components and project-specific user data directories.

```go
func SdkRootPath(sdkName string) string {
        return filepath.Join(dirs.WorkshopSdksDir, sdkName)
}

func SdkRevPath(sdkName string, rev string) string {
        return filepath.Join(SdkRootPath(sdkName), rev)
}

func SdkCurrentPath(sdkName string) string {
        return filepath.Join(SdkRootPath(sdkName), "current")
}

func SdkMetaDir(sdkName string) string {
        return filepath.Join(SdkCurrentPath(sdkName), "meta")
}

func SdkMetaPath(sdkName string) string {
        return filepath.Join(SdkMetaDir(sdkName), "sdk.yaml")
}

func SdkHooksDir(sdkName string) string {
        return filepath.Join(SdkCurrentPath(sdkName), "sdk", "hooks")
}

func SdkHookPath(sdkName, hookName string) string {
        return filepath.Join(SdkHooksDir(sdkName), hookName)
}

func ProjectUserData(homedir, pid string) string {
        return filepath.Join(homedir, ".local", "share", "workshop", "project", pid)
}

func ProjectContentDir(homedir, pid string) string {
        return filepath.Join(ProjectUserData(homedir, pid), "mount")
}

func ProjectSketchSdkDir(homedir, pid string) string {
        return filepath.Join(ProjectUserData(homedir, pid), "sdk", "sketch")
}

func WorkshopSketchSdk(homedir, pid, wp string) string {
        return filepath.Join(ProjectSketchSdkDir(homedir, pid), wp)
}

func WorkshopSketchSdkCurrent(homedir, pid, wp string) string {
        return filepath.Join(ProjectSketchSdkDir(homedir, pid), wp, "current")
}

func WorkshopSketchSdkStash(homedir, pid, wp string) string {
        return filepath.Join(ProjectSketchSdkDir(homedir, pid), wp, "stash")
}

func SdkMountHostSource(homedir, pid, wp, sdk, plug string) string {
        dir := strings.Join([]string{wp, sdk, plug}, "_") + ".sdk"
        return filepath.Join(ProjectContentDir(homedir, pid), dir)
}
```

--------------------------------

### Implement Mount Interface Methods

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the mount interface logic for connecting plugs and slots, including fallback mechanisms for host-based sources.

```go
func (iface *mountInterface) MountConnectedSlot(spec *lxd_device.Specification, plug *interfaces.ConnectedPlug, slot *interfaces.ConnectedSlot) error {
        return nil
}

// Interactions with the mount backend.
func (iface *mountInterface) MountConnectedPlug(spec *lxd_device.Specification, plug *interfaces.ConnectedPlug, slot *interfaces.ConnectedSlot) error {
        source, err := iface.workshopSource(slot)
        if err != nil && !errors.Is(err, sdk.AttributeNotFoundError{}) {
                return err
        }
        if err == nil {
                return spec.AddMountEntry(workshop.Mount{Name: plug.Name(), What: source, Where: iface.target(plug), Type: workshop.WorkshopWorkshop})
        }

        source, err = iface.hostSource(spec.User.HomeDir, plug, slot)
        if err == nil {
                return spec.AddMountEntry(workshop.Mount{Name: plug.Name(), What: source, Where: iface.target(plug), Type: workshop.HostWorkshop})
        }

        return err
}

func init() {
        registerIface(&mountInterface{})
}
```

--------------------------------

### Apply semantic line breaks in reStructuredText

Source: https://github.com/canonical/workshop/blob/main/docs/doc-style-guide.md

Examples demonstrating the application of semantic line breaks within reStructuredText documentation blocks.

```restructuredtext
This is the first section of the :ref:`four-part series <tut_index>`;
a practical introduction
that takes you on a tour
of the essential |ws_markup| activities.
```

```restructuredtext
To make use of these interfaces,
SDKs and :ref:`workshops <exp_workshop_definition_connections>` define *slots*.
For example, a :ref:`mount interface <exp_mount_interface>` slot
creates a source directory to be mounted inside the workshop via a plug.
```

```restructuredtext
When crafting SDKs for |ws_markup|,
publishers face design decisions
that affect how their SDKs install, integrate, and work inside workshops.
Understanding the best practices outlined below
helps publishers create more maintainable, reliable, and user-friendly SDKs
that better align with |ws_markup|'s architecture and ideology.
```

```restructuredtext
Interfaces are a mechanism for communication and resource sharing.
It is an integral part of workshop confinement,
ensuring that each workshop operates in its own isolated environment,
while still allowing controlled interactions among the SDKs and with the host.
```

--------------------------------

### Implement the launch command execution logic

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles the execution flow, including argument validation, mode selection, and error reporting for workshop operations.

```go
func (c *CmdLaunch) Run(cmd *cobra.Command, av []string) error {
        av = strutil.Deduplicate(av)

        if c.Abort && c.Continue {
                return fmt.Errorf("cannot launch: '--abort' incompatible with '--continue'")
        }

        if c.WaitOnError && c.Abort {
                return fmt.Errorf("cannot launch: '--wait-on-error' incompatible with '--abort'")
        }

        if c.WaitOnError && c.Continue {
                return fmt.Errorf("cannot launch: '--wait-on-error' incompatible with '--continue'")
        }

        // We should have no more than one argument (a single workshop) for a
        // wait-on-error operation
        if (c.Abort || c.Continue || c.WaitOnError) && len(av) > 1 {
                return fmt.Errorf("cannot launch: '--wait-on-error' incompatible with multiple workshops")
        }

        cli, err := c.root.client()
        if err != nil {
                return err
        }

        project, err := cli.Project(c.root.project)
        if err != nil {
                return err
        }

        if len(av) == 0 {
                name, err := cli.SingleWorkshopName(project)
                if err != nil {
                        return err
                }
                av = []string{name}
        }

        mode := "transactional"
        if c.WaitOnError {
                mode = "wait-on-error"
        }
        if c.Continue {
                mode = "continue"
        }
        if c.Abort {
                mode = "abort"
        }

        changeId, err := cli.Launch(project.Id, av, mode)
        if err != nil {
                return err
        }

        if _, err := c.wait(cli, changeId); err != nil {
                if err == errNoWait {
                        return nil
                }
                if err == errWaitOnError {
                        return fmt.Errorf("cannot launch; fix the errors reported,\n"+
                                "then run \"workshop launch --continue %s\".\n"+
                                "To abort and revert, run \"workshop launch --abort %s\"", workshopName(av[0]), workshopName(av[0]))
                }
                return fmt.Errorf("%v\n%s launch aborted", err, strutil.Quoted(av))
        }

        if c.Abort {
                fmt.Fprintf(Stdout, "%q launch aborted\n", av[0])
                return nil
        }

        for _, i := range av {
                fmt.Fprintf(Stdout, "%q launched\n", i)
        }

        return nil
}
```

--------------------------------

### Load Application State

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Acquires the state lock, determines the boot ID, and initializes or reads the state file.

```go
func (o *Overlord) loadState(statePath string, restartHandler restart.Handler, backend state.Backend) (*state.State, error) {
	flock, err := initStateFileLock()
	if err != nil {
		return nil, fmt.Errorf("fatal: error opening lock file: %v", err)
	}
	o.stateFLock = flock

	logger.Noticef("Acquiring state lock file")
	if err := lockWithTimeout(o.stateFLock, stateLockTimeout); err != nil {
		logger.Noticef("Failed to lock state file")
		return nil, fmt.Errorf("fatal: could not lock state file: %v", err)
	}
	logger.Noticef("Acquired state lock file")

	curBootID, err := osutil.BootID()
	if err != nil {
		return nil, fmt.Errorf("fatal: cannot find current boot ID: %w", err)
	}
	// If workshop is PID 1 we don't care about /proc/sys/kernel/random/boot_id
	// as we are most likely running in a container. LXD mounts it's own boot_id
	// to correctly emulate the boot_id behaviour of non-containerized systems.
	// Within containerd/docker, boot_id is consistent with the host, which provides
	// us no context of restarts, so instead fallback to /proc/sys/kernel/random/uuid.
	if os.Getpid() == 1 {
		curBootID, err = randutil.RandomKernelUUID()
		if err != nil {
			return nil, fmt.Errorf("fatal: cannot generate psuedo boot-id: %w", err)
		}
	}

	if !osutil.FileExists(statePath) {
		// fail fast, mostly interesting for tests, this dir is set up by workshop
		stateDir := filepath.Dir(statePath)
		if !osutil.IsDir(stateDir) {
			return nil, fmt.Errorf("fatal: directory %q must be present", stateDir)
		}
		s := state.New(backend)
		initRestart(s, curBootID, restartHandler)
		patch.Init(s)
		return s, nil
	}

	r, err := os.Open(statePath)
	if err != nil {
		return nil, fmt.Errorf("cannot read the state file: %w", err)
	}
	defer r.Close()

	var s *state.State
	s, err = state.ReadState(backend, r)
	if err != nil {
		return nil, err
	}
```

--------------------------------

### Disconnect a Specific Plug Interface

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-disconnect.rst

Example of disconnecting a specific plug interface ('mod-cache') from an SDK ('go') within a workshop ('nimble').

```console
$ workshop disconnect nimble/go:mod-cache
```

--------------------------------

### Create Test Context

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes a context with user and project identifiers for testing purposes.

```go
package ifacetest

import (
        "context"

        "github.com/canonical/workshop/internal/interfaces"
        "github.com/canonical/workshop/internal/sdk"
        "github.com/canonical/workshop/internal/workshop"
)

func CreateTestContext(username, projectId string) context.Context {
        ctx := context.WithValue(context.Background(), workshop.ContextUser, username)
        ctx = context.WithValue(ctx, workshop.ContextProjectId, projectId)
        return ctx
}
```

--------------------------------

### Project Identification and Creation Methods

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for managing project lifecycle, including finding existing projects, handling moves/copies, and creating new project entries.

```go
func (t *ProjectTracker) writeProjectId(path string) (*Project, TrackResult, error) {
        // Try to recover .lock file for this project
        // if it existed before and was accidentally removed.
        idx := slices.IndexFunc(t.Projects, func(p Project) bool { return p.Path == path })
        if idx >= 0 {
                if err := t.Projects[idx].updateLock(); err != nil {
                        return nil, ProjectError, err
                }
                return &t.Projects[idx], ProjectFound, nil
        }

        // No project found. If there is at least one workshop definition,
        // we consider the path as a project and create a project ID.
        if !isProject(path) {
                return nil, ProjectError, ErrNotProject
        }
        return t.createProject(path)
}
```

```go
func (t *ProjectTracker) maybeFindProject(path, id string) (*Project, TrackResult, error) {
        idx := slices.IndexFunc(t.Projects, func(p Project) bool { return p.ProjectId == id })
        if idx < 0 {
                return nil, ProjectError, nil
        }
        if t.Projects[idx].Path == path {
                return &t.Projects[idx], ProjectFound, nil
        }

        // Existing project was moved or copied.
        _, err := os.Stat(t.Projects[idx].Path)
        if err != nil {
                if errors.Is(err, os.ErrNotExist) {
                        // Moved: keep ID but update path.
                        t.Projects[idx].Path = path
                        return &t.Projects[idx], ProjectMoved, nil
                }
                return nil, ProjectError, err
        }

        // Copied: generate a new project ID and overwrite the copied .lock file.
        return t.createProject(path)
}
```

```go
func (t *ProjectTracker) createProject(path string) (*Project, TrackResult, error) {
        id, err := NewProjectId()
        if err != nil {
                return nil, ProjectError, err
        }

        project := Project{Path: path, ProjectId: id}
        if err = project.updateLock(); err != nil {
                return nil, ProjectError, err
        }

        t.Projects = append(t.Projects, project)
        return &project, ProjectAdded, nil
}
```

```go
func (t *ProjectTracker) createProjectWithId(path, id string) (*Project, TrackResult, error) {
        // If there is at least one workshop definition,
        // we consider the path as a project and use the given ID.
        if !isProject(path) {
                return nil, ProjectError, ErrNotProject
        }

        project := Project{ProjectId: id, Path: path}
        t.Projects = append(t.Projects, project)
        return &project, ProjectAdded, nil
}
```

--------------------------------

### Implement Fake Workshop Backend

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Mock backend structures and methods for simulating workshop environments, project tracking, and execution callbacks during testing.

```go
package fakebackend

import (
        "context"
        "encoding/json"
        "errors"
        "fmt"
        "io/fs"
        "net/http"
        "os"
        "path/filepath"

        "github.com/canonical/lxd/shared/api"
        "github.com/canonical/x-go/randutil"
        "github.com/spf13/afero"
        "golang.org/x/exp/slices"

        "github.com/canonical/workshop/internal/progress"
        "github.com/canonical/workshop/internal/sdk"
        "github.com/canonical/workshop/internal/workshop"
)

/* Fake backend implementation for tests */

type ExecFunc func(ctx context.Context, name string, args *workshop.Execution) (workshop.ExecContext, error)

type FakeWorkshop struct {
        *workshop.Workshop
        Config             map[string]string
        Devices            map[string]map[string]string
        WorkshopFilesystem *FakeInstanceFs
}

type ExecCall struct {
        Name string
        Args *workshop.Execution
}

type FsCall struct {
        Name string
}

type DownloadCall struct {
        Base string
}

type FakeWorkshopBackend struct {
        // the key is a project-id - workshop name
        Workshops map[string]map[string]*FakeWorkshop
        // workshops put to stash (e.g. during refresh)
        StashedWorkshops map[string]map[string]*FakeWorkshop
        // storage volumes, the key is a volume name
        WorkshopVolumes           map[string]bool
        WorkshopVolumeContents    map[string]map[string]bool
        WorkshopVolumeMountPoints map[string]string
        // the key is a username
        projects map[string][]workshop.Project

        ExecCallback ExecFunc
        ExecCalls    []*ExecCall

        WorkshopFsCallback func(ctx context.Context, name string) (workshop.WorkshopFs, error)
        WorkshopFsCalls    []*FsCall

        DownloadBaseCallback func(ctx context.Context, base string, report *progress.Reporter) error
        DownloadBaseCalls    []*DownloadCall

        BaseDir string
}

func New(baseDir string) (*FakeWorkshopBackend, error) {
        var be FakeWorkshopBackend
        be.Workshops = make(map[string]map[string]*FakeWorkshop)
        be.StashedWorkshops = make(map[string]map[string]*FakeWorkshop)
        be.WorkshopVolumes = make(map[string]bool)
        be.WorkshopVolumeContents = make(map[string]map[string]bool)
        be.WorkshopVolumeMountPoints = make(map[string]string)
        be.projects = make(map[string][]workshop.Project)

        be.ExecCallback = DoExecDefault
        be.BaseDir = baseDir

        return &be, nil
}

func (s *FakeWorkshopBackend) CreateOrLoadProject(ctx context.Context, path string) (*workshop.Project, bool, error) {
        username, ok := ctx.Value(workshop.ContextUser).(string)
        if !ok {
                return nil, false, errors.New("user not found")
        }
        if val, ok := s.projects[username]; ok {
                idx := slices.IndexFunc(val, func(p workshop.Project) bool { return p.Path == path })
                if idx != -1 {
                        return &val[idx], false, nil
                }
        } else {
                s.projects[username] = make([]workshop.Project, 0)
        }

        prjId, _ := workshop.NewProjectId()
        newPrj := workshop.Project{ProjectId: prjId, Path: path}
        s.projects[username] = append(s.projects[username], newPrj)
        return &newPrj, true, nil
}

func (f *FakeWorkshopBackend) Projects(ctx context.Context) (map[string][]workshop.Project, error) {
        userName, ok := ctx.Value(workshop.ContextUser).(string)
        if ok {
                return map[string][]workshop.Project{userName: f.projects[userName]}, nil
        }
        all := map[string][]workshop.Project{}
        for name, prjs := range f.projects {
                all[name] = prjs
        }
        return all, nil
}

func (f *FakeWorkshopBackend) project(user, id string) *workshop.Project {
        prjs := f.projects[user]
        idx := slices.IndexFunc(prjs, func(p workshop.Project) bool { return p.ProjectId == id })
        if idx != -1 {
                return &prjs[idx]
        }
        return nil
}

func (f *FakeWorkshopBackend) LaunchWorkshop(ctx context.Context, file *workshop.File) error {
        user, projectId, err := f.userProject(ctx)
        if err != nil {
                return err
        }

        prj := f.project(user, projectId)
```

--------------------------------

### Launch multiple workshops

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-launch.rst

Launch the 'nimble' and 'jazzy' workshops in the current project directory. Ensure the names match the 'name:' values in their respective definitions.

```console
$ workshop launch nimble jazzy
```

--------------------------------

### Launch Multiple Workshops

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Orchestrates the launch of multiple workshop instances by validating existence and setting up SDK configurations.

```go
func (w *WorkshopManager) LaunchMany(ctx context.Context, names []string, projectId string, opChangeId string) ([]*state.TaskSet, error) {
        project, err := w.loadProject(ctx, projectId)
        if err != nil {
                return nil, err
        }

        taskset := make([]*state.TaskSet, 0, len(names))
        var sdks []sdk.SdkResult
        for _, name := range names {
                // Make sure the workshop doesn't exist
                _, err := w.Workshop(ctx, name, projectId)
                if err == nil {
                        return nil, fmt.Errorf("cannot launch %q: workshop exists", name)
                } else if !errors.Is(err, workshop.ErrWorkshopNotLaunched) {
                        return nil, fmt.Errorf("cannot launch %q, failed to check whether the workshop exists: %w", name, err)
                }

                file, err := project.Workshop(name)
                if err != nil {
                        return nil, fmt.Errorf("cannot launch %q: %w", name, err)
                }

                sdks, err = launchStoreInfo(w.state, ctx, projectId, file)
                if err != nil {
                        return nil, err
                }

                sets := []sdk.Setup{}
                for _, s := range sdks {
                        sets = append(sets, sdk.Setup{Name: s.Name, Channel: s.Channel, Revision: s.Revision})
                }

                tasks := launch(w.state, file, sets, *project)
                taskset = append(taskset, tasks)
        }
        return taskset, nil
}
```

--------------------------------

### Create an implementation worktree

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/use-workshops-with-ai-agents.md

Initializes a new git worktree for implementation-related tasks.

```console
$ git worktree add implementation
```

--------------------------------

### Display Workshop Information and Shell Prompt

Source: https://github.com/canonical/workshop/blob/main/docs/release-notes/v0.9.2.md

Demonstrates the new friendly host name format in workshop info and the shell prompt.

```console
$ workshop info rocm
name:      rocm
base:      ubuntu@22.04
project:   ~/work/reference-workshops/rocm-samples
hostname:  rocm.rocm-samples.wp
...

$ workshop shell
workshop@rocm:/project$
```

--------------------------------

### Run Workshop Command

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Executes the workshop command, retrieves project data, and formats workshop details and SDK information to the console.

```go
func (c *CmdInfo) Run(cmd *cobra.Command, av []string) error {
        cli, err := c.root.client()
        if err != nil {
                return err
        }

        project, err := cli.Project(c.root.project)
        if err != nil {
                return err
        }

        if len(av) == 0 {
                name, err := cli.SingleWorkshopName(project)
                if err != nil {
                        return err
                }
                av = []string{name}
        }

        workshop, err := cli.Workshop(project.Id, av[0])
        if err != nil {
                return err
        }
        slices.SortFunc(workshop.Sdks, func(a, b *client.Sdk) int { return cmp.Compare(a.Name, b.Name) })

        w := tabWriter()

        fmt.Fprintf(w, "name:\t%s\n", workshop.Name)
        fmt.Fprintf(w, "base:\t%s\n", workshop.Base)
        fmt.Fprintf(w, "project:\t%s\n", project.Path)
        fmt.Fprintf(w, "status:\t%s\n", strings.ToLower(workshop.Status))

        // get the workshop notes
        notes := workshop.Notes

        // get the SDKs notes (if there is an ongoing health check)
        for _, sdk := range workshop.Sdks {
                if sdk.Health != nil && sdk.Health.Code != "" {
                        notes = append(notes, sdk.Health.Code)
                }
        }

        // combine notes from workshop and its SDKs
        notesFormatted := strings.Join(notes, ",")
        if len(workshop.Notes) == 0 {
                notesFormatted = "-"
        }

        fmt.Fprintf(w, "notes:\t%s\n", notesFormatted)

        if len(workshop.Sdks) > 0 {
                fmt.Fprintf(w, "sdks:\n")
                for _, sk := range workshop.Sdks {
                        fmt.Fprintf(w, "  %s:\n", sk.Name)
                        if sk.Name == sdk.Sketch {
                                sk.Channel = sketchSdkChannel(project.Id, workshop.Name)
                                if sk.BuildTime.IsZero() {
                                        sk.BuildTime = sk.InstallTime
                                }
                        } else if sk.Channel == "" {
                                sk.Channel = "~"
                        }
                        fmt.Fprintf(w, "    tracking:\t%s\n", sk.Channel)

                        var buildTime string
                        if !sk.BuildTime.IsZero() {
                                buildTime = "\t" + sk.BuildTime.Format(time.DateOnly)
                        }
                        var version string
                        if sk.Version != "" {
                                version = "\t" + sk.Version
                        }
                        fmt.Fprintf(w, "    installed:%s%s\t(%s)\n", version, buildTime, sk.Revision)
                        if sk.Health != nil {
                                fmt.Fprintf(w, "    message:\t%s\n", sk.Health.Message)
                        }

                        if len(sk.Mounts) > 0 {
                                fmt.Fprintf(w, "    mounts:\n")
                                slices.SortFunc(sk.Mounts, func(a, b *client.Mount) int { return cmp.Compare(a.Plug.Name, b.Plug.Name) })
                                for _, mount := range sk.Mounts {
                                        if mount.HostSource != "" {
                                                fmt.Fprintf(w, "      %s:\n", mount.Plug.Name)
                                                fmt.Fprintf(w, "        host-source:\t%s\n", shortenDefaulPath(mount.HostSource))
                                                fmt.Fprintf(w, "        workshop-target:\t%s\n", mount.WorkshopTarget)
                                                continue
                                        }
                                        if mount.WorkshopSource != "" {
                                                fmt.Fprintf(w, "      %s:\n", mount.Plug.Name)
                                                fmt.Fprintf(w, "        workshop-source:\t%s\n", mount.WorkshopSource)
                                                fmt.Fprintf(w, "        workshop-target:\t%s\n", mount.WorkshopTarget)
                                                continue
                                        }
                                }
                        }
                }
        }

        w.Flush()

        return nil
}
```

--------------------------------

### Search for an SDK

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-1-get-started.md

Use the find command to verify an SDK's existence and view its publisher and version.

```console
$ sdk find ollama

  NAME    VERSION  PUBLISHER     SUMMARY
  ollama  0.20.2   Canonical     Get up and running with large language models
```

--------------------------------

### Execute Command Logic

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles the execution flow, including waiting for I/O connections and setting up pipes.

```go
// do actually runs the command.
func (e *execution) do(ctx context.Context, task *state.Task, backend workshop.Backend) error {
        // Wait till client has connected to "stdio" websocket (and "stderr" if
        // separating stderr), to avoid race conditions forwarding I/O.
        err := e.waitIOConnected(ctx, task.ID())
        if err != nil {
                return err
        }

        // Files/pipes to close before and after waiting for output to be finished sending.
        var beforeClosers []io.Closer
        var afterClosers []io.Closer

        var stdinReader, stdinWriter = io.Pipe()
        afterClosers = append(afterClosers, stdinReader)
```

--------------------------------

### Build and test SDK with sdkcraft

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/write-runtime-hooks.md

Commands to build the SDK and verify workshop configuration.

```console
$ sdkcraft try
```

```yaml
name: dev
base: ubuntu@22.04
sdks:
  - name: try-dotfiles-sdk
```

```console
$ workshop launch dev
```

--------------------------------

### Build and Test SDKs

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-4-craft-sdks.md

Commands to pack SDKs and optionally clear the build cache before testing.

```console
$ sdkcraft try

  Packed ollama_amd64_ubuntu@22.04.sdk
  Packed ollama_amd64_ubuntu@24.04.sdk
  ...
```

```console
$ sdkcraft clean && sdkcraft try
```

--------------------------------

### Disconnect All Plugs from a Slot

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-disconnect.rst

Example of disconnecting all plugs that are currently connected to a specific slot ('mount') within an SDK ('system') in a workshop ('nimble').

```console
$ workshop disconnect nimble/system:mount
```

--------------------------------

### Initialize Connected Objects

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Constructors for creating new connected plug and slot instances.

```go
// NewConnectedSlot creates an object representing a connected slot.
func NewConnectedSlot(slot *sdk.SlotInfo, staticAttrs, dynamicAttrs map[string]interface{}) *ConnectedSlot {
        var static map[string]interface{}
        if staticAttrs != nil {
                static = staticAttrs
        } else {
                static = slot.Attrs
        }
        return &ConnectedSlot{
                slotInfo:     slot,
                staticAttrs:  utils.CopyAttributes(static),
                dynamicAttrs: utils.NormalizeInterfaceAttributes(dynamicAttrs).(map[string]interface{}),
        }
}

// NewConnectedPlug creates an object representing a connected plug.
func NewConnectedPlug(plug *sdk.PlugInfo, staticAttrs, dynamicAttrs map[string]interface{}) *ConnectedPlug {
        var static map[string]interface{}
        if staticAttrs != nil {
                static = staticAttrs
        } else {
                static = plug.Attrs
        }
        return &ConnectedPlug{
                plugInfo:     plug,
                staticAttrs:  utils.CopyAttributes(static),
                dynamicAttrs: utils.NormalizeInterfaceAttributes(dynamicAttrs).(map[string]interface{}),
        }
}
```

--------------------------------

### Load Workshop Instance

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes a workshop object by loading its configuration and associated SDK profiles from an LXD instance.

```go
func (b *Backend) loadWorkshop(conn lxd.InstanceServer, inst *api.Instance, p workshop.Project) (*workshop.Workshop, error) {
        f, err := workshopFile(inst.Config)
        if err != nil {
                return nil, fmt.Errorf("cannot load workshop: %v", err)
        }

        sdks := map[string]sdk.Setup{}
        if buf, exist := inst.Config[workshop.ConfigWorkshopSdks]; exist {
                if err := json.Unmarshal([]byte(buf), &sdks); err != nil {
                        return nil, err
                }
        }

        profs := make(map[string]workshop.SdkProfile, len(sdks))
        for _, s := range sdks {
                sp, err := Profile(conn, p.ProjectId, f.Name, s.Name)
                if err != nil && !errors.Is(err, workshop.ErrSdkProfileNotFound) {
                        return nil, err
                }
                if errors.Is(err, workshop.ErrSdkProfileNotFound) {
                        continue
                }

                profs[s.Name] = sp
        }

        return &workshop.Workshop{
                Backend:  b,
                Project:  p,
                Name:     f.Name,
                Base:     f.Base,
                Running:  inst.StatusCode == api.Running || inst.StatusCode == api.Ready,
                Sdks:     sdks,
                Profiles: profs,
                File:     f,
        }, nil
}
```

--------------------------------

### Execute nested timing spans

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Starts a new span under a parent measurer, executes the provided function, and stops the span upon completion.

```Go
func Run(meas Measurer, label, summary string, f func(nestedTiming Measurer)) {
        nested := meas.StartSpan(label, summary)
        f(nested)
        nested.Stop()
}
```

--------------------------------

### Authenticate and Register SDK

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/publish-an-sdk.md

Commands to log in, verify the active account, and register a unique name for the SDK.

```console
$ sdkcraft login
```

```console
$ sdkcraft whoami
```

```console
$ sdkcraft register <NAME>
```

--------------------------------

### Initialize and configure Timings

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Basic structure definitions and initialization functions for the Timings and Span types.

```go
type Timings struct {
        tags    map[string]string
        timings []*Span
}

// Span represents a single performance measurement with optional nested measurements.
type Span struct {
        label, summary string
        start, stop    time.Time
        timings        []*Span
}

type Measurer interface {
        StartSpan(label, summary string) *Span
}

// New creates a Timings object. Tags provide extra information (such as "task-id" and "change-id")
// that can be used by the client when retrieving timings.
func New(tags map[string]string) *Timings {
        return &Timings{
                tags: tags,
        }
}

// AddTag sets a tag on the Timings object.
func (t *Timings) AddTag(tag, value string) {
        if t.tags == nil {
                t.tags = make(map[string]string)
        }
        t.tags[tag] = value
}

func startSpan(label, summary string) *Span {
        tmeas := &Span{
                label:   label,
                summary: summary,
                start:   timeNow(),
        }
        return tmeas
}
```

--------------------------------

### Connect to GCS Store

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes a GCS client, supporting local emulation via environment variables.

```go
func storeConnectImpl(ctx context.Context) (*ClientWrapper, error) {
	opt := option.WithoutAuthentication()
	testing := false
	if url := os.Getenv("SDK_STORE_URL"); url != "" { // Set STORAGE_EMULATOR_HOST environment variable for GSC.
		err := os.Setenv("STORAGE_EMULATOR_HOST", "localhost:8080")
		if err != nil {
			return nil, err
		}
		opt = option.WithEndpoint(url)
		testing = true
	}
	client, err := storage.NewClient(ctx, opt)
	if err != nil {
		return nil, err
	}
	return &ClientWrapper{client, testing}, nil
}
```

--------------------------------

### Sketch SDK Template Structure

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the YAML structure for the sketch SDK, including placeholders for base configuration and commented-out examples for lifecycle hooks.

```yaml
var sketchTemplate = `# Sketch SDK for %s
# Sketch SDK provides local customisation of this specific workshop.

# To read more about SDKs, their components and syntax, see:
# https://canonical-workshop.readthedocs-hosted.com/en/latest/explanation/sdks/
name: sketch
base: %s

hooks:
  # EXAMPLE: setup-base runs once at workshop launch, use it to install some packages.
  # See https://canonical-workshop.readthedocs-hosted.com/en/latest/explanation/sdks/hooks/
  # setup-base: |
    # apt-get install -y --no-install-recommends PACKAGE...
    # snap install SNAP...

  # EXAMPLE: check-health runs after all SDK setup completes, call 'workshopctl set-health okay' for OK.
  # See https://canonical-workshop.readthedocs-hosted.com/en/latest/explanation/sdks/hooks/
  # check-health: |
    # if CHECK\_HEALTH\_COMMAND ; then
    #   workshopctl set-health okay
    # else
    #   workshopctl set-health --code=installation-failed error "Installation failed"
    # fi

plugs:
  # EXAMPLE: forward your SSH agent into the workshop enabling 'git push' inside the workshop.
  # See https://canonical-workshop.readthedocs-hosted.com/en/latest/explanation/interfaces/ssh-interface/
```

--------------------------------

### Generate SDK Interface Summary

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Creates a formatted string summarizing bad plugs or slots in an SDK.

```go
// BadInterfacesSummary returns a summary of the problems of bad plugs
// and slots in the sdk.
func BadInterfacesSummary(sdkInfo *Info) string {
        inverted := make(map[string][]string)
        for name, reason := range sdkInfo.BadInterfaces {
                inverted[reason] = append(inverted[reason], name)
        }
        var buf bytes.Buffer
        fmt.Fprintf(&buf, "%q SDK has bad plugs or slots: ", sdkInfo.Name)
        reasons := make([]string, 0, len(inverted))
        for reason := range inverted {
                reasons = append(reasons, reason)
        }
        sort.Strings(reasons)
        for _, reason := range reasons {
                names := inverted[reason]
                sort.Strings(names)
                for i, name := range names {
                        if i > 0 {
                                buf.WriteString(", ")
                        }
                        buf.WriteString(name)
                }
                fmt.Fprintf(&buf, " (%s); ", reason)
        }
        return strings.TrimSuffix(buf.String(), "; ")
}
```

--------------------------------

### Generate Custom reStructured Text for Cobra Commands

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Uses a template to render command details, flags, and structured examples into reStructured Text format.

```go
// GenReSTCustom creates custom reStructured Text output with the specified formatting.
func GenReSTCustom(cmd *cobra.Command, w io.Writer, linkHandler func(string, string) string) error {
        cmd.InitDefaultHelpCmd()
        cmd.InitDefaultHelpFlag()

        // Prepare data for the template
        name := cmd.CommandPath()

        short := cmd.Short
        long := cmd.Long
        if len(long) == 0 {
                long = short
        }
        ref := "ref_" + strings.ReplaceAll(name, " ", "_")

        // Compute the heading separator
        headinglen := len(name)

        // Break down examples for further formatting
        entries := strings.Split(cmd.Example, "\n\n")
        var structuredExamples []ExampleDetail

        for _, entry := range entries {
                entry = strings.TrimSpace(entry)
                lines := strings.Split(entry, "\n")
                var infoLines, usageLines []string

                for i, line := range lines {
                        line = strings.TrimSpace(line)
                        if strings.HasPrefix(line, "$") {
                                infoLines = lines[:i]
                                usageLines = lines[i:]
                                break
                        }
                }

                if len(infoLines) > 0 && len(usageLines) > 0 {
                        structuredExamples = append(structuredExamples, ExampleDetail{
                                Info:  strings.Join(infoLines, "\n"),
                                Usage: strings.Join(usageLines, "\n"),
                        })
                }
        }

        // Collect flag details
        flags := cmd.NonInheritedFlags()
        var flagDetails []FlagDetail
        flags.VisitAll(func(flag *pflag.Flag) {
                flagDetails = append(flagDetails, FlagDetail{
                        Name:         flag.Name,
                        Usage:        flag.Usage,
                        DefaultValue: flag.DefValue,
                })
        })

        // Prepare the template data
        data := struct {
                Ref         string
                CommandName string
                Short       string
                Long        string
                Synopsis    string
                Examples    []ExampleDetail
                Flags       []FlagDetail
                HeadingLen  int
        }{
                Ref:         ref,
                CommandName: name,
                Short:       short,
                Long:        long,
                Synopsis:    cmd.UseLine(),
                Examples:    structuredExamples,
                Flags:       flagDetails,
                HeadingLen:  headinglen,
        }

        // Define the helper functions
        funcMap := template.FuncMap{
                "indent": func(spaces int, ss ...string) string {
                        padding := strings.Repeat(" ", spaces)
                        var indentedStrings []string
                        for _, s := range ss {
                                indentedStrings = append(indentedStrings, padding+strings.ReplaceAll(s, "\n", "\n"+padding))
                        }
                        return strings.Join(indentedStrings, "\n")
                },
                "repeat": strings.Repeat,
        }

        // Read and parse the template
        tmplContent, err := templates.ReadFile("command.tmpl")
        if err != nil {
                return err
        }

        tmpl, err := template.New("command").Funcs(funcMap).Parse(string(tmplContent))
        if err != nil {
                return err
        }

        // Render the template
        buf := new(bytes.Buffer)
        if err = tmpl.Execute(buf, data); err != nil {
                return err
        }

        _, err = buf.WriteTo(w)
        return err
}
```

--------------------------------

### Workshop connect command syntax

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

General usage pattern for connecting a plug to a slot.

```console
$ workshop connect <WORKSHOP>/<SDK>:<PLUG> [<WORKSHOP>/<SDK>][:<SLOT>] [flags]
```

--------------------------------

### Release SDK Revision to Multiple Channels

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-release.rst

Example of releasing a specific SDK revision (revision 9) to multiple channels ('beta' and 'edge') simultaneously.

```console
$ sdkcraft release my-sdk 9 beta,edge
```

--------------------------------

### Fake Workshop Backend and Filesystem

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Mock implementations for testing backend operations and filesystem interactions.

```go
        userName, ok := ctx.Value(workshop.ContextUser).(string)
        if !ok {
                return "", "", fmt.Errorf("context key user not found")
        }
        return userName, projectId, nil
}
func (b *FakeWorkshopBackend) Download(ctx context.Context, base string, report *progress.Reporter) error {
        b.DownloadBaseCalls = append(b.DownloadBaseCalls, &DownloadCall{Base: base})
        if b.DownloadBaseCallback != nil {
                return b.DownloadBaseCallback(ctx, base, report)
        }
        return nil
}

/* Fake workshop fs implementation for tests */

type FakeInstanceFs struct {
        afero.Fs
}

func NewWorkshopFs(baseDir string) (*FakeInstanceFs, error) {
        var fs FakeInstanceFs
        osfs := afero.NewOsFs()
        rndstring := randutil.RandomString(10)
        wfspath := filepath.Join(baseDir, rndstring)
        err := os.MkdirAll(wfspath, 0700)
        if err != nil {
                return nil, err
        }
        fs.Fs = afero.NewBasePathFs(osfs, wfspath)
        return &fs, nil
}

func (w *FakeInstanceFs) Symlink(source, target string) error {
        return w.Fs.(*afero.BasePathFs).SymlinkIfPossible(source, target)
}

func (w *FakeInstanceFs) ReadLink(p string) (string, error) {
        return w.Fs.(*afero.BasePathFs).ReadlinkIfPossible(p)
}

func (w *FakeInstanceFs) Close() {
}
```

--------------------------------

### Update LXD Instance State

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Updates the state of an LXD instance to a desired action, such as starting or stopping, while handling ETag validation and context-aware operations.

```go
func (s *Backend) updateInstanceState(conn lxd.InstanceServer, ctx context.Context, name, action string, force bool) error {
        projectId, ok := ctx.Value(workshop.ContextProjectId).(string)
        if !ok {
                return fmt.Errorf("context key project-id not found")
        }

        inst, etag, err := conn.GetInstance(InstanceName(name, projectId))
        if err != nil {
                return err
        }

        // Do nothing if the instance is already in the desired state
        if (inst.StatusCode == api.Running && action == "start") ||
                (inst.StatusCode == api.Stopped && action == "stop") {
                return nil
        }

        req := api.InstanceStatePut{
                Action:  action,
                Timeout: 45,
                Force:   force,
        }

        op, err := conn.UpdateInstanceState(inst.Name, req, etag)
        if err != nil {
                return err
        }

        return op.WaitContext(ctx)
}
```

--------------------------------

### Run Okay Command

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Executes the logic to acknowledge warnings by updating the timestamp via the client.

```go
func (c *CmdOkay) Run(cmd *cobra.Command, av []string) error {
        last, err := lastWarningTimestamp()
        if err != nil {
                return err
        }

        cli, err := c.root.client()
        if err != nil {
                return err
        }

        return cli.Okay(last)
}
```

--------------------------------

### Initialize SDK Info from YAML

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Parses raw YAML data into an Info struct and triggers the sanitization process.

```go
var SanitizePlugsSlots = func(snapInfo *Info) {
        panic("SanitizePlugsSlots function not set")
}

func ReadSdkInfo(yamlData []byte, projectId, workshop string) (*Info, error) {
        var sdkYaml sdkYaml
        err := yaml.Unmarshal(yamlData, &sdkYaml)
        if err != nil {
                return &Info{}, err
        }

        if sdkYaml.Type == "" {
                sdkYaml.Type = Regular.String()
        }

        sdkInfo := &Info{
                ProjectId:     projectId,
                Workshop:      workshop,
                Name:          sdkYaml.Name,
                Base:          sdkYaml.Base,
                Version:       sdkYaml.Version,
                Type:          Type(sdkYaml.Type),
                BuildTime:     sdkYaml.BuildTime,
                Plugs:         make(map[string]*PlugInfo),
                PlugBinds:     make(map[string]*PlugBind),
                Slots:         make(map[string]*SlotInfo),
                BadInterfaces: make(map[string]string),
        }

        if err := setPlugsFromSdkYaml(&sdkYaml, sdkInfo); err != nil {
                return nil, err
        }

        if err := setSlotsFromSdkYaml(&sdkYaml, sdkInfo); err != nil {
                return nil, err
        }

        SanitizePlugsSlots(sdkInfo)
        return sdkInfo, nil
}
```

--------------------------------

### Release SDK Revision to Latest/Stable Channel

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-release.rst

Example of releasing a specific SDK revision (revision 8) to the 'latest/stable' channel, indicating a track and risk level.

```console
$ sdkcraft release my-sdk 8 latest/stable
```

--------------------------------

### Publish an SDK to the Store

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-4-craft-sdks.md

Authenticates the user, registers the SDK name, and uploads the artifact to the SDK Store.

```console
$ sdkcraft login
$ sdkcraft register ollama
$ sdkcraft upload ./ollama_amd64_ubuntu@24.04.sdk --release latest/beta
```

--------------------------------

### Meter Interface Definition

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the contract for progress tracking, including methods for starting, updating, and finishing progress, as well as handling notifications and writing data.

```go
type Meter interface {
        // Start progress with max "total" steps
        Start(label string, total float64)

        // set progress to the "current" step
        Set(current float64)

        // set "total" steps needed
        SetTotal(total float64)

        // Finish the progress display
        Finished()

        // Indicate indefinite activity by showing a spinner
        Spin(msg string)

        // interface for writer
        Write(p []byte) (n int, err error)

        // notify the user of miscellaneous events
        Notify(string)
}
```

--------------------------------

### Workshop refresh error example

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/fix-workshops/debug-issues.md

This console output shows an error encountered during a 'workshop refresh' command, specifically failing on a hook for an SDK. It indicates a problem that requires further investigation.

```console
$ workshop refresh

  Error: cannot perform the following tasks:
  - Run hook "setup-base" for "go" SDK (command failed with an error code (1))
  Refresh aborted
```

--------------------------------

### Repository Structure and Initialization

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the Repository struct for managing plugs and slots, and provides a constructor for initialization.

```go
// Repository stores all known plugs and slots and ifaces.
type Repository struct {
		// Protects the internals from concurrent access.
		m      sync.Mutex
		ifaces map[string]Interface
		// Indexed by [project-id-workshop-sdk][plugName]
		plugs map[string]map[string]*sdk.PlugInfo
		// Indexed by [project-id-workshop-sdk][slotName]
		slots map[string]map[string]*sdk.SlotInfo
		// given a slot and a plug, are they connected?
		slotPlugs map[*sdk.SlotInfo]map[*sdk.PlugInfo]*Connection
		// given a plug and a slot, are they connected?
		plugSlots map[*sdk.PlugInfo]map[*sdk.SlotInfo]*Connection
		backends  []SecurityBackend
}

// NewRepository creates an empty plug repository.
func NewRepository() *Repository {
	repo := &Repository{
		ifaces:    make(map[string]Interface),
		plugs:     make(map[string]map[string]*sdk.PlugInfo),
		slots:     make(map[string]map[string]*sdk.SlotInfo),
		slotPlugs: make(map[*sdk.SlotInfo]map[*sdk.PlugInfo]*Connection),
		plugSlots: make(map[*sdk.PlugInfo]map[*sdk.SlotInfo]*Connection),
	}

	return repo
}
```

--------------------------------

### Define a workshop with an unstable SDK

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/fix-workshops/debug-issues.md

This YAML defines a workshop named 'dev-volatile' that uses an unstable SDK from the 'latest/edge' channel. It's a common setup for testing or developing with bleeding-edge features.

```yaml
name: dev-volatile
base: ubuntu@22.04
sdks:
  - name: go
    channel: edge
```

--------------------------------

### Inspect SDK details

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-1-get-started.md

View available channels, bases, and build information for a specific SDK.

```console
$ sdk info ollama

  name:       ollama
  publisher:  Canonical (canonical)
  license:    MIT
  website:    https://github.com/canonical/ollama-sdk

  Get up and running with Llama 3.3, ...

  CHANNELS
    CHANNEL        VERSION  BUILD       BASE          REV   SIZE
    latest/stable  0.20.2   2026-04-15  ubuntu@24.04    7  2.27GB
                                        ubuntu@22.04    8  2.27GB
    ...
    cpu/stable     0.20.2   2026-04-15  ubuntu@24.04    2  15.22MB
                                        ubuntu@22.04    5  15.22MB
    cpu/candidate  ^
    cpu/beta       ^
    cpu/edge       ^
```

--------------------------------

### LXD Backend Implementation

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Core logic for the LXD backend, including instance creation and configuration management.

```go
package lxdbackend

import (
        "context"
        _ "embed"
        "encoding/json"
        "errors"
        "fmt"
        "net/http"
        "os"
        "path/filepath"
        "runtime"
        "sync"

        lxd "github.com/canonical/lxd/client"
        "github.com/canonical/lxd/shared/api"
        "golang.org/x/exp/slices"
        "gopkg.in/yaml.v3"

        "github.com/canonical/workshop/internal/dirs"
        "github.com/canonical/workshop/internal/logger"
        "github.com/canonical/workshop/internal/sdk"
        "github.com/canonical/workshop/internal/workshop"
)

const (
        LxdSock     = "/var/snap/lxd/common/lxd/unix.socket"
        storagePool = "default"
)

var (
        defaultDevices     = createDefaultDevices
        checkNvidiaRuntime = checkNvidia
)

var (
        // However many backend instances are created, downloads are always a single
        // instance map with the LXD backend.
        imageLock        sync.Mutex
        currentDownloads map[string]*downloadOp
)

//go:embed start_command.sh
var startCommand string

func init() {
        imageLock.Lock()
        defer imageLock.Unlock()
        if currentDownloads == nil {
                currentDownloads = make(map[string]*downloadOp)
        }
}

type Backend struct {
}

func InstanceName(name string, project_id string) string {
        return fmt.Sprintf("%s-%s", name, project_id)
}

func ImageAlias(name string) string {
        return fmt.Sprintf("workshop-%s-%s", name, runtime.GOARCH)
}

func New() (*Backend, error) {
        server := Backend{}

        if srv := os.Getenv("WORKSHOP_IMAGE_SERVER"); srv != "" {
                imageServer = srv
        }

        return &server, nil
}

func (s *Backend) LaunchWorkshop(ctx context.Context, file *workshop.File) error {
        var err error
        var image *api.Image

        conn, err := s.LxdClient(ctx)
        if err != nil {
                return err
        }
        defer conn.Disconnect()

        projectId, ok := ctx.Value(workshop.ContextProjectId).(string)
        if !ok {
                return fmt.Errorf("context key project-id not found")
        }

        userName, ok := ctx.Value(workshop.ContextUser).(string)
        if !ok {
                return fmt.Errorf("context key user not found")
        }

        // Check if we have the base image stored locally
        alias, _, err := conn.GetImageAlias(ImageAlias(file.Base))
        if err != nil {
                return err
        }

        image, _, err = conn.GetImage(alias.Target)
        if err != nil {
                return err
        }

        usr, err := workshop.LookupUsername(userName)
        if err != nil {
                return err
        }

        config, err := s.workshopConfig(projectId, usr.Uid, usr.Gid, file)
        if err != nil {
                return err
        }
        req := api.InstancesPost{
                InstancePut: api.InstancePut{
                        Devices: defaultDevices(),
                        Config:  config,
                },
                Name: InstanceName(file.Name, projectId),
                Type: api.InstanceType("container"),
                Source: api.InstanceSource{
                        Type:        "image",
                        Fingerprint: image.Fingerprint,
                        Project:     LxdProjectName(userName),
                },
        }

        op, err := conn.CreateInstance(req)
        if err != nil {
                return err
        }

        return op.WaitContext(ctx)
}
```

--------------------------------

### LXD Backend Initialization and Client Connection

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Backend structure definition and helper function to establish a connection to the LXD Unix socket.

```go
const (
        LxdSock = "/var/snap/lxd/common/lxd/unix.socket"
)

var workshopFs = sftpFs

type Backend struct {
}

func (b *Backend) Initialize() error {
        return nil
}

// Name returns the name of the backend.
func (b *Backend) Name() interfaces.SecuritySystem {
        return interfaces.SecurityLxdDevice
}

func lxdClient(ctx context.Context) (lxd.InstanceServer, error) {
        user, ok := ctx.Value(workshop.ContextUser).(string)
        if !ok {
                return nil, fmt.Errorf("context key %s not found", workshop.ContextUser)
        }

        srv, err := lxd.ConnectLXDUnixWithContext(ctx, LxdSock, nil)
        if err != nil {
                return nil, err
        }

        return srv.UseProject("workshop." + user), nil
}
```

--------------------------------

### Retrieve Project List

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Fetches the list of available projects from the workshop backend.

```go
package daemon

import (
        "encoding/json"
        "errors"
        "net/http"

        "github.com/canonical/workshop/internal/workshop"
)

func v1GetProjects(c *Command, r *http.Request, _ *userState) Response {
        st := c.d.overlord.State()
        st.Lock()
        defer st.Unlock()

        projects, err := c.d.overlord.WorkshopBackend().Projects(r.Context())
        if err != nil {
                return statusInternalError("cannot get projects list: %w", err)
        }
```

--------------------------------

### Run a command with environment and directory settings

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Configures environment variables and working directory before executing the build command.

```console
$ workshop exec --env GO111MODULE=off -w /project nimble -- go build -x
```

--------------------------------

### Basic workshop run command

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-run.rst

Run a named action within a specified workshop in the current project directory. Ensure the workshop is in a 'Ready' or 'Waiting' state before execution.

```console
$ workshop run nimble build
```

--------------------------------

### Add API Routes

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes the router and registers API handlers.

```go
func (d *Daemon) addRoutes() {
        d.router = mux.NewRouter()

        for _, c := range api {
                c.d = d
                if c.PathPrefix == "" {
                        d.router.Handle(c.Path, c).Name(c.Path)
                } else {
                        d.router.PathPrefix(c.PathPrefix).Handler(c).Name(c.PathPrefix)
                }
        }

        // also maybe add a /favicon.ico handler...

        d.router.NotFoundHandler = statusNotFound("invalid API endpoint requested")
}
```

--------------------------------

### Version Management

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Utilities for handling build-time versioning and mocking versions during tests.

```go
var Version = "unknown"

func MockVersion(version string) (restore func()) {
        old := Version
        Version = version
        return func() { Version = old }
}
```

--------------------------------

### Client Utility Methods

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for managing idle connections, maintenance status, and warning summaries.

```go
// CloseIdleConnections closes any API connections that are currently unused.
func (client *Client) CloseIdleConnections() {
	c, ok := client.doer.(*http.Client)
	if ok {
		c.CloseIdleConnections()
	}
}

// Maintenance returns an error reflecting the daemon maintenance status or nil.
func (client *Client) Maintenance() error {
	return client.maintenance
}

// WarningsSummary returns the number of warnings that are ready to be shown to
// the user, and the timestamp of the most recently added warning (useful for
// silencing the warning alerts, and OKing the returned warnings).
func (client *Client) WarningsSummary() (count int, timestamp time.Time) {
	return client.warningCount, client.warningTimestamp
}
```

--------------------------------

### Implement Status Helper Methods

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Provides methods to check if a status is ready and to retrieve its string representation.

```go
func (s Status) Ready() bool {
        switch s {
        case DoneStatus, UndoneStatus, HoldStatus, ErrorStatus:
                return true
        }
        return false
}

func (s Status) String() string {
        switch s {
        case DefaultStatus:
                return "Default"
        case DoStatus:
                return "Do"
        case DoingStatus:
                return "Doing"
        case DoneStatus:
                return "Done"
        case WaitStatus:
                return "Wait"
        case AbortStatus:
                return "Abort"
        case UndoStatus:
                return "Undo"
        case UndoingStatus:
                return "Undoing"
        case UndoneStatus:
                return "Undone"
        case HoldStatus:
                return "Hold"
        case ErrorStatus:
                return "Error"
        }
        panic(fmt.Sprintf("internal error: unknown task status code: %d", s))
}
```

--------------------------------

### Configure LXD connection arguments

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Reads TLS certificates and keys from the workshop directory to construct connection arguments for LXD.

```go
func lxdConnectionArgs() (*lxd.ConnectionArgs, error) {
        args := &lxd.ConnectionArgs{}

        // Server certificate
        scrt := filepath.Join(dirs.WorkshopTlsDir, "server.crt")
        if osutil.FileExists(scrt) {
                content, err := os.ReadFile(scrt)
                if err != nil {
                        return nil, err
                }

                args.TLSServerCert = string(content)
        }

        // Client certificate
        ccrt := filepath.Join(dirs.WorkshopTlsDir, "client.crt")
        if osutil.FileExists(ccrt) {
                content, err := os.ReadFile(ccrt)
                if err != nil {
                        return nil, err
                }

                args.TLSClientCert = string(content)
        }

        // Client CA
        cca := filepath.Join(dirs.WorkshopTlsDir, "client.ca")
        if osutil.FileExists(cca) {
                content, err := os.ReadFile(cca)
                if err != nil {
                        return nil, err
                }

                args.TLSCA = string(content)
        }

        // Client key
        ckey := filepath.Join(dirs.WorkshopTlsDir, "client.key")
        if osutil.FileExists(ckey) {
                content, err := os.ReadFile(ckey)
                if err != nil {
                        return nil, err
                }

                pemKey, _ := pem.Decode(content)
                // Golang has deprecated all methods relating to PEM encryption due to a vulnerability.
                // However, the weakness does not make PEM unsafe for our purposes as it pertains to password protection on the
                // key file (client.key is only readable to the user in any case), so we'll ignore deprecation.
                if x509.IsEncryptedPEMBlock(pemKey) { //nolint:staticcheck
                        return nil, fmt.Errorf("Private key is password protected and no helper was configured")
                }

                args.TLSClientKey = string(content)
        }
        return args, nil
}
```

--------------------------------

### Refresh and remount workshop

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/add-mounts.md

Commands to apply configuration changes and point a plug to a specific host directory.

```console
$ workshop refresh
$ workshop stop dev
$ workshop remount dev/uv:readonly ~/refdata
$ workshop start dev
```

--------------------------------

### Create or Load LXD Project

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Checks for the existence of an LXD project and creates it if it is not found, using a predefined configuration.

```go
if err := createOrLoadLxdProject(conn, LxdSystemProjectName(username)); err != nil {
                return err
        }
        return nil
}

func createOrLoadLxdProject(conn lxd.InstanceServer, projectName string) error {
        if _, _, err := conn.GetProject(projectName); err != nil {
                if api.StatusErrorCheck(err, http.StatusNotFound) {
                        return conn.CreateProject(api.ProjectsPost{
                                ProjectPut: api.ProjectPut{
                                        Config: lxdProjectConfig,
                                },
                                Name: projectName,
                        })
                } else {
                        return err
                }
        }
        return nil
}
```

--------------------------------

### TaskRunner Configuration Methods

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for registering task handlers, error callbacks, and cleanup functions.

```go
// OnTaskError sets an error callback executed when any task errors out.
func (r *TaskRunner) OnTaskError(f func(err error)) {
	r.taskErrorCallback = f
}

// AddHandler registers the functions to concurrently call for doing and
// undoing tasks of the given kind. The undo handler may be nil.
func (r *TaskRunner) AddHandler(kind string, do, undo HandlerFunc) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.handlers[kind] = handlerPair{do, undo}
}

// AddOptionalHandler register functions for doing and undoing tasks that match
// the given predicate if no explicit handler was registered for the task kind.
func (r *TaskRunner) AddOptionalHandler(match func(t *Task) bool, do, undo HandlerFunc) {
	r.optional = append(r.optional, optionalHandler{match, handlerPair{do, undo}})
}

// AddCleanup registers a function to be called after the change completes,
// for cleaning up data left behind by tasks of the specified kind.
// The provided function will be called no matter what the final status of the
// task is. This mechanism enables keeping data around for a potential undo
// until there's no more chance of the task being undone.
//
// The cleanup function is run concurrently with other cleanup functions,
// despite any wait ordering between the tasks. If it returns an error,
// it will be retried later.
//
// The handler for tasks of the provided kind must have been previously
// registered before AddCleanup is called for it.
func (r *TaskRunner) AddCleanup(kind string, cleanup HandlerFunc) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.handlers[kind]; !ok {
		panic("internal error: attempted to register cleanup for unknown task kind")
	}
	r.cleanups[kind] = cleanup
}
```

--------------------------------

### List Connections for All Workshops

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-connections.rst

Use this command to list all interface connections for all workshops in the current project directory. This includes disconnected plugs if the --all flag is used.

```console
$ workshop connections
```

--------------------------------

### Execute Connect Command

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles the logic for parsing arguments and executing the connection between a plug and a slot.

```go
func (c *CmdConnect) Run(cmd *cobra.Command, av []string) error {
	cli, err := c.root.client()
	if err != nil {
		return err
	}

	project, err := cli.Project(c.root.project)
	if err != nil {
		return err
	}

	plugRef, err := client.ParseShortPlugRef(av[0])
	if err != nil {
		return err
	}
	plugRef.ProjectId = project.Id

	slotRef := &client.SlotRef{}
	if len(av) > 1 {
		// check if the second arg is a short version of the system-provided slot reference
		if strings.HasPrefix(av[1], ":") {
			slotRef.Workshop = plugRef.Workshop
			slotRef.Sdk = "system"
			slotRef.Name = av[1][1:]
		} else {
			slotRef, err = client.ParseShortSlotRef(av[1])
			if err != nil {
				// see if an SDK (empty slot) reference provided
				slotRef, err = client.ParseSlotSdkRef(av[1])
				if err != nil {
					return err
				}
			}
		}
		slotRef.ProjectId = plugRef.ProjectId
	} else {
		// workshop connect <workshop>/<sdk>:plug which means that the plug will
		// be attempted to connect to the same name slot in the system SDK (if
		// exists)
		slotRef.ProjectId = plugRef.ProjectId
		slotRef.Workshop = plugRef.Workshop
		slotRef.Sdk = "system"
		slotRef.Name = plugRef.Name
	}

	if plugRef.ProjectId != slotRef.ProjectId {
		return fmt.Errorf("cannot connect plugs and slots across different workshops")
	}

	if plugRef.Workshop != slotRef.Workshop {
		return fmt.Errorf("cannot connect plugs and slots across different workshops")
	}

	changeId, err := cli.Connect(plugRef.ProjectId, plugRef.Workshop, plugRef.Sdk, plugRef.Name,
		slotRef.ProjectId, slotRef.Workshop, slotRef.Sdk, slotRef.Name, nil)
	if err != nil {
		return err
	}

	if _, err := c.wait(cli, changeId); err != nil {
		if err == errNoWait {
			return nil
		}
		return err
	}

	return nil
}
```

--------------------------------

### Define Client Configuration

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Configuration structure for customizing the Workshop client behavior, including base URL and socket path settings.

```go
type Config struct {
        // BaseURL contains the base URL where the Workshop daemon is expected to be.
        // It can be empty for a default behavior of talking over a unix socket.
        BaseURL string

        // Socket is the path to the unix socket to use.
        Socket string

        // DisableKeepAlive indicates that the connections should not be kept
        // alive for later reuse (the default is to keep them alive).
        DisableKeepAlive bool

        // UserAgent is the User-Agent header sent to the Workshop daemon.
        UserAgent string
}
```

--------------------------------

### Initialize LXD

Source: https://github.com/canonical/workshop/blob/main/docs/contributing/maintenance.md

Initialize the LXD environment after updating group permissions and restarting the session.

```console
$ lxd init
```

--------------------------------

### Initialize LXD Project Namespace

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines project configuration constants and provides functions to manage LXD project naming and initialization.

```go
package lxdbackend

import (
        "bytes"
        "context"
        "encoding/json"
        "fmt"
        "net/http"
        "strings"

        lxd "github.com/canonical/lxd/client"
        "github.com/canonical/lxd/shared/api"

        "github.com/canonical/workshop/internal/logger"
        "github.com/canonical/workshop/internal/osutil"
        "github.com/canonical/workshop/internal/workshop"
)

var lxdProjectConfig = map[string]string{
        "features.images":          "false",
        "features.profiles":        "true",
        "features.storage.volumes": "true",
}

func LxdProjectName(user string) string {
        return "workshop." + user
}

func lxdProjectUser(project string) string {
        if strings.HasPrefix(project, "workshop.") {
                return strings.TrimPrefix(project, "workshop.")
        }
        return ""
}

func LxdSystemProjectName(user string) string {
        return LxdProjectName(user) + ".stash"
}

// Initialise the Workshop project namespace.
func InitLxdProject(conn lxd.InstanceServer, username string) error {
        if username == "" {
                return fmt.Errorf("cannot init LXD project: username is empty")
        }
        if err := createOrLoadLxdProject(conn, LxdProjectName(username)); err != nil {
                return err
        }
```

--------------------------------

### Global Configuration and Streams

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines standard I/O streams and the global client configuration.

```go
var (
        // Standard streams, redirected for testing.
        Stdin  io.Reader = os.Stdin
        Stdout io.Writer = os.Stdout
        Stderr io.Writer = os.Stderr
)

// ClientConfig is the configuration of the Client used by all commands.
var ClientConfig = client.Config{
        // we need the powerful socket
        Socket: dirs.SocketPath,
}
```

--------------------------------

### TaskSet Definition and Initialization

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Structures and constructors for managing sets of tasks.

```go
type TaskSetEdge string
```

```go
type TaskSet struct {
        tasks []*Task

        edges map[TaskSetEdge]*Task
}
```

```go
func NewTaskSet(tasks ...*Task) *TaskSet {
        // we init all members of TaskSet so that `go vet` will not complain
        return &TaskSet{tasks, nil}
}
```

```go
func (ts TaskSet) MaybeEdge(e TaskSetEdge) *Task {
        return ts.edges[e]
}
```

--------------------------------

### Helper function to create WorkshopFileInfo

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Utility to instantiate a WorkshopFileInfo object.

```go
func workshopFileToInfo(pid string, name string, path string) *WorkshopFileInfo {
        var ws WorkshopFileInfo
        ws.ProjectId = pid
        ws.Name = name
        ws.Path = path
        return &ws
}
```

--------------------------------

### Implement SDK Reader

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Connects to the SDK store and returns an io.ReadCloser for the requested SDK, configured with custom backoff policies.

```go
func storeSdkReaderImpl(ctx context.Context, setup sdk.Setup) (io.ReadCloser, error) {
        client, err := storeConnect(ctx)
        if err != nil {
                return nil, err
        }
        defer client.Close()

        var sa = strings.Split(setup.Channel, "/")
        if len(sa) != 2 {
                return nil, fmt.Errorf("%s has an invalid channel %s, must take the form <track>/<risk>", setup.Name, setup.Channel)
        }
        track, risk := sa[0], sa[1]
        bkt := client.Bucket(SDK_STORE_BUCKET_NAME)

        obj := bkt.Object(fmt.Sprintf("%s/%s/%s/%s.sdk", setup.Name, track, risk, setup.Name)).Retryer(
                storage.WithBackoff(gax.Backoff{Initial: 2 * time.Second}),
                storage.WithPolicy(storage.RetryIdempotent),
        )
        r, err := obj.NewReader(ctx)
        if err != nil {
                if errors.Is(err, storage.ErrObjectNotExist) {
                        return nil, errors.New("SDK not found")
                }
                return nil, err
        }
        return r, nil
}
```

--------------------------------

### Define SDK Parts

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-4-craft-sdks.md

Specify source plugins for downloading binaries and including local service files.

```yaml
# ...
parts:
  ollama:
    plugin: dump
    source: https://github.com/ollama/ollama/releases/download/v${CRAFT_PROJECT_VERSION}/ollama-linux-amd64.tgz
    source-type: tar
  user-service:
    plugin: dump
    source: ollama.service
    source-type: file
```

--------------------------------

### Create Directories with Ownership

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Recursively creates directories and applies specific UID/GID ownership using a mutex for concurrency safety.

```go
var mu sync.Mutex

// MkdirAllChown is like os.MkdirAll but it calls os.Chown on any
// directories it creates.
func MkdirAllChown(path string, perm os.FileMode, uid sys.UserID, gid sys.GroupID) error {
        mu.Lock()
        defer mu.Unlock()
        return mkdirAllChown(filepath.Clean(path), perm, uid, gid)
}

func mkdirAllChown(path string, perm os.FileMode, uid sys.UserID, gid sys.GroupID) error {
        // split out so filepath.Clean isn't called twice for each inner path
        if s, err := os.Stat(path); err == nil {
                if s.IsDir() {
                        return nil
                }

                // emulate os.MkdirAll
                return &os.PathError{
                        Op:   "mkdir",
                        Path: path,
                        Err:  syscall.ENOTDIR,
                }
        }

        dir := filepath.Dir(path)
        if dir != "/" {
                if err := mkdirAllChown(dir, perm, uid, gid); err != nil {
                        return err
                }
        }

        cand := path + ".mkdir-new"

        if err := os.Mkdir(cand, perm); err != nil && !os.IsExist(err) {
                return err
        }

        if err := sys.ChownPath(cand, uid, gid); err != nil {
                return err
        }

        if err := os.Rename(cand, path); err != nil {
                return err
        }

        fd, err := os.Open(dir)
        if err != nil {
                return err
        }
        defer fd.Close()

        return fd.Sync()
}
```

--------------------------------

### Access Workshop Filesystem

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Retrieves an SFTP client for a specific instance to interact with its filesystem.

```go
func (s \*Backend) WorkshopFs(ctx context.Context, name string) (workshop.WorkshopFs, error) {
        conn, err := s.LxdClient(ctx)
        if err != nil {
                return nil, err
        }
        defer conn.Disconnect()

        projectId, ok := ctx.Value(workshop.ContextProjectId).(string)
        if !ok {
                return nil, fmt.Errorf("context key project-id not found")
        }

        sftp, err := conn.GetInstanceFileSFTP(InstanceName(name, projectId))
        if err != nil {
                return nil, err
        }

        return workshop.NewWorkshopFs(sftp), nil
}
```

--------------------------------

### Scaffold workshop definition

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-1-get-started.md

Initialize a workshop definition file with specified base and SDK channels.

```console
$ workshop init dev --sdks ollama/cpu/stable --base ubuntu@22.04

  "dev" workshop created at /home/user/ollama-python-project/.workshop/dev.yaml
```

```yaml
name: dev
base: ubuntu@22.04
sdks:
  - name: ollama
    channel: cpu/stable
```

--------------------------------

### Implement Connection Management Methods

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Client methods for retrieving connection lists and performing connect/disconnect actions.

```go
// Connections returns matching plugs, slots and their connections. Unless
// specified by matching options, returns established connections.
func (client *Client) Connections(opts *ConnectionOptions) (Connections, error) {
        var conns Connections
        query := url.Values{}
        if opts != nil && opts.ProjectId != "" {
                query.Set("project-id", opts.ProjectId)
        }
        if opts != nil && opts.Workshop != "" {
                query.Set("workshop", opts.Workshop)
        }
        if opts != nil && opts.Interface != "" {
                query.Set("interface", opts.Interface)
        }
        if opts != nil && opts.All {
                query.Set("select", "all")
        }
        _, err := client.doSync("GET", "/v1/connections", query, nil, nil, &conns)
        return conns, err
}

// performInterfaceAction performs a single action on the interface system.
func (client *Client) performInterfaceAction(sa *InterfaceAction) (changeID string, err error) {
        b, err := json.Marshal(sa)
        if err != nil {
                return "", err
        }
        return client.doAsync("POST", "/v1/connections", nil, nil, bytes.NewReader(b))
}

// Disconnect breaks the connection between a plug and a slot.
func (client *Client) Disconnect(plugProjectId, plugWorkshop, plugSdkName, plugName, slotProjectId, slotWorkshop, slotSdkName, slotName string, opts *DisconnectOptions) (changeID string, err error) {
        return client.performInterfaceAction(&InterfaceAction{
                Action: "disconnect",
                Forget: opts != nil && opts.Forget,
                Plugs:  []Plug{{ProjectId: plugProjectId, Workshop: plugWorkshop, Sdk: plugSdkName, Name: plugName}},
                Slots:  []Slot{{ProjectId: slotProjectId, Workshop: slotWorkshop, Sdk: slotSdkName, Name: slotName}},
        })
}

// Connects a plug and a slot.
func (client *Client) Connect(plugProjectId, plugWorkshop, plugSdkName, plugName, slotProjectId, slotWorkshop, slotSdkName, slotName string, opts *DisconnectOptions) (changeID string, err error) {
        return client.performInterfaceAction(&InterfaceAction{
                Action: "connect",
                Plugs:  []Plug{{ProjectId: plugProjectId, Workshop: plugWorkshop, Sdk: plugSdkName, Name: plugName}},
                Slots:  []Slot{{ProjectId: slotProjectId, Workshop: slotWorkshop, Sdk: slotSdkName, Name: slotName}},
        })
}
```

--------------------------------

### Batch Auto-Connect Tasks

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Creates a task set for connecting plugs to slots and setting up SDK profiles.

```go
func (m *InterfaceManager) batchAutoConnectTasks(wp *workshop.Workshop, info *sdk.Info, refs []*interfaces.ConnRef, plugDynamic, slotDynamic map[string]map[string]interface{}) (*state.TaskSet, error) {

        connectTs := state.NewTaskSet()
        var affected = map[sdk.Ref]bool{}
        for _, ref := range refs {
                connect := m.state.NewTask("connect", fmt.Sprintf("Connect %q to %q", ref.PlugRef.ShortRef(), ref.SlotRef.ShortRef()))

                connect.Set("plug", ref.PlugRef)
                connect.Set("slot", ref.SlotRef)
                connect.Set("auto", true)
                connect.Set("delayed-setup-profile", true)

                if plugDynamic != nil {
                        connect.Set("plug-dynamic", plugDynamic[ref.ID()])
                }
                if slotDynamic != nil {
                        connect.Set("slot-dynamic", slotDynamic[ref.ID()])
                }
                connectTs.AddTask(connect)

                plugSdk := sdk.Ref{ProjectId: ref.PlugRef.ProjectId, Workshop: ref.PlugRef.Workshop, Sdk: ref.PlugRef.Sdk}
                affected[plugSdk] = true

                slotSdk := sdk.Ref{ProjectId: ref.SlotRef.ProjectId, Workshop: ref.SlotRef.Workshop, Sdk: ref.SlotRef.Sdk}
                affected[slotSdk] = true
        }

        setup := m.state.NewTask("setup-profiles", fmt.Sprintf("Setup %q SDK profile", info.Name))
        setup.Set("sdks", maps.Keys(affected))
        setup.WaitAll(connectTs)

        if len(connectTs.Tasks()) > 0 {
                connectTs.AddTask(setup)
        }

        for _, tsk := range connectTs.Tasks() {
                tsk.Set("workshop", info.Workshop)
                tsk.Set("sdk", info.Name)
                tsk.Set("project", wp.Project)
        }

        return connectTs, nil
}
```

--------------------------------

### Initialize Overlord System Manager

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

The New function initializes the Overlord with required state managers and backend configurations. It requires an absolute directory path and an optional restart handler.

```go
func New(dir string, restartHandler restart.Handler) (*Overlord, error) {
        o := &Overlord{
                stateDir: dir,
                loopTomb: new(tomb.Tomb),
                inited:   true,
        }

        var err error

        if !filepath.IsAbs(dir) {
                return nil, fmt.Errorf("directory %q must be absolute", dir)
        }
        if !osutil.IsDir(dir) {
                return nil, fmt.Errorf("directory %q does not exist", dir)
        }

        statePath := filepath.Join(dir, "state.json")

        backend := &overlordStateBackend{
                path:         statePath,
                ensureBefore: o.ensureBefore,
        }
        s, err := o.loadState(statePath, restartHandler, backend)
        if err != nil {
                return nil, err
        }

        o.stateEng = NewStateEngine(s)
        o.runner = state.NewTaskRunner(s)

        sto := store.New()
        sdk.ReplaceStore(s, sto)

        if workshopBackendOverride != nil {
                workshop.ReplaceBackend(s, workshopBackendOverride)
        } else {
                wbe, err := lxdbackend.New()
                if err != nil {
                        return nil, err
                }
                workshop.ReplaceBackend(s, wbe)
        }

        // any unknown task should be ignored and succeed
        matchAnyUnknownTask := func(_ *state.Task) bool {
                return true
        }
        o.runner.AddOptionalHandler(matchAnyUnknownTask, handleUnknownTask, nil)

        o.workshopmgr = workshopstate.New(s, o.runner)
        o.addManager(o.workshopmgr)

        o.hookmgr = hookstate.New(s, o.runner)
        o.addManager(o.hookmgr)

        healthstate.Init(o.hookmgr)

        o.commandmgr = cmdstate.New(s, o.runner)
        o.addManager(o.commandmgr)

        o.ifacemgr = ifacestate.New(s, o.runner)
        o.addManager(o.ifacemgr)

        o.sdkmgr = sdkstate.New(s, o.runner, o.ifacemgr.Repository())
        o.addManager(o.sdkmgr)

        // the shared task runner should be added last!
        o.stateEng.AddManager(o.runner)

        return o, nil
}
```

--------------------------------

### View runner help options

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/run-github-actions-locally.md

Displays the available command-line arguments for the github-runner command.

```console
$ workshop exec ci github-runner --help
```

--------------------------------

### Add the launch-workshop action to a workflow

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/run-workshops-in-github-actions.md

A basic workflow configuration that checks out the repository, launches the default workshop, and executes a command.

```yaml
on:
  pull_request:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: canonical/launch-workshop@v1

      - run: workshop exec -- pytest
```

--------------------------------

### sdkcraft release Command Usage

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-release.rst

Shows the basic syntax for the sdkcraft release command, including the required arguments for SDK, revision, and channels.

```console
$ sdkcraft release SDK REVISION CHANNELS
```

--------------------------------

### Retrieve User Environment via systemd

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Fetches the user environment by executing systemctl --user show-environment. Requires XDG_RUNTIME_DIR to be set for the target user.

```go
// Returns the environment for the user as set by systemd.
// This is the equivalent of running 'systemctl --user show-environment'
func UserEnvironment(user *user.User) (map[string]string, error) {
        cmd := exec.Command("sudo", "-E", "-u", user.Username, "systemctl", "--user", "show-environment")
        // XDG_RUNTIME_DIR may not be set if a command invoked by sudo or
        // systemd-run; set it here to the default location. It is required for the
        // systemctl to work with --user. See:
        // https://unix.stackexchange.com/questions/346841/why-does-sudo-i-not-set-xdg-runtime-dir-for-the-target-user
        defaultXdg := filepath.Join(dirs.XdgRuntimeDirBase, user.Uid)
        cmd.Env = append(cmd.Env, "XDG_RUNTIME_DIR="+defaultXdg)
        out, errOut, err := osutil.RunCmd(cmd)
        if err != nil {
                return nil, fmt.Errorf("%s", string(errOut))
        }

        rawEnv := strings.FieldsFunc(string(out), func(r rune) bool { return r == '\n' })
        return osutil.ParseEnvironment(rawEnv)
}
```

--------------------------------

### Initialize WorkshopManager and register handlers

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Sets up the WorkshopManager with state and registers task handlers for various workshop lifecycle operations.

```go
func New(st *state.State, runner *state.TaskRunner) *WorkshopManager {
	manager := &WorkshopManager{
		state: st,
	}

	st.Lock()
	manager.backend = workshop.WorkshopBackend(st)
	st.Unlock()

	runner.AddHandler("download-base", OnDo(manager.doDownloadBase), nil)
	runner.AddHandler("create-workshop", OnDo(manager.doCreateWorkshop), manager.undoCreateWorkshop)
	runner.AddHandler("start-workshop", OnDo(manager.doStart), manager.doStop)
	runner.AddHandler("stop-workshop", OnDo(manager.doStop), manager.doStart)
	runner.AddHandler("remove-workshop", OnDo(manager.doRemoveWorkshop), nil)
	runner.AddHandler("mount-project", OnDo(manager.doMountProject), manager.undoMountProject)
	runner.AddHandler("create-apt-cache", OnDo(manager.doCreateAptCache), manager.doRemoveAptCache)
	runner.AddHandler("remove-apt-cache", OnDo(manager.doRemoveAptCache), nil)
	runner.AddHandler("mount-apt-cache", OnDo(manager.doMountAptCache), manager.undoMountAptCache)
	runner.AddHandler("remove-workshop-stash", OnDo(manager.doRemoveWorkshopStash), nil)
	runner.AddHandler("stash-workshop", OnDo(manager.doStashWorkshop), manager.undoStashWorkshop)
	runner.AddHandler("create-state-storage", OnDo(manager.doCreateStateStorage), manager.doRemoveStateStorage)
	runner.AddHandler("remove-state-storage", OnDo(manager.doRemoveStateStorage), nil)

	return manager
}
```

--------------------------------

### Status Ordering and Initialization

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the order of statuses and validates the configuration at package initialization.

```go
var statusOrder = []Status{
        AbortStatus,
        UndoingStatus,
        UndoStatus,
        DoingStatus,
        DoStatus,
        WaitStatus,
        ErrorStatus,
        UndoneStatus,
        DoneStatus,
        HoldStatus,
}

func init() {
        if len(statusOrder) != nStatuses-1 {
                panic("statusOrder has wrong number of elements")
        }
}
```

--------------------------------

### Expandable Environment Management

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Utilities for creating and extending environments with shell-like variable expansion.

```go
type ExpandableEnv struct {
	*strutil.OrderedMap
}
```

```go
func NewExpandableEnv(pairs ...string) ExpandableEnv {
	return ExpandableEnv{OrderedMap: strutil.NewOrderedMap(pairs...)}
}
```

```go
func (env *Environment) ExtendWithExpanded(eenv ExpandableEnv) {
	if *env == nil {
		*env = make(Environment)
	}

	for _, key := range eenv.Keys() {
		(*env)[key] = os.Expand(eenv.Get(key), func(varName string) string {
			return (*env)[varName]
		})
	}
}
```

--------------------------------

### sdk list

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdk.md

List all local SDK volumes available on the machine.

```APIDOC
## sdk list

### Description
Lists all local SDK volumes currently stored on the system.

### Usage
`sdk list [flags]`

### Parameters
- **--no-headers** (flag) - Optional - Hide the table header in the output.
```

--------------------------------

### File System Operation Snippet

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles file writing, permission setting, and renaming with cleanup logic.

```go
        temp := file.Name()
        rev.Add(func() { _ = fs.Remove(temp) })

        _, err = source.WriteTo(file)
        // TODO: Call file.Sync() here. This is currently a no-op for sftpfs,
        // see https://github.com/spf13/afero/pull/429.
        // Also, LXD uses pkg/sftp as its SFTP server,
        // and that doesn't support the fsync@openssh.com extension.
        file.Close()
        if err != nil {
                return err
        }

        if err = fs.Chmod(temp, perm); err != nil {
                return err
        }

        if err = fs.Rename(temp, filename); err != nil {
                return err
        }

        rev.Success()
        return nil
}
```

--------------------------------

### Initialize maps in Go

Source: https://github.com/canonical/workshop/blob/main/docs/coding-style-guide.md

Always initialize maps using make() before writing to them to avoid runtime panics.

```go
func newRegistry() *Registry {
    return &Registry{
        workshops: make(map[string]*Workshop),
        sdks:      make(map[string]*SDK),
    }
}

func addWorkshop(r *Registry, w *Workshop) {
    if r.workshops == nil {
        r.workshops = make(map[string]*Workshop)
    }
    r.workshops[w.Name] = w
}
```

```go
func addWorkshop(r *Registry, w *Workshop) {
    r.workshops[w.Name] = w // Panic if workshops is nil
}
```

--------------------------------

### Manage Workshop Lifecycle

Source: https://github.com/canonical/workshop/blob/main/docs/readme.rst

Commands to launch, enter, execute actions, and refresh the workshop environment.

```console
workshop launch       # download and install the SDKs
workshop shell        # open an interactive session
workshop run -- analyzer  # run a named action
workshop refresh      # apply edits to the definition, update SDKs
```

--------------------------------

### Manage Connection References

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for creating, identifying, comparing, and parsing connection references.

```go
// NewConnRef creates a connection reference for given plug and slot
func NewConnRef(plug *sdk.PlugInfo, slot *sdk.SlotInfo) *ConnRef {
        return &ConnRef{
                PlugRef: PlugRef{ProjectId: plug.Sdk.ProjectId, Workshop: plug.Sdk.Workshop, Sdk: plug.Sdk.Name, Name: plug.Name},
                SlotRef: SlotRef{ProjectId: slot.Sdk.ProjectId, Workshop: slot.Sdk.Workshop, Sdk: slot.Sdk.Name, Name: slot.Name},
        }
}

// ID returns a string identifying a given connection.
func (conn *ConnRef) ID() string {
        return fmt.Sprintf("%s/%s/%s:%s %s/%s/%s:%s",
                conn.PlugRef.ProjectId, conn.PlugRef.Workshop, conn.PlugRef.Sdk, conn.PlugRef.Name,
                conn.SlotRef.ProjectId, conn.SlotRef.Workshop, conn.SlotRef.Sdk, conn.SlotRef.Name)
}

// SortsBefore returns true when connection should be sorted before the other
func (conn *ConnRef) SortsBefore(other *ConnRef) bool {
        if conn.PlugRef != other.PlugRef {
                return conn.PlugRef.SortsBefore(other.PlugRef)
        }
        return conn.SlotRef.SortsBefore(other.SlotRef)
}

// ParseConnRef parses an ID string
func ParseConnRef(id string) (*ConnRef, error) {
        var conn ConnRef
        parts := strings.SplitN(id, " ", 2)
        if len(parts) != 2 {
                return nil, fmt.Errorf("malformed connection identifier: %q", id)
        }
        plugParts := strings.Split(parts[0], ":")
        slotParts := strings.Split(parts[1], ":")
        if len(plugParts) != 2 || len(slotParts) != 2 {
                return nil, fmt.Errorf("malformed connection identifier: %q", id)
        }

        // plug's project / workshop / sdk
        plugPwsParts := strings.Split(plugParts[0], "/")
        slotPwsParts := strings.Split(slotParts[0], "/")
        if len(plugPwsParts) != 3 || len(slotPwsParts) != 3 {
                return nil, fmt.Errorf("malformed connection identifier: %q", id)
        }

        conn.PlugRef.ProjectId = plugPwsParts[0]
        conn.PlugRef.Workshop = plugPwsParts[1]
        conn.PlugRef.Sdk = plugPwsParts[2]
        conn.PlugRef.Name = plugParts[1]

        conn.SlotRef.ProjectId = slotPwsParts[0]
        conn.SlotRef.Workshop = slotPwsParts[1]
        conn.SlotRef.Sdk = slotPwsParts[2]
        conn.SlotRef.Name = slotParts[1]
        return &conn, nil
}
```

--------------------------------

### Multi-base SDK Configuration

Source: https://github.com/canonical/workshop/blob/main/docs/reference/definition-files/sdkcraft-definition.md

Demonstrates an SDK definition that supports multiple base operating systems without defining specific parts.

```yaml
name: multibase
version: "0.1"
summary: Multibase SDK
description: |
  This is my multibase SDK description.
license: GPL-3.0
platforms:
  noble:
    build-on: [ubuntu@24.04:amd64, ubuntu@24.04:arm64]
    build-for: ubuntu@24.04:all
  jammy:
    build-on: [ubuntu@22.04:amd64, ubuntu@22.04:arm64]
    build-for: ubuntu@22.04:all
```

--------------------------------

### Progress Meter Factory and Mocking

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Provides utilities to mock the progress meter for tests and a factory function to select the appropriate meter based on the environment.

```go
// testMeter, if set, is returned by MakeProgressBar; set it from tests.
var testMeter Meter

func MockMeter(meter Meter) func() {
        testMeter = meter
        return func() {
                testMeter = nil
        }
}

var inTesting bool = len(os.Args) > 0 && strings.HasSuffix(os.Args[0], ".test") || os.Getenv("SPREAD_SYSTEM") != ""

// MakeProgressBar creates an appropriate progress.Meter for the environ in
// which it is called:
//
//   - if MockMeter has been called, return that.
//   - if no terminal is attached, or we think we're running a test, a
//     minimalistic QuietMeter is returned.
//   - otherwise, an ANSIMeter is returned.
//
// TODO: instead of making the pivot at creation time, do it at every call.
func MakeProgressBar() Meter {
        if testMeter != nil {
                return testMeter
        }
        if !inTesting && term.IsTerminal(int(os.Stdin.Fd())) {
                return &ANSIMeter{}
        }

        return QuietMeter{}
}
```

--------------------------------

### Execute Sketch SDK Commands

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Implementation of the Run method for the CmdSketch command, handling stash and restore logic based on command flags.

```go
func (c *CmdSketch) Run(cmd *cobra.Command, av []string) error {
        cli, err := c.root.client()
        if err != nil {
                return err
        }
        p, err := cli.Project(c.root.project)
        if err != nil {
                return err
        }

        var wp *client.Workshop
        if len(av) > 0 {
                wp, err = cli.Workshop(p.Id, av[0])
                if err != nil {
                        return err
                }
        } else {
                wp, err = cli.SingleWorkshop(p)
                if err != nil {
                        return err
                }
        }

        user, err := osutil.UserMaybeSudoUser()
        if err != nil {
                return err
        }

        sketchdir := sdk.WorkshopSketchSdkCurrent(user.HomeDir, p.Id, wp.Name)

        if c.stash {
                stashdir := sdk.WorkshopSketchSdkStash(user.HomeDir, p.Id, wp.Name)
                reverter, err := stashSketch(sketchdir, stashdir)
                if err != nil {
                        return err
                }
                defer reverter.Fail()

                cmdrefresh := &CmdRefresh{root: c.root}
                if err = cmdrefresh.Run(cmd, []string{wp.Name}); err != nil {
                        // Refresh failed, revert the stash operation so a possible subsequent
                        // "workshop refresh <WORKSHOP>/sketch" won't fail due to the lack of
                        // sketch SDK definition.
                        return err
                }
                reverter.Success()
                return nil
        }

        if c.restore {
                cmdrefresh := &CmdRefresh{root: c.root}
                cmdrefresh.WaitOnError = true

                storedir := sdk.WorkshopSketchSdkStash(user.HomeDir, p.Id, wp.Name)

                if err = restoreSketch(sketchdir, storedir); err != nil {
                        return err
                }

                // Run refresh with the stored sketch SDK. We do not revert dirs exchange
                // on a failed refresh here as it is run with the content from "stored"
                // and with --wait-on-error. Hence, there is always a possibility to
                // workshop refresh --abort and workshop sketch-sdk --restore to restore the
                // original sketch content.
                return cmdrefresh.Run(cmd, []string{fmt.Sprintf("%s/sketch", wp.Name)})
        }
```

--------------------------------

### Inspect workshop runtime information

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-1-get-started.md

Displays detailed runtime configuration, including SDK versions and mount points.

```console
$ workshop info

  name:     dev
  base:     ubuntu@22.04
  project:  /home/user/ollama-python-project
  status:   ready
  notes:    -
  sdks:
    system:
      installed:  (1)
    ollama:
      tracking:   cpu/stable
      installed:  0.20.2  2026-04-15  (5)
      mounts:
        models:
          host-source:      .../6b79e889/dev/mount/ollama/models
          workshop-target:  /home/workshop/.ollama/models
```

--------------------------------

### Implement Change Sorting and Creation

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Provides sorting logic for changes based on ready time and a constructor for new Change instances.

```go
type byReadyTime []*Change

func (a byReadyTime) Len() int           { return len(a) }
func (a byReadyTime) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }
func (a byReadyTime) Less(i, j int) bool { return a[i].readyTime.Before(a[j].readyTime) }

func newChange(state *State, id, kind, summary string) *Change {
        return &Change{
                state:   state,
                id:      id,
                kind:    kind,
                summary: summary,
                data:    make(customData),
                ready:   make(chan struct{}),

                spawnTime: timeNow(),
        }
}
```

--------------------------------

### Configure SDK Plugs and Slots

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for binding plugs and adding slots to an SDK instance, including validation logic and sanitization.

```go
func (i *Info) SetupPlugBinds(binds map[string]*PlugBind) error {
        if i.Type == System {
                return nil
        }

        for name, plug := range binds {
                if _, ok := i.Plugs[name]; ok {
                        // Check plugs that are bound. The existence of plugs that are
                        // "bound to" it will be checked at the connecting stage, i.e. when
                        // all plugs from all SDKs are in the repository already.
                        i.PlugBinds[name] = plug
                } else {
                        return fmt.Errorf("plug binding failed: SDK %q has no plug named %q", i.Ref().ShortRef(), name)
                }
        }
        return nil
}

// Adds slots defined for this SDK in a workshop file.
func (i *Info) SetupWorkshopSlots(slots map[string]interface{}) error {
        for name, data := range slots {
                if _, exist := i.Slots[name]; exist {
                        return fmt.Errorf("cannot add slot %q to %q SDK: already exists", name, i.Name)
                }
                iface, label, attrs, err := convertToSlotOrPlugData("slot", name, data)
                if err != nil {
                        return err
                }
                i.Slots[name] = &SlotInfo{
                        Sdk:       i,
                        Name:      name,
                        Interface: iface,
                        Attrs:     attrs,
                        Label:     label,
                }
        }

        SanitizePlugsSlots(i)
        return nil
}

// Adds slots defined for this SDK in a workshop file.
func (i *Info) SetupWorkshopPlugs(plugs map[string]interface{}) error {
        for name, data := range plugs {
                if _, exist := i.Plugs[name]; exist {
                        return fmt.Errorf("cannot add plug %q to %q SDK: already exists", name, i.Name)
                }
                iface, label, attrs, err := convertToSlotOrPlugData("plug", name, data)
                if err != nil {
                        return err
                }
                i.Plugs[name] = &PlugInfo{
                        Sdk:       i,
                        Name:      name,
                        Interface: iface,
                        Attrs:     attrs,
                        Label:     label,
                }
        }

        SanitizePlugsSlots(i)
        return nil
}
```

--------------------------------

### Create Prompts Directory

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/use-workshops-with-ai-agents.md

Create a directory at the repository root to store shared agent prompts.

```console
$ mkdir prompts
```

--------------------------------

### Query vendor and product IDs with udevadm

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/interfaces/custom-device-interface.md

Use these properties to narrow down device selection when the subsystem matches multiple devices.

```console
$ udevadm info --query=property --property=ID_VENDOR_ID --property=ID_MODEL_ID /dev/ttyUSB0

  ID_VENDOR_ID=0403
  ID_MODEL_ID=6001
```

--------------------------------

### Define Launch Command Structure

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the structure for the launch command, including configuration flags and root command reference.

```go
package main

import (
        "fmt"

        "github.com/canonical/x-go/strutil"
        "github.com/spf13/cobra"
)

type CmdLaunch struct {
        waitMixin
        root        *CmdRoot
        WaitOnError bool
        Continue    bool
        Abort       bool
}
```

--------------------------------

### Register an SDK name via CLI

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-register.rst

Use this command to reserve a unique SDK name for your account.

```console
$ sdkcraft register SDK
```

--------------------------------

### Plug and Slot Preparation Logic

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for validating plug and slot attributes before preparation, ensuring required fields like workshop-target are present and valid.

```go
func (iface *mountInterface) BeforePreparePlug(plug *sdk.PlugInfo) error {
	for name := range plug.Attrs {
		if !slices.Contains(knownPlugAttributes, name) {
			return fmt.Errorf(`unknown attribute for mount interface plug: %q`, name)
		}
	}
	target, ok := plug.Attrs["workshop-target"].(string)
	if !ok || len(target) == 0 {
		return fmt.Errorf("mount plug must contain target path")
	}
	if err := validatePath(target); err != nil {
		return err
	}
	return nil
}

func (iface *mountInterface) BeforePrepareSlot(slot *sdk.SlotInfo) error {
	for name := range slot.Attrs {
		if !slices.Contains(knownSlotAttributes, name) {
			return fmt.Errorf(`unknown attribute for mount interface slot: %q`, name)
		}
	}
	source, exist := slot.Attrs["workshop-source"]
	if !exist {
		// perfectly fine scenario for the default mount slot
		return nil
	}
	path, ok := source.(string)
	if !ok {
		return fmt.Errorf(`mount slot "workshop-source" is not a string (found %T)`, source)
	}

	if strings.HasPrefix(path, "$SDK") {
		path = strings.Replace(path, "$SDK", sdk.SdkCurrentPath(slot.Sdk.Name), 1)
	}

	if !filepath.IsAbs(path) {
		return fmt.Errorf(`mount slot "workshop-source" must be absolute`)
	}
	return nil
}
```

--------------------------------

### Execute Command and Manage Process Lifecycle

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Encodes execution parameters into a JSON payload, initiates the request, and sets up websocket streams for stdin/stdout/stderr handling.

```go
payload := execPayload{
                Command:     opts.Command,
                Script:      opts.Script,
                Environment: opts.Environment,
                WorkingDir:  opts.WorkingDir,
                UserId:      opts.UserId,
                GroupId:     opts.GroupId,
                Timeout:     timeoutStr,
                Terminal:    opts.Terminal,
                Interactive: opts.Interactive,
                SplitStderr: false,
                Width:       opts.Width,
                Height:      opts.Height,
        }
        var body bytes.Buffer
        err := json.NewEncoder(&body).Encode(&payload)
        if err != nil {
                return nil, fmt.Errorf("cannot encode JSON payload: %w", err)
        }
        headers := map[string]string{
                "Content-Type": "application/json",
        }
        resultBytes, changeID, err := client.doAsyncFull("POST", "/v1/projects/"+projectId+"/workshops/"+workshop+"/exec", nil, headers, &body)
        if err != nil {
                return nil, err
        }
        var result execResult
        err = json.Unmarshal(resultBytes, &result)
        if err != nil {
                return nil, fmt.Errorf("cannot unmarshal JSON response: %w", err)
        }

        // Connect to the "control" websocket.
        taskID := result.TaskID
        controlConn, err := client.getTaskWebsocket(taskID, "control")
        if err != nil {
                return nil, err
        }

        // Forward stdin and stdout.
        var stdinDone, stdoutDone, stderrDone chan bool
        var stdioConn, stdoutConn, stderrConn clientWebsocket

        stdioConn, err = client.getTaskWebsocket(taskID, "stdio")
        if err != nil {
                return nil, err
        }
        stdinDone = wsutil.WebsocketSendStream(stdioConn, stdin, -1)

        if opts.Interactive {
                stdoutDone = wsutil.WebsocketRecvStream(stdout, stdioConn)
        } else {
                stdoutConn, err = client.getTaskWebsocket(taskID, "stdout")
                if err != nil {
                        return nil, err
                }
                stdoutDone = wsutil.WebsocketRecvStream(stdout, stdoutConn)

                stderrConn, err = client.getTaskWebsocket(taskID, "stderr")
                if err != nil {
                        return nil, err
                }
                stderrDone = wsutil.WebsocketRecvStream(stderr, stderrConn)
        }

        // Fire up a goroutine to wait for writes to be done.
        writesDone := make(chan struct{})
        go func() {
                // Wait till the WebsocketRecvStream goroutines are done writing to
                // stdout and stderr. This happens when EOF is signalled or websocket
                // is closed.
                <-stdoutDone
                if stderrDone != nil {
                        <-stderrDone
                }

                // Try to close websocket connections gracefully, but ignore errors.
                _ = stdioConn.Close()
                if stdoutConn != nil {
                        stdoutConn.Close()
                }
                if stderrConn != nil {
                        _ = stderrConn.Close()
                }
                _ = controlConn.Close()

                // Tell ExecProcess.Wait we're done writing to stdout/stderr.
                close(writesDone)
        }()

        process := &ExecProcess{
                changeID:    changeID,
                client:      client,
                timeout:     opts.Timeout,
                writesDone:  writesDone,
                controlConn: controlConn,
                stdinDone:   stdinDone,
        }
        return process, nil
}
```

--------------------------------

### Add Workshop Mount

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes the process of adding a mount device to a workshop instance.

```go
func (s *Backend) AddWorkshopMount(ctx context.Context, name string, device workshop.Mount) error {
        conn, err := s.LxdClient(ctx)
        if err != nil {
                return err
        }
        defer conn.Disconnect()

        projectId, ok := ctx.Value(workshop.ContextProjectId).(string)
        if !ok {
                return fmt.Errorf("context key project-id not found")
        }
```

--------------------------------

### Workshop Data Structures

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Core structs representing workshop information, files, and configuration options.

```go
type Workshops struct {
        Workshops []*WorkshopInfo `json:"workshops"`
        Files     []*WorkshopFile `json:"files"`
}

type WorkshopInfo struct {
        ProjectId string   `json:"project-id"`
        Name      string   `json:"name"`
        Base      string   `json:"base"`
        Status    string   `json:"status"`
        Sdks      []*Sdk   `json:"sdks,omitempty"`
        Notes     []string `json:"notes,omitempty"`
}

type WorkshopFile struct {
        ProjectId string `json:"project-id"`
        Name      string `json:"name"`
        Path      string `json:"path"`
}

type Workshop struct {
        WorkshopInfo
        Path string `json:"path"`
}

type Script struct {
        Script string `json:"script"`
}

type ListOptions struct {
        ProjectId string
}

type Remount struct {
        Action     string   `json:"action"`
        Plug       *PlugRef `json:"plug"`
        HostSource string   `json:"host-source"`
}
```

--------------------------------

### Import Dependencies

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Standard imports for the main package.

```go
package main

import (
	"fmt"
	"slices"
	"sort"
	"strings"
)
```

--------------------------------

### Mock Image Server

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Utility to temporarily override the global image server for testing purposes.

```go
func FakeImageServer(server string) func() {
		oldImageServer := imageServer
		imageServer = server
		return func() { imageServer = oldImageServer }
}
```

--------------------------------

### ExecProcess and Exec Method Implementation

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the ExecProcess type for tracking running processes and the Exec method to initiate command execution.

```go
type execResult struct {
        TaskID string `json:"task-id"`
}

// ExecProcess represents a running process. Use Wait to wait for it to finish.
type ExecProcess struct {
        changeID    string
        client      *Client
        timeout     time.Duration
        writesDone  chan struct{}
        controlConn jsonWriter
        stdinDone   chan bool // only used by tests
}

// Exec starts a command with the given options, returning a value
// representing the process.
func (client *Client) Exec(opts *ExecOptions, workshop, projectId string) (*ExecProcess, error) {
        // Set up stdin/stdout defaults.
        stdin := opts.Stdin
        if stdin == nil {
                stdin = bytes.NewReader(nil)
        }
        stdout := opts.Stdout
        if stdout == nil {
                stdout = io.Discard
        }
        stderr := opts.Stderr
        if stderr == nil {
                stderr = io.Discard
        }

        var timeoutStr string
        if opts.Timeout != 0 {
                timeoutStr = opts.Timeout.String()
        }
```

--------------------------------

### Run documentation test suites

Source: https://github.com/canonical/workshop/blob/main/docs/contributing/development.md

Commands to execute specific end-to-end test suites using Spread.

```console
$ spread tests/docs-tutorial/
$ spread tests/docs-how-to/
```

--------------------------------

### Implement Response Methods

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Provides methods for managing maintenance errors, warnings, JSON marshaling, and HTTP serving.

```go
func (r *resp) transmitMaintenance(kind errorKind, message string) {
        r.Maintenance = &errorResult{
                Kind:    kind,
                Message: message,
        }
}

func (r *resp) addWarningsToMeta(count int, stamp time.Time) {
        if r.WarningCount != 0 {
                return
        }
        if count == 0 {
                return
        }
        r.WarningCount = count
        r.WarningTimestamp = &stamp
}

func (r *resp) MarshalJSON() ([]byte, error) {
        return json.Marshal(respJSON{
                Type:             r.Type,
                Status:           r.Status,
                StatusText:       http.StatusText(r.Status),
                Change:           r.Change,
                Result:           r.Result,
                WarningTimestamp: r.WarningTimestamp,
                WarningCount:     r.WarningCount,
                Maintenance:      r.Maintenance,
        })
}

func (r *resp) ServeHTTP(w http.ResponseWriter, _ *http.Request) {
        status := r.Status
        bs, err := r.MarshalJSON()
        if err != nil {
                logger.Noticef("cannot marshal %#v to JSON: %v", *r, err)
                bs = nil
                status = 500
        }

        hdr := w.Header()
        if r.Status == 202 || r.Status == 201 {
                if m, ok := r.Result.(map[string]interface{}); ok {
                        if location, ok := m["resource"]; ok {
                                if location, ok := location.(string); ok && location != "" {
                                        hdr.Set("Location", location)
                                }
                        }
                }
        }

        hdr.Set("Content-Type", "application/json")
        w.WriteHeader(status)
        w.Write(bs)
}
```

--------------------------------

### Register Security Backends

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Returns a list of available security backends for the application.

```go
package backend

import (
        "github.com/canonical/workshop/internal/interfaces"
        "github.com/canonical/workshop/internal/interfaces/lxd_device"
)

func All() []interfaces.SecurityBackend {
        all := []interfaces.SecurityBackend{
                &lxd_device.Backend{},
        }
        return all
}
```

--------------------------------

### sdkcraft build Command Usage

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-build.rst

This snippet shows the general usage of the 'sdkcraft build' command, including optional flags and arguments.

```console
$ sdkcraft build [--destructive-mode | --use-lxd] [--shell | --shell-after] [--debug]
                   [--platform name | --build-for arch]
                   [part-name ...]
```

--------------------------------

### Implement Standby Logic in Go

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Manages the transition to socket activation mode based on system state and external opinions.

```go
return state.NewTaskSet(install, link)
}

// Copyright (c) 2014-2020 Canonical Ltd
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3 as
// published by the Free Software Foundation.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

package standby

import (
	"time"

	"github.com/canonical/workshop/internal/overlord/restart"
	"github.com/canonical/workshop/internal/overlord/state"
)

var standbyWait = 5 * time.Second
var maxWait = 5 * time.Minute

type Opinionator interface {
	CanStandby() bool
}

// StandbyOpinions tracks if workshop can go into socket activation mode
type StandbyOpinions struct {
	state     *state.State
	startTime time.Time
	opinions  []Opinionator

	stoppingCh chan struct{}
	stoppedCh  chan struct{}
}

// CanStandby returns true if the main ensure loop can go into
// "socket-activation" mode. This is only possible once seeding is done
// and there are no snaps on the system. This is to reduce the memory
// footprint on e.g. containers.
func (m *StandbyOpinions) CanStandby() bool {
	st := m.state
	st.Lock()
	defer st.Unlock()

	// check if enough time has passed
	if m.startTime.Add(standbyWait).After(time.Now()) {
		return false
	}
	// check if there are any changes in flight
	for _, chg := range st.Changes() {
		if !chg.Status().Ready() || !chg.IsClean() {
			return false
		}
	}
	// check the voice of the crowd
	for _, ct := range m.opinions {
		if !ct.CanStandby() {
			return false
		}
	}
	return true
}

func New(st *state.State) *StandbyOpinions {
	return &StandbyOpinions{
		state:      st,
		startTime:  time.Now(),
		stoppingCh: make(chan struct{}),
		stoppedCh:  make(chan struct{}),
	}
}

func (m *StandbyOpinions) Start() {
	go func() {
		wait := standbyWait
		timer := time.NewTimer(wait)
		for {
			if m.CanStandby() {
				m.state.Lock()
				restart.Request(m.state, restart.RestartSocket)
				m.state.Unlock()
			}
			select {
			case <-timer.C:
				if wait < maxWait {
					wait *= 2
				}
			case <-m.stoppingCh:
				close(m.stoppedCh)
				return
			}
			timer.Reset(wait)
		}
	}()
}

func (m *StandbyOpinions) Stop() {
	select {
	case <-m.stoppedCh:
		// nothing left to do
		return
	case <-m.stoppingCh:
		// nearly nothing to do
	default:
		close(m.stoppingCh)
	}
	<-m.stoppedCh
}

func (m *StandbyOpinions) AddOpinion(opi Opinionator) {
	if opi != nil {
		m.opinions = append(m.opinions, opi)
	}
}

func FakeStandbyWait(d time.Duration) (restore func()) {
	oldStandbyWait := standbyWait
	standbyWait = d
	return func() {
		standbyWait = oldStandbyWait
	}
}

// -*- Mode: Go; indent-tabs-mode: t -*-
```

--------------------------------

### SDK Manager Initialization

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Constructor and structure definition for the SdkManager, including task handler registration.

```go
package sdkstate

import (
        "github.com/canonical/workshop/internal/interfaces"
        . "github.com/canonical/workshop/internal/overlord/handlersetup"
        "github.com/canonical/workshop/internal/overlord/state"
        "github.com/canonical/workshop/internal/workshop"
        backend "github.com/canonical/workshop/internal/workshop"
)

type SdkManager struct {
        backend backend.Backend
        repo    *interfaces.Repository
}

func New(s *state.State, runner *state.TaskRunner, repo *interfaces.Repository) *SdkManager {
        manager := &SdkManager{repo: repo}

        s.Lock()
        manager.backend = workshop.WorkshopBackend(s)
        s.Unlock()

        runner.AddHandler("retrieve-sdk", OnDo(manager.doRetrieveSdk), nil)
        runner.AddHandler("install-sdk", OnDo(manager.doInstallSdk), manager.undoInstallSdk)
        runner.AddHandler("install-local-sdk", OnDo(manager.doInstallLocalSdk), manager.undoInstallLocalSdk)
        runner.AddHandler("link-sdk", OnDo(manager.doLinkSdk), manager.undoLinkSdk)

        return manager
}

func (w *SdkManager) Ensure() error {
        return nil
}
```

--------------------------------

### Initialize a new Task

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Constructor function for creating a new Task instance with initialized custom data and spawn time.

```go
func newTask(state *State, id, kind, summary string) *Task {
        return &Task{
                state:   state,
                id:      id,
                kind:    kind,
                summary: summary,
                data:    make(customData),

                spawnTime: timeNow(),
        }
}
```

--------------------------------

### Structure for SDK definitions

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/workshops/projects.md

Store SDK definitions in subdirectories of .workshop/ to make them available to any workshop within the project.

```none
.workshop/build-tools/sdk.yaml
.workshop/system-services/sdk.yaml
```

--------------------------------

### Handle Project Workshop Requests

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Retrieves workshop information and files for a specific project, returning a synchronized response.

```go
        ctx := context.WithValue(r.Context(), workshop.ContextProjectId, projectId)
        sdks, err := w.SdkInfos(ctx)
        if err != nil {
                return statusBadRequest("%w", err)
        }

        ms, err := mounts(w, sdks)
        if err != nil {
                return statusBadRequest("%w", err)
        }

        files, err := wrkmgr.WorkshopFiles(ctx, projectId)
        if err != nil {
                return statusBadRequest("%w", err)
        }

        rsp := Workshop{
                WorkshopInfo: *workshopToInfo(w, sdks, health, ms),
                Path:         files[w.Name],
        }

        return SyncResponse(rsp, http.StatusOK)
}
```

--------------------------------

### Daemon Configuration and Structure

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the Options for daemon initialization and the core Daemon struct for request routing.

```go
// Options holds the daemon setup required for the initialization of a new daemon.
type Options struct {
        // Dir is the workshop directory where all setup is found. Defaults to /var/lib/workshop.
        Dir string

        // SocketPath is an optional path for the unix socket used for the client
        // to communicate with the daemon. Defaults to a hidden (dotted) name inside
        // the workshop directory.
        SocketPath string

        // HTTPAddress is the address for the plain HTTP API server, for example
        // ":4000" to listen on any address, port 4000. If not set, the HTTP API
        // server is not started.
        HTTPAddress string
}

// A Daemon listens for requests and routes them to the right command
type Daemon struct {
        Version             string
        StartTime           time.Time
        workshopDir         string
        normalSocketPath    string
        untrustedSocketPath string
        httpAddress         string
        overlord            *overlord.Overlord
        state               *state.State
        generalListener     net.Listener
        untrustedListener   net.Listener
        httpListener        net.Listener
        connTracker         *connTracker
        serve               *http.Server
        tomb                tomb.Tomb
        router              *mux.Router
        standbyOpinions     *standby.StandbyOpinions

        // set to remember we need to restart the system
        restartSystem bool
```

--------------------------------

### Access Workshop Filesystem

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Retrieves the filesystem for a specific workshop by name.

```go
func (s *FakeWorkshopBackend) WorkshopFs(ctx context.Context, name string) (workshop.WorkshopFs, error) {
        s.WorkshopFsCalls = append(s.WorkshopFsCalls, &FsCall{Name: name})
        if s.WorkshopFsCallback != nil {
                return s.WorkshopFsCallback(ctx, name)
        }

        _, projectId, err := s.userProject(ctx)
        if err != nil {
                return nil, err
        }
        fs, exists := s.Workshops[projectId][name]
        if !exists {
                return nil, fmt.Errorf("%q filesystem is not available", name)
        }
        return fs.WorkshopFilesystem, nil
}
```

--------------------------------

### Run Go Build in Nimble Workshop

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-exec.rst

Executes the 'go build main.go' command within the 'nimble' workshop in the current project directory.

```console
$ workshop exec nimble -- go build main.go
```

--------------------------------

### Search for SDKs with Multiple Keywords

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdk-find.rst

Combine multiple words into a single query to narrow down search results. The command searches across SDK name, title, summary, description, and publisher.

```console
$ sdk find jupyter notebooks
```

--------------------------------

### Retrieve Plugs by SDK

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Retrieves all plugs offered by a specific SDK, sorted by workshop and name.

```go
func (r *Repository) Plugs(projectId, workshop, sdkName string) []*sdk.PlugInfo {
        r.m.Lock()
        defer r.m.Unlock()

        key := plugOrSlotKey(projectId, workshop, sdkName)

        var result []*sdk.PlugInfo
        for _, plug := range r.plugs[key] {
                result = append(result, plug)
        }
        sort.Sort(byPlugWorkshopSdkAndName(result))
        return result
}
```

--------------------------------

### Write Sketch SDK Configuration

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Parses SDK YAML content and writes configuration files and hook scripts to the sketch directory.

```go
func writeSketchSdk(sketchdir string, content []byte) error {
        var rec workshop.SdkRecord
        r := revert.New()
        defer r.Fail()

        if err := yaml.Unmarshal(content, &rec); err != nil {
                return err
        }

        if rec.Name != sdk.Sketch {
                return fmt.Errorf("cannot sketch: SDK must be named %q (now: %q)", sdk.Sketch, rec.Name)
        }

        metadir := filepath.Join(sketchdir, "meta")
        metapath := filepath.Join(metadir, "sdk.yaml")
        if err := os.MkdirAll(metadir, 0755); err != nil {
                return err
        }
        r.Add(func() { os.RemoveAll(metadir) })
        if err := os.WriteFile(metapath, content, 0644); err != nil {
                return err
        }

        hooksdir := filepath.Join(sketchdir, "hooks")
        if len(rec.Hooks) > 0 {
                if err := os.MkdirAll(hooksdir, 0755); err != nil {
                        return err
                }
                r.Add(func() { os.RemoveAll(hooksdir) })
        }
        for _, hook := range []string{"setup-base", "save-state", "restore-state", "check-health"} {
                hookpath := filepath.Join(hooksdir, hook)
                if script := rec.Hooks[hook]; len(script) > 0 {
                        if err := os.WriteFile(hookpath, []byte(script+"\n"), 0644); err != nil {
                                return err
                        }
                } else {
                        if err := os.Remove(hookpath); err != nil && !errors.Is(err, os.ErrNotExist) {
                                return err
                        }
                }
        }

        r.Success()
        return nil
}
```

--------------------------------

### Manage Workshop Configuration

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for adding or removing configuration items from a workshop instance.

```go
func (s *Backend) AddWorkshopConfig(ctx context.Context, name string, item *workshop.WorkshopConfigValue) error {
        conn, err := s.LxdClient(ctx)
        if err != nil {
                return err
        }
        defer conn.Disconnect()

        return s.addWorkshopConfig(conn, ctx, name, item)
}

func (s *Backend) addWorkshopConfig(conn lxd.InstanceServer, ctx context.Context, name string, item *workshop.WorkshopConfigValue) error {
        projectId, ok := ctx.Value(workshop.ContextProjectId).(string)
        if !ok {
                return fmt.Errorf("context key project-id not found")
        }

        inst, etag, err := conn.GetInstance(InstanceName(name, projectId))
        if err != nil {
                return err
        }

        inst.Config[item.Name] = item.Value
        op, err := conn.UpdateInstance(inst.Name, inst.Writable(), etag)
        if err != nil {
                return err
        }

        return op.WaitContext(ctx)
}

func (s *Backend) RemoveWorkshopConfig(ctx context.Context, name string, key string) error {
        conn, err := s.LxdClient(ctx)
        if err != nil {
                return err
        }
        defer conn.Disconnect()

        projectId, ok := ctx.Value(workshop.ContextProjectId).(string)
        if !ok {
                return fmt.Errorf("context key project-id not found")
        }

        inst, etag, err := conn.GetInstance(InstanceName(name, projectId))
        if err != nil {
                return err
        }

        delete(inst.Config, key)
        op, err := conn.UpdateInstance(inst.Name, inst.Writable(), etag)
        if err != nil {
                return err
        }

        return op.Wait()
}
```

--------------------------------

### Workshop CLI command structures

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Core structs and imports for the workshop CLI command implementation.

```go
package main

import (
        "errors"
        "fmt"
        "os"
        "os/signal"
        "slices"
        "strings"
        "time"

        "github.com/spf13/cobra"
        "github.com/spf13/pflag"
        "golang.org/x/sys/unix"
        "gopkg.in/yaml.v3"

        "github.com/canonical/workshop/client"
        "github.com/canonical/workshop/internal/logger"
        "github.com/canonical/workshop/internal/ptyutil"
)

type CmdExec struct {
        root  *CmdRoot
        flags ExecFlags
}

type CmdShell struct {
        root *CmdRoot
}

type CmdRun struct {
        root  *CmdRoot
        flags ExecFlags
}

type ExecFlags struct {
        WorkingDir     string
        Env            []string
        UserId         int
        GroupId        int
        Timeout        time.Duration
        Interactive    bool
        NonInteractive bool
}

type ExecArgs struct {
        workshop string
        implicit bool
        command  []string
        script   bool
}
```

--------------------------------

### Add SDK to workshop definition

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/build-an-sdk.md

Include the SDK in your workshop configuration using the try- prefix.

```yaml
name: dev
base: ubuntu@24.04
sdks:
  - name: try-<NAME>
```

--------------------------------

### Upload an SDK artifact

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-upload.rst

Basic usage of the upload command to push a .sdk file to the store.

```console
$ sdkcraft upload [--release CHANNELS] SDK
```

--------------------------------

### Retrieve SDK Information

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Fetches SDK metadata from the configured storage bucket.

```go
func storeSdkInfoImpl(ctx context.Context, name, channel string) (storeSdk, error) {
	var sSdk storeSdk
	client, err := storeConnect(ctx)
	if err != nil {
		return sSdk, err
	}
	defer client.Close()
	bkt := client.Bucket(SDK_STORE_BUCKET_NAME)
```

--------------------------------

### LXD Profile and Device Key Utilities

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Helper functions for generating profile names and configuration keys for LXD instances.

```go
package lxdbackend

import (
        "encoding/json"
        "fmt"
        "net/http"
        "strings"

        lxd "github.com/canonical/lxd/client"
        "github.com/canonical/lxd/shared/api"

        "github.com/canonical/workshop/internal/logger"
        "github.com/canonical/workshop/internal/workshop"
)

func ProfileName(pid, workshop, sdk string) string {
        return strings.Join([]string{InstanceName(workshop, pid), sdk}, "-")
}

func DeviceConfigKey(sdk, dev string) string {
        return fmt.Sprintf("user.workshop.%s.%s", sdk, dev)
}

func DeviceTypeConfigKey(sdk, dev string) string {
        return fmt.Sprintf("user.workshop.%s.%s.type", sdk, dev)
}
```

--------------------------------

### List All Local SDK Volumes

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdk-list.rst

Use this command to list all SDK volumes currently stored on your system. This is the default behavior of the 'sdk list' command.

```console
$ sdk list
```

--------------------------------

### Remount Workshop Logic

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles project identification and workshop remounting via the CLI client.

```go
        project, err := cli.Project(c.root.project)
        if err != nil {
                return err
        }

        plugRef.ProjectId = project.Id

        changeId, err := cli.Remount(plugRef, source)
        if err != nil {
                return err
        }

        if _, err := c.wait(cli, changeId); err != nil {
                if err == errNoWait {
                        return nil
                }
                return err
        }

        return nil
}
```

--------------------------------

### List project sketches

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Enumerate all sketches in the current project directory.

```console
$ workshop sketches [flags]
```

```console
$ workshop sketches
```

--------------------------------

### Configure X11 and Xauthority for Desktop Interfaces

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles X11 socket passthrough and mounts the Xauthority file to ensure containerized desktop applications can connect to the host display.

```Go
// We pass through the X11 socket regardless of whether XAUTHORITY is present
		// on the host. This then gives users the option to modify their xhost
		// settings to allow connections from the container and container user.
		if display != "" {
			desktop.X11 = &workshop.ProxyEntry{}
			desktop.X11.Name = plug.Sdk().Name + "-" + "x11"
			desktop.X11.Connect = filepath.Join("/tmp/.X11-unix", "X"+strings.TrimPrefix(display, ":"))
			desktop.X11.Listen = desktop.X11.Connect
		}

		// We mount the Xauthority inside a parent folder to ensure that the mounted
		// cookie is updated when the host cookie changes (ie. reboot).
		// https://discuss.linuxcontainers.org/t/mount-single-file/17975
		workshopdXauth := filepath.Join(dirs.WorkshopdRunDir, spec.User.Uid, "Xauthority")
		xauth := env["XAUTHORITY"]
		if xauth != "" {
			m := workshop.Mount{}
			m.Name = plug.Sdk().Name + "-" + "xauth"
			m.Type = 0
			m.What = workshopdXauth
			m.Where = filepath.Join(dirs.WorkshopRunDir, "Xauthority")
			spec.AddMountEntry(m)
		}

		return spec.SetDesktop(desktop)
}

func init() {
		registerIface(&desktopInterface{})
}
```

--------------------------------

### Create Workshop State Change

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes a new state change object with a formatted summary based on the action and workshop names.

```go
func newWorkshopChange(st *state.State, kind string, user, projectId, action string, names []string) *state.Change {
        var summary string
        switch len(names) {
        case 1:
                summary = fmt.Sprintf("%s %q workshop", cases.Title(language.BritishEnglish).String(action), names[0])
        default:
                summary = fmt.Sprintf("%s %s workshops", cases.Title(language.BritishEnglish).String(action), strutil.Quoted(names))
        }

        change := st.NewChange(kind, summary)
        change.Set("user", user)
        change.Set("project-id", projectId)
        return change
}
```

--------------------------------

### Finding Auto-Connection Candidates

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods to find viable slots for a plug or plugs for a slot based on policy checks and interface auto-connection rules.

```go
func (r *Repository) AutoConnectCandidateSlots(projectId, workshop, plugSdkName, plugName string, policyCheck func(*ConnectedPlug, *ConnectedSlot) (bool, error)) []*sdk.SlotInfo {
	r.m.Lock()
	defer r.m.Unlock()

	key := plugOrSlotKey(projectId, workshop, plugSdkName)

	plugInfo := r.plugs[key][plugName]
	if plugInfo == nil {
		return nil
	}

	var candidates []*sdk.SlotInfo
	for _, slotsForSdk := range r.slots {
		for _, slotInfo := range slotsForSdk {
			if slotInfo.Interface != plugInfo.Interface {
				continue
			}
			iface := slotInfo.Interface

			ok, err := policyCheck(NewConnectedPlug(plugInfo, nil, nil), NewConnectedSlot(slotInfo, nil, nil))
			if !ok || err != nil {
				continue
			}

			if r.ifaces[iface].AutoConnect(plugInfo, slotInfo) {
				candidates = append(candidates, slotInfo)
			}
		}
	}
	return candidates
}
```

```go
func (r *Repository) AutoConnectCandidatePlugs(projectId, workshop, slotSdkName, slotName string, policyCheck func(*ConnectedPlug, *ConnectedSlot) (bool, error)) []*sdk.PlugInfo {
	r.m.Lock()
	defer r.m.Unlock()

	key := plugOrSlotKey(projectId, workshop, slotSdkName)

	slotInfo := r.slots[key][slotName]
	if slotInfo == nil {
		return nil
	}

	var candidates []*sdk.PlugInfo
	for _, plugsForSdk := range r.plugs {
		for _, plugInfo := range plugsForSdk {
			if slotInfo.Interface != plugInfo.Interface {
				continue
			}
			iface := slotInfo.Interface

			ok, err := policyCheck(NewConnectedPlug(plugInfo, nil, nil), NewConnectedSlot(slotInfo, nil, nil))
			if !ok || err != nil {
				continue
			}

			if r.ifaces[iface].AutoConnect(plugInfo, slotInfo) {
				candidates = append(candidates, plugInfo)
			}
		}
	}
	return candidates
}
```

--------------------------------

### Iterate and Check Plugs

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Iterates through SDK plugs and validates each one.

```go
for _, plug := range ic.Sdk.Plugs {
		err := ic.checkPlug(plug)
		if err != nil {
			return err
		}
}

return nil
}
```

--------------------------------

### Pack the SDK using SDKcraft

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/publish-an-sdk.md

Builds the SDK and generates artifacts for each platform defined in sdkcraft.yaml, leaving them in the current working directory.

```console
$ sdkcraft pack
```

--------------------------------

### Verify mount configuration

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/configure-mount.md

Use the workshop exec command to inspect directory permissions or verify read-only status through write attempts.

```console
$ workshop exec dev -- ls -ldn /home/workshop/.private-secrets

  drwx------ 2 1000 1000 4096 May 14 10:32 /home/workshop/.private-secrets
```

```console
$ workshop exec dev -- touch /home/workshop/.local/share/example-toolchain/probe

  touch: cannot touch '/home/workshop/.local/share/example-toolchain/probe': Read-only file system
```

--------------------------------

### Define the list command structure

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes the structure for the list command, including dependencies and configuration flags.

```go
package main

import (
        "cmp"
        "fmt"
        "os"
        "strings"
        "sync"
        "text/tabwriter"

        "github.com/spf13/cobra"
        "golang.org/x/exp/slices"

        "github.com/canonical/workshop/client"
)

type CmdList struct {
        root   *CmdRoot
        global bool
}
```

--------------------------------

### Expose service to local network

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/forward-ports.md

Bind the system SDK plug to 0.0.0.0 to allow access from other machines on the network.

```yaml
sdks:
  - name: go
    slots:
      caddy:
        interface: tunnel
        endpoint: localhost:8080        # service in the workshop
  - name: system
    plugs:
      caddy:
        interface: tunnel
        endpoint: 0.0.0.0:8080          # all host interfaces
```

--------------------------------

### Build Activation Listeners

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Constructs a map of addresses to listeners passed via systemd activation.

```go
// ActivationListeners builds a map of addresses to listeners that were passed
// during systemd activation
func ActivationListeners() (lns map[string]net.Listener, err error) {
        // pass false to keep LISTEN_* environment variables passed by systemd
        files := activation.Files(false)
        lns = make(map[string]net.Listener, len(files))

        for _, f := range files {
                ln, err := net.FileListener(f)
                if err != nil {
                        return nil, err
                }
                addr := ln.Addr().String()
                lns[addr] = ln
        }
        return lns, nil
}
```

--------------------------------

### Task Logging and Mocking

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Utilities for logging task events and mocking time for deterministic testing.

```go
const (
        // Messages logged in tasks are guaranteed to use the time formatted
        // per RFC3339 plus the following strings as a prefix, so these may
        // be handled programmatically and parsed or stripped for presentation.
        LogInfo  = "INFO"
        LogError = "ERROR"
)

var timeNow = time.Now

func MockTime(now time.Time) (restore func()) {
        timeNow = func() time.Time { return now }
        return func() { timeNow = time.Now }
}

func (t *Task) addLog(kind, format string, args []interface{}) {
        if len(t.log) > 9 {
                copy(t.log, t.log[len(t.log)-9:])
                t.log = t.log[:9]
        }

        tstr := timeNow().Format(time.RFC3339)
        msg := tstr + " " + kind + " " + fmt.Sprintf(format, args...)
        t.log = append(t.log, msg)
        logger.Debugf("%s", msg)
}
```

--------------------------------

### Retrieve User Projects

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Helper method to fetch and deserialize the workshop project configuration for a specific user from LXD.

```go
func (s *Backend) userProjects(ctx context.Context, user string) ([]workshop.Project, error) {
        client, err := s.LxdClient(ctx)
        if err != nil {
                return nil, err
        }
        defer client.Disconnect()

        lxdPrj, etag, err := client.GetProject(LxdProjectName(user))
        if err != nil {
                return nil, err
        }

        projects, err := readProjects([]byte(lxdPrj.Config["user.workshop.projects"]))
        if err != nil {
                return nil, err
        }
```

--------------------------------

### Download SDK with Locking and Cleanup

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Downloads an SDK file with file locking, progress reporting, and automatic cleanup of failed or old downloads.

```go
func (c *GcsStore) DownloadSdk(ctx context.Context, setup sdk.Setup, report *progress.Reporter) error {
	fl, err := sdk.OpenLock(setup.Name)
	if err != nil {
		return err
	}
	if err = fl.Lock(); err != nil {
		return err
	}
	defer fl.Close()

	info, err := storeSdkInfo(ctx, setup.Name, setup.Channel)
	if err != nil {
		return err
	}

	r, err := storeSdkReader(ctx, setup)
	if err != nil {
		return err
	}
	defer r.Close()

	target := setup.Filename()
	if !osutil.FileExists(target) {
		file, err := os.Create(target)
		if err != nil {
			return err
		}
		defer func() {
			// Remove the target as due to the error it may be corrupted.
			if err != nil {
				if err1 := os.Remove(target); err1 != nil {
					logger.Noticef("SDK Store on Download: Cannot remove %q on a failed download: %v", target, err1)
				}
				return
			}
			// If the SDK was downloaded successfully, remove its previous rev if any.
			matches, err1 := filepath.Glob(filepath.Join(filepath.Dir(target), setup.Name+"_*.sdk"))
			if err1 != nil {
				logger.Noticef("SDK Store on Download: Cannot cleanup previous downloads for %q: %v", setup.Name, err1)
			}
			for _, m := range matches {
				if m != target {
					if err1 = os.Remove(m); err1 != nil {
						logger.Noticef("SDK Store on Download: Cannot cleanup previous download (%s): %v", m, err1)
					}
				}
			}
		}()
		defer file.Close()

		var writer io.Writer
		if report != nil {
			writer = io.MultiWriter(file, &reporterWriter{r: report, total: int(info.Size)})
		} else {
			writer = file
		}

		if _, err = io.Copy(writer, r); err != nil {
			return err
		}
	} else {
		logger.Debugf("SDK Store on Download: SDK %q found locally: %s", setup.Name, target)
	}

	return nil
}
```

--------------------------------

### Workshop Configuration and Data Structures

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines constants, regex patterns, and structs for managing workshop SDK records, plugs, slots, and script serialization.

```go
package workshop

import (
        "cmp"
        "errors"
        "fmt"
        "os"
        "path/filepath"
        "regexp"
        "strings"

        "golang.org/x/exp/maps"
        "golang.org/x/exp/slices"
        "gopkg.in/yaml.v3"

        "github.com/canonical/workshop/internal/sdk"
)

var (
        SupportedBases = []string{"ubuntu@20.04", "ubuntu@22.04", "ubuntu@24.04"}
        sdkBlocklist   = []string{"agent"}

        workshopName = regexp.MustCompile(`^[a-z][a-z0-9-]*$`)
        channel      = regexp.MustCompile(`^(?P<track>[a-zA-Z0-9\.-]+)/(?P<risk>(stable|candidate|beta|edge))$`)

        Directory = ".workshop"
        Filenames = []string{"workshop.yaml", ".workshop.yaml"}
)

func filename(name string) string {
        return fmt.Sprintf("%s.yaml", name)
}

func Filepath(project, name string) string {
        return filepath.Join(project, Directory, filename(name))
}

type Plug struct {
        Bind       *PlugRef               `yaml:"bind,omitempty"`
        Attributes map[string]interface{} `yaml:",inline"`
}

type PlugRef struct {
        Sdk  string
        Name string
}

func (p PlugRef) String() string {
        return fmt.Sprintf("%s:%s", p.Sdk, p.Name)
}

type SlotRef = PlugRef

func (b *PlugRef) UnmarshalYAML(value *yaml.Node) error {
        var refStr string
        if err := value.Decode(&refStr); err != nil {
                return err
        }

        parts := strings.Split(refStr, ":")
        if len(parts) != 2 {
                return fmt.Errorf("%q is not a valid plug or slot reference (use <sdk>:<plug or slot>)", refStr)
        }
        if len(parts[0]) == 0 {
                parts[0] = sdk.System.String()
        }
        if !workshopName.MatchString(parts[0]) {
                return fmt.Errorf("%q is not a valid plug or slot reference (%q is an invalid SDK name)", refStr, parts[0])
        }

        b.Sdk = parts[0]
        b.Name = parts[1]
        return nil
}

func (b PlugRef) MarshalYAML() (interface{}, error) {
        return fmt.Sprintf("%s:%s", b.Sdk, b.Name), nil
}

type SdkRecord struct {
        Name    string                 `yaml:"name"`
        Channel string                 `yaml:"channel"`
        Plugs   map[string]Plug        `yaml:"plugs,omitempty"`
        Slots   map[string]interface{} `yaml:"slots,omitempty"`
        Hooks   map[string]string      `yaml:"hooks,omitempty"`
}

type Connection struct {
        PlugRef PlugRef `yaml:"plug"`
        SlotRef SlotRef `yaml:"slot"`
}

type Script string

type File struct {
        Name        string            `yaml:"name"`
        Base        string            `yaml:"base"`
        Sdks        []SdkRecord       `yaml:"sdks,omitempty"`
        Connections []Connection      `yaml:"connections,omitempty"`
        Scripts     map[string]Script `yaml:"scripts,omitempty"`
}

func (p Script) String() string {
        // Trim newlines, then append a newline for multi-line scripts.
        script := strings.Trim(string(p), "\n")
        if strings.ContainsRune(script, '\n') {
                script += "\n"
        }
        return script
}

func (p Script) MarshalYAML() (interface{}, error) {
        node := &yaml.Node{}
        err := node.Encode(p.String())
        return node, err
}
```

--------------------------------

### Define a workshop with AI agent SDKs

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/use-workshops-with-ai-agents.md

Create a workshop definition file to specify base images, SDKs, and encapsulated shell actions for AI agents.

```yaml
name: agent-dev
base: ubuntu@24.04
sdks:
  - name: claude-code
  - name: copilot

actions:
  claude-auto: |
    claude --model $CLAUDE_MODEL --dangerously-skip-permissions --print "$@"

  claude: |
    claude --model $CLAUDE_MODEL --dangerously-skip-permissions "$@"

  copilot-auto: |
    copilot --model $COPILOT_MODEL --yolo --silent --prompt "$@"

  copilot: |
    copilot --model $COPILOT_MODEL --yolo --interactive "$@"
```

--------------------------------

### SDK with Mount and GPU Plugs

Source: https://github.com/canonical/workshop/blob/main/docs/reference/definition-files/sdkcraft-definition.md

Configures an SDK for ROS 2 development, including mount interfaces for caching and a GPU interface plug.

```yaml
name: ros2
title: The ROS 2 SDK
base: ubuntu@24.04
version: "0.1"
summary: The strictly necessary ROS 2 development environment for your project.
description: |
  The ROS 2 SDK creates a minimum viable development environment
  for your ROS 2 project. It sets up a bare-bones ROS 2 workspace
  before installing all of the dependencies for the ROS 2 project
  mounted by workshop.

  A developer can then connect to the workshop and immediately build the project.
license: LGPL-2.1
platforms:
  amd64:
  arm64:

plugs:
  ros-cache:
    interface: mount
    workshop-target: /home/workshop/.ros

  colcon-artifacts:
    interface: mount
    workshop-target: /home/workshop/colcon

  gpu:
    interface: gpu
```

--------------------------------

### System SDK Metadata Generation

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Generates system SDK configuration based on a provided base string.

```go
package sdk

import (
        "fmt"
)

var systemSdkYaml = `name: system
base: %s
type: system
slots:
  camera:
    interface: camera
  mount:
    interface: mount
  gpu:
    interface: gpu
  ssh-agent:
    interface: ssh-agent
  desktop:
    interface: desktop
`

func SystemSdkMeta(base string) string {
        return fmt.Sprintf(systemSdkYaml, base)
}
```

--------------------------------

### Compile plug rules

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Maps subrule keys to compilers and provides the main entry point for compiling a plug rule.

```go
var plugRuleCompilers = map[string]subruleCompiler{
        "allow-installation":    compilePlugInstallationConstraints,
        "deny-installation":     compilePlugInstallationConstraints,
        "allow-connection":      compilePlugConnectionConstraints,
        "deny-connection":       compilePlugConnectionConstraints,
        "allow-auto-connection": compilePlugConnectionConstraints,
        "deny-auto-connection":  compilePlugConnectionConstraints,
}

func compilePlugRule(interfaceName string, rule interface{}) (*PlugRule, error) {
        context := fmt.Sprintf("plug rule for interface %q", interfaceName)
        plugRule := &PlugRule{
                Interface: interfaceName,
        }
        err := baseCompileRule(context, rule, plugRule, ruleSubrules, plugRuleCompilers, defaultOutcome, invertedOutcome)
        if err != nil {
                return nil, err
        }
        return plugRule, nil
}
```

--------------------------------

### Workshop Client Methods

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for listing, retrieving, and managing workshop resources via the API client.

```go
func (client *Client) List(opts *ListOptions) ([]*WorkshopInfo, []*WorkshopFile, error) {
        query := url.Values{}
        query.Set("state", "available")
        var info Workshops
        _, err := client.doSync("GET", "/v1/projects/"+opts.ProjectId+"/workshops", query, nil, nil, &info)
        if err != nil {
                return nil, nil, fmt.Errorf("cannot list workshops: %w", err)
        }
        return info.Workshops, info.Files, nil
}

func (client *Client) Workshop(projectId, name string) (*Workshop, error) {
        var workshop Workshop
        _, err := client.doSync("GET", "/v1/projects/"+projectId+"/workshops/"+name, nil, nil, nil, &workshop)
        if err != nil {
                return nil, err
        }
        return &workshop, nil
}

func (client *Client) SingleWorkshopName(project *Project) (string, error) {
        info, file, err := client.singleWorkshopOrFile(project)
        if err != nil {
                return "", fmt.Errorf("cannot infer workshop name: %w", err)
        }

        if info != nil {
                return info.Name, nil
        }
        if file != nil {
                return file.Name, nil
        }
        return "", errors.New("internal error: singleWorkshopOrFile returned nothing")
}

func (client *Client) SingleWorkshop(project *Project) (*Workshop, error) {
        info, file, err := client.singleWorkshopOrFile(project)
        if err != nil {
                return nil, fmt.Errorf("cannot infer workshop name: %w", err)
        }

        if info == nil {
                return nil, errors.New("workshop not launched")
        }
        workshop := Workshop{WorkshopInfo: *info}
        if file != nil {
                workshop.Path = file.Path
        }
        return &workshop, nil
}

func (client *Client) singleWorkshopOrFile(project *Project) (*WorkshopInfo, *WorkshopFile, error) {
        var info Workshops
        _, err := client.doSync("GET", "/v1/projects/"+project.Id+"/workshops", nil, nil, nil, &info)
        if err != nil {
                return nil, nil, err
        }

        var names []string
        for _, workshop := range info.Workshops {
                names = append(names, workshop.Name)
        }
        for _, file := range info.Files {
                if !slices.Contains(names, file.Name) {
                        names = append(names, file.Name)
                }
        }

        if len(names) < 1 {
                return nil, nil, fmt.Errorf("no workshops found in %q", project.Path)
        }
        if len(names) > 1 {
                return nil, nil, fmt.Errorf("multiple workshops found: %s", strutil.Quoted(names))
        }

        var workshop *WorkshopInfo
        if len(info.Workshops) > 0 {
                workshop = info.Workshops[0]
        }
        var file *WorkshopFile
        if len(info.Files) > 0 {
                file = info.Files[0]
        }
        return workshop, file, nil
}

func (client *Client) ListScripts(projectId, name string) (map[string]Script, error) {
        var scripts map[string]Script
        _, err := client.doSync("GET", "/v1/projects/"+projectId+"/workshops/"+name+"/scripts", nil, nil, nil, &scripts)
        if err != nil {
                return nil, err
        }
        return scripts, nil
}

func (client *Client) Remount(plug *PlugRef, source string) (changeId string, err error) {
        var body bytes.Buffer
        var remoutReq = Remount{
                Action:     "remount",
                Plug:       plug,
                HostSource: source,
        }
        if err := json.NewEncoder(&body).Encode(remoutReq); err != nil {
                return "", err
        }

        return client.doAsync("POST", "/v1/projects/"+plug.ProjectId+"/workshops/"+plug.Workshop+"/mounts", nil, nil, &body)
}
```

--------------------------------

### Shell into a workshop

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/use-multiple-workshops.md

Open a shell session inside a specific workshop.

```console
$ workshop shell backend
```

--------------------------------

### Execute Sketches List Command

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Implements the logic to fetch and display the list of sketches using a tabbed writer.

```go
func (c *CmdSketches) Run(cmd *cobra.Command, _ []string) error {
        cli, err := c.root.client()
        if err != nil {
                return err
        }

        w := tabWriter()
        var header sync.Once
        printHeader := func() {
                fmt.Fprintf(w, "Project\tWorkshop\tRev\tNotes\n")
        }

        p, err := cli.Project(c.root.project)
        if err != nil {
                return err
        }

        wps, _, err := cli.List(&client.ListOptions{ProjectId: p.Id})
        if err != nil {
                return err
        }
```

--------------------------------

### Verify workshop connections

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/add-mounts.md

List active connections to confirm that the SDKs are correctly paired.

```console
$ workshop connections dev

  INTERFACE  PLUG              SLOT                 NOTES
  mount      dev/jupyter:venv  dev/uv:venv          -
  mount      dev/uv:cache      dev/system:mount     -
  tunnel     -                 dev/jupyter:jupyter  -
```

--------------------------------

### Execute Commands and Validate Permissions

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Logic for running commands, managing output buffers, and validating user permissions based on UID and command arguments.

```go
// nonRootAllowed lists the commands that can be performed even when workshopctl
// is invoked not by root.
var nonRootAllowed = []string{"set-health"}

// Run runs the requested command.
func Run(context *hookstate.Context, args []string, uid uint32) (stdout, stderr []byte, err error) {
        if len(args) == 0 {
                return nil, nil, fmt.Errorf("workshopctl cannot run without args")
        }

        if !isAllowedToRun(uid, args) {
                return nil, nil, &ForbiddenCommandError{Message: fmt.Sprintf("cannot use %q with uid %d, try with sudo", args[0], uid)}
        }

        parser := flags.NewNamedParser("workshopctl", flags.PassDoubleDash|flags.HelpFlag)

        // Create stdout/stderr buffers, and make sure commands use them.
        var stdoutBuffer bytes.Buffer
        var stderrBuffer bytes.Buffer
        for name, cmdInfo := range commands {
                cmd := cmdInfo.generator()
                cmd.setName(name)
                cmd.setStdout(&stdoutBuffer)
                cmd.setStderr(&stderrBuffer)
                cmd.setContext(context)

                theCmd, err := parser.AddCommand(name, cmdInfo.shortHelp, cmdInfo.longHelp, cmd)
                theCmd.Hidden = cmdInfo.hidden
                if err != nil {
                        logger.Panicf("cannot add command %q: %s", name, err)
                }
        }

        _, err = parser.ParseArgs(args)
        return stdoutBuffer.Bytes(), stderrBuffer.Bytes(), err
}

func isAllowedToRun(uid uint32, args []string) bool {
        // A command can run if any of the following are true:
        //        * It runs as root
        //        * It's contained in nonRootAllowed
        //        * It's used with the -h or --help flags
        // note: commands still need valid context and workshops can only access own config.
        return uid == 0 ||
                strutil.ListContains(nonRootAllowed, args[0]) ||
                strutil.ListContains(args, "-h") ||
                strutil.ListContains(args, "--help")
}
```

--------------------------------

### Search for SDKs

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdk.md

Commands to search the SDK store using keywords or multiple words, with options to format output.

```console
$ sdk find <QUERY> [flags]
```

```console
$ sdk find openvino
```

```console
$ sdk find jupyter notebooks
```

```console
$ sdk find openvino --no-headers
```

--------------------------------

### Retrieve Workshop and Files

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for fetching specific workshop instances or files, requiring a locked state and project ID context.

```go
// Loads a workshop, the state must be locked as it is used to find out the
// workshop state
func (w *WorkshopManager) Workshop(ctx context.Context, name, pId string) (*workshop.Workshop, error) {
        // project-id must be in the context for this query
        pCtx := context.WithValue(ctx, workshop.ContextProjectId, pId)

        workshop, err := w.backend.Workshop(pCtx, name)
        if err != nil {
                return nil, err
        }

        return workshop, nil
}
```

```go
// Returns latest file for a workshop. The state must be locked,
// as listing projects can update project metadata.
func (w *WorkshopManager) WorkshopFile(ctx context.Context, name, pId string) (*workshop.File, error) {
        user, ok := ctx.Value(workshop.ContextUser).(string)
        if !ok {
                return nil, fmt.Errorf("context key %s not found", workshop.ContextUser)
        }

        projects, err := w.backend.Projects(ctx)
        if err != nil {
                return nil, err
        }

        idx := slices.IndexFunc(projects[user], func(p workshop.Project) bool { return p.ProjectId == pId })
        if idx == -1 {
                return nil, fmt.Errorf("project %q not found", pId)
        }
        p := projects[user][idx]

        return p.Workshop(name)
}
```

```go
// Returns all workshop files for a project. The state must be locked,
// as listing projects can update project metadata.
func (w *WorkshopManager) WorkshopFiles(ctx context.Context, pId string) (map[string]string, error) {
        user, ok := ctx.Value(workshop.ContextUser).(string)
        if !ok {
                return nil, fmt.Errorf("context key %s not found", workshop.ContextUser)
        }

        projects, err := w.backend.Projects(ctx)
        if err != nil {
                return nil, err
        }

        idx := slices.IndexFunc(projects[user], func(p workshop.Project) bool { return p.ProjectId == pId })
        if idx == -1 {
                return nil, fmt.Errorf("project %q not found", pId)
        }
        p := projects[user][idx]

        files, err := p.ReadWorkshops()
        if err != nil {
                return files, &WorkshopFileError{err}
        }
        return files, nil
}
```

--------------------------------

### Load Mount Profile

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Loads a mount profile from a file, returning an empty profile if the file does not exist.

```go
// MountProfile represents an array of mount entries.
type MountProfile struct {
        Entries []MountEntry
}

// LoadMountProfile loads a mount profile from a given file.
//
// The file may be absent, in such case an empty profile is returned without errors.
func LoadMountProfile(fname string) (*MountProfile, error) {
        f, err := os.Open(fname)
        if err != nil && os.IsNotExist(err) {
                return &MountProfile{}, nil
        }
        if err != nil {
                return nil, err
        }
        defer f.Close()
        return ReadMountProfile(f)
}
```

--------------------------------

### Constructing Change Information

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Logic for mapping internal task and change states to API-compatible structures.

```go
taskInfo := &taskInfo{
                        ID:      t.ID(),
                        Kind:    t.Kind(),
                        Summary: t.Summary(),
                        Status:  t.Status().String(),
                        Log:     t.Log(),
                        Progress: taskInfoProgress{
                                Label: label,
                                Done:  done,
                                Total: total,
                        },
                        SpawnTime: t.SpawnTime(),
                }
                readyTime := t.ReadyTime()
                if !readyTime.IsZero() {
                        taskInfo.ReadyTime = &readyTime
                }
                var data map[string]*json.RawMessage
                if t.Get("api-data", &data) == nil {
                        taskInfo.Data = data
                }
                taskInfos[j] = taskInfo
        }
        chgInfo.Tasks = taskInfos

        var prjId string
        if chg.Get("project-id", &prjId) == nil {
                chgInfo.ProjectId = prjId
        }

        var data map[string]*json.RawMessage
        if chg.Get("api-data", &data) == nil {
                chgInfo.Data = data
        }

        return chgInfo
}
```

--------------------------------

### workshop init

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Initializes a new workshop definition file within the project directory.

```APIDOC
## workshop init

### Description
Create a new workshop definition file in the project’s .workshop/ directory. Fails if a workshop with the same name already exists.

### Usage
`workshop init <NAME> --sdks <SDKs> [--base <BASE>] [flags]`

### Parameters
- **NAME** (string) - Required - The name of the workshop.
- **--sdks** (string) - Required - A comma-separated list of SDKs. Optionally includes channels using <name>/<channel> syntax.
- **--base** (string) - Optional - The base environment for the workshop.
```

--------------------------------

### Usage of sdkcraft create-track

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-create-track.rst

Basic syntax for creating tracks using the sdkcraft CLI.

```console
$ sdkcraft create-track --track TRACKS SDK
```

--------------------------------

### List available workshop connections

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/run-workshops-in-github-actions.md

Use this command to identify mount plugs that can be persisted between workflow runs.

```console
$ workshop connections --all

  INTERFACE  PLUG      SLOT          NOTES
  mount      uv:cache  system:mount  -
```

--------------------------------

### List workshops

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Commands to display workshops in the current project or globally.

```console
$ workshop list [flags]
```

```console
$ workshop list
```

```console
$ workshop list --global
```

--------------------------------

### Retrieving Connection References

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods to query established connections for specific plugs, slots, or SDKs.

```go
// Connected returns references for all connections that are currently
// established with the provided plug or slot.
func (r *Repository) Connected(projectId, workshop, sdkName, plugOrSlotName string) ([]*ConnRef, error) {
        r.m.Lock()
        defer r.m.Unlock()

        return r.connected(projectId, workshop, sdkName, plugOrSlotName)
}

func (r *Repository) connected(projectId, workshop, sk, plugOrSlotName string) ([]*ConnRef, error) {
        if workshop == "" {
                return nil, fmt.Errorf("internal error: cannot obtain workshop name while computing connections")
        }

        if sk == "" {
                return nil, fmt.Errorf("internal error: cannot obtain SDK name while computing connections")
        }

        key := plugOrSlotKey(projectId, workshop, sk)

        var conns []*ConnRef
        if plugOrSlotName == "" {
                return nil, fmt.Errorf("plug or slot name is empty")
        }
        // Check if plugOrSlotName actually maps to anything
        if r.plugs[key][plugOrSlotName] == nil && r.slots[key][plugOrSlotName] == nil {
                sdkRef := sdk.Ref{ProjectId: projectId, Workshop: workshop, Sdk: sk}
                return nil, &NoPlugOrSlotError{
                        message: fmt.Sprintf("SDK %q has no plug or slot named %q",
                                sdkRef.ShortRef(), plugOrSlotName)}
        }
        // Collect all the relevant connections

        if plug, ok := r.plugs[key][plugOrSlotName]; ok {
                for slotInfo := range r.plugSlots[plug] {
                        connRef := NewConnRef(plug, slotInfo)
                        conns = append(conns, connRef)
                }
        }

        if slot, ok := r.slots[key][plugOrSlotName]; ok {
                for plugInfo := range r.slotPlugs[slot] {
                        connRef := NewConnRef(plugInfo, slot)
                        conns = append(conns, connRef)
                }
        }

        return conns, nil
}

func (r *Repository) Connections(projectId, workshop, sdk string) ([]*ConnRef, error) {
        r.m.Lock()
        defer r.m.Unlock()
        if workshop == "" {
                return nil, fmt.Errorf("internal error: cannot obtain workshop name while computing connections")
        }

        if sdk == "" {
                return nil, fmt.Errorf("internal error: cannot obtain sdk name while computing connections")
        }

        key := plugOrSlotKey(projectId, workshop, sdk)
```

--------------------------------

### Root Workshop Command Configuration

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes the root 'workshop' command with persistent pre-run and post-run hooks.

```go
func (c *CmdRoot) Command(cwd string) *cobra.Command {
        cmd := &cobra.Command{
                Use: "workshop",
                // Avoid printing errors twice
                SilenceErrors:    true,
                SilenceUsage:     true,
                TraverseChildren: true,

                PersistentPreRunE: c.preRun,
                PersistentPostRun: c.postRun,
        }
```

--------------------------------

### SDK Find Command Usage

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdk-find.rst

Basic syntax for the 'sdk find' command. Replace <QUERY> with your search term and optionally add flags.

```console
$ sdk find <QUERY> [flags]
```

--------------------------------

### Run Warnings Command

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Executes the logic to fetch and display warnings, including verbose details and timestamp management.

```go
func (c *CmdWarnings) Run(cmd *cobra.Command, av []string) error {
        now := time.Now()

        cli, err := c.root.client()
        if err != nil {
                return err
        }

        warnings, err := cli.Warnings(client.WarningsOptions{All: c.All})
        if err != nil {
                return err
        }
        if len(warnings) == 0 {
                if t, _ := lastWarningTimestamp(); t.IsZero() {
                        fmt.Fprintln(Stdout, "No warnings.")
                } else {
                        fmt.Fprintln(Stdout, "No further warnings.")
                }
                return nil
        }

        if err := writeWarningTimestamp(now); err != nil {
                return err
        }

        termWidth, _ := termSize()
        if termWidth > 100 {
                // any wider than this and it gets hard to read
                termWidth = 100
        }

        esc := c.getEscapes()
        w := tabWriter()
        for i, warning := range warnings {
                if i > 0 {
                        fmt.Fprintln(w, "---")
                }
                if c.Verbose {
                        fmt.Fprintf(w, "first-occurrence:\t%s\n", c.fmtTime(warning.FirstAdded))
                }
                fmt.Fprintf(w, "last-occurrence:\t%s\n", c.fmtTime(warning.LastAdded))
                if c.Verbose {
                        lastShown := esc.dash
                        if !warning.LastShown.IsZero() {
                                lastShown = c.fmtTime(warning.LastShown)
                        }
                        fmt.Fprintf(w, "acknowledged:\t%s\n", lastShown)
                        // TODO: cmd.fmtDuration() using timeutil.HumanDuration
                        fmt.Fprintf(w, "repeats-after:\t%s\n", quantity.FormatDuration(warning.RepeatAfter.Seconds()))
                        fmt.Fprintf(w, "expires-after:\t%s\n", quantity.FormatDuration(warning.ExpireAfter.Seconds()))
                }
                fmt.Fprintln(w, "warning: |")
                printDescr(w, warning.Message, termWidth)
                w.Flush()
        }

        return nil
}
```

--------------------------------

### Lint source code

Source: https://github.com/canonical/workshop/blob/main/docs/contributing/development.md

Run golangci-lint to check for formatting and common issues.

```console
$ workshop run dev lint
```

```console
$ golangci-lint run
$ golangci-lint run --new-from-rev='HEAD~' --config=.golangci.incremental.yaml
```

--------------------------------

### Execute the list command

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles command execution and validates flag compatibility.

```go
func (c *CmdList) Run(cmd *cobra.Command, _ []string) error {
        // check if both --project and --global were provided
        if cmd.Parent().Flag("project").Changed && cmd.Flag("global").Changed {
                return fmt.Errorf("cannot list: '--project' incompatible with '--global'")
        }
        return c.runList()
}
```

--------------------------------

### Manage Mount Profiles and Commands

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Functions to read, write, and reload /etc/fstab mount profiles and execute mount/umount commands via LXD.

```go
func readMountProfile(fs workshop.WorkshopFs) (*osutil.MountProfile, error) {
        fstab, err := fs.Open("/etc/fstab")
        if errors.Is(err, os.ErrNotExist) {
                return &osutil.MountProfile{}, nil
        } else if err != nil {
                return nil, err
        }
        defer fstab.Close()

        return osutil.ReadMountProfile(fstab)
}
```

```go
func writeMountProfile(fs workshop.WorkshopFs, mounts *osutil.MountProfile) error {
        return workshop.AtomicWrite(fs, "/etc/fstab", mounts, 0644)
}
```

```go
func runMountCommand(conn lxd.InstanceServer, pid, w string, cmd []string) error {
        var out bytes.Buffer

        c := api.InstanceExecPost{
                Command:     cmd,
                Interactive: false,
        }

        args := lxd.InstanceExecArgs{Stderr: &out}

        op, err := conn.ExecInstance(lxdbackend.InstanceName(w, pid), c, &args)
        if err != nil {
                return err
        }

        if err = op.Wait(); err != nil {
                logger.Noticef("On workshop mount: %v (%s)", err, out.String())
        }
        return err
}
```

```go
func reloadMounts(conn lxd.InstanceServer, pid, w string) error {
        return runMountCommand(conn, pid, w, []string{
                "mount",
                "-a",
        })
}
```

```go
func removeMount(conn lxd.InstanceServer, fs workshop.WorkshopFs, pid, w string, mnt workshop.Mount) error {
        if mnt.Type != workshop.WorkshopWorkshop {
                return nil
        }

        mounts, err := readMountProfile(fs)
        if err != nil {
                return err
        }

        cnt := len(mounts.Entries)
        deleter := func(me osutil.MountEntry) bool {
                return me.Name == mnt.What && me.Dir == mnt.Where
        }
        mounts.Entries = slices.DeleteFunc(mounts.Entries, deleter)
        if cnt == len(mounts.Entries) {
                return nil
        }

        if err = writeMountProfile(fs, mounts); err != nil {
                return err
        }

        return runMountCommand(conn, pid, w, []string{
                "umount",
                mnt.Where,
        })
}
```

--------------------------------

### Workshop Client Data Structures and Execution

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the options and data structures for workshopctl requests, including a method to execute commands with stdin support.

```go
package client

import (
        "bytes"
        "encoding/json"
        "fmt"
        "io"
)

// WorkshopCtlOptions holds the various options with which workshopctl is invoked.
type WorkshopCtlOptions struct {
        // ContextID is a string used to determine the context of this call (e.g.
        // which context and handler should be used, etc.)
        ContextID string `json:"context-id"`

        // Args contains a list of parameters to use for this invocation.
        Args []string `json:"args"`
}

// WorkshopCtlPostData is the data posted to the daemon /v2/workshopctl endpoint
// TODO: this can be removed again once we no longer need to pass stdin data
// but instead use a real stdin stream
type WorkshopCtlPostData struct {
        WorkshopCtlOptions

        Stdin []byte `json:"stdin,omitempty"`
}

type workshopctlOutput struct {
        Stdout string `json:"stdout"`
        Stderr string `json:"stderr"`
}

// protect against too much data via stdin
var stdinReadLimit = int64(4 * 1000 * 1000)

// RunWorkshopctl requests a workshopctl run for the given options.
func (client *Client) RunWorkshopctl(options *WorkshopCtlOptions, stdin io.Reader) (stdout, stderr []byte, err error) {
        // TODO: instead of reading all of stdin here we need to forward it to
        //       the daemon eventually
        var stdinData []byte
        if stdin != nil {
                limitedStdin := &io.LimitedReader{R: stdin, N: stdinReadLimit + 1}
                stdinData, err = io.ReadAll(limitedStdin)
                if err != nil {
                        return nil, nil, fmt.Errorf("cannot read stdin: %v", err)
                }
                if limitedStdin.N <= 0 {
                        return nil, nil, fmt.Errorf("cannot read more than %v bytes of data from stdin", stdinReadLimit)
                }
        }

        b, err := json.Marshal(WorkshopCtlPostData{
                WorkshopCtlOptions: *options,
                Stdin:              stdinData,
        })
        if err != nil {
                return nil, nil, fmt.Errorf("cannot marshal options: %s", err)
        }

        var output workshopctlOutput
        _, err = client.doSync("POST", "/v1/workshopctl", nil, nil, bytes.NewReader(b), &output)
        if err != nil {
                return nil, nil, err
        }

        return []byte(output.Stdout), []byte(output.Stderr), nil
}
```

--------------------------------

### Workshop Management Interfaces

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Interfaces for managing workshop stashes, storage volumes, and base image downloads.

```go
type Stash interface {
        StashWorkshop(ctx context.Context, name string) error
        UnstashWorkshop(ctx context.Context, name string) error
        RemoveWorkshopStash(ctx context.Context, name string) error
}

type VolumeManager interface {
        CreateVolume(ctx context.Context, name string) error
        AttachVolume(ctx context.Context, wp, name, what string) error
        DetachVolume(ctx context.Context, wp, name string) error
        DeleteVolume(ctx context.Context, name string) error
}

type BaseImageManager interface {
        Download(ctx context.Context, base string, report *progress.Reporter) error
}
```

--------------------------------

### Workshop run with environment and working directory

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-run.rst

Execute a workshop action while setting specific environment variables and the working directory. This is useful for controlling the execution context of the action.

```console
$ workshop run --env GO111MODULE=off -w /project nimble -- build
```

--------------------------------

### Execute Command and Initialize Execution State

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes an execution object with websocket channels and registers it with the manager before running the command.

```go
func (m *CommandManager) doExec(task *state.Task, tomb *tomb.Tomb) error {
        user, prj, w, err := UserProjectWorkshop(task)
        if err != nil {
                return err
        }

        ctx, cancel := BackendContext(tomb, user, prj.ProjectId)
        defer cancel()

        st := task.State()
        st.Lock()
        argsObj := st.Cached(ExecArgsKey(task.ID()))
        st.Unlock()
        args, ok := argsObj.(*workshop.ExecArgs)
        if !ok || args == nil {
                return fmt.Errorf("cannot get exec args for task %q: task was probably interrupted", task.ID())
        }

        // Set up the object that will track the execution.
        e := &execution{
                workshop:         w,
                execArgs:         args,
                websockets:       make(map[string]*websocket.Conn),
                ioConnected:      make(chan struct{}),
                controlConnected: make(chan struct{}),
        }

        // Populate the websockets map (with nil connections until connected).
        e.websockets[wsControl] = nil
        e.websockets[wsStdio] = nil
        e.websockets[wsStdout] = nil
        e.websockets[wsStderr] = nil

        // Store the execution object on the manager (for Connect).
        m.executionsMutex.Lock()
        m.executions[task.ID()] = e
        m.executionsMutex.Unlock()
        m.executionsCond.Broadcast() // signal that Connects can start happening
        defer func() {
                m.executionsMutex.Lock()
                delete(m.executions, task.ID())
                m.executionsMutex.Unlock()
        }()

        // Run the command! Killing the tomb will terminate the command.
        return e.do(ctx, task, m.backend)
}
```

--------------------------------

### Initialize and Lock State File

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles file lock creation and implements a retry loop with systemd notification for long-running lock acquisitions.

```go
func initStateFileLock() (*osutil.FileLock, error) {
	lockFilePath := dirs.WorkshopStateLockFile
	if err := os.MkdirAll(filepath.Dir(lockFilePath), 0755); err != nil {
		return nil, err
	}

	return osutil.NewFileLockWithMode(lockFilePath, 0644)
}

func lockWithTimeout(l *osutil.FileLock, timeout time.Duration) error {
	startTime := time.Now()
	systemdWasNotified := false
	for {
		err := l.TryLock()
		if err != osutil.ErrAlreadyLocked {
			// We return nil if err is nil (that is, if we got the lock); we
			// also return for any error except for ErrAlreadyLocked, because
			// in that case we want to continue trying.
			return err
		}

		// The state is locked. Let's notify systemd that our startup might be
		// longer than usual, or we risk getting killed if we overstep the
		// systemd timeout.
		if !systemdWasNotified {
			logger.Noticef("Adjusting startup timeout by %v", timeout)
			systemdSdNotify(fmt.Sprintf("EXTEND_TIMEOUT_USEC=%d", timeout.Microseconds()))
			systemdWasNotified = true
		}

		if time.Since(startTime) >= timeout {
			return errors.New("timeout for state lock file expired")
		}
		time.Sleep(stateLockRetryInterval)
	}
}
```

--------------------------------

### Mock SDK Information for Testing

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Helper functions to mock SDK validation and attribute sanitization during unit tests.

```go
func MockSanitizePlugsSlots(f func(sdkInfo *Info)) (restore func()) {
        old := SanitizePlugsSlots
        SanitizePlugsSlots = f
        return func() { SanitizePlugsSlots = old }
}

func MockInfo(c *check.C, yamlText string, projectId, workshop string) *Info {
        restoreSanitize := MockSanitizePlugsSlots(func(sdkInfo *Info) {})
        defer restoreSanitize()
        info, err := ReadSdkInfo([]byte(yamlText), projectId, workshop)
        c.Assert(err, check.IsNil)

        err = Validate(info)
        c.Assert(err, check.IsNil)
        return info
}

func MockInvalidInfo(c *check.C, yamlText string) *Info {
        restoreSanitize := MockSanitizePlugsSlots(func(sdkInfo *Info) {})
        defer restoreSanitize()

        sdkInfo, err := ReadSdkInfo([]byte(yamlText), "invalid", "ws")
        c.Assert(err, check.IsNil)
        err = Validate(sdkInfo)
        c.Assert(err, check.NotNil)
        return sdkInfo
}
```

--------------------------------

### InfoOptions Configuration

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Configuration struct for defining options when retrieving information from the repository.

```go
// InfoOptions describes options for Info.
//
// Names: return just this subset if non-empty.
// Doc: return documentation.
// Plugs: return information about plugs.
// Slots: return information about slots.
// Connected: only consider interfaces with at least one connection.
type InfoOptions struct {
	Names     []string
	Doc       bool
	Plugs     bool
	Slots     bool
	Connected bool
}
```

--------------------------------

### Load Project from Context

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Retrieves a project by ID from the backend using the user identity stored in the context.

```go
func (w *WorkshopManager) loadProject(ctx context.Context, id string) (*workshop.Project, error) {
        username, ok := ctx.Value(workshop.ContextUser).(string)
        if !ok {
                return nil, fmt.Errorf("context key user not found")
        }

        projects, err := w.backend.Projects(ctx)
        if err != nil {
                return nil, err
        }

        idx := slices.IndexFunc(projects[username], func(p workshop.Project) bool { return p.ProjectId == id })
        if idx == -1 {
                return nil, fmt.Errorf("no project found with \"id\" %v", id)
        }
        return &projects[username][idx], nil
}
```

--------------------------------

### Define an in-project SDK with a mount plug

Source: https://github.com/canonical/workshop/blob/main/docs/reference/definition-files/sdk-definition.md

Use this structure to declare a project-specific SDK that exposes a mount target for persistent storage.

```yaml
name: ccache
version: "0.1"
summary: Shared ccache
description: |
  Project-specific SDK that exposes a mount target
  for preserving cache across workshop updates.
plugs:
  ccache:
    interface: mount
    workshop-target: /home/workshop/.cache/ccache
```

--------------------------------

### Launch workshop for inspection

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/build-an-sdk.md

Launch the workshop with verbose output and a wait-on-error breakpoint to facilitate debugging hook failures.

```console
$ workshop launch --verbose --wait-on-error
```

--------------------------------

### Download Operation Structures

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Data structures for tracking download updates and managing progress reporters.

```go
type downloadUpdate struct {
		Label string
		Done  int
		Total int
}

type downloadOp struct {
		waitCh chan error

		reportersLock sync.Mutex
		reporters     map[string]*progress.Reporter
}
```

--------------------------------

### Define Workshop Directory Paths

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Configures standard directory paths for the workshop environment, including SDKs, state storage, and run directories.

```go
package dirs

import (
        "fmt"
        "os"
        "path/filepath"
)

// defaultBaseDir is the Workshop directory used if $WORKSHOP is not set. It is
// created by the daemon ("workshopd run") if it doesn't exist, and also used by
// the workshop client.
const defaultBaseDir = "/var/lib/workshop"

// Variables for paths inside a workshop
var (
        // base directory inside a workshop
        WorkshopBaseDir = defaultBaseDir

        // SDKs directory to install an SDK in a workshop
        WorkshopSdksDir = filepath.Join(WorkshopBaseDir, "sdk")

        // Base directory for the state storage
        WorkshopStateDir = filepath.Join(WorkshopBaseDir, "state")

        // Base directory for the SDK state storage
        WorkshopSdkStateDir = filepath.Join(WorkshopStateDir, "sdk")

        // Run directory inside workshop
        WorkshopRunDir = filepath.Join(WorkshopBaseDir, "run")

        // Directory for scripts inside workshop
        WorkshopScriptsDir = filepath.Join(WorkshopRunDir, "scripts")

        // Cache directory for deb packages
        AptCachePath = "/var/cache/apt/archives"
)
```

--------------------------------

### Execute Command in Instance

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Executes a command within an LXD instance and returns an execution context for tracking completion.

```go
func (s *Backend) execCommand(conn lxd.InstanceServer, ctx context.Context, name string, args *workshop.Execution) (workshop.ExecContext, error) {
        projectId, ok := ctx.Value(workshop.ContextProjectId).(string)
        if !ok {
                return workshop.ExecContext{}, fmt.Errorf("context key project-id not found")
        }

        req := api.InstanceExecPost{
                Command:     args.Command,
                WaitForWS:   true,
                Interactive: args.Interactive,
                Environment: args.Environment,
                Width:       args.Width,
                Height:      args.Height,
                User:        uint32(args.UserId),
                Group:       uint32(args.GroupId),
                Cwd:         args.WorkDir,
        }

        done := make(chan bool)

        op, err := conn.ExecInstance(InstanceName(name, projectId), req, &lxd.InstanceExecArgs{
                Stdin:    args.Stdin,
                Stdout:   args.Stdout,
                Stderr:   args.Stderr,
                Control:  args.Control,
                DataDone: done,
        })
        if err != nil {
                return workshop.ExecContext{}, err
        }

        opmeta := op.Get()
        var env = map[string]string{}
        for k, v := range opmeta.Metadata["environment"].(map[string]any) {
                if value, ok := v.(string); ok {
                        env[k] = value
                }
        }

        return workshop.ExecContext{
                Environment: env,
                WaitExecution: func(ctx context.Context) error {
                        defer conn.Disconnect()

                        if err := op.WaitContext(ctx); err != nil {
                                return err
                        }

                        // waiting for any remaining data IO to be flushed LXD closes this channel
                        // unconditionally right after the operation has exited, so it will not be
                        // blocked if we are here
                        <-done
                        var status = int(op.Get().Metadata["return"].(float64))
                        if status != 0 {
                                return &workshop.ErrExec{Status: status}
                        }
                        return nil
                },
        }, nil
}

func (s *Backend) Exec(ctx context.Context, name string, args *workshop.Execution) (workshop.ExecContext, error) {
        conn, err := s.LxdClient(ctx)
        if err != nil {
                return workshop.ExecContext{}, err
        }

        return s.execCommand(conn, ctx, name, args)
}
```

--------------------------------

### Define a minimal workshop

Source: https://github.com/canonical/workshop/blob/main/docs/reference/definition-files/workshop-definition.md

A basic workshop configuration featuring one Store SDK and two defined actions.

```yaml
name: golang
base: ubuntu@22.04
sdks:
  - name: go
    channel: "1.26"
actions:
  lint: |
    go vet
    golangci-lint run
  tests: go test "$@"
```

--------------------------------

### List All Workshop Changes

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-changes.rst

Execute this command to view a list of all recent changes across all workshops in the current project directory. It displays key details for each change.

```console
$ workshop changes
```

--------------------------------

### Build project artifacts

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft.md

Command to build artifacts for specified parts or all parts.

```console
$ sdkcraft build [--destructive-mode | --use-lxd] [--shell | --shell-after] [--debug]
                   [--platform name | --build-for arch]
                   [part-name ...]
```

--------------------------------

### Record Interface Slots and Plugs

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods to record permanent slots and plugs for workshop interfaces.

```go
// AddPermanentSlot records side-effects of having a slot.
func (s *Specification) AddPermanentSlot(iface interfaces.Interface, slot *sdk.SlotInfo) error {
        return nil
}

// AddPermanentPlug records side-effects of having a plug.
func (s *Specification) AddPermanentPlug(iface interfaces.Interface, plug *sdk.PlugInfo) error {
        return nil
}
```

--------------------------------

### Inspect Workshop Tunnel Configuration

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/interfaces/tunnel-interface.md

View detailed information about SDKs and their configured tunnel mappings.

```console
$ workshop info dev

  name:     dev
  base:     ubuntu@22.04
  project:  /home/user/workshop/dev
  status:   ready
  notes:    -
  sdks:
    system:
      tunnels:
        app:
          from:  0.0.0.0:8081/tcp
          to:    127.0.0.1:8080/tcp
    client-sdk:
      tracking:   latest/stable
      installed:  2024-03-02  (1)
      tunnels:
        shared:
          from:  [::1]:1080/tcp
          to:    127.0.0.1:18080/tcp
    service-sdk:
      tracking:   latest/edge
      installed:  2025-06-07  (2)
```

--------------------------------

### Connect SDKs in workshop definition

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/share-content-between-sdks.md

Pair a specific plug and slot using the connections entry in the workshop configuration.

```yaml
name: dev
base: ubuntu@24.04
sdks:
  - name: cachekit
  - name: builder-sdk
connections:
  - plug: builder-sdk:cache
    slot: cachekit:shared
```

--------------------------------

### Manage Hook Contexts

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for retrieving or creating ephemeral workshop contexts based on cookie IDs.

```go
func (w *HookManager) Ensure() error {
        return nil
}

func (m *HookManager) ephemeralContext(cookieID string) (context *Context, err error) {
        var contexts map[string]string
        m.state.Lock()
        defer m.state.Unlock()
        err = m.state.Get("workshop-cookies", &contexts)
        if err != nil {
                return nil, fmt.Errorf("cannot get workshop cookies: %v", err)
        }
        if workshop, ok := contexts[cookieID]; ok {
                // create new ephemeral context
                context, err = NewContext(nil, m.state, &HookSetup{Workshop: workshop}, nil, cookieID)
                return context, err
        }
        return nil, fmt.Errorf("invalid workshop cookie requested")
}

// Context obtains the context for the given cookie ID.
func (m *HookManager) Context(cookieID string) (*Context, error) {
        m.contextsMutex.RLock()
        defer m.contextsMutex.RUnlock()

        var err error
        context, ok := m.contexts[cookieID]
        if !ok {
                context, err = m.ephemeralContext(cookieID)
                if err != nil {
                        return nil, err
                }
        }

        return context, nil
}
```

--------------------------------

### Remounting Workshop Plugs

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles the remounting of a plug by updating its host-source attribute and performing necessary filesystem renames. Requires an active backend context and task state management.

```go
        ctx, cancel := handlersetup.BackendContext(tomb, user, project.ProjectId)
        defer cancel()

        st := task.State()
        st.Lock()
        defer st.Unlock()

        var plug interfaces.PlugRef
        if err := task.Get("plug", &plug); err != nil {
                return err
        }

        var source string
        if err := task.Get("host-source", &source); err != nil {
                return err
        }

        inst, err := m.backend.Workshop(ctx, w)
        if err != nil {
                return err
        }

        return m.remount(ctx, task, &plug, source, inst.Running)
}

func (m *InterfaceManager) remount(ctx context.Context, task *state.Task, plug *interfaces.PlugRef, source string, workshopRunning bool) error {
        revert := revert.New()
        defer revert.Fail()

        conns, err := getConns(m.state)
        if err != nil {
                return err
        }

        plugConns, err := m.repo.Connected(plug.ProjectId, plug.Workshop, plug.Sdk, plug.Name)
        if err != nil {
                return err
        }
        if len(plugConns) != 1 {
                return fmt.Errorf("plug %q must have exactly one connection to be remounted", plug.ShortRef())
        }
        connRef := plugConns[0]
        // get the connected plug-slot pair to get its existing attributes (source)
        connection, err := m.repo.Connection(connRef)
        if err != nil {
                return err
        }

        var oldSource string
        if err := connection.Slot.Attr("host-source", &oldSource); err != nil {
                return err
        }

        if err := connection.Slot.SetAttr("host-source", source); err != nil {
                return err
        }

        // the connection exists already; this connect is required to update the
        // plug's source attribute
        newConnection, err := m.repo.Connect(connRef, connection.Plug.StaticAttrs(),
                connection.Plug.DynamicAttrs(), connection.Slot.StaticAttrs(), connection.Slot.DynamicAttrs(), nil)
        if err != nil {
                return err
        }

        revert.Add(func() {
                _ = connection.Slot.SetAttr("host-source", oldSource)
                if _, err := m.repo.Connect(connRef, connection.Plug.StaticAttrs(),
                        connection.Plug.DynamicAttrs(), connection.Slot.StaticAttrs(), connection.Slot.DynamicAttrs(), nil); err != nil {
                        logger.Debugf("On doRemount: cannot reconnect %q plug on a failed remount", plug.ShortRef())
                }
        })

        _, err = os.Stat(oldSource)
        if osutil.IsDirNotExist(err) {
                task.State().Warnf("cannot find source %q for %q; will attempt to recreate", oldSource, plug.ShortRef())
        } else if err != nil {
                return err
        } else {
                if err := osutil.Rename(oldSource, source); err != nil {
                        if errno, ok := err.(syscall.Errno); ok {
                                if workshopRunning {
                                        if errno == syscall.ENOTEMPTY {
                                                return fmt.Errorf("source %q is not empty; workshop must be stopped to remount safely", source)
                                        }
                                        if errno == syscall.EXDEV {
                                                return fmt.Errorf("sources %q and %q are not on the same mounted filesystem; workshop must be stopped to remount safely", oldSource, source)
                                        }
                                        return err
                                } else {
                                        // if the workshop is stopped, we can perform a remount safely
                                        // (other fs or non-empty dir), otherwise, return the error
                                        if errno != syscall.ENOTEMPTY && errno != syscall.EXDEV {
                                                return err
                                        }
                                }
                        } else {
                                return err
                        }
                } else {
                        revert.Add(func() {
                                if err := os.Rename(source, oldSource); err != nil {
                                        logger.Debugf("On doRemount: Cannot rename %q to %q on a failed remount", source, oldSource)
                                }
                        })
                }
        }

        for _, backend := range m.repo.Backends() {
                if err := backend.Setup(ctx, connection.Plug.Sdk().Ref(), m.repo); err != nil {
                        return err
                }
        }

        var auto bool
        if old, ok := conns[connRef.ID()]; ok {
                auto = old.Auto
        }
```

--------------------------------

### Download Workshop Image

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles concurrent image downloads with progress reporting.

```go
func (b *Backend) Download(ctx context.Context, base string, report *progress.Reporter) error {
        defer func() {
                if report != nil {
                        imageLock.Lock()
                        if op, exist := currentDownloads[base]; exist {
                                op.RemoveReporter(report.Name)
                        }
                        imageLock.Unlock()
                }
        }()

        imageLock.Lock()
        op, exist := currentDownloads[base]
        if exist {
                if report != nil {
                        op.AddReporter(report)
                }
                imageLock.Unlock()
                return waitDownloadOp(ctx, op)
        }

        op = newImageDownloadOp()
        if report != nil {
                op.AddReporter(report)
        }
        currentDownloads[base] = op
        imageLock.Unlock()

        go b.download(ctx, op, base)

        return waitDownloadOp(ctx, op)
}
```

--------------------------------

### PlugConnectionConstraints Methods

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for managing plug connection constraints and feature checks.

```go
func (c *PlugConnectionConstraints) feature(flabel string) bool {
        if flabel == nameConstraintsFeature {
                return c.PlugNames != nil || c.SlotNames != nil
        }
        return c.PlugAttributes.feature(flabel) || c.SlotAttributes.feature(flabel)
}

func (c *PlugConnectionConstraints) setNameConstraints(field string, cstrs *NameConstraints) {
        switch field {
        case "plug-names":
                c.PlugNames = cstrs
        case "slot-names":
                c.SlotNames = cstrs
        default:
                panic("unknown PlugConnectionConstraints field " + field)
        }
}

func (c *PlugConnectionConstraints) setAttributeConstraints(field string, cstrs *AttributeConstraints) {
        switch field {
        case "plug-attributes":
                c.PlugAttributes = cstrs
        case "slot-attributes":
                c.SlotAttributes = cstrs
        default:
                panic("unknown PlugConnectionConstraints field " + field)
        }
}

func (c *PlugConnectionConstraints) setIDConstraints(field string, cstrs []string) {
        switch field {
        case "slot-sdk-type":
                c.SlotSdkTypes = cstrs
        default:
                panic("unknown PlugConnectionConstraints field " + field)
        }
}

func (c *PlugConnectionConstraints) setSlotsPerPlug(a SideArityConstraint) {
        c.SlotsPerPlug = a
}

func (c *PlugConnectionConstraints) setPlugsPerSlot(a SideArityConstraint) {
        c.PlugsPerSlot = a
}

func (c *PlugConnectionConstraints) slotsPerPlug() SideArityConstraint {
        return c.SlotsPerPlug
}

func (c *PlugConnectionConstraints) plugsPerSlot() SideArityConstraint {
        return c.PlugsPerSlot
}
```

--------------------------------

### Retrieve Workshops by Configuration

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Filters workshops based on a provided configuration filter.

```go
func (f *FakeWorkshopBackend) GetWorkshopsByConfig(ctx context.Context, filter workshop.WorkshopConfigFilter) ([]*workshop.Workshop, error) {
        res := make([]*workshop.Workshop, 0)
        for _, i := range f.Workshops {
                for _, j := range i {
                        if filter(j.Config) {
                                res = append(res, j.Workshop)
                        }
                }
        }
        return res, nil
}
```

--------------------------------

### Migrate Xauthority file

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Copies the user's Xauthority file to the workshop run directory while validating file ownership to prevent unauthorized access.

```go
// Copies the user's $XAUTHORITY file to the Workshopd run directory.
func MigrateXauthority(user *user.User, xauth string) (err error) {
        if xauth == "" {
                return fmt.Errorf("xauth cannot be empty")
        }

        // We place the Xauthority inside a parent folder to ensure that the mounted
        // cookie is updated when the host cookie changes (ie. reboot). This entire
        // parent folder is mounted inside the workshop.
        // https://discuss.linuxcontainers.org/t/mount-single-file/17975
        destDir := filepath.Join(dirs.WorkshopdRunDir, user.Uid, "Xauthority")
        if err := os.MkdirAll(destDir, 0755); err != nil {
                return err
        }

        // We are performing a Stat() here to ensure that the user can't steal
        // another user's Xauthority file. Note that while Stat() uses fstat() on the
        // file descriptor created during Open(), the file might have changed
        // ownership between the Open() and the Stat(). That's ok because we aren't
        // trying to block access that the user already has: if the user has the
        // privileges to chown another user's Xauthority file, we won't block that
        // since the user can just steal it without having to use workshop. This code
        // is just to ensure that a user who doesn't have those privileges can't
        // steal the file via 'workshop connect'
        f, err := os.Stat(xauth)
        if err != nil {
                return err
        }
        fsys := f.Sys()
        if fsys == nil {
                return fmt.Errorf("cannot validate owner of file %s", f.Name())
        }
        // cheap comparison as the current uid is only available as a string
        // but it is better to convert the uid from the stat result to a
        // string than a string into a number.
        if fmt.Sprintf("%d", fsys.(*syscall.Stat_t).Uid) != user.Uid {
                return fmt.Errorf("Xauthority file isn't owned by the current user %s", user.Uid)
        }

        destFile := filepath.Join(destDir, ".Xauthority")
        err = osutil.CopyFile(xauth, filepath.Join(destDir, ".Xauthority"), osutil.CopyFlagOverwrite)
        if err != nil {
                return err
        }

        uid, gid, err := osutil.UidGid(user)
        if err != nil {
                return err
        }

        if err = sys.ChownPath(destFile, uid, gid); err != nil {
                return err
        }

        return nil
}
```

--------------------------------

### List Global Workshops

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/move-projects.md

Command to list all workshops available globally, showing their project paths, names, statuses, and notes.

```console
$ workshop list --global
```

--------------------------------

### Create Task Timings in Go

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes a new Timings tree with task-specific metadata tags.

```go
func TimingsForTask(task *Task) *timings.Timings {
	tags := map[string]string{
		"task-id":     task.ID(),
		"task-kind":   task.Kind(),
		"task-status": task.Status().String(),
	}
	if chg := task.Change(); chg != nil {
		tags["change-id"] = chg.ID()
	}
	return timings.New(tags)
}
```

--------------------------------

### Define a runtime SDK configuration

Source: https://github.com/canonical/workshop/blob/main/docs/reference/definition-files/sdk-definition.md

This format represents a runtime sdk.yaml file generated by SDKcraft, specifying base images, architecture, and mount plugs.

```yaml
name: go
title: Go SDK
version: "1.25.1"
summary: The Go programming language
description: |
  Go is an open source programming language that enables the production of simple,
  efficient and reliable software at scale.
base: ubuntu@24.04
architecture: amd64
license: LGPL-2.1
sdkcraft-started-at: "2026-04-12T08:30:00Z"
plugs:
  mod-cache:
    interface: mount
    workshop-target: /home/workshop/go/pkg/mod
```

--------------------------------

### Refresh and connect workshop services

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/forward-ports.md

Commands to apply configuration changes and establish the connection between SDK plugs and slots.

```console
$ workshop refresh
```

```console
$ workshop connect mlflow/mlflow:postgres mlflow/system:postgres
```

--------------------------------

### Remount and verify info

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/fix-workshops/resolve-plug-conflicts.md

Demonstrates that remounting one bound plug updates the shared mount information for all associated plugs.

```console
$ mkdir -p .cache/hub
$ workshop remount digits/torchaudio:hub .cache/hub
$ workshop info digits

  ...
  mounts:
    hub:
      host-source:      /home/user/digits/.cache/hub
      workshop-target:  /home/workshop/.cache/torch/hub
```

--------------------------------

### Execute a workshop action

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/workshops/concepts.md

Command to run a specific action defined in the workshop configuration.

```console
$ workshop run dev -- lint
```

--------------------------------

### Command execution logic

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles the execution of the connections command, including client initialization and argument validation.

```go
func (c *CmdConnections) Run(cmd *cobra.Command, av []string) error {
        cli, err := c.root.client()
        if err != nil {
                return err
        }

        project, err := cli.Project(c.root.project)
        if err != nil {
                return err
        }

        workshop := ""
        if len(av) > 0 {
                workshop = av[0]
                if c.all {
                        // passing a workshop name already implies --all, error out
                        // when it was passed explicitly
                        return fmt.Errorf("cannot use --all with workshop name")
                }
                c.all = true
        }

        connections, err := cli.Connections(&client.ConnectionOptions{ProjectId: project.Id, Workshop: workshop, All: c.all})
        if err != nil {
                return err
        }

        if len(connections.Plugs) == 0 && len(connections.Slots) == 0 {
                return nil
        }
```

--------------------------------

### Workshop Connect Command Usage

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-connect.rst

This is the general usage syntax for the 'workshop connect' command. It outlines the required arguments and optional flags.

```console
$ workshop connect <WORKSHOP>/<SDK>:PLUG [<WORKSHOP>/<SDK>][:<SLOT>] [flags]
```

--------------------------------

### Workshop Exec Usage Syntax

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-exec.rst

Displays the general syntax for the 'workshop exec' command, including flags and arguments.

```console
$ workshop exec [flags] [<WORKSHOP>] [--] <COMMAND>...
```

--------------------------------

### Verify remount configuration with workshop info

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/add-mounts.md

Use workshop info to display the current host-source and workshop-target mapping after a remount.

```console
$ workshop remount dev/uv:shared ~/datasets
$ workshop info dev

  ...
  sdks:
    uv:
      mounts:
        shared:
          host-source:      /home/user/datasets
          workshop-target:  /home/workshop/shared
  ...
```

--------------------------------

### Define a basic workshop configuration

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/workshops/concepts.md

A minimal YAML definition specifying the workshop name, base OS image, and required SDKs.

```yaml
name: dev
base: ubuntu@22.04
sdks:
  - name: go
    channel: "1.26"
```

--------------------------------

### Execute Shell Logic

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Implements the 'shell' command execution, defaulting to the 'workshop' user.

```go
func (c *CmdShell) Run(cmd *cobra.Command, av []string) error {
        args := &ExecArgs{command: []string{"sudo", "-i", "-u", "workshop", "bash", "-c", "cd /project; exec bash"}}

        if len(av) > 0 {
                args.workshop = av[0]
        } else {
                args.implicit = true
        }

        return exec(c.root, &ExecFlags{WorkingDir: "/project"}, args)
}
```

--------------------------------

### Define an SDK build configuration

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/sdks/concepts.md

The sdkcraft.yaml file specifies build-time metadata, supported platforms, and parts for an SDK.

```yaml
name: go
build-base: ubuntu@24.04
title: Go SDK
summary: The Go programming language
description: |
  Go is an open source programming language that enables the production of simple, efficient and reliable software at scale.
version: "1.25.1"
license: LGPL-2.1
platforms:
  amd64:
    build-on: [amd64]
    build-for: [amd64]
  arm64:
    build-on: [amd64]
    build-for: [arm64]
  riscv64:
    build-on: [amd64]
    build-for: [riscv64]

plugs:
  mod-cache:
    interface: mount
    workshop-target: /home/workshop/go/pkg/mod

parts:
  go:
    plugin: dump
    source: https://go.dev/dl/go$CRAFT_PROJECT_VERSION.linux-$CRAFT_ARCH_BUILD_FOR.tar.gz
    source-type: tar
```

--------------------------------

### Define a multi-part SDK configuration

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/sdks/best-practices.md

Use multiple parts to separate runtime binaries from service configurations, enabling independent updates and faster build times.

```yaml
parts:
  ollama:
    plugin: dump
    source: https://github.com/ollama/ollama/releases/download/v0.9.6/ollama-linux-amd64.tgz
    source-type: tar
  user-service:
    plugin: dump
    source: ollama.service
    source-type: file
```

--------------------------------

### List available workshop actions

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/workshops/concepts.md

Command to display all actions currently defined for a specific workshop.

```console
$ workshop actions dev
```

--------------------------------

### Configure in-project SDK in workshop definition

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-3-sketch-sdks.md

Add the ejected SDK to the workshop definition file using the project- prefix.

```yaml
sdks:
  - name: project-console
```

--------------------------------

### Implement Desktop Interface in Go

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the desktop interface for accessing host Wayland compositors, including environment variable validation and proxy configuration.

```go
package builtin

import (
        "fmt"
        "path/filepath"
        "strings"

        "github.com/canonical/workshop/internal/dirs"
        "github.com/canonical/workshop/internal/interfaces"
        "github.com/canonical/workshop/internal/interfaces/lxd_device"
        "github.com/canonical/workshop/internal/sdk"
        "github.com/canonical/workshop/internal/systemd"
        "github.com/canonical/workshop/internal/workshop"
)

const desktopSummary = `allows SDKs to use the host's wayland compositor`

const desktopBaseDeclarationSlots = `
  desktop:
    allow-installation:
      slot-sdk-type:
        - system
      slot-names:
        - $INTERFACE
    allow-connection: true
    deny-auto-connection: true
`

const desktopDeclarationPlugs = `
  desktop:
    allow-installation:
      plug-sdk-type:
        - regular
      plug-names:
        - $INTERFACE
    allow-connection: true
    deny-auto-connection: true
`

type desktopInterface struct{}

func (iface *desktopInterface) Name() string {
        return "desktop"
}

func (iface *desktopInterface) StaticInfo() interfaces.StaticInfo {
        return interfaces.StaticInfo{
                Summary:              desktopSummary,
                BaseDeclarationPlugs: desktopDeclarationPlugs,
                BaseDeclarationSlots: desktopBaseDeclarationSlots,
                AffectsPlugOnRefresh: true,
        }
}

func (iface *desktopInterface) AutoConnect(plug *sdk.PlugInfo, slot *sdk.SlotInfo) bool {
        return true
}

func (iface *desktopInterface) MountConnectedPlug(spec *lxd_device.Specification, plug *interfaces.ConnectedPlug, slot *interfaces.ConnectedSlot) error {
        env, err := systemd.UserEnvironment(spec.User)
        if err != nil {
                return err
        }

        xdg := env["XDG_RUNTIME_DIR"]
        if xdg == "" {
                return fmt.Errorf("XDG_RUNTIME_DIR is either empty or unset for user %q", spec.User.Username)
        }

        desktop := workshop.Desktop{}

        wayland := env["WAYLAND_DISPLAY"]
        display := env["DISPLAY"]

        if wayland == "" && display == "" {
                return fmt.Errorf("neither DISPLAY nor WAYLAND_DISPLAY are set for user %q", spec.User.Username)
        }

        if wayland != "" {
                desktop.Wayland = &workshop.ProxyEntry{}
                desktop.Wayland.Name = plug.Sdk().Name + "-" + "wayland"
                desktop.Wayland.Connect = filepath.Join(xdg, wayland)
                desktop.Wayland.Listen = filepath.Join("/run/user/1000/", wayland)
        }
```

--------------------------------

### Create a new workshop SDK change

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes a state change object for SDK modifications, including user and project-id metadata.

```go
func newWorkshopSdkChange(st *state.State, kind string, user, projectId, action string, wp, sk string) *state.Change {
        sdkRef := sdk.Ref{ProjectId: projectId, Workshop: wp, Sdk: sk}
        summary := fmt.Sprintf(`%s %q SDK`, cases.Title(language.BritishEnglish).String(action), sdkRef.ShortRef())
        change := st.NewChange(kind, summary)
        change.Set("user", user)
        change.Set("project-id", projectId)
        return change
}
```

--------------------------------

### Define Plug, Slot, and Interface Structures

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Data models for representing connections between snaps, including references and interface metadata.

```go
// Plug represents the potential of a given snap to connect to a slot.
type Plug struct {
        ProjectId   string                 `json:"project-id"`
        Workshop    string                 `json:"workshop"`
        Sdk         string                 `json:"sdk"`
        Name        string                 `json:"plug"`
        Interface   string                 `json:"interface,omitempty"`
        Attrs       map[string]interface{} `json:"attrs,omitempty"`
        Label       string                 `json:"label,omitempty"`
        Bind        *PlugRef               `json:"bind,omitempty"`
        Connections []SlotRef              `json:"connections,omitempty"`
}

func (p *Plug) Ref() PlugRef {
        return PlugRef{ProjectId: p.ProjectId, Workshop: p.Workshop, Sdk: p.Sdk, Name: p.Name}
}

// PlugRef is a reference to a plug.
type PlugRef struct {
        ProjectId string `json:"project-id"`
        Workshop  string `json:"workshop"`
        Sdk       string `json:"sdk"`
        Name      string `json:"plug"`
}

// Slot represents a capacity offered by a snap.
type Slot struct {
        ProjectId   string                 `json:"project-id"`
        Workshop    string                 `json:"workshop"`
        Sdk         string                 `json:"sdk"`
        Name        string                 `json:"slot"`
        Interface   string                 `json:"interface,omitempty"`
        Attrs       map[string]interface{} `json:"attrs,omitempty"`
        Label       string                 `json:"label,omitempty"`
        Connections []PlugRef              `json:"connections,omitempty"`
}

// SlotRef is a reference to a slot.
type SlotRef struct {
        ProjectId string `json:"project-id"`
        Workshop  string `json:"workshop"`
        Sdk       string `json:"sdk"`
        Name      string `json:"slot"`
}

// Interface holds information about a given interface and its instances.
type Interface struct {
        Name    string `json:"name,omitempty"`
        Summary string `json:"summary,omitempty"`
        DocURL  string `json:"doc-url,omitempty"`
        Plugs   []Plug `json:"plugs,omitempty"`
        Slots   []Slot `json:"slots,omitempty"`
}
```

--------------------------------

### List Workshops in Current Project

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-list.rst

Lists all workshops in the current project directory. This is the default behavior when no flags are specified.

```console
$ workshop list
```

--------------------------------

### File Ownership Management

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Wrappers for changing file ownership using file descriptors or paths.

```go
func Chown(f *os.File, uid UserID, gid GroupID) error {
        return Fchown(int(f.Fd()), uid, gid)
}

func Fchown(fd int, uid UserID, gid GroupID) error {
        _, _, errno := syscall.Syscall(syscall.SYS_FCHOWN, uintptr(fd), uintptr(uid), uintptr(gid))
        if errno == 0 {
                return nil
        }
        return errno
}

func ChownPath(path string, uid UserID, gid GroupID) error {
        AT_FDCWD := -100 // also written as -0x64 in ztypes_linux_*.go (but -100 in sys_linux_*.s, and /usr/include/linux/fcntl.h)
        return FchownAt(uintptr(AT_FDCWD), path, uid, gid, 0)
}

func FchownAt(dirfd uintptr, path string, uid UserID, gid GroupID, flags int) error {
        p0, err := syscall.BytePtrFromString(path)
        if err != nil {
                return err
        }
        _, _, errno := syscall.Syscall6(_SYS_FCHOWNAT, dirfd, uintptr(unsafe.Pointer(p0)), uintptr(uid), uintptr(gid), uintptr(flags), 0)
        if errno == 0 {
                return nil
        }
        return errno
}
```

--------------------------------

### Retrieve User Project

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Extracts the project ID from the context.

```go
func (s *FakeWorkshopBackend) userProject(ctx context.Context) (string, string, error) {
        projectId, ok := ctx.Value(workshop.ContextProjectId).(string)
        if !ok {
                return "", "", fmt.Errorf("context key project-id not found")
        }
```

--------------------------------

### Manage ExecProcess Control Methods

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Provides methods for sending resize signals, process signals, and managing stdin synchronization.

```go
// SendResize sends a resize message to the running process.
func (p *ExecProcess) SendResize(width, height int) error {
        msg := api.InstanceExecControl{}
        msg.Command = "window-resize"
        msg.Args = make(map[string]string)
        msg.Args["width"] = strconv.Itoa(width)
        msg.Args["height"] = strconv.Itoa(height)
        return p.controlConn.WriteJSON(msg)
}

// SendSignal sends a signal to the running process.
func (p *ExecProcess) SendSignal(sig unix.Signal) error {
        msg := api.InstanceExecControl{}
        msg.Command = "signal"
        msg.Signal = int(sig)
        return p.controlConn.WriteJSON(msg)
}

// WaitStdinDone waits for WebsocketSendStream to be finished calling
// WriteMessage to avoid a race condition.
func (p *ExecProcess) WaitStdinDone() {
        <-p.stdinDone
}
```

--------------------------------

### Manage Download Reporters

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods to initialize, add, remove, and update progress reporters for download operations.

```go
func newImageDownloadOp() *downloadOp {
		return &downloadOp{waitCh: make(chan error), reporters: make(map[string]*progress.Reporter, 0)}
}

func (r *downloadOp) AddReporter(rep *progress.Reporter) {
		r.reportersLock.Lock()
		defer r.reportersLock.Unlock()

		r.reporters[rep.Name] = rep
}

func (r *downloadOp) RemoveReporter(name string) {
		r.reportersLock.Lock()
		defer r.reportersLock.Unlock()
		delete(r.reporters, name)
}

func (r *downloadOp) Update(upd downloadUpdate) {
		r.reportersLock.Lock()
		defer r.reportersLock.Unlock()

		for _, rep := range r.reporters {
			rep.Report(upd.Label, upd.Done, upd.Total)
		}
}
```

--------------------------------

### Define a complex workshop with slots, plugs, and connections

Source: https://github.com/canonical/workshop/blob/main/docs/reference/definition-files/workshop-definition.md

Advanced configuration using multiple SDKs with custom tunnel slots, plugs, and explicit connection mappings.

```yaml
name: notebook
base: ubuntu@24.04
sdks:
  - name: ollama
    channel: vulkan/stable
  - name: uv
    slots:
      api:
        interface: tunnel
        endpoint: 8000
  - name: jupyter
  - name: system
    plugs:
      jupyter:
        interface: tunnel
        endpoint: 127.0.0.1:8989
      app:
        interface: tunnel
        endpoint: 127.0.0.1:8090
      inference:
        interface: tunnel
        endpoint: 127.0.0.1:11434
connections:
  - plug: jupyter:venv
    slot: uv:venv
  - plug: system:app
    slot: uv:api
  - plug: system:inference
    slot: ollama:ollama-server
```

--------------------------------

### Generate ReST Documentation Tree

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Generates ReST documentation files for a command tree and creates an index.rst file using a template.

```go
func GenReSTTreeCustom(cmd *cobra.Command, dir string, filePrepender func(string) string, linkHandler func(string, string) string) error {
        var files []string

        // Recursive function to generate documentation for each command
        var generateDocs func(*cobra.Command) error
        generateDocs = func(c *cobra.Command) error {
                if !c.IsAvailableCommand() || c.IsAdditionalHelpTopicCommand() {
                        return nil
                }

                // Generate docs for subcommands
                for _, subCmd := range c.Commands() {
                        if err := generateDocs(subCmd); err != nil {
                                return err
                        }
                }

                // Generate RST file for the command
                basename := strings.ReplaceAll(c.CommandPath(), " ", "-") + ".rst"
                filename := filepath.Join(dir, basename)
                f, err := os.Create(filename)
                if err != nil {
                        return err
                }
                defer f.Close()

                if _, err := io.WriteString(f, filePrepender(filename)); err != nil {
                        return err
                }
                if err := GenReSTCustom(c, f, linkHandler); err != nil {
                        return err
                }

                // Track generated files for index
                files = append(files, basename)
                return nil
        }

        // Generate docs for subcommands only
        for _, subCmd := range cmd.Commands() {
                if err := generateDocs(subCmd); err != nil {
                        return err
                }
        }

        // Sort the RST files in alphabetical order
        sort.Strings(files)

        // Prepare data for the index template
        data := struct {
                Files []string
        }{
                Files: files,
        }

        // Read and parse the template
        templateContent, err := templates.ReadFile("cli.tmpl")
        if err != nil {
                return err
        }

        tmpl, err := template.New("index").Parse(string(templateContent))
        if err != nil {
                return err
        }

        // Create and write the workshop.rst file
        indexPath := filepath.Join(dir, "workshop.rst")
        indexFile, err := os.Create(indexPath)
        if err != nil {
                return err
        }
        defer indexFile.Close()

        if err := tmpl.Execute(indexFile, data);
        return nil
}
```

--------------------------------

### Define Interface and Action Structures

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Data structures for managing interface actions, options, and disconnect configurations.

```go
// InterfaceAction represents an action performed on the interface system.
type InterfaceAction struct {
        Action string `json:"action"`
        Forget bool   `json:"forget,omitempty"`
        Plugs  []Plug `json:"plugs,omitempty"`
        Slots  []Slot `json:"slots,omitempty"`
}

// InterfaceOptions represents opt-in elements include in responses.
type InterfaceOptions struct {
        Names     []string
        Doc       bool
        Plugs     bool
        Slots     bool
        Connected bool
}

// DisconnectOptions represents extra options for disconnect op
type DisconnectOptions struct {
        Forget bool
}
```

--------------------------------

### Configure bind mounts

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/sdks/sdk-vs-dockerfile.md

Shows complex bind mount configurations in Docker and the equivalent plug interface in Workshop.

```console
$ docker run -it \
  --name ros2_container \
  --mount type=bind,source=/home/user/ros-project,target=/home/ws/src,consistency=cached \
  --mount type=bind,source=/home/user/.ros,target=/root/.ros,consistency=cached \
  --mount type=bind,source=/tmp/.X11-unix,target=/tmp/.X11-unix,consistency=cached \
  --mount type=bind,source=/dev/dri,target=/dev/dri,consistency=cached \
  ros2
```

```yaml
plugs:
  ros-cache:
    interface: mount
    workshop-target: /home/workshop/.ros
# ...
```

```console
$ workshop launch ros2jazzy  # the plugs are mounted automatically
```

```console
$ workshop remount ros2jazzy/ros2:ros-cache ~/new-cache-mount/
```

--------------------------------

### Implement Okay Command

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the 'okay' command structure using Cobra to acknowledge warnings.

```go
func (c *CmdOkay) Command() *cobra.Command {
        var cmd = &cobra.Command{
                Use:   "okay",
                Args:  cobra.ExactArgs(0),
                Short: "Acknowledge listed warnings",
                Long: `
This command acknowledges all warnings
listed previously by the 'workshop warnings' command.
`,
                Example: `
Acknowledge the globally registered warnings across all workshops
(must run after 'workshop warnings'):
$ workshop okay`,
                RunE: c.Run,
        }

        return cmd
}
```

--------------------------------

### Implement Systemctl Command Wrapper

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Executes systemctl commands and provides a mechanism to override the command for testing purposes.

```go
// systemctlCmd calls systemctl with the given args, returning its standard output (and wrapped error)
var systemctlCmd = func(args ...string) ([]byte, error) {
        bs, err := exec.Command("systemctl", args...).CombinedOutput()
        if err != nil {
                exitCode, _ := osutil.ExitCode(err)
                return nil, &Error{cmd: args, exitCode: exitCode, msg: bs}
        }

        return bs, nil
}

// FakeSystemctl is called from the commands to actually call out to
// systemctl. It's exported so it can be overridden by testing.
func FakeSystemctl(f func(args ...string) ([]byte, error)) func() {
        oldSystemctlCmd := systemctlCmd
        systemctlCmd = f
        return func() {
                systemctlCmd = oldSystemctlCmd
        }
}
```

--------------------------------

### Connect Plug and Slot

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Validates compatibility between a plug and slot, performs policy checks, and establishes the connection in the repository.

```go
// Ensure that such plug exists
        plug := r.plugs[plugKey][plugName]
        if plug == nil {
                return nil, &NoPlugOrSlotError{
                        message: fmt.Sprintf("cannot connect plug %q: plug not found", ref.PlugRef.ShortRef())}
        }
        // Ensure that such slot exists
        slot := r.slots[slotKey][slotName]
        if slot == nil {
                return nil, &NoPlugOrSlotError{
                        message: fmt.Sprintf("cannot connect slot %q: slot not found", ref.SlotRef.ShortRef())}
        }
        // Ensure that plug and slot are compatible
        if slot.Interface != plug.Interface {
                return nil, fmt.Errorf(`cannot connect plug %q (%q interface) to %q (%q interface)`,
                        ref.PlugRef.ShortRef(), plug.Interface, ref.SlotRef.ShortRef(), slot.Interface)
        }

        iface, ok := r.ifaces[plug.Interface]
        if !ok {
                return nil, fmt.Errorf("internal error: unknown interface %q", plug.Interface)
        }

        cplug := NewConnectedPlug(plug, plugStaticAttrs, plugDynamicAttrs)
        cslot := NewConnectedSlot(slot, slotStaticAttrs, slotDynamicAttrs)

        // policyCheck is null when reloading connections
        if policyCheck != nil {
                if i, ok := iface.(plugValidator); ok {
                        if err := i.BeforeConnectPlug(cplug); err != nil {
                                return nil, fmt.Errorf("cannot connect plug %q: %w", ref.PlugRef.ShortRef(), err)
                        }
                }
                if i, ok := iface.(slotValidator); ok {
                        if err := i.BeforeConnectSlot(cslot); err != nil {
                                return nil, fmt.Errorf("cannot connect slot %q: %w", ref.SlotRef.ShortRef(), err)
                        }
                }

                // autoconnect policy checker returns false to indicate disallowed auto-connection, but it's not an error.
                ok, err := policyCheck(cplug, cslot)
                if !ok || err != nil {
                        return nil, err
                }
        }

        // Connect the plug
        if r.slotPlugs[slot] == nil {
                r.slotPlugs[slot] = make(map[*sdk.PlugInfo]*Connection)
        }
        if r.plugSlots[plug] == nil {
                r.plugSlots[plug] = make(map[*sdk.SlotInfo]*Connection)
        }

        conn := &Connection{Plug: cplug, Slot: cslot}
        r.slotPlugs[slot][plug] = conn
        r.plugSlots[plug][slot] = conn
        return conn, nil
}
```

--------------------------------

### Manage Change Readiness

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods to check and update the readiness state of a change based on its constituent tasks.

```go
// Ready returns a channel that is closed the first time the change becomes ready.
func (c *Change) Ready() <-chan struct{} {
        return c.ready
}
```

```go
// taskStatusChanged is called by tasks when their status is changed,
// to give the opportunity for the change to close its ready channel.
func (c *Change) taskStatusChanged(t *Task, old, new Status) {
        if old.Ready() == new.Ready() {
                return
        }
        for _, tid := range c.taskIDs {
                task := c.state.tasks[tid]
                if task != t && !task.status.Ready() {
                        return
                }
        }
        // Here is the exact moment when a change goes from unready to ready,
        // and from ready to unready. For now handle only the first of those.
        // For the latter the channel might be replaced in the future.
        if c.IsReady() && !c.Status().Ready() {
                panic(fmt.Errorf("change %s unexpectedly became unready (%s)", c.ID(), c.Status()))
        }
        c.markReady()
}
```

```go
// IsReady returns whether the change is considered ready.
//
// The result is similar to calling Ready on the status returned by the Status
// method, but this function is more efficient as it doesn't need to recompute
// the aggregated state of tasks on every call.
//
// As an exception, IsReady returns false for a Change without any tasks that
// never had its status explicitly set and was never unmarshalled out of the
// persistent state, despite its initial status being Hold. This is how the
// system represents changes right after they are created.
func (c *Change) IsReady() bool {
        select {
        case <-c.ready:
                return true
        default:
        }
        return false
}
```

--------------------------------

### Testing Utilities

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Functions for mocking the workshop backend and creating fake Overlord instances for test environments.

```go
func MockWorkshopBackend(b workshop.Backend) func() {
        workshopBackendOverride = b
        return func() {
                workshopBackendOverride = nil
        }
}

func Fake() *Overlord {
        return FakeWithState(nil)
}

func FakeWithState(handleRestart func(restart.RestartType)) *Overlord {
        o := &Overlord{
                loopTomb: new(tomb.Tomb),
                inited:   false,
        }
        s := state.New(fakeBackend{o: o})
        o.stateEng = NewStateEngine(s)
        o.runner = state.NewTaskRunner(s)
        return o
}
```

--------------------------------

### List and execute workshop actions

Source: https://github.com/canonical/workshop/blob/main/docs/contributing/development.md

Displays available actions and executes the linting process within the workshop.

```console
$ workshop actions dev
$ workshop run dev lint
```

--------------------------------

### Project Existence and Workshop Retrieval

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods to check if a project exists and to retrieve specific workshop files.

```go
func (p *Project) Exists() bool {
		exists, dir, _ := osutil.ExistsIsDir(p.Path)
		return exists && dir
}

func (w *Project) Workshop(workshop string) (*File, error) {
		path, err := w.maybeSingleWorkshop()
		if err != nil {
				return nil, err
		}
		if path != "" {
				file, err := readWorkshop(path)
				if err != nil {
						return nil, fmt.Errorf("invalid file %q: %w", path, err)
				}
				if file.Name != workshop {
						return nil, fmt.Errorf("workshop %q not found (only found %q)",
								workshop, file.Name)
				}
				return file, nil
		}

		path = Filepath(w.Path, workshop)
		file, err := readWorkshop(path)
		if err != nil {
				return nil, err
		}

		if file.Name != workshop {
				return nil, fmt.Errorf("%q workshop file must be named %q (now: %q)",
						file.Name, filename(file.Name), filepath.Base(path))
		}
		return file, nil
}

func (w *Project) ReadWorkshops() (map[string]string, error) {
		path, err := w.maybeSingleWorkshop()
		if err != nil {
				return nil, err
		}

		if path != "" {
				file, err := readWorkshop(path)
				if err != nil {
						return nil, fmt.Errorf("invalid file %q: %w", path, err)
				}
				return map[string]string{file.Name: path}, nil
		}
```

--------------------------------

### Interface Management Helpers

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Utility functions for generating keys and managing interface lifecycle within the repository.

```go
func plugOrSlotKey(projectId, workshop, sdkName string) string {
	return strings.Join([]string{projectId, workshop, sdkName}, "-")
}

// Interface returns an interface with a given name.
func (r *Repository) Interface(interfaceName string) Interface {
	r.m.Lock()
	defer r.m.Unlock()

	return r.ifaces[interfaceName]
}

// AddInterface adds the provided interface to the repository.
func (r *Repository) AddInterface(i Interface) error {
	r.m.Lock()
	defer r.m.Unlock()

	interfaceName := i.Name()
	if err := sdk.ValidateInterfaceName(interfaceName); err != nil {
		return err
	}
	if _, ok := r.ifaces[interfaceName]; ok {
		return fmt.Errorf("cannot add interface: %q, interface name is in use", interfaceName)
	}
	r.ifaces[interfaceName] = i

	return nil
}

// AllInterfaces returns all the interfaces added to the repository, ordered by name.
func (r *Repository) AllInterfaces() []Interface {
	r.m.Lock()
	defer r.m.Unlock()

	ifaces := make([]Interface, 0, len(r.ifaces))
	for _, iface := range r.ifaces {
		ifaces = append(ifaces, iface)
	}
	sort.Sort(byInterfaceName(ifaces))
	return ifaces
}
```

--------------------------------

### Initialize CommandManager

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Creates a new CommandManager instance and registers task handlers and cleanup routines.

```go
// New creates a new CommandManager.
func New(st *state.State, runner *state.TaskRunner) *CommandManager {
        manager := &CommandManager{
                executions:     make(map[string]*execution),
                executionsCond: sync.NewCond(&sync.Mutex{}),
        }
        st.Lock()
        manager.backend = workshop.WorkshopBackend(st)
        st.Unlock()

        runner.AddHandler("exec", manager.doExec, nil)
        runner.AddHandler("install-script", manager.doInstallScript, nil)

        // Delete in-memory ExecArgs objects when the tasks are done.
        runner.AddCleanup("exec", deleteExecArgs)
        runner.AddCleanup("install-script", deleteExecArgs)

        return manager
}

func deleteExecArgs(task *state.Task, tomb *tomb.Tomb) error {
        st := task.State()
        st.Lock()
        defer st.Unlock()
        st.Cache(ExecArgsKey(task.ID()), nil)
        return nil
}

type ExecArgsKey string

// Ensure is part of the overlord.StateManager interface.
func (m *CommandManager) Ensure() error {
        return nil
}
```

--------------------------------

### Create a design worktree

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/use-workshops-with-ai-agents.md

Initializes a new git worktree for design-related tasks.

```console
$ git worktree add design
```

--------------------------------

### Retrieve All Plugs

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Returns all plugs for a given interface, or all plugs if the interface name is empty.

```go
// AllPlugs returns all plugs of the given interface.
// If interfaceName is the empty string, all plugs are returned.
func (r *Repository) AllPlugs(interfaceName string) []*sdk.PlugInfo {
	r.m.Lock()
	defer r.m.Unlock()
```

--------------------------------

### FakeStore Implementation for Testing

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Provides a mock implementation of the Store interface for unit testing.

```go
func NewFakeStore() Store {
        return &FakeStore{
                ActionCalls: make([]TestActionCall, 0),
        }
}

type TestActionCall struct {
        Actions []SdkAction
}

type TestDownloadCall struct {
        Setup Setup
}

type FakeStore struct {
        ActionCalls []TestActionCall

        downloadLock  sync.Mutex
        DownloadCalls []TestDownloadCall

        ActionCallback   func(ctx context.Context, actions []SdkAction) ([]SdkResult, error)
        DownloadCallback func(ctx context.Context, setup Setup, report *progress.Reporter) error
}

func (f *FakeStore) SetActionCallback(fa func(ctx context.Context, actions []SdkAction) ([]SdkResult, error)) func() {
        old := f.ActionCallback
        f.ActionCallback = fa
        return func() {
                f.ActionCallback = old
        }
}

func (f *FakeStore) SetDownloadCallback(fa func(ctx context.Context, setup Setup, report *progress.Reporter) error) func() {
        old := f.DownloadCallback
        f.DownloadCallback = fa
        return func() {
                f.DownloadCallback = old
        }
}

func (f *FakeStore) SdkAction(ctx context.Context, actions []SdkAction) ([]SdkResult, error) {
        f.ActionCalls = append(f.ActionCalls, TestActionCall{
                Actions: actions,
        })
        if f.ActionCallback != nil {
                return f.ActionCallback(ctx, actions)
        }
        return nil, nil
}

func (f *FakeStore) DownloadSdk(ctx context.Context, setup Setup, report *progress.Reporter) error {
        f.downloadLock.Lock()
        defer f.downloadLock.Unlock()
        f.DownloadCalls = append(f.DownloadCalls, TestDownloadCall{
                Setup: setup,
        })
        if f.DownloadCallback != nil {
                return f.DownloadCallback(ctx, setup, report)
        }
        return nil
}
```

--------------------------------

### Workshop sketch-sdk usage

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Syntax for customizing a workshop using the sketch SDK.

```console
$ workshop sketch-sdk [--stash|--restore|--eject|--remove] [<WORKSHOP>] [flags]
```

--------------------------------

### Ship binary artifacts as parts

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/sdks/best-practices.md

Use this configuration to pin specific versions or distribute custom builds that are not available in system repositories.

```yaml
parts:
  uv:
    plugin: rust
    source: https://github.com/astral-sh/uv
    source-tag: $CRAFT_PROJECT_VERSION
    source-type: git
    organize:
      uv: bin/uv
      uvx: bin/uvx
    prime:
      - bin/uv
      - bin/uvx
```

--------------------------------

### Update Xauthority

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Determines user environment and migrates Xauthority files.

```go
func updateXauthority(user string) error {
        usr, err := workshop.LookupUsername(user)
        if err != nil {
                return err
        }

        env, err := systemd.UserEnvironment(usr)
        if err != nil {
                return err
        }

        if err = x11.MigrateXauthority(usr, env["XAUTHORITY"]); err != nil {
                return err
        }

        return nil
}
```

--------------------------------

### OS Utility helper functions

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

A collection of system-level utilities for checking file attributes, executable availability, and path accessibility.

```go
// FileExists returns true if stat succeeds on the given path.
// It may return false on permission issues.
func FileExists(path string) bool {
        _, err := os.Stat(path)
        return err == nil
}
```

```go
// IsDir returns true if the given path is a directory.
// It may return false on permission issues.
func IsDir(path string) bool {
        fileInfo, err := os.Stat(path)
        if err != nil {
                return false
        }
        return fileInfo.IsDir()
}
```

```go
// IsDevice returns true if mode coresponds to a device (char/block).
func IsDevice(mode os.FileMode) bool {
        return (mode & (os.ModeDevice | os.ModeCharDevice)) != 0
}
```

```go
// IsSymlink returns true if path is a symlink.
func IsSymlink(path string) bool {
        fileInfo, err := os.Lstat(path)
        if err != nil {
                return false
        }

        return (fileInfo.Mode() & os.ModeSymlink) != 0
}
```

```go
// IsExec returns true if path points to an executable file.
func IsExec(path string) bool {
        stat, err := os.Stat(path)
        if err != nil {
                return false
        }
        return !stat.IsDir() && (stat.Mode().Perm()&0111 != 0)
}
```

```go
// IsExecInPath returns true if name is an executable in $PATH.
func IsExecInPath(name string) bool {
        _, err := exec.LookPath(name)
        return err == nil
}
```

```go
var lookPath func(name string) (string, error) = exec.LookPath

// LookPathDefault searches for a given command name in all directories
// listed in the environment variable PATH and returns the found path or the
// provided default path.
func LookPathDefault(name string, defaultPath string) string {
        p, err := lookPath(name)
        if err != nil {
                return defaultPath
        }
        return p
}
```

```go
// IsWritable checks if the given file/directory can be written by
// the current user
func IsWritable(path string) bool {
        // from "fcntl.h"
        const W_OK = 2

        err := syscall.Access(path, W_OK)
        return err == nil
}
```

```go
// IsDirNotExist tells you whether the given error is due to a directory not existing.
func IsDirNotExist(err error) bool {
        switch pe := err.(type) {
        case nil:
                return false
        case *os.PathError:
                err = pe.Err
        case *os.LinkError:
                err = pe.Err
        case *os.SyscallError:
                err = pe.Err
        }

        return err == syscall.ENOTDIR || err == syscall.ENOENT || err == os.ErrNotExist
}
```

--------------------------------

### Initialize Workshop Context

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Creates a new context for workshop callbacks, generating a random ID if one is not provided.

```go
// NewContext returns a new context associated with the provided task or
// an ephemeral context if task is nil.
//
// A random ID is generated if contextID is empty.
func NewContext(task *state.Task, state *state.State, setup *HookSetup, handler Handler, contextID string) (*Context, error) {
        if contextID == "" {
                var err error
                contextID, err = randutil.CryptoToken(32)
                if err != nil {
                        return nil, err
                }
        }
```

--------------------------------

### Verify workshop connections

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/manage-python-environments.md

Use the workshop connections command to confirm that the environment wiring is correctly established.

```console
$ workshop connections --all

  INTERFACE  PLUG                SLOT                NOTES
  mount      pyenv/jupyter:venv  pyenv/uv:venv       -
  mount      pyenv/uv:cache      pyenv/system:mount  -
```

--------------------------------

### Initialize State

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Creates a new empty state instance with initialized maps and default flags.

```go
// New returns a new empty state.
func New(backend Backend) *State {
        return &State{
                backend:             backend,
                data:                make(customData),
                changes:             make(map[string]*Change),
                tasks:               make(map[string]*Task),
                warnings:            make(map[string]*Warning),
                modified:            true,
                cache:               make(map[interface{}]interface{}),
                pendingChangeByAttr: make(map[string]func(*Change) bool),
        }
}
```

--------------------------------

### List workshop connections

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Commands to list interface connections for a specific workshop or the entire project.

```console
$ workshop connections [<WORKSHOP>] [flags]
```

```console
$ workshop connections nimble
```

```console
$ workshop connections
```

--------------------------------

### Task Management Methods

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Methods for creating, retrieving, and counting tasks linked to changes.

```go
// NewTask creates a new task.
// It usually will be registered with a Change using AddTask or
// through a TaskSet.
func (s *State) NewTask(kind, summary string) *Task {
        s.writing()
        s.lastTaskId++
        id := strconv.Itoa(s.lastTaskId)
        t := newTask(s, id, kind, summary)
        s.tasks[id] = t
        return t
}

// Tasks returns all tasks currently known to the state and linked to changes.
func (s *State) Tasks() []*Task {
        s.reading()
        res := make([]*Task, 0, len(s.tasks))
        for _, t := range s.tasks {
                if t.Change() == nil { // skip unlinked tasks
                        continue
                }
                res = append(res, t)
        }
        return res
}

// Task returns the task for the given ID if the task has been linked to a change.
func (s *State) Task(id string) *Task {
        s.reading()
        t := s.tasks[id]
        if t == nil || t.Change() == nil {
                return nil
        }
        return t
}

// TaskCount returns the number of tasks that currently exist in the state,
// whether linked to a change or not.
func (s *State) TaskCount() int {
        s.reading()
        return len(s.tasks)
}

func (s *State) tasksIn(tids []string) []*Task {
        res := make([]*Task, len(tids))
        for i, tid := range tids {
                res[i] = s.tasks[tid]
        }
        return res
}
```

--------------------------------

### Define SDK platforms by architecture

Source: https://github.com/canonical/workshop/blob/main/docs/reference/sdks.md

Use this format to define platforms based on CPU architecture with a shared base image.

```yaml
# ...
base: ubuntu@24.04
platforms:
  amd64:
  arm64:
```

--------------------------------

### Define SDK Info and Reference Structures

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

The Info struct holds core SDK metadata, while the Ref struct provides methods for generating string representations of SDK identifiers.

```go
type Info struct {
        ProjectId string
        Workshop  string
        Name      string
        Base      string
        Version   string
        Type      Type
        Revision  Revision
        Channel   string
        BuildTime *time.Time

        Plugs     map[string]*PlugInfo
        PlugBinds map[string]*PlugBind
        Slots     map[string]*SlotInfo
        // Plugs or slots with issues (they are not included in Plugs or Slots)
        BadInterfaces map[string]string
}

func (i *Info) Ref() Ref {
        return Ref{
                ProjectId: i.ProjectId,
                Workshop:  i.Workshop,
                Sdk:       i.Name,
        }
}

type Ref struct {
        ProjectId string
        Workshop  string
        Sdk       string
}

func (r Ref) String() string {
        return fmt.Sprintf("%s/%s/%s", r.ProjectId, r.Workshop, r.Sdk)
}

func (r Ref) ShortRef() string {
        return fmt.Sprintf("%s/%s", r.Workshop, r.Sdk)
}
```

--------------------------------

### Define SDK Profile Structures

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Data structures representing the configuration of an SDK profile, including desktop environment, GPU, and mount settings.

```go
type Desktop struct {
        Wayland *ProxyEntry
        X11     *ProxyEntry
}

type Gpu struct {
        Name string
}

type SdkProfile struct {
        Sdk string

        Camera  *Camera
        Mounts  map[string]Mount
        Agent   *SshAgent
        Gpu     *Gpu
        Desktop *Desktop
}

func NewSdkProfile(sdkName string) SdkProfile {
        return SdkProfile{
                Sdk:    sdkName,
                Mounts: make(map[string]Mount),
        }
}
```

--------------------------------

### Convert LXD Profile to SDK Profile

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Maps LXD device configurations and metadata into a structured workshop SDK profile.

```go
        return lxdToSdkProfile(profile, lxdp.Devices, lxdp.Config)
}

func lxdToSdkProfile(profile string, devs map[string]map[string]string, config map[string]string) (workshop.SdkProfile, error) {
        var pr = workshop.NewSdkProfile(profile)
        for name, dev := range devs {
                switch dev["type"] {
                case "disk":
                        pr.Mounts[name] = workshop.Mount{Name: name, What: dev["source"], Where: dev["path"], Type: workshop.HostWorkshop}
                case "gpu":
                        pr.Gpu = &workshop.Gpu{Name: name}
                case "proxy":
                        devtype := config[DeviceTypeConfigKey(profile, name)]
                        switch devtype {
                        case "ssh-agent":
                                pr.Agent = &workshop.SshAgent{ProxyEntry: workshop.ProxyEntry{Name: name, Connect: dev["connect"], Listen: dev["listen"]}}
                        case "desktop-wayland":
                                if pr.Desktop == nil {
                                        pr.Desktop = &workshop.Desktop{}
                                }
                                pr.Desktop.Wayland = &workshop.ProxyEntry{Name: name, Connect: dev["connect"], Listen: dev["listen"]}
                        case "desktop-x11":
                                if pr.Desktop == nil {
                                        pr.Desktop = &workshop.Desktop{}
                                }
                                pr.Desktop.X11 = &workshop.ProxyEntry{Name: name, Connect: dev["connect"], Listen: dev["listen"]}
                        default:
                                logger.Noticef("On reading %q SDK profile: unknown device type: %q", profile, devtype)
                        }
                case "unix-char":
                        devtype := config[DeviceTypeConfigKey(profile, name)]
                        if devtype == "camera" {
                                continue
                        }

                        logger.Noticef("On reading %q SDK profile: unknown device type %q", profile, devtype)
                case "none":
                        cfg, exist := config[DeviceConfigKey(profile, name)]
                        if !exist {
                                logger.Noticef("On reading %q SDK profile: unknown device %q", profile, name)
                                continue
                        }

                        devtype := config[DeviceTypeConfigKey(profile, name)]
                        switch devtype {
                        case "camera":
                                var camera workshop.Camera
                                if err := json.Unmarshal([]byte(cfg), &camera); err != nil {
                                        return pr, err
                                }
                                pr.Camera = &camera
                        case "mount":
                                var mnt workshop.Mount
                                if err := json.Unmarshal([]byte(cfg), &mnt); err != nil {
                                        return pr, err
                                }
                                pr.Mounts[name] = mnt
                        default:
                                logger.Noticef("On reading %q SDK profile: unknown device type %q", profile, devtype)
                        }
                default:
                        logger.Noticef("On reading %q SDK profile: unknown device type %q", profile, dev["type"])
                }
        }
        return pr, nil
}
```

--------------------------------

### Create a new connection change

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes a state change object for connection actions, including user and project metadata.

```go
func newConnectionChange(st *state.State, user string, tasks []*state.TaskSet, reqData *interfaceAction) *state.Change {
        summary := fmt.Sprintf("%s %s", cases.Title(language.BritishEnglish).String(reqData.Action),
                fmt.Sprintf("%s/%s:%s", reqData.Plugs[0].Workshop, reqData.Plugs[0].Sdk, reqData.Plugs[0].Name))

        change := st.NewChange(reqData.Action, summary)
        change.Set("user", user)
        change.Set("project-id", reqData.Plugs[0].ProjectId)
        for _, ts := range tasks {
                change.AddAll(ts)
        }
        return change
}
```

--------------------------------

### Retrieve Project Filesystem Root

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Queries running instances using findmnt to determine the filesystem root for a specific project ID.

```go
func (s *Backend) projectFsRoot(conn lxd.InstanceServer, ctx context.Context, projectId string) (path string, err error) {
        workshops, err := s.filterLxdInstancesByConfig(conn, workshop.NewWorkshopConfigFilter(workshop.ConfigProjectId, projectId))
        if err != nil {
                return "", err
        }

        for _, i := range workshops {
                // attempt to execute the command only in a running instance
                if i.StatusCode != api.Ready && i.StatusCode != api.Running {
                        continue
                }

                var outbuf bytes.Buffer
                var errbuf strings.Builder

                /* Get the mount point directory from findmnt */
                args := workshop.Execution{
                        ExecArgs: workshop.ExecArgs{
                                UserId:  0,
                                GroupId: 0,
                                Command: []string{"findmnt", "--json", "--mountpoint", "/project", "--output", "fsroot"},
                                WorkDir: "/",
                        },
                        ExecControls: workshop.ExecControls{
                                Stdin:  nil,
                                Stdout: &outbuf,
                                Stderr: &errbuf,
                        },
                }

                execCtx := context.WithValue(ctx, workshop.ContextProjectId, projectId)
                meta, err := s.execCommand(conn, execCtx, workshop.WorkshopName(i.Name), &args)
                if err != nil {
                        logger.Debugf("cannot check %q bind-mounts: %v", i.Name, err)
                        continue
                }
                if err = meta.WaitExecution(ctx); err != nil {
                        logger.Debugf("cannot check %q bind-mounts: %v, findmnt output: %s", i.Name, err, errbuf.String())
                        continue
                }
```

--------------------------------

### Reference an in-project SDK in the workshop

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/use-host-devices.md

Include the in-project SDK in the workshop definition using the project- prefix.

```yaml
name: dev
base: ubuntu@24.04
sdks:
  - name: project-input-sdk
```

--------------------------------

### Create a faked command

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initializes a fake command that logs invocations to a file and optionally adds it to the PATH.

```go
func FakeCommand(c *check.C, basename, script string) *FakeCmd {
        var wholeScript bytes.Buffer
        var binDir, exeFile, logFile string
        if filepath.IsAbs(basename) {
                binDir = filepath.Dir(basename)
                exeFile = basename
                logFile = basename + ".log"
        } else {
                binDir = c.MkDir()
                exeFile = path.Join(binDir, basename)
                logFile = path.Join(binDir, basename+".log")
                os.Setenv("PATH", binDir+":"+os.Getenv("PATH"))
        }
        fmt.Fprintf(&wholeScript, scriptTpl, logFile, script)
        err := os.WriteFile(exeFile, wholeScript.Bytes(), 0700)
        if err != nil {
                panic(err)
        }

        maybeShellcheck(c, script, &wholeScript)

        return &FakeCmd{binDir: binDir, exeFile: exeFile, logFile: logFile}
}
```

--------------------------------

### Define workshop environment

Source: https://github.com/canonical/workshop/blob/main/docs/doc-style-guide.md

Use this format to define the workshop container environment.

```default
A workshop is a development environment running in a container.
```

--------------------------------

### Configure SDK Plugs and Slots

Source: https://github.com/canonical/workshop/blob/main/docs/tutorial/part-4-craft-sdks.md

Define the required interfaces for GPU access, model persistence, and API tunneling in the sdkcraft.yaml file.

```yaml
name: ollama
version: "0.9.6"
summary: Get up and running with large language models
description: |
  Get up and running with Llama 3.3, DeepSeek-R1, Phi-4,
  Gemma 3, Mistral Small 3.1 and other large language models.
license: MIT
platforms:
  ubuntu@22.04:amd64:
  ubuntu@24.04:amd64:

plugs:
  gpu:
    interface: gpu
  models:
    interface: mount
    workshop-target: /home/workshop/.ollama/models

slots:
  ollama-server:
    interface: tunnel
    endpoint: 11434

# ...
```

--------------------------------

### Mocking Backup Utility

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Backs up values of pointers before mocking and provides a restoration function.

```go
// Backup the specified list of elements before further mocking.
func Backup(mockablesByPtr ...interface{}) (restore func()) {
        backup := backupMockables(mockablesByPtr)

        return func() {
                for i, ptr := range mockablesByPtr {
                        mockedPtr := reflect.ValueOf(ptr)
                        mockedPtr.Elem().Set(backup[i].Elem())
                }
        }
}

func backupMockables(mockablesByPtr []interface{}) (backup []*reflect.Value) {
        backup = make([]*reflect.Value, len(mockablesByPtr))

        for i, ptr := range mockablesByPtr {
                mockedPtr := reflect.ValueOf(ptr)

                if mockedPtr.Type().Kind() != reflect.Ptr {
                        panic("Backup: each mockable must be passed by pointer!")
                }

                saved := reflect.New(mockedPtr.Elem().Type())
                saved.Elem().Set(mockedPtr.Elem())
                backup[i] = &saved
        }
        return backup
}
```

--------------------------------

### Connect and disconnect the desktop interface

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/interfaces/desktop-interface.md

Manually manage the connection between the workshop and the host display interface.

```console
$ workshop connect ws/desktop-sdk:desktop
$ workshop disconnect ws/desktop-sdk:desktop
```

--------------------------------

### Base Test Suite Structure

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Provides a base test suite with cleanup handler support for gopkg.in/check.v1 tests.

```go
// BaseTest is a structure used as a base test suite for many of the workshop
// tests.
type BaseTest struct {
        cleanupHandlers []func()
}

// SetUpTest prepares the cleanup
func (s *BaseTest) SetUpTest(c *check.C) {
        s.cleanupHandlers = nil
}

// TearDownTest cleans up the channel.ini files in case they were changed by
// the test.
// It also runs the cleanup handlers
func (s *BaseTest) TearDownTest(c *check.C) {
        // run cleanup handlers and clear the slice
        for _, f := range s.cleanupHandlers {
                f()
        }
        s.cleanupHandlers = nil
}

// AddCleanup adds a new cleanup function to the test
func (s *BaseTest) AddCleanup(f func()) {
        s.cleanupHandlers = append(s.cleanupHandlers, f)
}
```

--------------------------------

### Retrieve and display workshop data

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Fetches workshop information and prints it using a tabwriter.

```go
func (c *CmdList) runList() error {
        cli, err := c.root.client()
        if err != nil {
                return err
        }

        w := tabWriter()
        var header sync.Once
        printHeader := func() {
                fmt.Fprintf(w, "Project\tWorkshop\tStatus\tNotes\n")
        }

        if !c.global {
                project, err := cli.Project(c.root.project)
                if err != nil {
                        return err
                }

                workshops, files, err := cli.List(&client.ListOptions{ProjectId: project.Id})
                if err != nil {
                        return err
                }

                /* List all workshops for the current project */
                if len(workshops) != 0 || len(files) != 0 {
                        header.Do(printHeader)
                        print(w, workshops, files, *project)
                }
        } else {
                projects, err := cli.Projects()
                if err != nil {
                        return err
                }

                for _, p := range projects {
                        workshops, _, err := cli.List(&client.ListOptions{ProjectId: p.Id})
                        if err != nil {
                                return err
                        }
                        header.Do(printHeader)
                        // --global flag does not list files for consistency. We may not be
                        // aware of all the project directories on the system and, thus,
                        // will not know all the available "Off" workshops (contrary to the
                        // workshops that are in any other state, i.e. running instances,
                        // which we always know about from the workshop backend).
                        print(w, workshops, nil, p)
                }
        }

        w.Flush()

        return nil
}
```

--------------------------------

### Add Plug to Repository

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Registers a new plug in the repository, ensuring the name is valid and unique within the SDK.

```go
func (r *Repository) AddPlug(plug *sdk.PlugInfo) error {
        r.m.Lock()
        defer r.m.Unlock()

        key := plugOrSlotKey(plug.Sdk.ProjectId, plug.Sdk.Workshop, plug.Sdk.Name)

        // Reject plugs with invalid names
        if err := sdk.ValidatePlugName(plug.Name); err != nil {
                return err
        }
        i := r.ifaces[plug.Interface]
        if i == nil {
                return fmt.Errorf("cannot add plug, interface %q is not known", plug.Interface)
        }
        if _, ok := r.plugs[key][plug.Name]; ok {
                return fmt.Errorf("sdk %q has plugs conflicting on name %q", plug.Sdk.Name, plug.Name)
        }
        if _, ok := r.slots[key][plug.Name]; ok {
                return fmt.Errorf("sdk %q has plug and slot conflicting on name %q", plug.Sdk.Name, plug.Name)
        }
        if r.plugs[key] == nil {
                r.plugs[key] = make(map[string]*sdk.PlugInfo)
        }
        r.plugs[key][plug.Name] = plug
        return nil
}
```

--------------------------------

### Define Naming Conventions

Source: https://github.com/canonical/workshop/blob/main/docs/reference/definition-files/sdkcraft-definition.md

Schema patterns and constraints for naming projects, plugs, and slots.

```json
"PlugName": {
      "description": "The name of the plug. This is used when connecting and disconnecting.\n\nThe plug name must consist only of lower-case ASCII letters (``a-z``), numerals\n(``0-9``), and hyphens (``-``). It must start with a letter, not end with a\nhyphen, and not contain two consecutive hyphens.\n",
      "examples": [
        "desktop",
        "gpu",
        "ssh-agent"
      ],
      "pattern": "^[a-z](-?[a-z0-9])*$",
      "title": "Plug Name",
      "type": "string"
    }
```

```json
"ProjectName": {
      "description": "The name of the project. This is used when uploading, publishing, or installing.\n\nThe project name must consist only of lower-case ASCII letters (``a``-``z``), numerals\n(``0``-``9``), and hyphens (``-``). It must contain at least one letter, not start or\nend with a hyphen, and not contain two consecutive hyphens. The maximum length is 40\ncharacters.\n",
      "examples": [
        "ubuntu",
        "jupyterlab-desktop",
        "lxd",
        "digikam",
        "kafka",
        "mysql-router-k8s"
      ],
      "maxLength": 40,
      "minLength": 1,
      "pattern": "(?!^(system|try-.*|project-.*|sketch)$)^([a-z0-9][a-z0-9-]?)*[a-z]+([a-z0-9-]?[a-z0-9])*$",
      "title": "Project Name",
      "type": "string"
    }
```

```json
"SlotName": {
      "description": "The name of the slot. This is used when connecting and disconnecting.\n\nThe slot name must consist only of lower-case ASCII letters (``a-z``), numerals\n(``0-9``), and hyphens (``-``). It must start with a letter, not end with a\nhyphen, and not contain two consecutive hyphens.\n",
      "examples": [
        "dashboard",
        "gdb",
        "toolchain"
      ],
      "pattern": "^[a-z](-?[a-z0-9])*$",
      "title": "Slot Name",
      "type": "string"
    }
```

--------------------------------

### Manage Mount Profiles in Go

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Functions for loading, saving, and parsing fstab-formatted mount profiles.

```go
// LoadMountProfileText loads a mount profile from a given string.
func LoadMountProfileText(fstab string) (*MountProfile, error) {
        return ReadMountProfile(strings.NewReader(fstab))
}

func SaveMountProfileText(p *MountProfile) (string, error) {
        var buf bytes.Buffer
        _, err := p.WriteTo(&buf)
        if err != nil {
                return "", err
        }
        return buf.String(), nil
}

// Save saves a mount profile (fstab-like) to a given file.
// The profile is saved with an atomic write+rename+sync operation.
func (p *MountProfile) Save(fname string) error {
        var buf bytes.Buffer
        if _, err := p.WriteTo(&buf); err != nil {
                return err
        }
        return AtomicWriteFile(fname, buf.Bytes(), 0644, AtomicWriteFlags(0))
}

// ReadMountProfile reads and parses a mount profile.
//
// The supported format is described by fstab(5).
func ReadMountProfile(reader io.Reader) (*MountProfile, error) {
        var p MountProfile
        scanner := bufio.NewScanner(reader)
        for scanner.Scan() {
                s := scanner.Text()
                s = strings.TrimSpace(s)
                // Skip lines that only contain a comment, that is, those that start
                // with the '#' character (ignoring leading spaces). This specifically
                // allows us to parse '#' inside individual fields, which the fstab(5)
                // specification allows.
                if strings.IndexByte(s, '#') == 0 {
                        continue
                }
                // Skip lines that are totally empty
                if s == "" {
                        continue
                }
                entry, err := ParseMountEntry(s)
                if err != nil {
                        return nil, err
                }
                p.Entries = append(p.Entries, entry)
        }
        if err := scanner.Err(); err != nil {
                return nil, err
        }
        return &p, nil
}

// WriteTo writes a mount profile to the given writer.
//
// The supported format is described by fstab(5).
// Note that there is no support for comments.
func (p *MountProfile) WriteTo(writer io.Writer) (int64, error) {
        var written int64
        for i := range p.Entries {
                var n int
                var err error
                if n, err = fmt.Fprintf(writer, "%s\n", p.Entries[i]); err != nil {
                        return written, err
                }
                written += int64(n)
        }
        return written, nil
}
```

--------------------------------

### Client Package Imports

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Required imports for the client package.

```go
import (
        "bytes"
        "encoding/json"
        "net/url"
)
```

--------------------------------

### Verify plug connections

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/fix-workshops/resolve-plug-conflicts.md

Check the status of plug bindings to confirm they share the same mount point.

```console
$ workshop connections digits

  INTERFACE  PLUG                    SLOT                 NOTES
  mount      digits/torchaudio:hub   digits/system:mount  bind.1
  mount      digits/torchvision:hub  digits/system:mount  bind.1
```

--------------------------------

### Define Run Command

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Configures the 'run' command for executing scripts within a workshop.

```go
func (c *CmdRun) Command() *cobra.Command {
        var cmd = &cobra.Command{
                Use:   "run [flags] [<WORKSHOP>] [--] <SCRIPT> <ARGUMENTS>...",
                Args:  maybeNameAndScript,
                Short: shortRunHelp,
                Long:  longRunHelp,
                Example: `
Run the 'build' script under the 'nimble' workshop
in the current project directory:
$ workshop run nimble build

A similar command that sets an environment variable and the working directory:
$ workshop run --env GO111MODULE=off -w /project nimble build

The workshop name is optional if the project only has one workshop:
$ workshop run build`,
                RunE: c.Run,
        }

        return cmd
}
```

--------------------------------

### Create a new release track

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/publish-an-sdk.md

Creates a new track for an SDK, provided the track name matches an existing store-side guardrail.

```console
$ sdkcraft create-track <NAME> --track 1.x
```

--------------------------------

### Builtin Package Imports

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Initial imports for the builtin package.

```go
package builtin

import (
        "fmt"
        "sort"

```

--------------------------------

### Retrieve Connection References

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Iterates through plugs and slots to generate and return a list of connection references.

```go
var conns []*ConnRef
	for _, plugInfo := range r.plugs[key] {
		for slotInfo := range r.plugSlots[plugInfo] {
			connRef := NewConnRef(plugInfo, slotInfo)
			conns = append(conns, connRef)
		}
	}
	for _, slotInfo := range r.slots[key] {
		for plugInfo := range r.slotPlugs[slotInfo] {
			// self-connection, ignore here as we got it already in the plugs loop above
			if plugInfo.Sdk == slotInfo.Sdk {
				continue
			}
			connRef := NewConnRef(plugInfo, slotInfo)
			conns = append(conns, connRef)
		}
	}

	return conns, nil
}
```

--------------------------------

### Define Workshop Data Models

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Core data structures for workshop configuration, mounts, and proxy entries.

```go
package workshop

type MountType int

const (
        HostWorkshop MountType = iota
        WorkshopWorkshop
        Volume
)

type ProxyEntry struct {
        Name    string
        Connect string
        Listen  string
}

type Camera struct {
        Name string `json:"name"`
}

type Mount struct {
        Name  string    `json:"name"`
        What  string    `json:"what"`
        Where string    `json:"where"`
        Type  MountType `json:"type"`
}

type SshAgent struct {
        ProxyEntry
}
```

--------------------------------

### Verify workshop connections

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/use-host-devices.md

Lists all connections to confirm the plug is correctly wired to the slot.

```console
$ workshop connections --all
```

--------------------------------

### Raw Request Execution

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Performs a raw HTTP request using the client configuration.

```go
// raw performs a request and returns the resulting http.Response and
// error you usually only need to call this directly if you expect the
// response to not be JSON, otherwise you'd call Do(...) instead.
func (client *Client) raw(ctx context.Context, method, urlpath string, query url.Values, headers map[string]string, body io.Reader) (*http.Response, error) {
	// fake a url to keep http.Client happy
	u := client.baseURL
	u.Path = path.Join(client.baseURL.Path, urlpath)
	u.RawQuery = query.Encode()
	req, err := http.NewRequestWithContext(ctx, method, u.String(), body)
	if err != nil {
		return nil, RequestError{err}
	}
	if client.userAgent != "" {
		req.Header.Set("User-Agent", client.userAgent)
	}

	for key, value := range headers {
		req.Header.Set(key, value)
	}

	rsp, err := client.doer.Do(req)
	if err != nil {
		return nil, ConnectionError{err}
	}

	return rsp, nil
}

var (
	doRetry   = 250 * time.Millisecond
	doTimeout = 5 * time.Second
)
```

--------------------------------

### Manage LXD Profile Lifecycle

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles the creation or update of LXD profiles, including cleanup of existing mounts and agents when updating.

```go
// Either create or update an existing LXD profile for the SDK so that later
        // it can be assigned to the required workshop.
        prevp, err := lxdbackend.Profile(conn, sdkInfo.ProjectId, sdkInfo.Workshop, sdkInfo.Sdk)
        if err == nil {
                // Find the difference between a set of old and new devices to detect if any
                // clean up is required when a new profile will be assigned (updated).
                for key, dev := range prevp.Mounts {
                        if _, exist := spec.Profile.Mounts[key]; !exist {
                                if err = removeMount(conn, fs, sdkInfo.ProjectId, sdkInfo.Workshop, dev); err != nil {
                                        return err
                                }
                        }
                }
                if prevp.Agent != nil {
                        if spec.Profile.Agent == nil || *prevp.Agent != *spec.Profile.Agent {
                                if err = removeSshAgent(fs, *prevp.Agent); err != nil {
                                        return err
                                }
                        }
                }
                if prevp.Desktop != nil {
                        if spec.Profile.Desktop == nil || *prevp.Desktop != *spec.Profile.Desktop {
                                if err = removeDesktop(fs); err != nil {
                                        return err
                                }
                        }
                }
                return conn.UpdateProfile(name, newp, "")
        }

        if errors.Is(err, workshop.ErrSdkProfileNotFound) {
                if err = conn.CreateProfile(api.ProfilesPost{ProfilePut: newp, Name: name}); err != nil {
                        return err
                }

                iname := lxdbackend.InstanceName(sdkInfo.Workshop, sdkInfo.ProjectId)
                inst, etag, err := conn.GetInstance(iname)
                if err != nil {
                        return err
                }

                // Assigning the profile for the first time.
                inst.Profiles = append(inst.Profiles, name)
                op, err := conn.UpdateInstance(iname, inst.Writable(), etag)
                if err != nil {
                        return err
                }

                return op.WaitContext(ctx)
        }

        return err
}
```

--------------------------------

### List SDK Revisions (Console)

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-revisions.rst

Use this command to list all available channels and revisions for a specified SDK from the store. This is useful for identifying revision numbers needed for other commands like 'sdkcraft release'.

```console
$ sdkcraft revisions SDK
```

--------------------------------

### Verify device availability in workshop shell

Source: https://github.com/canonical/workshop/blob/main/docs/explanation/interfaces/custom-device-interface.md

List devices inside the workshop to confirm they are accessible after connection.

```console
$ workshop shell ws
workshop@ws:/project$ ls /dev/input/

  event0  event1  mice
```

--------------------------------

### List Sketches in Current Project

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop-sketches.rst

Use this command to enumerate all sketches in the current project directory. It displays a compact list including the project path, workshop name, sketch SDK revision, and notes.

```console
$ workshop sketches
```

--------------------------------

### Authenticate with SDK Store

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-login.rst

Executes the login process for the SDK Store.

```console
$ sdkcraft login
```

--------------------------------

### Define SDK build parts

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/build-an-sdk.md

Specify how to obtain the SDK payload using the dump plugin. Use environment variables for dynamic versioning and architecture targeting.

```yaml
parts:
  <NAME>:
    plugin: dump
    source: https://example.com/releases/v${CRAFT_PROJECT_VERSION}/<NAME>-linux-${CRAFT_ARCH_BUILD_FOR}.tar.gz
    source-type: tar
```

```yaml
parts:
  <NAME>:
    plugin: dump
    source: https://example.com/releases/v${CRAFT_PROJECT_VERSION}/<NAME>-linux-${CRAFT_ARCH_BUILD_FOR}.tar.gz
    source-type: tar
  service-unit:
    plugin: dump
    source: <NAME>.service
    source-type: file
```

--------------------------------

### Manage workshop environments with Git worktrees

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-with-workshops/use-git.md

Use Git worktrees to switch between different workshop base images for debugging.

```console
$ git worktree add ../hotfix
$ cd ../hotfix/
```

```yaml
name: dev
base: ubuntu@24.04
sdks:
  - name: go
    channel: 1.26
```

```console
$ workshop launch
$ # Hacking away until the problem is solved
$ git commit -m "solve problem with hotfix"
$ cd ../original/
$ git merge hotfix
```

--------------------------------

### Format Workshop Entry and Path

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Utility functions to format workshop information for display and contract file paths by replacing the home directory with a tilde.

```go
func workshopEntry(w *client.WorkshopInfo, p client.Project) []string {
        comment := "-"
        if len(w.Notes) > 0 {
                comment = strings.Join(w.Notes, ",")
        }
        line := []string{
                contractHomeDirectory(p.Path),
                w.Name,
                w.Status,
                comment,
        }
        return line
}

/*
Make the path nicer and shorter by contracting $HOME with a ~

        TODO: Make it fully correct, strings module is not path-aware
*/
func contractHomeDirectory(path string) string {
        if home, err := os.UserHomeDir(); err == nil {
                if strings.HasPrefix(path, home) {
                        return strings.Replace(path, home, "~", 1)
                } else if strings.HasPrefix(path, "(") {
                        return "-"
                }
        }
        return path
}
```

--------------------------------

### Run workshop actions

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/workshop.md

Commands to execute actions defined in the workshop configuration, with support for environment variables, working directories, and argument forwarding.

```console
$ workshop run [flags] [<WORKSHOP>] [--] <ACTION> <ARGUMENTS>...
```

```console
$ workshop run nimble build
```

```console
$ workshop run --env GO111MODULE=off -w /project nimble -- build
```

```console
$ workshop run -- build
```

```console
$ workshop run build
```

```console
$ workshop run dev -- tests -run TestFoo ./pkg/...
```

--------------------------------

### sdkcraft try Command Usage

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft-try.rst

This is the general usage syntax for the sdkcraft try command. It outlines the available flags and their order.

```console
$ sdkcraft try [--destructive-mode] [--shell | --shell-after] [--debug]
                   [--platform name | --build-for arch] [--output OUTPUT]
                   [SDKs ...]
```

--------------------------------

### Project Management Handlers

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Handles project listing and creation requests. Requires an active command context and state locking.

```go
        result := make([]workshop.Project, 0)
        for _, val := range projects {
                result = append(result, val...)
        }

        return SyncResponse(result, http.StatusOK)
}

func v1PostProjects(c *Command, r *http.Request, _ *userState) Response {
        state := c.d.overlord.State()
        state.Lock()
        defer state.Unlock()

        var reqData struct {
                Path string `json:"path"`
        }

        decoder := json.NewDecoder(r.Body)
        if err := decoder.Decode(&reqData); err != nil {
                return statusBadRequest("cannot decode data from request body: %w", err)
        }

        wBackend := c.d.overlord.WorkshopBackend()

        prj, created, err := wBackend.CreateOrLoadProject(r.Context(), reqData.Path)
        if err != nil && !errors.Is(err, workshop.ErrNotProject) {
                return statusInternalError("cannot create or load project at %q: %w", reqData.Path, err)
        } else if errors.Is(err, workshop.ErrNotProject) {
                return statusBadRequest("%w", err)
        }

        if created {
                return SyncResponse(prj, http.StatusCreated)
        } else {
                return SyncResponse(prj, http.StatusOK)
        }
}
```

--------------------------------

### Create Function Mocking Utility

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

A utility to temporarily replace a function with a mock and restore the original state.

```go
package testutil

func FakeFunc[Func any](mock Func, original *Func) (restore func()) {
        oldFunc := *original
        *original = mock
        return func() {
                *original = oldFunc
        }
}
```

--------------------------------

### CLI Flag Configuration

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines common flags for workshop execution, such as working directory, environment variables, and user permissions.

```go
func commonVars(f *pflag.FlagSet, flags *ExecFlags) {
        f.StringVarP(&flags.WorkingDir, "cwd", "w", "/project", "Set the working directory in the workshop.")
        f.StringArrayVar(&flags.Env, "env", []string{}, "Set an environment variable, e.g. 'FOO=bar'; if only the name is provided, the value is inherited from the CLI environment.")
        f.IntVar(&flags.UserId, "uid", 1000, "Run as a specific workshop user.")
        f.IntVar(&flags.GroupId, "gid", 1000, "Run as a member of a specific workshop group.")
        f.DurationVar(&flags.Timeout, "timeout", 0, "Set a timeout; valid units are ns, us or µs, ms, s, m, h.")
        f.BoolVarP(&flags.Interactive, "interactive", "i", false, "Force interactive mode.")
        f.BoolVarP(&flags.NonInteractive, "non-interactive", "I", false, "Force non-interactive mode.")
}
```

--------------------------------

### Mount Interface Implementation in Go

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Defines the mount interface structure and its associated metadata, including base declarations for plugs and slots.

```go
import (
	"errors"
	"fmt"
	"path/filepath"
	"slices"
	"strings"

	"github.com/canonical/workshop/internal/interfaces"
	"github.com/canonical/workshop/internal/interfaces/lxd_device"
	"github.com/canonical/workshop/internal/sdk"
	"github.com/canonical/workshop/internal/workshop"
)

const mountSummary = `allows sharing host code and data with SDKs`

const mountBaseDeclarationSlots = `
  mount:
    allow-installation:
      slot-sdk-type:
        - system
        - regular
    deny-installation:
      slot-attributes:
        host-source: .*
    allow-connection: true
    allow-auto-connection: true
`

const mountBaseDeclarationPlugs = `
  mount:
    allow-installation:
      plug-sdk-type:
        - regular
    allow-connection: true
    allow-auto-connection:
      -
        slot-names:
          - $INTERFACE
      -
        plug-attributes:
          auto-explicit: true
`

var knownPlugAttributes = []string{"workshop-target"}
var knownSlotAttributes = []string{"workshop-source", "host-source"}

// mountInterface allows sharing content between sdks
type mountInterface struct{}

func (iface *mountInterface) Name() string {
	return "mount"
}

func (iface *mountInterface) StaticInfo() interfaces.StaticInfo {
	return interfaces.StaticInfo{
		Summary:              mountSummary,
		BaseDeclarationPlugs: mountBaseDeclarationPlugs,
		BaseDeclarationSlots: mountBaseDeclarationSlots,
		AffectsPlugOnRefresh: true,
	}
}
```

--------------------------------

### Package Imports

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Standard imports for the lxd_device package.

```go
package lxd_device

import (
        "encoding/json"
        "fmt"
        "os/user"

```

--------------------------------

### List SDK revisions

Source: https://github.com/canonical/workshop/blob/main/docs/reference/cli/sdkcraft.md

Displays available channels and revisions for a specified SDK.

```console
$ sdkcraft revisions SDK
```

```console
$ sdkcraft revisions my-sdk
```

--------------------------------

### Clean and pack the SDK

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/develop-sdks/publish-an-sdk.md

Removes existing build state before packing to ensure a clean build from scratch.

```console
$ sdkcraft clean && sdkcraft pack
```

--------------------------------

### Configure Camera Interface Plug

Source: https://github.com/canonical/workshop/blob/main/docs/reference/sdks.md

Defines a camera plug to expose host video capture devices to the workshop.

```yaml
 # ...
 plugs:
   <NAME>:
     interface: camera
```

--------------------------------

### Add SDK to Repository

Source: https://github.com/canonical/workshop/wiki/coverage/coverage.html

Registers plugs and slots declared by an SDK. The SDK must not already exist in the repository.

```go
func (r *Repository) AddSdk(sdkInfo *sdk.Info) error {
        err := sdk.Validate(sdkInfo)
        if err != nil {
                return err
        }

        r.m.Lock()
        defer r.m.Unlock()

        key := plugOrSlotKey(sdkInfo.ProjectId, sdkInfo.Workshop, sdkInfo.Name)

        if r.plugs[key] != nil || r.slots[key] != nil {
                return fmt.Errorf("cannot register interfaces for %q SDK more than once", key)
        }

        for plugName, plugInfo := range sdkInfo.Plugs {
                if _, ok := r.ifaces[plugInfo.Interface]; !ok {
                        continue
                }
                if r.plugs[key] == nil {
                        r.plugs[key] = make(map[string]*sdk.PlugInfo)
                }
                r.plugs[key][plugName] = plugInfo
        }

        for slotName, slotInfo := range sdkInfo.Slots {
                if _, ok := r.ifaces[slotInfo.Interface]; !ok {
                        continue
                }
                if r.slots[key] == nil {
                        r.slots[key] = make(map[string]*sdk.SlotInfo)
                }
                r.slots[key][slotName] = slotInfo
        }
        return nil
}
```

--------------------------------

### Copy Project Directory

Source: https://github.com/canonical/workshop/blob/main/docs/how-to/customize-workshops/move-projects.md

Command to copy a project directory to a new location. Initially, 'workshop list --global' shows only the original project.

```console
$ cp -r /home/user/old/ /home/user/new/
```

```console
$ workshop list --global

  PROJECT                 WORKSHOP  STATUS  NOTES
  /home/user/old          golang    Ready   -
```
