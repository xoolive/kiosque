if [[ $(uname) == "Darwin" ]]; then
    poetry run kiosque -v $(pbpaste) - | bat - -l md
elif [[ $(uname) == "Linux" ]]; then
    # consider xsel -op (middle-click)
    poetry run kiosque -v $(xsel -ob) - | bat - -l md
fi