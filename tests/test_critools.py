import testinfra
import pytest

def test_critools_installed(host):
  assert host.package("cri-tools").is_installed

def test_critools_config(host):
  config = host.file("/etc/crictl.yaml")
  assert config.is_file
  assert config.user == "root"
  assert config.group == "root"
  assert oct(config.mode) == "0o644"

def test_critools_execute(host):
  result = host.run("crictl ps")
  assert result.rc == 0
