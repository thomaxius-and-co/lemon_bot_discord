async def exec(log, tx):
    # Fix incorrect reminder times
    await tx.execute("UPDATE reminder SET ts = ts - interval '2 hours'")
