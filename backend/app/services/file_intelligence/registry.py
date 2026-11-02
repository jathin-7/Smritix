from __future__ import annotations
import os
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.orm import selectinload

from app.models.file_record import FileRoot, FileRecord, FileVersion, FileChunk, FileJob
from app.services.file_intelligence.extractor import FileExtractionService, SUPPORTED_EXTENSIONS

EXCLUDED_DIR_NAMES = {
    ".git", ".svn", ".hg", "node_modules", ".next", "__pycache__", ".venv",
    "venv", "env", "dist", "build", "target", "AppData", "Windows", "Program Files",
    "Program Files (x86)", "$RECYCLE.BIN", "System Volume Information"
}

class FileRegistryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        h = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return ""

    async def register_root(
        self,
        user_id: uuid.UUID,
        root_path: str,
        display_name: str | None = None,
        is_monitored: bool = True
    ) -> FileRoot:
        clean_path = str(Path(root_path).resolve())
        if not os.path.exists(clean_path) or not os.path.isdir(clean_path):
            raise ValueError(f"Path does not exist or is not a directory: {clean_path}")

        # Check if already registered
        existing = await self.session.execute(
            select(FileRoot).where(
                and_(FileRoot.user_id == user_id, FileRoot.root_path == clean_path)
            )
        )
        root = existing.scalars().first()
        if root:
            root.is_monitored = is_monitored
            if display_name:
                root.display_name = display_name
            await self.session.commit()
            return root

        name = display_name or Path(clean_path).name or clean_path
        root = FileRoot(
            user_id=user_id,
            root_path=clean_path,
            display_name=name,
            is_monitored=is_monitored
        )
        self.session.add(root)
        await self.session.commit()
        await self.session.refresh(root)
        return root

    async def list_roots(self, user_id: uuid.UUID) -> Sequence[FileRoot]:
        res = await self.session.execute(
            select(FileRoot)
            .where(FileRoot.user_id == user_id)
            .order_by(FileRoot.created_at.desc())
        )
        return res.scalars().all()

    async def get_root(self, user_id: uuid.UUID, root_id: uuid.UUID) -> FileRoot | None:
        res = await self.session.execute(
            select(FileRoot).where(
                and_(FileRoot.user_id == user_id, FileRoot.id == root_id)
            )
        )
        return res.scalars().first()

    async def delete_root(self, user_id: uuid.UUID, root_id: uuid.UUID) -> bool:
        root = await self.get_root(user_id, root_id)
        if not root:
            return False
        await self.session.delete(root)
        await self.session.commit()
        return True

    async def scan_root(self, user_id: uuid.UUID, root_id: uuid.UUID) -> dict[str, int]:
        root = await self.get_root(user_id, root_id)
        if not root:
            raise ValueError("Root not found")

        root_path = Path(root.root_path)
        if not root_path.exists():
            return {"discovered": 0, "new": 0, "modified": 0, "deleted": 0}

        # Query existing file records for this root
        existing_res = await self.session.execute(
            select(FileRecord).where(
                and_(FileRecord.user_id == user_id, FileRecord.root_id == root_id)
            )
        )
        existing_records = {rec.relative_path: rec for rec in existing_res.scalars().all()}

        discovered_rel_paths: set[str] = set()
        new_count = 0
        modified_count = 0

        # Walk approved root safely
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Prune excluded directories
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIR_NAMES and not d.startswith(".")]

            for fname in filenames:
                file_full = Path(dirpath) / fname
                ext = file_full.suffix.lower()

                # Filter supported document & code extensions
                if ext not in SUPPORTED_EXTENSIONS:
                    continue

                try:
                    stat = file_full.stat()
                except Exception:
                    continue

                rel_path = str(file_full.relative_to(root_path)).replace("\\", "/")
                discovered_rel_paths.add(rel_path)
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                file_size = stat.st_size

                rec = existing_records.get(rel_path)
                if not rec:
                    # New file
                    content_hash = self.calculate_sha256(file_full)
                    new_rec = FileRecord(
                        root_id=root_id,
                        user_id=user_id,
                        relative_path=rel_path,
                        absolute_path=str(file_full.resolve()),
                        file_name=fname,
                        extension=ext,
                        file_size=file_size,
                        content_hash=content_hash,
                        modified_at=mtime,
                        indexing_status="pending"
                    )
                    self.session.add(new_rec)
                    new_count += 1
                else:
                    # Check if modified
                    if rec.file_size != file_size or rec.modified_at != mtime:
                        new_hash = self.calculate_sha256(file_full)
                        if new_hash != rec.content_hash:
                            # Record previous version
                            if rec.content_hash:
                                ver = FileVersion(
                                    file_id=rec.id,
                                    content_hash=rec.content_hash,
                                    file_size=rec.file_size,
                                    modified_at=rec.modified_at
                                )
                                self.session.add(ver)

                            rec.content_hash = new_hash
                            rec.file_size = file_size
                            rec.modified_at = mtime
                            rec.indexing_status = "pending"
                            rec.error_message = None
                            modified_count += 1

        # Check for deleted files
        deleted_count = 0
        for rel_path, rec in existing_records.items():
            if rel_path not in discovered_rel_paths:
                await self.session.delete(rec)
                deleted_count += 1

        root.last_scanned_at = datetime.now(timezone.utc)
        await self.session.commit()

        return {
            "discovered": len(discovered_rel_paths),
            "new": new_count,
            "modified": modified_count,
            "deleted": deleted_count
        }

    async def list_files(
        self,
        user_id: uuid.UUID,
        root_id: uuid.UUID | None = None,
        extension: str | None = None,
        indexing_status: str | None = None,
        search_query: str | None = None,
        is_starred: bool | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[FileRecord], int]:
        filters = [FileRecord.user_id == user_id]

        if root_id:
            filters.append(FileRecord.root_id == root_id)
        if extension:
            clean_ext = f".{extension.lstrip('.')}".lower()
            filters.append(FileRecord.extension == clean_ext)
        if indexing_status:
            filters.append(FileRecord.indexing_status == indexing_status)
        if is_starred is not None:
            filters.append(FileRecord.is_starred == is_starred)
        if search_query:
            q = f"%{search_query.strip()}%"
            filters.append(or_(FileRecord.file_name.ilike(q), FileRecord.relative_path.ilike(q)))

        count_query = select(func.count(FileRecord.id)).where(and_(*filters))
        total = (await self.session.execute(count_query)).scalar() or 0

        query = (
            select(FileRecord)
            .where(and_(*filters))
            .options(selectinload(FileRecord.chunks))
            .order_by(FileRecord.modified_at.desc())
            .offset(skip)
            .limit(limit)
        )
        records = (await self.session.execute(query)).scalars().all()
        return list(records), total

    async def get_file(self, user_id: uuid.UUID, file_id: uuid.UUID) -> FileRecord | None:
        query = (
            select(FileRecord)
            .where(and_(FileRecord.user_id == user_id, FileRecord.id == file_id))
            .options(selectinload(FileRecord.chunks), selectinload(FileRecord.root))
        )
        return (await self.session.execute(query)).scalars().first()

    async def toggle_star(self, user_id: uuid.UUID, file_id: uuid.UUID) -> bool:
        file = await self.get_file(user_id, file_id)
        if not file:
            return False
        file.is_starred = not file.is_starred
        await self.session.commit()
        return file.is_starred
