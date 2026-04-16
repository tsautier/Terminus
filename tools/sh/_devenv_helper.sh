
_HELP_DEV_=

_desc_section(){
  _HELP_DEV_="${_HELP_DEV_}
${@}
$(echo "${@}" | sed 's/./-/g')
"
}
_desc_cmd(){
  _HELP_DEV_="${_HELP_DEV_}$(printf "  %-16s -> %s" "$1" "${*:2:20}")
"
}

_desc_var(){
  _HELP_DEV_="${_HELP_DEV_}$(printf "  %-14s => %s" "$1" "${*:2:20}")
"
}

devenv_help(){
  echo -e """${_HELP_DEV_}\n(to show again this, type 'devenv_help')"""
}

_deffunc(){
    if alias $1 2> /dev/null; then
        unalias $1
    fi
}

_finalize_help(){
  unset _desc_section
  unset _desc_cmd
  unset _desc_var
  unset _deffunc
  unset _finalize_help
}
