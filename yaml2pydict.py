import yaml

with open("fonts/icons.yml") as f:
    data = yaml.safe_load(f)
    import pdb

    for v in data.values():
        for i in ("aliases", "changes", "search", "voted"):
            v.pop(i, None)
        v["unicode"] = chr(int(v["unicode"], 16))

    pdb.set_trace()
