import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from lcc.database.models import Base, Scan
from lcc.database.repository import ScanRepository

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
    
    await engine.dispose()

@pytest.mark.asyncio
async def test_create_scan(db_session):
    repo = ScanRepository(db_session)
    scan = Scan(project_name="test-project", status="queued")
    created = await repo.create_scan(scan)
    
    assert created.id is not None
    assert created.project_name == "test-project"
    assert created.status == "queued"

@pytest.mark.asyncio
async def test_get_scan(db_session):
    repo = ScanRepository(db_session)
    scan = Scan(project_name="test-project", status="running")
    created = await repo.create_scan(scan)
    
    fetched = await repo.get_scan(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.project_name == "test-project"

@pytest.mark.asyncio
async def test_update_scan(db_session):
    repo = ScanRepository(db_session)
    scan = Scan(project_name="test-project", status="queued")
    created = await repo.create_scan(scan)
    
    updated = await repo.update_scan(created.id, status="complete", violations_count=5)
    assert updated.status == "complete"
    assert updated.violations_count == 5
    
    fetched = await repo.get_scan(created.id)
    assert fetched.status == "complete"

@pytest.mark.asyncio
async def test_list_scans(db_session):
    repo = ScanRepository(db_session)
    await repo.create_scan(Scan(project_name="p1", status="complete"))
    await repo.create_scan(Scan(project_name="p2", status="failed"))
    
    scans = await repo.list_scans()
    assert len(scans) == 2
    assert scans[0].project_name == "p2"  # Ordered by created_at desc
