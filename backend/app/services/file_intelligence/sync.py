from __future__ import annotations
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete

from app.models.file_record import FileRoot, FileRecord, FileChunk, FileJob, FileEvent
from app.services.file_intelligence.registry import FileRegistryService
from app.services.file_intelligence.indexer import FileIndexingService
from app.services.file_intelligence.extractor import SUPPORTED_EXTENSIONS

class FileSyncService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.registry = FileRegistryService(session)
        self.indexer = FileIndexingService(session)

    async def handle_file_event(
        self,
        user_id: uuid.UUID,
        root_path: str,
        file_path: str,
        event_type: str,
        old_path: str | None = None
    ) -> bool:
        clean_root = str(Path(root_path).resolve())
        clean_file = str(Path(file_path).resolve())

        # Find matching root
        roots = await self.registry.list_roots(user_id)
        matching_root = next((r for r in roots if r.root_path == clean_root), None)
        if not matching_root:
            return False

        ext = Path(clean_file).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS and event_type != "deleted":
            return False

        try:
            rel_path = str(Path(clean_file).relative_to(Path(clean_root))).replace("\\", "/")
        except ValueError:
            return False

        # Record event in event table
        evt = FileEvent(
            user_id=user_id,
            root_id=matching_root.id,
            file_path=clean_file,
            event_type=event_type,
            is_processed=False
        )
        self.session.add(evt)
        await self.session.commit()

        if event_type in ["created", "modified"]:
            if not os.path.exists(clean_file):
                return False

            stat = Path(clean_file).stat()
            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            content_hash = self.registry.calculate_sha256(Path(clean_file))

            # Query existing record
            res = await self.session.execute(
                select(FileRecord).where(
                    and_(FileRecord.root_id == matching_root.id, FileRecord.relative_path == rel_path)
                )
            )
            rec = res.scalars().first()

            if not rec:
                rec = FileRecord(
                    root_id=matching_root.id,
                    user_id=user_id,
                    relative_path=rel_path,
                    absolute_path=clean_file,
                    file_name=Path(clean_file).name,
                    extension=ext,
                    file_size=stat.st_size,
                    content_hash=content_hash,
                    modified_at=mtime,
                    indexing_status="pending"
                )
                self.session.add(rec)
                await self.session.commit()
                await self.session.refresh(rec)
            else:
                if rec.content_hash != content_hash:
                    rec.content_hash = content_hash
                    rec.file_size = stat.st_size
                    rec.modified_at = mtime
                    rec.indexing_status = "pending"
                    await self.session.commit()

            # Trigger indexing
            await self.indexer.index_file(user_id, rec.id)
            evt.is_processed = True
            evt.processed_at = datetime.now(timezone.utc)
            await self.session.commit()
            return True

        elif event_type == "deleted":
            res = await self.session.execute(
                select(FileRecord).where(
                    and_(FileRecord.root_id == matching_root.id, FileRecord.relative_path == rel_path)
                )
            )
            rec = res.scalars().first()
            if rec:
                await self.session.delete(rec)
                evt.is_processed = True
                evt.processed_at = datetime.now(timezone.utc)
                await self.session.commit()
                return True

        elif event_type == "renamed" and old_path:
            clean_old = str(Path(old_path).resolve())
            try:
                old_rel = str(Path(clean_old).relative_to(Path(clean_root))).replace("\\", "/")
            except ValueError:
                old_rel = None

            if old_rel:
                res = await self.session.execute(
                    select(FileRecord).where(
                        and_(FileRecord.root_id == matching_root.id, FileRecord.relative_path == old_rel)
                    )
                )
                rec = res.scalars().first()
                if rec:
                    rec.relative_path = rel_path
                    rec.absolute_path = clean_file
                    rec.file_name = Path(clean_file).name
                    rec.extension = ext
                    evt.is_processed = True
                    evt.processed_at = datetime.now(timezone.utc)
                    await self.session.commit()
                    return True

        return False

    async def get_storage_overview(self, user_id: uuid.UUID) -> dict:
        total_roots = (await self.session.execute(
            select(func.count(FileRoot.id)).where(FileRoot.user_id == user_id)
        )).scalar() or 0

        monitored_roots = (await self.session.execute(
            select(func.count(FileRoot.id)).where(
                and_(FileRoot.user_id == user_id, FileRoot.is_monitored == True)
            )
        )).scalar() or 0

        total_files = (await self.session.execute(
            select(func.count(FileRecord.id)).where(FileRecord.user_id == user_id)
        )).scalar() or 0

        total_indexed = (await self.session.execute(
            select(func.count(FileRecord.id)).where(
                and_(FileRecord.user_id == user_id, FileRecord.indexing_status == "indexed")
            )
        )).scalar() or 0

        total_chunks = (await self.session.execute(
            select(func.count(FileChunk.id)).where(FileChunk.user_id == user_id)
        )).scalar() or 0

        total_bytes = (await self.session.execute(
            select(func.sum(FileRecord.file_size)).where(FileRecord.user_id == user_id)
        )).scalar() or 0

        return {
            "total_approved_roots": total_roots,
            "total_monitored_folders": monitored_roots,
            "total_files": total_files,
            "total_indexed_files": total_indexed,
            "total_indexed_chunks": total_chunks,
            "total_bytes_tracked": total_bytes,
            "supported_extensions": sorted(list(SUPPORTED_EXTENSIONS)),
            "recent_jobs": []
        }
