import asyncio
from sqlalchemy import text
from lcc.database.session import engine
from lcc.database.models import Base

async def init_models():
    async with engine.begin() as conn:
        # Force drop tables with CASCADE to handle legacy dependencies
        await conn.execute(text("DROP TABLE IF EXISTS components CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS scans CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS dependencies CASCADE")) # proactive cleanup
        await conn.execute(text("DROP TABLE IF EXISTS violations CASCADE"))   # proactive cleanup
        
        # Create new schema
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("Database initialized successfully.")

if __name__ == "__main__":
    asyncio.run(init_models())
