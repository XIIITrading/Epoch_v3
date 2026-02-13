import base64, pathlib, sys
b = pathlib.Path(sys.argv[1]).read_text()
d = base64.b64decode(b).decode()
pathlib.Path(sys.argv[2]).write_text(d, encoding="utf-8")
print(f"Written {len(d)} bytes")
