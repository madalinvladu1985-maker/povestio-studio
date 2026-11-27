# Construieste info JSON pentru Metricool createScheduledPost (postarea principala + Pinterest) din spec + manifest.
# Folosire: python scripts/metricool_postare.py <id_clip>
import json, sys
cid = sys.argv[1]
data = cid.split("_")[1]; data = f"{data[:4]}-{data[4:6]}-{data[6:]}"
s = json.load(open(f"clipuri/{data}/{cid}.json"))
m = json.load(open(f"publicat/{cid}.json"))
ora = s["programare"]["ora"]
dt = f"{data}T{ora}:00"
pl = s["platforme"]
main = {
    "autoPublish": True, "draft": False, "descendants": [], "hasNotReadNotes": False, "shortener": False,
    "smartLinkData": {"ids": []},
    "text": pl["instagram"]["text"],
    "firstCommentText": s.get("prim_comentariu", ""),
    "media": [m["video_url"]], "mediaAltText": [],
    "providers": [{"network": n} for n in ("tiktok", "instagram", "facebook", "youtube", "threads")],
    "publicationDate": {"dateTime": dt, "timezone": "Europe/Bucharest"},
    "tiktokData": {"title": s["titlu_scurt"][:90], "isAigc": True, "commercialContentOwnBrand": True,
                   "privacyOption": "PUBLIC_TO_EVERYONE"},
    "instagramData": {"type": "REEL", "showReelOnFeed": True, "isAiGenerated": True},
    "facebookData": {"type": "REEL", "title": s["titlu_scurt"]},
    "youtubeData": {"title": pl["youtube"]["titlu"], "type": "short", "privacy": "public",
                    "tags": pl["youtube"]["tags"], "category": s.get("youtube_categorie", "HOWTO_STYLE"),
                    "madeForKids": False, "isAiGeneratedContent": True},
    "threadsData": {},
}
pin = {
    "autoPublish": True, "draft": False, "descendants": [], "hasNotReadNotes": False, "shortener": False,
    "smartLinkData": {"ids": []},
    "text": pl["pinterest"]["text"][:500], "firstCommentText": "",
    "media": [m["video_url"]], "mediaAltText": [],
    "providers": [{"network": "pinterest"}],
    "publicationDate": {"dateTime": dt, "timezone": "Europe/Bucharest"},
    "pinterestData": {"boardId": "267823577779759925", "pinTitle": pl["pinterest"]["titlu"],
                      "pinLink": pl["pinterest"]["link"], "pinNewFormat": True,
                      "isAiGenerated": True, "isAiGeneratedPerson": False},
}
assert len(main["text"]) <= 500, len(main["text"])
print(dt + "+02:00")
print(json.dumps(main, ensure_ascii=False))
print(json.dumps(pin, ensure_ascii=False))
