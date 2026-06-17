# Homebrew Tap README
# 
# To install JEBAT via Homebrew:
#
#   brew tap humm1ngb1rd/jebat https://github.com/humm1ngb1rd/homebrew-jebat.git
#   brew install jebat
#
# This tap repo should live at: https://github.com/humm1ngb1rd/homebrew-jebat
# The formula(s) live in Formula/ directory.
#
# After publishing jebat v6.0.0 to PyPI:
#   1. Download the sdist: pip download jebat==6.0.0 --no-binary :all:
#   2. Compute SHA256: sha256sum jebat-6.0.0.tar.gz
#   3. Update the sha256 field in Formula/jebat.rb
#   4. Push to github.com/humm1ngb1rd/homebrew-jebat