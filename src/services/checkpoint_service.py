"""Checkpoint service for resuming interrupted batch processing"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.core.models import ExecutionLog
from src.services.logger_service import get_logger

logger = get_logger(__name__)


class CheckpointManager:
    """Manage batch processing checkpoints for resumability"""

    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        """
        Initialize checkpoint manager

        Args:
            checkpoint_dir: Directory for storing checkpoint files
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def create_checkpoint(
        self,
        session_id: str,
        batch_name: str,
        total_rows: int,
        processed_rows: int,
        execution_logs: List[ExecutionLog],
        config: Dict,
    ) -> str:
        """
        Create a checkpoint for current batch processing state

        Args:
            session_id: Session ID
            batch_name: Batch identifier (e.g., filename)
            total_rows: Total rows in batch
            processed_rows: Number of rows processed so far
            execution_logs: List of execution logs
            config: Current configuration

        Returns:
            Checkpoint file path
        """
        checkpoint_data = {
            "session_id": session_id,
            "batch_name": batch_name,
            "timestamp": datetime.now().isoformat(),
            "total_rows": total_rows,
            "processed_rows": processed_rows,
            "completion_percentage": (processed_rows / total_rows * 100) if total_rows > 0 else 0,
            "execution_logs": [
                {
                    "row_number": log.row_number,
                    "brand_name": log.brand_name,
                    "amazon_link": log.amazon_link,
                    "website_selected": log.website_selected,
                    "confidence": log.confidence,
                    "status": log.status,
                    "reason": log.reason,
                    "execution_time": log.execution_time,
                }
                for log in execution_logs
            ],
            "config": config,
        }

        checkpoint_file = self.checkpoint_dir / f"{session_id}_{batch_name}.json"

        try:
            with open(checkpoint_file, "w") as f:
                json.dump(checkpoint_data, f, indent=2)
            logger.info(f"Checkpoint created: {checkpoint_file}")
            return str(checkpoint_file)
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            raise

    def load_checkpoint(self, checkpoint_file: str) -> Dict:
        """
        Load a checkpoint

        Args:
            checkpoint_file: Path to checkpoint file

        Returns:
            Checkpoint data
        """
        try:
            with open(checkpoint_file, "r") as f:
                data = json.load(f)
            logger.info(f"Checkpoint loaded: {checkpoint_file}")
            return data
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            raise

    def get_processed_rows(self, checkpoint_file: str) -> int:
        """
        Get number of rows already processed from checkpoint

        Args:
            checkpoint_file: Path to checkpoint file

        Returns:
            Number of processed rows
        """
        data = self.load_checkpoint(checkpoint_file)
        return data.get("processed_rows", 0)

    def get_remaining_rows(self, checkpoint_file: str) -> int:
        """
        Get number of rows still to process

        Args:
            checkpoint_file: Path to checkpoint file

        Returns:
            Number of remaining rows
        """
        data = self.load_checkpoint(checkpoint_file)
        total = data.get("total_rows", 0)
        processed = data.get("processed_rows", 0)
        return max(0, total - processed)

    def list_checkpoints(self, session_id: Optional[str] = None) -> List[str]:
        """
        List available checkpoints

        Args:
            session_id: Optional session ID to filter by

        Returns:
            List of checkpoint file paths
        """
        pattern = f"{session_id}_*.json" if session_id else "*.json"
        checkpoints = sorted(self.checkpoint_dir.glob(pattern))
        return [str(cp) for cp in checkpoints]

    def resume_from_checkpoint(
        self,
        checkpoint_file: str,
    ) -> Dict:
        """
        Prepare to resume from a checkpoint

        Args:
            checkpoint_file: Path to checkpoint file

        Returns:
            Resume data with already-processed row numbers
        """
        data = self.load_checkpoint(checkpoint_file)

        processed_row_numbers = {
            log["row_number"] for log in data.get("execution_logs", [])
        }

        resume_data = {
            "session_id": data["session_id"],
            "batch_name": data["batch_name"],
            "total_rows": data["total_rows"],
            "processed_row_numbers": processed_row_numbers,
            "execution_logs": data.get("execution_logs", []),
            "checkpoint_timestamp": data["timestamp"],
        }

        logger.info(
            f"Resuming from checkpoint: {data['processed_rows']}/"
            f"{data['total_rows']} rows already processed"
        )

        return resume_data

    def delete_checkpoint(self, checkpoint_file: str) -> None:
        """
        Delete a checkpoint (after successful completion)

        Args:
            checkpoint_file: Path to checkpoint file
        """
        try:
            Path(checkpoint_file).unlink()
            logger.info(f"Checkpoint deleted: {checkpoint_file}")
        except Exception as e:
            logger.warning(f"Failed to delete checkpoint: {e}")

    def cleanup_old_checkpoints(self, max_age_hours: int = 24) -> int:
        """
        Clean up old checkpoints

        Args:
            max_age_hours: Maximum age of checkpoints to keep

        Returns:
            Number of checkpoints deleted
        """
        from datetime import timedelta

        now = datetime.now()
        max_age = timedelta(hours=max_age_hours)
        deleted_count = 0

        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                data = self.load_checkpoint(str(checkpoint_file))
                checkpoint_time = datetime.fromisoformat(data["timestamp"])

                if now - checkpoint_time > max_age:
                    self.delete_checkpoint(str(checkpoint_file))
                    deleted_count += 1
            except Exception as e:
                logger.debug(f"Error cleaning checkpoint {checkpoint_file}: {e}")

        logger.info(f"Cleaned up {deleted_count} old checkpoints")
        return deleted_count
