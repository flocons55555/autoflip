"""Collecte uniquement des flux JSON explicitement autorisés par leurs fournisseurs.
Configure AUTOF LIP_FEED_URLS sans espace dans le nom : AUTOFLIP_FEED_URLS.
Format attendu : {"listings":[{"id":"...", "title":"...", "price":3000, "resale_estimate":4200, "url":"...", "source":"..."}]}.
Aucune extraction de Leboncoin ou La Centrale n'est incluse.
"""
import json, os, urllib.request, pathlib, datetime
OUT=pathlib.Path("data/listings.json")
urls=[x.strip() for x in os.environ.get("AUTOFLIP_FEED_URLS","").split(",") if x.strip()]
if not urls:
    print("Aucun flux autorisé configuré; données de démonstration conservées.")
    raise SystemExit(0)
all_items={}
for url in urls:
    if not url.startswith("https://"):
        print("Source ignorée (HTTPS obligatoire)")
        continue
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"AutoFlip/0.1 (authorized-feed-client)"})
        with urllib.request.urlopen(req,timeout=20) as response:
            payload=response.read(2_000_001)
        if len(payload)>2_000_000: raise ValueError("Flux trop volumineux")
        records=json.loads(payload).get("listings",[])
        for a in records[:500]:
            if not isinstance(a,dict): continue
            price=float(a.get("price",0)); resale=float(a.get("resale_estimate",0))
            if not 0<price<1_000_000 or not 0<resale<1_000_000: continue
            if not a.get("title"): continue
            item={k:a.get(k) for k in ("id","title","price","resale_estimate","url","source","year","mileage")}
            item["price"],item["resale_estimate"]=price,resale
            all_items[str(item.get("id") or item.get("url") or item["title"])]=item
    except Exception as exc:
        print("Flux indisponible:",type(exc).__name__,str(exc)[:120])
if all_items:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({"live":True,"updated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"listings":list(all_items.values())},ensure_ascii=False,indent=2),encoding="utf-8")
    print(len(all_items),"annonces enregistrées")
else:
    print("Aucune annonce valide; données précédentes conservées.")
