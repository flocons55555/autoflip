"""AutoFlip : collecte modérée via le connecteur MCP public de Karoto.
Source : https://karoto.fr/connecteur-ia
Aucune annonce fictive n'est présentée comme réelle.
"""
import asyncio, datetime, json, pathlib, re
from urllib.parse import urlparse

OUT = pathlib.Path("data/listings.json")

def objects(v, depth=0):
    if depth > 12: return
    if isinstance(v, str):
        try:
            yield from objects(json.loads(v), depth+1)
        except (ValueError, TypeError):
            return
    elif isinstance(v, list):
        for x in v: yield from objects(x, depth+1)
    elif isinstance(v, dict):
        if any(k in v for k in ("price", "prix", "prix_eur", "asking_price")):
            yield v
        for x in v.values():
            if isinstance(x, (dict,list,str)):
                yield from objects(x, depth+1)

def number(v):
    if isinstance(v, (int, float)): return float(v)
    if isinstance(v, str):
        m = re.search(r"\d[\d\s.,]*", v.replace("\u202f", " "))
        if m:
            return float(re.sub(r"[^0-9]", "", m.group()).strip() or 0)
    return 0.0

def normalize(a):
    price = number(next((a[k] for k in ("price","prix","prix_eur","asking_price") if k in a),0))
    if not 100 <= price <= 500000: return None
    title = next((str(a[k]) for k in ("title","titre","name","label") if a.get(k)), "")
    if not title:
        title = " ".join(str(a.get(k,"")) for k in ("make","model","year")).strip()
    if not title: return None
    url = next((str(a[k]) for k in ("url","link","listing_url","annonce_url") if a.get(k)), "")
    if url and urlparse(url).scheme not in ("http","https"): url=""
    valuation = number(next((a[k] for k in ("estimated_price","market_price","cote","valuation","fair_price","prix_marche") if k in a),0))
    # Estimation indisponible : pas de profit inventé.
    resale = valuation if valuation >= price else price
    return {"id":str(a.get("id") or url or title+str(price)), "title":title, "price":price,
            "resale_estimate":resale, "url":url, "source":"Karoto",
            "year":a.get("year",a.get("annee")), "mileage":a.get("mileage",a.get("kilometrage")),
            "image":a.get("image",a.get("image_url"))}

async def main():
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    async with streamablehttp_client("https://karoto.fr/mcp", timeout=25) as (read,write,_):
        async with ClientSession(read,write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {t.name:t for t in tools.tools}
            name = "best_deals" if "best_deals" in names else "search_listings"
            if name not in names: raise RuntimeError("Outil Karoto indisponible")
            schema = names[name].inputSchema or {}
            props = schema.get("properties",{})
            args = {}
            for k in schema.get("required",[]):
                if k in ("limit","page_size","per_page"): args[k]=15
                elif k in ("country","pays"): args[k]="FR"
                elif k in ("query","q"): args[k]="voiture"
                elif k in ("max_price","prix_max"): args[k]=10000
                else: raise RuntimeError("Paramètre requis inconnu : "+k)
            if "limit" in props: args["limit"]=min(15,int(args.get("limit",15)))
            result = await session.call_tool(name,args)
            if result.isError: raise RuntimeError("Karoto a refusé la recherche")
            payloads=[]
            if result.structuredContent: payloads.append(result.structuredContent)
            for c in result.content:
                if getattr(c,"type",None)=="text":
                    try: payloads.append(json.loads(c.text))
                    except (ValueError,TypeError): pass
            found={}
            for payload in payloads:
                for a in objects(payload):
                    item=normalize(a)
                    if item: found[item["id"]]=item
            if not found:
                print("Diagnostic Karoto: outil =", name)
                print("Diagnostic Karoto: contenu structuré =", type(result.structuredContent).__name__)
                for i,c in enumerate(result.content[:3]):
                    raw = getattr(c,"text","")
                    print("Diagnostic Karoto: bloc", i, "type =", getattr(c,"type","inconnu"), "longueur =", len(raw))
                    print("Diagnostic Karoto: aperçu =", raw[:900].replace("\\n"," "))
                print("Aucune annonce reconnue; démonstration conservée")
                return
            OUT.parent.mkdir(exist_ok=True)
            OUT.write_text(json.dumps({"live":True,"updated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "attribution":"Source : Karoto — https://karoto.fr", "listings":list(found.values())[:30]},ensure_ascii=False,indent=2))
            print(len(found),"annonces Karoto récupérées")

if __name__=="__main__":
    asyncio.run(main())
