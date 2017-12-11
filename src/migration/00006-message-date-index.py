async def exec(log, tx):
    # Add index for message date to make statistics queries faster
    await tx.execute("CREATE INDEX message_ts_date_idx ON message ((ts::date))")

