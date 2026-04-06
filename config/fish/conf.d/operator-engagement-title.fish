# Engagement-aware terminal and tmux helpers

function engagement-name
    set -l path (pwd)
    set -l match (string match -r '.*/engagements/([^/]+)' $path)
    if test -n "$match"
        echo (string replace -r '.*/engagements/' '' $match | string split '/' | head -n 1)
        return 0
    end
    return 1
end

function title-engagement
    set -l name (engagement-name)
    if test -z "$name"
        echo 'not inside an engagement workspace'
        return 1
    end
    set -gx ALACRITTY_TITLE "$OPERATOR_PROFILE:$name"
    printf '\e]2;%s\a' "$ALACRITTY_TITLE"
    echo "Set terminal title to $ALACRITTY_TITLE"
end

function tmux-rename-engagement
    set -l name (engagement-name)
    if test -z "$name"
        echo 'not inside an engagement workspace'
        return 1
    end
    if set -q TMUX
        tmux rename-session "$OPERATOR_PROFILE-$name"
        echo "Renamed tmux session to $OPERATOR_PROFILE-$name"
    else
        echo 'not inside tmux'
        return 1
    end
end

function ops-context
    set -l name (engagement-name)
    if test -n "$name"
        echo "profile=$OPERATOR_PROFILE engagement=$name title=$ALACRITTY_TITLE"
    else
        echo "profile=$OPERATOR_PROFILE engagement=none title=$ALACRITTY_TITLE"
    end
end
