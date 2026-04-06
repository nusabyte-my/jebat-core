"""
File Processing Skill
Provides comprehensive file operations including reading, writing, copying, moving, and processing various file formats.
"""

import csv
import hashlib
import json
import mimetypes
import os
import shutil
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base_skill import BaseSkill, SkillParameter, SkillResult, SkillType


class FileProcessingSkill(BaseSkill):
    """
    Skill for handling various file operations and processing tasks.
    Supports reading, writing, copying, moving, archiving, and metadata operations.
    """

    def __init__(
        self,
        skill_id: str = "file_processing_001",
        name: str = "File Processing",
        description: str = "Comprehensive file operations and processing capabilities",
        version: str = "1.0.0",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the File Processing Skill.

        Args:
            skill_id: Unique skill identifier
            name: Skill name
            description: Skill description
            version: Skill version
            config: Configuration parameters
        """
        super().__init__(
            skill_id=skill_id,
            name=name,
            skill_type=SkillType.FILE_OPERATIONS,
            description=description,
            version=version,
            config=config or {},
        )

        # Default configuration
        default_config = {
            "max_file_size_mb": 100,
            "allowed_extensions": [
                ".txt",
                ".csv",
                ".json",
                ".xml",
                ".yaml",
                ".yml",
                ".log",
                ".md",
                ".py",
                ".js",
                ".html",
                ".css",
            ],
            "encoding": "utf-8",
            "backup_enabled": True,
            "temp_directory": "./temp",
            "backup_directory": "./backup",
        }

        # Merge with provided config
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value

        # Create necessary directories
        os.makedirs(self.config["temp_directory"], exist_ok=True)
        if self.config["backup_enabled"]:
            os.makedirs(self.config["backup_directory"], exist_ok=True)

    async def execute(self, parameters: Dict[str, Any]) -> SkillResult:
        """
        Execute file processing operation.

        Args:
            parameters: Operation parameters including:
                - operation: Type of file operation
                - file_path: Source file path
                - Additional operation-specific parameters

        Returns:
            SkillResult with operation results
        """
        operation = parameters.get("operation", "").lower()

        try:
            if operation == "read":
                return await self._read_file(parameters)
            elif operation == "write":
                return await self._write_file(parameters)
            elif operation == "copy":
                return await self._copy_file(parameters)
            elif operation == "move":
                return await self._move_file(parameters)
            elif operation == "delete":
                return await self._delete_file(parameters)
            elif operation == "exists":
                return await self._check_exists(parameters)
            elif operation == "info":
                return await self._get_file_info(parameters)
            elif operation == "list_directory":
                return await self._list_directory(parameters)
            elif operation == "create_directory":
                return await self._create_directory(parameters)
            elif operation == "archive":
                return await self._create_archive(parameters)
            elif operation == "extract":
                return await self._extract_archive(parameters)
            elif operation == "hash":
                return await self._calculate_hash(parameters)
            elif operation == "find":
                return await self._find_files(parameters)
            elif operation == "backup":
                return await self._backup_file(parameters)
            elif operation == "restore":
                return await self._restore_file(parameters)
            else:
                raise ValueError(f"Unsupported operation: {operation}")

        except Exception as e:
            return SkillResult(
                success=False,
                error=f"File operation '{operation}' failed: {str(e)}",
                skill_used=self.name,
            )

    async def _read_file(self, parameters: Dict[str, Any]) -> SkillResult:
        """Read file content"""
        file_path = Path(parameters["file_path"])
        read_mode = parameters.get("mode", "text")  # text, binary, json, csv
        encoding = parameters.get("encoding", self.config["encoding"])

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.config["max_file_size_mb"]:
            raise ValueError(
                f"File too large: {file_size_mb:.2f}MB (max: {self.config['max_file_size_mb']}MB)"
            )

        try:
            if read_mode == "binary":
                with open(file_path, "rb") as f:
                    content = f.read()
            elif read_mode == "json":
                with open(file_path, "r", encoding=encoding) as f:
                    content = json.load(f)
            elif read_mode == "csv":
                content = []
                with open(file_path, "r", encoding=encoding, newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        content.append(row)
            else:  # text mode
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()

            return SkillResult(
                success=True,
                data={
                    "content": content,
                    "file_path": str(file_path),
                    "mode": read_mode,
                    "size_bytes": file_path.stat().st_size,
                    "encoding": encoding if read_mode != "binary" else None,
                },
                metadata={
                    "operation": "read",
                    "file_size": file_size_mb,
                    "read_mode": read_mode,
                },
            )

        except Exception as e:
            raise Exception(f"Failed to read file: {str(e)}")

    async def _write_file(self, parameters: Dict[str, Any]) -> SkillResult:
        """Write content to file"""
        file_path = Path(parameters["file_path"])
        content = parameters["content"]
        write_mode = parameters.get("mode", "text")  # text, binary, json, csv
        encoding = parameters.get("encoding", self.config["encoding"])
        create_backup = parameters.get("backup", self.config["backup_enabled"])

        # Create backup if file exists and backup is enabled
        if file_path.exists() and create_backup:
            await self._backup_file({"file_path": str(file_path)})

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if write_mode == "binary":
                with open(file_path, "wb") as f:
                    f.write(content)
            elif write_mode == "json":
                with open(file_path, "w", encoding=encoding) as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
            elif write_mode == "csv":
                with open(file_path, "w", encoding=encoding, newline="") as f:
                    if (
                        content
                        and isinstance(content, list)
                        and isinstance(content[0], dict)
                    ):
                        fieldnames = content[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(content)
                    else:
                        writer = csv.writer(f)
                        if isinstance(content, list):
                            writer.writerows(content)
                        else:
                            writer.writerow(content)
            else:  # text mode
                with open(file_path, "w", encoding=encoding) as f:
                    f.write(str(content))

            return SkillResult(
                success=True,
                data={
                    "file_path": str(file_path),
                    "bytes_written": file_path.stat().st_size,
                    "mode": write_mode,
                },
                metadata={
                    "operation": "write",
                    "write_mode": write_mode,
                    "backup_created": create_backup and file_path.exists(),
                },
            )

        except Exception as e:
            raise Exception(f"Failed to write file: {str(e)}")

    async def _copy_file(self, parameters: Dict[str, Any]) -> SkillResult:
        """Copy file or directory"""
        source_path = Path(parameters["source_path"])
        dest_path = Path(parameters["dest_path"])
        preserve_metadata = parameters.get("preserve_metadata", True)

        if not source_path.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")

        # Create destination parent directories
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if source_path.is_file():
                if preserve_metadata:
                    shutil.copy2(source_path, dest_path)
                else:
                    shutil.copy(source_path, dest_path)
                operation_type = "file"
            else:  # directory
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                operation_type = "directory"

            return SkillResult(
                success=True,
                data={
                    "source_path": str(source_path),
                    "dest_path": str(dest_path),
                    "type": operation_type,
                    "size": dest_path.stat().st_size
                    if dest_path.is_file()
                    else self._get_directory_size(dest_path),
                },
                metadata={
                    "operation": "copy",
                    "preserve_metadata": preserve_metadata,
                },
            )

        except Exception as e:
            raise Exception(f"Failed to copy: {str(e)}")

    async def _move_file(self, parameters: Dict[str, Any]) -> SkillResult:
        """Move/rename file or directory"""
        source_path = Path(parameters["source_path"])
        dest_path = Path(parameters["dest_path"])

        if not source_path.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")

        # Create destination parent directories
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.move(str(source_path), str(dest_path))

            return SkillResult(
                success=True,
                data={
                    "old_path": str(source_path),
                    "new_path": str(dest_path),
                    "type": "file" if dest_path.is_file() else "directory",
                },
                metadata={"operation": "move"},
            )

        except Exception as e:
            raise Exception(f"Failed to move: {str(e)}")

    async def _delete_file(self, parameters: Dict[str, Any]) -> SkillResult:
        """Delete file or directory"""
        file_path = Path(parameters["file_path"])
        create_backup = parameters.get("backup", self.config["backup_enabled"])

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Create backup if enabled
        if create_backup:
            await self._backup_file({"file_path": str(file_path)})

        try:
            if file_path.is_file():
                file_path.unlink()
                operation_type = "file"
            else:  # directory
                shutil.rmtree(file_path)
                operation_type = "directory"

            return SkillResult(
                success=True,
                data={
                    "deleted_path": str(file_path),
                    "type": operation_type,
                },
                metadata={
                    "operation": "delete",
                    "backup_created": create_backup,
                },
            )

        except Exception as e:
            raise Exception(f"Failed to delete: {str(e)}")

    async def _check_exists(self, parameters: Dict[str, Any]) -> SkillResult:
        """Check if file or directory exists"""
        file_path = Path(parameters["file_path"])

        return SkillResult(
            success=True,
            data={
                "path": str(file_path),
                "exists": file_path.exists(),
                "is_file": file_path.is_file() if file_path.exists() else None,
                "is_directory": file_path.is_dir() if file_path.exists() else None,
            },
            metadata={"operation": "exists"},
        )

    async def _get_file_info(self, parameters: Dict[str, Any]) -> SkillResult:
        """Get detailed file information"""
        file_path = Path(parameters["file_path"])

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            stat = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))

            info = {
                "path": str(file_path),
                "name": file_path.name,
                "stem": file_path.stem,
                "suffix": file_path.suffix,
                "size_bytes": stat.st_size,
                "size_mb": stat.st_size / (1024 * 1024),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "is_file": file_path.is_file(),
                "is_directory": file_path.is_dir(),
                "mime_type": mime_type,
                "permissions": oct(stat.st_mode)[-3:],
            }

            if file_path.is_dir():
                info["contents_count"] = len(list(file_path.iterdir()))

            return SkillResult(
                success=True,
                data=info,
                metadata={"operation": "info"},
            )

        except Exception as e:
            raise Exception(f"Failed to get file info: {str(e)}")

    async def _list_directory(self, parameters: Dict[str, Any]) -> SkillResult:
        """List directory contents"""
        dir_path = Path(parameters["directory_path"])
        recursive = parameters.get("recursive", False)
        include_hidden = parameters.get("include_hidden", False)
        file_pattern = parameters.get("pattern", "*")

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")

        try:
            items = []

            if recursive:
                pattern = f"**/{file_pattern}" if file_pattern != "*" else "**/*"
                paths = dir_path.glob(pattern)
            else:
                paths = dir_path.glob(file_pattern)

            for path in paths:
                if not include_hidden and path.name.startswith("."):
                    continue

                item_info = {
                    "name": path.name,
                    "path": str(path),
                    "is_file": path.is_file(),
                    "is_directory": path.is_dir(),
                    "size": path.stat().st_size if path.is_file() else None,
                    "modified": datetime.fromtimestamp(
                        path.stat().st_mtime
                    ).isoformat(),
                }

                items.append(item_info)

            return SkillResult(
                success=True,
                data={
                    "directory": str(dir_path),
                    "items": items,
                    "total_items": len(items),
                    "files": sum(1 for item in items if item["is_file"]),
                    "directories": sum(1 for item in items if item["is_directory"]),
                },
                metadata={
                    "operation": "list_directory",
                    "recursive": recursive,
                    "pattern": file_pattern,
                },
            )

        except Exception as e:
            raise Exception(f"Failed to list directory: {str(e)}")

    async def _create_directory(self, parameters: Dict[str, Any]) -> SkillResult:
        """Create directory"""
        dir_path = Path(parameters["directory_path"])
        parents = parameters.get("parents", True)
        exist_ok = parameters.get("exist_ok", True)

        try:
            dir_path.mkdir(parents=parents, exist_ok=exist_ok)

            return SkillResult(
                success=True,
                data={
                    "directory": str(dir_path),
                    "created": True,
                },
                metadata={"operation": "create_directory"},
            )

        except Exception as e:
            raise Exception(f"Failed to create directory: {str(e)}")

    async def _create_archive(self, parameters: Dict[str, Any]) -> SkillResult:
        """Create archive from files/directories"""
        source_paths = parameters["source_paths"]
        archive_path = Path(parameters["archive_path"])
        archive_type = parameters.get("type", "zip")  # zip, tar, tar.gz, tar.bz2

        if not isinstance(source_paths, list):
            source_paths = [source_paths]

        try:
            if archive_type == "zip":
                with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for source_path in source_paths:
                        source = Path(source_path)
                        if source.is_file():
                            zipf.write(source, source.name)
                        elif source.is_dir():
                            for file_path in source.rglob("*"):
                                if file_path.is_file():
                                    arcname = file_path.relative_to(source.parent)
                                    zipf.write(file_path, arcname)

            elif archive_type.startswith("tar"):
                mode = "w"
                if archive_type == "tar.gz":
                    mode = "w:gz"
                elif archive_type == "tar.bz2":
                    mode = "w:bz2"

                with tarfile.open(archive_path, mode) as tarf:
                    for source_path in source_paths:
                        source = Path(source_path)
                        tarf.add(source, arcname=source.name)

            return SkillResult(
                success=True,
                data={
                    "archive_path": str(archive_path),
                    "archive_type": archive_type,
                    "archive_size": archive_path.stat().st_size,
                    "source_count": len(source_paths),
                },
                metadata={"operation": "archive"},
            )

        except Exception as e:
            raise Exception(f"Failed to create archive: {str(e)}")

    async def _extract_archive(self, parameters: Dict[str, Any]) -> SkillResult:
        """Extract archive contents"""
        archive_path = Path(parameters["archive_path"])
        extract_path = Path(parameters.get("extract_path", archive_path.parent))

        if not archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        try:
            extracted_files = []

            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path, "r") as zipf:
                    zipf.extractall(extract_path)
                    extracted_files = zipf.namelist()

            elif (
                archive_path.suffix in [".tar", ".gz", ".bz2"]
                or ".tar." in archive_path.name
            ):
                with tarfile.open(archive_path, "r:*") as tarf:
                    tarf.extractall(extract_path)
                    extracted_files = tarf.getnames()

            return SkillResult(
                success=True,
                data={
                    "archive_path": str(archive_path),
                    "extract_path": str(extract_path),
                    "extracted_files": extracted_files,
                    "files_count": len(extracted_files),
                },
                metadata={"operation": "extract"},
            )

        except Exception as e:
            raise Exception(f"Failed to extract archive: {str(e)}")

    async def _calculate_hash(self, parameters: Dict[str, Any]) -> SkillResult:
        """Calculate file hash"""
        file_path = Path(parameters["file_path"])
        hash_type = parameters.get("hash_type", "md5")  # md5, sha1, sha256, sha512

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        try:
            hash_func = getattr(hashlib, hash_type.lower())()

            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_func.update(chunk)

            hash_value = hash_func.hexdigest()

            return SkillResult(
                success=True,
                data={
                    "file_path": str(file_path),
                    "hash_type": hash_type,
                    "hash_value": hash_value,
                    "file_size": file_path.stat().st_size,
                },
                metadata={"operation": "hash"},
            )

        except Exception as e:
            raise Exception(f"Failed to calculate hash: {str(e)}")

    async def _find_files(self, parameters: Dict[str, Any]) -> SkillResult:
        """Find files matching criteria"""
        search_path = Path(parameters["search_path"])
        pattern = parameters.get("pattern", "*")
        recursive = parameters.get("recursive", True)
        file_type = parameters.get("file_type", "all")  # all, files, directories
        min_size = parameters.get("min_size_mb", 0)
        max_size = parameters.get("max_size_mb", float("inf"))

        if not search_path.exists():
            raise FileNotFoundError(f"Search path not found: {search_path}")

        try:
            found_items = []

            if recursive:
                search_pattern = f"**/{pattern}"
            else:
                search_pattern = pattern

            for path in search_path.glob(search_pattern):
                # Filter by type
                if file_type == "files" and not path.is_file():
                    continue
                if file_type == "directories" and not path.is_dir():
                    continue

                # Filter by size (only for files)
                if path.is_file():
                    size_mb = path.stat().st_size / (1024 * 1024)
                    if size_mb < min_size or size_mb > max_size:
                        continue

                found_items.append(
                    {
                        "path": str(path),
                        "name": path.name,
                        "is_file": path.is_file(),
                        "is_directory": path.is_dir(),
                        "size_mb": size_mb if path.is_file() else None,
                        "modified": datetime.fromtimestamp(
                            path.stat().st_mtime
                        ).isoformat(),
                    }
                )

            return SkillResult(
                success=True,
                data={
                    "search_path": str(search_path),
                    "pattern": pattern,
                    "found_items": found_items,
                    "count": len(found_items),
                },
                metadata={
                    "operation": "find",
                    "recursive": recursive,
                    "file_type": file_type,
                },
            )

        except Exception as e:
            raise Exception(f"Failed to find files: {str(e)}")

    async def _backup_file(self, parameters: Dict[str, Any]) -> SkillResult:
        """Create backup of file"""
        file_path = Path(parameters["file_path"])

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = Path(self.config["backup_directory"]) / backup_name

            if file_path.is_file():
                shutil.copy2(file_path, backup_path)
            else:
                shutil.copytree(file_path, backup_path, dirs_exist_ok=True)

            return SkillResult(
                success=True,
                data={
                    "original_path": str(file_path),
                    "backup_path": str(backup_path),
                    "backup_size": backup_path.stat().st_size
                    if backup_path.is_file()
                    else self._get_directory_size(backup_path),
                },
                metadata={"operation": "backup"},
            )

        except Exception as e:
            raise Exception(f"Failed to create backup: {str(e)}")

    async def _restore_file(self, parameters: Dict[str, Any]) -> SkillResult:
        """Restore file from backup"""
        backup_path = Path(parameters["backup_path"])
        restore_path = Path(parameters.get("restore_path", parameters["backup_path"]))

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        try:
            if backup_path.is_file():
                shutil.copy2(backup_path, restore_path)
            else:
                if restore_path.exists():
                    shutil.rmtree(restore_path)
                shutil.copytree(backup_path, restore_path)

            return SkillResult(
                success=True,
                data={
                    "backup_path": str(backup_path),
                    "restore_path": str(restore_path),
                    "restored_size": restore_path.stat().st_size
                    if restore_path.is_file()
                    else self._get_directory_size(restore_path),
                },
                metadata={"operation": "restore"},
            )

        except Exception as e:
            raise Exception(f"Failed to restore file: {str(e)}")

    def _get_directory_size(self, path: Path) -> int:
        """Calculate total size of directory"""
        return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

    def get_parameters(self) -> List[SkillParameter]:
        """Get list of parameters this skill accepts"""
        return [
            SkillParameter(
                name="operation",
                param_type=str,
                required=True,
                description="Type of file operation to perform",
            ),
            SkillParameter(
                name="file_path",
                param_type=str,
                required=False,
                description="Path to the file or directory",
            ),
            SkillParameter(
                name="content",
                param_type=str,
                required=False,
                description="Content to write to file",
            ),
            SkillParameter(
                name="source_path",
                param_type=str,
                required=False,
                description="Source path for copy/move operations",
            ),
            SkillParameter(
                name="dest_path",
                param_type=str,
                required=False,
                description="Destination path for copy/move operations",
            ),
            SkillParameter(
                name="mode",
                param_type=str,
                required=False,
                default="text",
                description="File operation mode (text, binary, json, csv)",
            ),
            SkillParameter(
                name="encoding",
                param_type=str,
                required=False,
                default="utf-8",
                description="Text encoding for file operations",
            ),
            SkillParameter(
                name="backup",
                param_type=bool,
                required=False,
                default=True,
                description="Whether to create backup before destructive operations",
            ),
        ]
