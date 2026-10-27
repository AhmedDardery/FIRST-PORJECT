import asyncio, ssl, edge_tts, edge_tts.communicate as c
c._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
lines = ["لستَ جاهزًا أن تُجابِهَ العالم...", "ما زلتَ صغيرًا.",
 "لا تلتفت للعمر... إنه لا يعني الكثير.",
 "فكم من رجلٍ كَبُرَ عمرُه، وما زال في داخله طفلٌ يبحث عن الأمان.",
 "وكم من روحٍ أتعبتها الحياة، وما زالت تتعلّم كيف تقف من جديد.",
 "لا بأس... لستَ مُطالَبًا بأن تكون قويًّا طوال الوقت."]
async def m():
    for i,t in enumerate(lines):
        await edge_tts.Communicate(t, "ar-SA-HamedNeural", rate="-6%", pitch="-12Hz").save(f"vo{i}.mp3")
asyncio.run(m())
