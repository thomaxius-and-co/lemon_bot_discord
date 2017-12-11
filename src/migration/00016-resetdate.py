async def exec(log, tx):
    await tx.execute("""
        CREATE TABLE resetdate (
            nextresetdate timestamp NOT NULL
        );
    """)

