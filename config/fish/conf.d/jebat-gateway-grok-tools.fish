# Jebat Gateway Grok helpers

function use-grok-sso
    set -gx OPENCLAW_PRIMARY_MODEL grok-sso/grok-3
    echo 'JEBAT_GATEWAY_PRIMARY_MODEL=grok-sso/grok-3'
    echo 'Note: SSO mode is chat/reasoning oriented and may not support tool-calling well.'
end

function use-grok-api
    set -gx OPENCLAW_PRIMARY_MODEL xai/grok-4
    echo 'JEBAT_GATEWAY_PRIMARY_MODEL=xai/grok-4'
end

function jebat-gateway-grok-check
    echo '--- plugin list ---'
    openclaw plugins list | grep -i 'xai\|grok' || true
    echo '--- auth hints ---'
    echo 'openclaw models auth login --provider grok-sso --method sso-cookie'
    echo 'openclaw models auth login --provider grok-sso --method api-key'
    echo '--- current model env ---'
    echo $JEBAT_GATEWAY_PRIMARY_MODEL
end
