# tmux bootstrap layouts for operator workflows

function tmux-redteam-layout
    if not command -q tmux
        echo 'tmux not installed'
        return 1
    end
    tmux new-session -d -s redteam-main
    tmux rename-window -t redteam-main:1 'recon'
    tmux split-window -h -t redteam-main:1
    tmux split-window -v -t redteam-main:1.1
    tmux send-keys -t redteam-main:1.1 'recon-dir; clear' C-m
    tmux send-keys -t redteam-main:1.2 'ports-wide; clear' C-m
    tmux send-keys -t redteam-main:1.3 'note-recon-template; clear' C-m
    tmux new-window -t redteam-main -n 'web'
    tmux send-keys -t redteam-main:2 'clear' C-m
    tmux new-window -t redteam-main -n 'loot'
    tmux send-keys -t redteam-main:3 'lootdir; clear' C-m
    tmux select-window -t redteam-main:1
    tmux attach -t redteam-main
end

function tmux-blueteam-layout
    if not command -q tmux
        echo 'tmux not installed'
        return 1
    end
    tmux new-session -d -s blueteam-main
    tmux rename-window -t blueteam-main:1 'triage'
    tmux split-window -h -t blueteam-main:1
    tmux split-window -v -t blueteam-main:1.1
    tmux send-keys -t blueteam-main:1.1 'fastfetch; clear' C-m
    tmux send-keys -t blueteam-main:1.2 'ports-wide; clear' C-m
    tmux send-keys -t blueteam-main:1.3 'note-finding-template; clear' C-m
    tmux new-window -t blueteam-main -n 'logs'
    tmux send-keys -t blueteam-main:2 'clear' C-m
    tmux new-window -t blueteam-main -n 'notes'
    tmux send-keys -t blueteam-main:3 'clear' C-m
    tmux select-window -t blueteam-main:1
    tmux attach -t blueteam-main
end

function tmux-ops-layout
    if not command -q tmux
        echo 'tmux not installed'
        return 1
    end
    tmux new-session -d -s jebat-ops
    tmux rename-window -t jebat-ops:1 'main'
    tmux split-window -h -t jebat-ops:1
    tmux send-keys -t jebat-ops:1.1 'fastfetch; clear' C-m
    tmux send-keys -t jebat-ops:1.2 'clear' C-m
    tmux new-window -t jebat-ops -n 'workspace'
    tmux send-keys -t jebat-ops:2 'cd ~/Desktop/Jebat\ Online; clear' C-m
    tmux select-window -t jebat-ops:1
    tmux attach -t jebat-ops
end
