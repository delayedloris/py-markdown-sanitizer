# Prefix / host confusion (string startswith bypasses)

![subdomain](https://example.com.evil.com/t.png)
![userinfo](https://example.com@evil.com/t.png)
![port-userinfo](https://example.com:443@evil.com/t.png)
![encoded-at](https://example.com%40evil.com/t.png)
![encoded-dot](https://example.com%2eevil.com/t.png)
![path-dotdot](https://prefix.com/prefix/../secret.png)
![path-encoded-dotdot](https://prefix.com/prefix/%2e%2e/secret.png)

<img src="https://example.com.evil.com/t.png" alt="html-sub">
<img src="https://example.com@evil.com/t.png" alt="html-user">
