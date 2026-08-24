import asyncio, json, hashlib, os, sys
import edge_tts

VOICE="en-US-AvaNeural"
OUT="audio"
os.makedirs(OUT, exist_ok=True)

words=json.load(open('words_base.json'))
texts=[]
for w in words:
    if w.get('word'): texts.append(w['word'])
    if w.get('ex'): texts.append(w['ex'])
# dedupe
seen=set(); uniq=[]
for t in texts:
    t=t.strip()
    if t and t not in seen:
        seen.add(t); uniq.append(t)
print(f"生成対象: {len(uniq)} 件", flush=True)

def key(t): return hashlib.md5(t.strip().encode()).hexdigest()[:12]

sem=asyncio.Semaphore(8)
done=[0]; failed=[]

async def one(t):
    k=key(t); path=f"{OUT}/{k}.mp3"
    if os.path.exists(path) and os.path.getsize(path)>500:
        done[0]+=1; return k
    async with sem:
        for attempt in range(3):
            try:
                c=edge_tts.Communicate(t, VOICE, rate="-8%")
                await c.save(path)
                if os.path.getsize(path)>500:
                    done[0]+=1
                    if done[0]%50==0: print(f"  {done[0]}/{len(uniq)}", flush=True)
                    return k
            except Exception as e:
                await asyncio.sleep(1.5*(attempt+1))
        failed.append(t); return None

async def main():
    ks=await asyncio.gather(*[one(t) for t in uniq])
    good=sorted({k for k in ks if k})
    open('audio.js','w').write("// 音声インデックス（自動生成）\nconst AUDIO_KEYS="+json.dumps(good)+";\n")
    print(f"\n完了: {len(good)} 件  失敗: {len(failed)}")
    if failed: print("失敗例:", failed[:5])

asyncio.run(main())
