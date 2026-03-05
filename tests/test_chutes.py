import asyncio
import os
from openai import AsyncOpenAI

async def test():
    try:
        api_key = "cpk_537a3f80bbca4c77868e92f87269d1ab.79264ee311c155e4aedab77e80ee2672.8zuNSB4BKiG0dKILr4iCNN50jtj1moLJ"
        client = AsyncOpenAI(api_key=api_key, base_url="https://chutes-moonshotai-kimi-k2-5-tee.chutes.ai/v1")
        response = await client.chat.completions.create(
            model="moonshotai/Kimi-K2.5-TEE",
            max_tokens=500,
            messages=[{"role": "user", "content": "Hai."}],
        )
        print("Success! Tokens:", response.usage.total_tokens)
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
