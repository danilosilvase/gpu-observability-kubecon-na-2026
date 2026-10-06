import boto3, json, base64, sys, os
rt = boto3.client("bedrock-runtime", region_name="us-west-2")
style = ("cinematic editorial illustration, high quality, dramatic lighting, dark background with teal and green accents, "
         "subtle magenta highlight, 16:9 widescreen, no text, no letters, no logos, clean composition, suitable for a conference slide")
neg = "text, letters, words, numbers, watermark, logo, signature, blurry, low quality, deformed hands, extra fingers"
concepts = {
 "A": "An on-call engineer seen from behind at 2am, alone in a dim office, facing a huge wall of monitoring dashboards. Every panel glows calm green except one small panel glowing red. Coffee mug on the desk, phone with alert lighting up. Mood: tension, confusion, isolation. " + style,
 "B": "A sleek matte black server box sitting in a data center rack, completely opaque, with a row of small green status LEDs and a single red LED. Faint glowing data streams enter one side and exit the other but nothing is visible inside. Concept of a black box you cannot see into. " + style,
 "C": "Isometric illustration of a large GPU accelerator card at the center, with a long queue of tiny glowing request tokens waiting in line to enter it, while every indicator light on the card shines green. Minimalist, technical, clean. Concept: healthy-looking hardware hiding a bottleneck. " + style,
}
for k, p in concepts.items():
    body = {"prompt": p, "negative_prompt": neg, "aspect_ratio": "16:9", "output_format": "png", "mode": "text-to-image"}
    try:
        r = rt.invoke_model(modelId="stability.stable-image-ultra-v1:1", body=json.dumps(body), contentType="application/json", accept="application/json")
        out = json.loads(r["body"].read())
        img = base64.b64decode(out["images"][0])
        fn = f"gen-{k}.png"
        open(fn, "wb").write(img)
        print(k, "ok", len(img), out.get("finish_reasons"))
    except Exception as e:
        print(k, "FAIL", e)
