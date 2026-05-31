# JEBAT — Homebrew formula (tap)
# Usage: brew tap humm1ngb1rd/jebat https://github.com/humm1ngb1rd/homebrew-jebat.git
#        brew install jebat

class Jebat < Formula
  desc "41-CLI AI Agent with pentest toolkit, ReAct loop, MCP, and 97 tools"
  homepage "https://github.com/humm1ngb1rd/jebat"
  url "https://files.pythonhosted.org/packages/source/j/jebat/jebat-6.0.0.tar.gz"
  sha256 ""  # Fill after publish: sha256sum dist/jebat-6.0.0.tar.gz
  license "MIT"
  version "6.0.0"

  depends_on "python@3.12"

  resource "pip" do
    url "https://bootstrap.pypa.io/get-pip.py"
  end

  def install
    # Create a virtualenv
    venv = virtualenv_create(libexec, "python3.12")

    # Install JEBAT from PyPI
    system libexec/"bin/pip", "install", "--no-cache-dir", "jebat==#{version}"

    # Link the binary
    bin.install_symlink libexec/"bin/jebat"
  end

  test do
    assert_match "JEBAT CLI v#{version}", shell_output("#{bin}/jebat --help 2>&1")
    assert_match "pentest", shell_output("#{bin}/jebat --help 2>&1")
  end
end