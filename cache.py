# dns_cache.py
import time, json, lmdb

ENV = lmdb.open("./data/dns_cache", map_size=10*1024*1024, subdir=True, max_dbs=1, lock=True)

def _make_key(name: str, rtype: str, rclass: str = "IN") -> bytes:
    return f"{name.lower()}|{rtype.upper()}|{rclass.upper()}".encode("utf-8")

def get_records(name: str, rtype: str, rclass: str = "IN"):
    now = time.time()
    key = _make_key(name, rtype, rclass)
    with ENV.begin() as txn:
        raw = txn.get(key)
        if not raw:
            return []

        obj = json.loads(raw.decode("utf-8"))

        # expired set
        if obj.get("set_expires_at", 0) <= now:
            return []

        live = []
        for r in obj.get("records", []):
            expires_at = r.get("expires_at", 0)
            if expires_at > now:
                remaining_ttl = int(expires_at - now)
                live.append({"value": r["value"], "ttl": remaining_ttl})

        # remove duplicates by value, keeping the first occurrence
        seen = set()
        unique_live = []
        for r in live:
            if r["value"] not in seen:
                seen.add(r["value"])
                unique_live.append(r)

        return unique_live

def set_records(name: str, values_with_ttl: list, rtype: str, rclass: str = "IN"):
    # values_with_ttl: iterable of (value, ttl_seconds)
    now = time.time()
    records, set_expires_at = [], None
    for val, ttl in values_with_ttl:
        ttl = max(0, int(ttl))
        exp = now + ttl
        records.append({"value": val, "ttl": ttl, "cached_at": now, "expires_at": exp})
        set_expires_at = exp if set_expires_at is None else min(set_expires_at, exp)
    value_obj = {"records": records, "set_expires_at": set_expires_at or now}
    key = _make_key(name, rtype, rclass)
    with ENV.begin(write=True) as txn:
        txn.put(key, json.dumps(value_obj, separators=(",", ":")).encode("utf-8"))

def delete_key(name: str, rtype: str, rclass: str = "IN"):
    key = _make_key(name, rtype, rclass)
    with ENV.begin(write=True) as txn:
        txn.delete(key)

def clear_all():
    with ENV.begin(write=True) as txn:
        cur = txn.cursor()
        # delete all K/V pairs
        for k, _v in list(cur):  # list() to snapshot keys before deleting
            txn.delete(k)

def purge_expired(now: float | None = None):
    now = time.time() if now is None else now
    removed = 0
    with ENV.begin(write=True) as txn:
        cur = txn.cursor()
        for k, v in list(cur):
            try:
                obj = json.loads(v.decode("utf-8"))
            except Exception:
                txn.delete(k); removed += 1; continue
            if obj.get("set_expires_at", 0) <= now:
                txn.delete(k); removed += 1
            else:
                # Optional: rewrite value keeping only live records which are not expired
                live = [r for r in obj.get("records", []) if r.get("expires_at", 0) > now]
                if len(live) != len(obj.get("records", [])):
                    obj["records"] = live
                    obj["set_expires_at"] = min((r["expires_at"] for r in live), default=0)
                    txn.put(k, json.dumps(obj, separators=(",", ":")).encode("utf-8"))
    return removed


def view_all():
    """
    Return a list of dicts: {"key": "name|rtype|rclass", "value": <parsed JSON>}.
    Raw values are returned without filtering expired per-record entries.
    """
    out = []
    with ENV.begin() as txn:
        cur = txn.cursor()
        for k, v in cur:
            try:
                obj = json.loads(v.decode("utf-8"))
            except Exception:
                obj = {"_error": "unable to decode value"}
            out.append({"key": k.decode("utf-8", errors="replace"), "value": obj})
    return out

def print_view(all_entries=True):
    """
    Convenience printer for CLI usage.
    """
    entries = view_all() if all_entries else view_live()
    for item in entries:
        print(f"Key: {item['key']}")
        print(json.dumps(item["value"], indent=2, sort_keys=True))
        print("-" * 40)