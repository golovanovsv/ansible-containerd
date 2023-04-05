import testinfra
import pytest

@pytest.fixture()
def AnsibleVars(host):
  default_vars = host.ansible("include_vars", "file=defaults/main.yml")["ansible_facts"]
  test_vars = host.ansible("include_vars", "file=molecule/default/vars.yml")["ansible_facts"]
  merged_vars = { **default_vars, **test_vars }
  return merged_vars

def test_service_is_enabled(host):
  assert host.service("containerd").is_enabled

def test_service_is_running(host):
  assert host.service("containerd").is_running

def test_containerd_config_is_exist(host):
  assert host.file("/etc/containerd/config.toml").is_file

def test_containerd_config_content(host, AnsibleVars):
  config = host.file("/etc/containerd/config.toml").content_string
  assert '[plugins."io.containerd.grpc.v1.cri"]' in config

def test_containerd_config_proxy(host, AnsibleVars):
  if len(AnsibleVars['proxy_server']) > 0:
    config = host.file("/etc/systemd/system/containerd.service.d/proxy.conf")
    assert config.is_file
    assert config.user == "root"
    assert config.group == "root"
    assert oct(config.mode) == "0o644"
  else:
    assert True

def test_containerd_config_proxy_content(host, AnsibleVars):
  if len(AnsibleVars['proxy_server']) > 0:
    config = host.file("/etc/systemd/system/containerd.service.d/proxy.conf").content_string
    assert f"HTTP_PROXY={AnsibleVars['proxy_server']}" in config
    assert f"HTTPS_PROXY={AnsibleVars['proxy_server']}" in config
    no_proxy = "127.0.0.1,localhost"
    for entry in AnsibleVars["proxy_ignores"]:
      no_proxy = f"{no_proxy},{entry}"
    for entry in AnsibleVars["containerd_insecure_repos"]:
      no_proxy = f"{no_proxy},{entry}"
    assert f"NO_PROXY={no_proxy}" in config
  else:
    assert True

def test_containerd_socket_is_listening(host):
  assert host.file("/run/containerd/containerd.sock").is_socket

def test_containerd_insecure(host, AnsibleVars):
  if len(AnsibleVars['containerd_insecure_repos']) > 0:
    for repo in AnsibleVars['containerd_insecure_repos']:
      config = host.file(f"/etc/containerd/certs.d/{repo}/hosts.toml")
      assert config.is_file
      assert config.user == "root"
      assert config.group == "root"
      assert oct(config.mode) == "0o644"
      config_content = config.content_string
      assert f"server = \"https://{repo}\"" in config_content
      assert f"[host.\"{repo}\"]" in config_content
  else:
      assert True

def test_containerd_mirrors(host, AnsibleVars):
  if len(AnsibleVars['containerd_mirrors']) > 0:
    for mirror in AnsibleVars['containerd_mirrors'].keys():
      config = host.file(f"/etc/containerd/certs.d/{mirror}/hosts.toml")
      assert config.is_file
      assert oct(config.mode) == "0o644"
      config_content = config.content_string
      assert f"server = \"https://{mirror}\"" in config_content
      assert f"[host.\"{AnsibleVars['containerd_mirrors'][mirror]}\"]" in config_content
  else:
    assert True
