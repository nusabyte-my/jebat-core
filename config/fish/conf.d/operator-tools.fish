# Jebat operator helpers

if not set -q OPERATOR_PROFILE
    set -gx OPERATOR_PROFILE default
end

function op-profile
    echo $OPERATOR_PROFILE
end

function use-redteam
    set -gx OPERATOR_PROFILE redteam
    set -gx ALACRITTY_TITLE REDTEAM-OPS
    cp -f ~/Desktop/Jebat\ Online/config/alacritty/alacritty-redteam.toml ~/.config/alacritty/alacritty.toml
    echo 'Switched Alacritty profile to redteam'
    echo 'Open a new Alacritty window to enter the redteam tmux session.'
end

function use-blueteam
    set -gx OPERATOR_PROFILE blueteam
    set -gx ALACRITTY_TITLE BLUETEAM-OPS
    cp -f ~/Desktop/Jebat\ Online/config/alacritty/alacritty-blueteam.toml ~/.config/alacritty/alacritty.toml
    echo 'Switched Alacritty profile to blueteam'
    echo 'Open a new Alacritty window to enter the blueteam tmux session.'
end

function use-defaultterm
    set -gx OPERATOR_PROFILE default
    set -gx ALACRITTY_TITLE JEBAT-OPS
    cp -f ~/Desktop/Jebat\ Online/config/alacritty/alacritty.toml ~/.config/alacritty/alacritty.toml
    echo 'Switched Alacritty profile to default'
end

function scope-note
    set -l note "$argv"
    if test -z "$note"
        echo 'usage: scope-note <text>'
        return 1
    end
    printf '[%s] %s\n' (date '+%F %T') "$note" >> ~/engagement-scope-notes.txt
    echo 'Appended to ~/engagement-scope-notes.txt'
end

function recon-dir
    mkdir -p ~/recon/(date +%Y-%m-%d)
    cd ~/recon/(date +%Y-%m-%d)
end

function ports-wide
    ss -tulpn | sort
end

function httpdump
    if test (count $argv) -lt 1
        echo 'usage: httpdump <url>'
        return 1
    end
    curl -skvI $argv[1] 2>&1 | tee httpdump-(date +%Y%m%d-%H%M%S).log
end

function tlspeek
    if test (count $argv) -lt 1
        echo 'usage: tlspeek <host:port>'
        return 1
    end
    echo | openssl s_client -connect $argv[1] -servername (string split ':' $argv[1])[1] 2>/dev/null | openssl x509 -noout -text | less
end

function whatweb-lite
    if test (count $argv) -lt 1
        echo 'usage: whatweb-lite <url>'
        return 1
    end
    curl -skI $argv[1]
    echo '---'
    http --headers $argv[1]
end

function lootdir
    mkdir -p ~/loot/(date +%Y-%m-%d)
    cd ~/loot/(date +%Y-%m-%d)
end
