# Web security helper wrappers

function burp-ca-note
    echo 'Burp CA cert path is usually managed inside Burp itself.'
    echo 'Use: Proxy -> Options -> Import / export CA certificate'
end

function burp-start
    set -l project ~/burp/project.burp
    mkdir -p ~/burp
    if test (count $argv) -ge 1
        set project $argv[1]
    end
    if command -q flatpak
        flatpak run net.portswigger.BurpSuite-Community --project-file=$project >/tmp/burp.log 2>&1 &
        disown
        echo "Burp started with project: $project"
    else
        echo 'flatpak not found'
        return 1
    end
end

function zap-start
    mkdir -p ~/zap
    if command -q flatpak
        flatpak run org.zaproxy.ZAP >/tmp/zap.log 2>&1 &
        disown
        echo 'OWASP ZAP started'
    else
        echo 'flatpak not found'
        return 1
    end
end

function proxy-on
    set -gx http_proxy http://127.0.0.1:8080
    set -gx https_proxy http://127.0.0.1:8080
    set -gx HTTP_PROXY http://127.0.0.1:8080
    set -gx HTTPS_PROXY http://127.0.0.1:8080
    echo 'Proxy env enabled -> 127.0.0.1:8080'
end

function proxy-off
    set -e http_proxy
    set -e https_proxy
    set -e HTTP_PROXY
    set -e HTTPS_PROXY
    echo 'Proxy env disabled'
end

function proxy-test
    echo 'http_proxy='$http_proxy
    echo 'https_proxy='$https_proxy
    curl -I https://example.com --max-time 10
end
