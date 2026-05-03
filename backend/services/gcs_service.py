"""
ElectaVerse — Google Cloud Storage Service
Persists election artifacts (debate transcripts, fact-check reports, incident exports)
to a GCS bucket for durable, scalable storage.
Gracefully degrades to local storage when GCS credentials are unavailable.
"""

import json
import logging
import os
from datetime import datetime, timezone
from config import Config
from google.cloud import storage as gcs_storage

logger = logging.getLogger('electaverse.gcs')

# Lazy-loaded GCS client
_client = None
_bucket = None
_initialized = False


def _get_bucket():
    """Lazy-init GCS client and bucket. Returns bucket or None."""
    global _client, _bucket, _initialized
    if _initialized:
        return _bucket

    _initialized = True
    bucket_name = Config.GCS_BUCKET_NAME
    if not bucket_name:
        logger.info('GCS_BUCKET_NAME not set — using local fallback storage')
        return None

    try:
        _client = gcs_storage.Client(project=Config.GCP_PROJECT_ID or None)
        _bucket = _client.bucket(bucket_name)
        # Verify bucket exists
        if not _bucket.exists():
            logger.warning(f'GCS bucket {bucket_name} does not exist — creating it')
            _bucket = _client.create_bucket(bucket_name, location='us-central1')
        logger.info(f'GCS initialized: bucket={bucket_name}')
        return _bucket
    except ImportError:
        logger.warning('google-cloud-storage not installed — using local fallback')
        return None
    except Exception as e:
        logger.warning(f'GCS initialization failed: {e} — using local fallback')
        return None


def _local_fallback_dir() -> str:
    """Return the local fallback directory for artifact storage."""
    base = os.path.join(os.path.dirname(__file__), '..', 'data', 'artifacts')
    os.makedirs(base, exist_ok=True)
    return base


def upload_json(blob_path: str, data: dict, metadata: dict = None) -> str:
    """
    Upload a JSON object to GCS. Falls back to local file storage.

    Args:
        blob_path: Path within the bucket (e.g., 'debates/2026-05-02/abc123.json')
        data: Dict to serialize as JSON
        metadata: Optional metadata dict for the blob

    Returns:
        The GCS URI (gs://bucket/path) or local file path
    """
    json_bytes = json.dumps(data, indent=2, default=str).encode('utf-8')

    bucket = _get_bucket()
    if bucket:
        try:
            blob = bucket.blob(blob_path)
            blob.upload_from_string(json_bytes, content_type='application/json')
            if metadata:
                blob.metadata = metadata
                blob.patch()
            uri = f'gs://{bucket.name}/{blob_path}'
            logger.info(f'Uploaded to GCS: {uri} ({len(json_bytes)} bytes)')
            return uri
        except Exception as e:
            logger.error(f'GCS upload failed: {e} — falling back to local')

    # Local fallback
    local_path = os.path.join(_local_fallback_dir(), blob_path.replace('/', os.sep))
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f'Saved locally: {local_path} ({len(json_bytes)} bytes)')
    return f'local://{local_path}'


def download_json(blob_path: str) -> dict | None:
    """
    Download a JSON object from GCS. Falls back to local file.

    Args:
        blob_path: Path within the bucket

    Returns:
        Parsed dict or None if not found
    """
    bucket = _get_bucket()
    if bucket:
        try:
            blob = bucket.blob(blob_path)
            if blob.exists():
                content = blob.download_as_text()
                return json.loads(content)
        except Exception as e:
            logger.error(f'GCS download failed: {e}')

    # Local fallback
    local_path = os.path.join(_local_fallback_dir(), blob_path.replace('/', os.sep))
    if os.path.exists(local_path):
        with open(local_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def list_blobs(prefix: str, max_results: int = 50) -> list[dict]:
    """
    List blobs under a prefix. Falls back to listing local files.

    Args:
        prefix: GCS prefix (e.g., 'debates/')
        max_results: Maximum number of results

    Returns:
        List of dicts with 'name', 'size', 'updated' keys
    """
    bucket = _get_bucket()
    if bucket:
        try:
            blobs = bucket.list_blobs(prefix=prefix, max_results=max_results)
            return [
                {
                    'name': blob.name,
                    'size': blob.size,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                }
                for blob in blobs
            ]
        except Exception as e:
            logger.error(f'GCS list failed: {e}')

    # Local fallback
    local_dir = os.path.join(_local_fallback_dir(), prefix.replace('/', os.sep))
    results = []
    if os.path.exists(local_dir):
        for root, _, files in os.walk(local_dir):
            for fname in files[:max_results]:
                fpath = os.path.join(root, fname)
                results.append({
                    'name': os.path.relpath(fpath, _local_fallback_dir()),
                    'size': os.path.getsize(fpath),
                    'updated': datetime.fromtimestamp(
                        os.path.getmtime(fpath), tz=timezone.utc
                    ).isoformat(),
                })
    return results


def delete_blob(blob_path: str) -> bool:
    """Delete a blob from GCS or local storage."""
    bucket = _get_bucket()
    if bucket:
        try:
            blob = bucket.blob(blob_path)
            blob.delete()
            logger.info(f'Deleted from GCS: {blob_path}')
            return True
        except Exception as e:
            logger.error(f'GCS delete failed: {e}')

    # Local fallback
    local_path = os.path.join(_local_fallback_dir(), blob_path.replace('/', os.sep))
    if os.path.exists(local_path):
        os.remove(local_path)
        return True
    return False


def is_gcs_available() -> bool:
    """Check if GCS is configured and operational."""
    return _get_bucket() is not None


def save_debate_transcript(battle_id: str, debate_data: dict) -> str:
    """Save a Prompt Wars debate transcript to GCS."""
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    blob_path = f'debates/{today}/{battle_id}.json'
    return upload_json(blob_path, debate_data, metadata={
        'type': 'debate_transcript',
        'battle_id': battle_id,
    })


def save_fact_check_report(user_id: int, claim: str, result: dict) -> str:
    """Save a fact-check verification report to GCS."""
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    timestamp = datetime.now(timezone.utc).strftime('%H%M%S')
    blob_path = f'fact-checks/{today}/user_{user_id}_{timestamp}.json'
    return upload_json(blob_path, {
        'user_id': user_id,
        'claim': claim,
        'result': result,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })


def save_incident_snapshot(incidents: list[dict]) -> str:
    """Save a periodic incident snapshot to GCS."""
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%S')
    blob_path = f'incidents/snapshots/{timestamp}.json'
    return upload_json(blob_path, {
        'snapshot_time': timestamp,
        'total_incidents': len(incidents),
        'incidents': incidents,
    })
