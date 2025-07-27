import asyncio
import os
import aiosqlite
from os import listdir
from os.path import isfile, join

class SearchParams:
    test = "hello"

class Database:
    migrationsFolder = "Migrations"

    def __init__(self, db_path: str = "games.db"):
        self.db_path = db_path

    async def connect(self):
        return await aiosqlite.connect(self.db_path)

    async def init_database(self):
        conn = await self.connect()
        await self.run_migrations(conn)
        await conn.commit()
        await conn.close()
    
    async def run_migrations(self, conn):
        cursor = await conn.cursor()
        await cursor.execute("PRAGMA user_version")
        version = (await cursor.fetchone())[0]
        migration_files = self.get_migration_files(version)
        running_version = version
        for file in migration_files:
            running_version = file["version"]
            try:
                with open(join(self.migrationsFolder, file["file_name"]), 'r') as f:
                    sql = f.read()
                    # Extract the UP section
                    up_section = sql.split('-- Up')[1].split('-- Down')[0]
                    await conn.executescript(up_section)
                    await conn.commit()
                version = running_version
                print(f"Ran migration {version:03d}")
            except Exception as e:
                print(f"ERROR! Unable to run migration {running_version:03d}: {e}")
        await cursor.execute("PRAGMA user_version = {v:d}".format(v=version))
    
    def get_migration_files(self, version: int):
        files = [{ "file_name": f, "version": int(f[:3])} for f in listdir(self.migrationsFolder) if isfile(join(self.migrationsFolder, f))]
        files = filter(lambda x: x["version"] > version, files)
        return sorted(files, key=lambda x: x["version"])

    async def get_games(params: SearchParams):
        test = ""

async def test():
    db = Database()
    await db.init_database()

asyncio.run(test())