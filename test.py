import asyncio
from aiocryptopay import AioCryptoPay, Networks

async def test():
    client = AioCryptoPay(
        token="588412:AACn6mkD3GlLiWb8Qubq7IEqFhvMLaMXmYZ",
        network=Networks.MAIN_NET
    )
    me = await client.get_me()
    print("OK:", me)
    await client.close()

asyncio.run(test())