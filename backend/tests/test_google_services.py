"""
ElectaVerse — Google Services Tests
Tests for GCS, Firebase, and Cloud Logging services with graceful fallback.
All tests run without real cloud credentials.
"""

import sys
import os
import json
import pytest
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ═══════════════════════════════════════════
# GCS Service Tests
# ═══════════════════════════════════════════

class TestGCSService:
    """Test Google Cloud Storage service with local fallback."""

    def test_upload_json_local_fallback(self, tmp_path, monkeypatch):
        """upload_json should fall back to local file storage."""
        import services.gcs_service as gcs
        # Force local fallback
        monkeypatch.setattr(gcs, '_initialized', True)
        monkeypatch.setattr(gcs, '_bucket', None)
        monkeypatch.setattr(gcs, '_local_fallback_dir', lambda: str(tmp_path))

        result = gcs.upload_json('test/data.json', {'key': 'value'})
        assert 'local://' in result

        # Verify file was written
        local_file = tmp_path / 'test' / 'data.json'
        assert local_file.exists()
        data = json.loads(local_file.read_text())
        assert data['key'] == 'value'

    def test_download_json_local_fallback(self, tmp_path, monkeypatch):
        """download_json should read from local file when GCS unavailable."""
        import services.gcs_service as gcs
        monkeypatch.setattr(gcs, '_initialized', True)
        monkeypatch.setattr(gcs, '_bucket', None)
        monkeypatch.setattr(gcs, '_local_fallback_dir', lambda: str(tmp_path))

        # Write a file first
        test_dir = tmp_path / 'test'
        test_dir.mkdir()
        (test_dir / 'data.json').write_text('{"loaded": true}')

        result = gcs.download_json('test/data.json')
        assert result is not None
        assert result['loaded'] is True

    def test_download_json_not_found(self, tmp_path, monkeypatch):
        """download_json should return None for missing files."""
        import services.gcs_service as gcs
        monkeypatch.setattr(gcs, '_initialized', True)
        monkeypatch.setattr(gcs, '_bucket', None)
        monkeypatch.setattr(gcs, '_local_fallback_dir', lambda: str(tmp_path))

        result = gcs.download_json('nonexistent/file.json')
        assert result is None

    def test_list_blobs_local_fallback(self, tmp_path, monkeypatch):
        """list_blobs should list local files when GCS unavailable."""
        import services.gcs_service as gcs
        monkeypatch.setattr(gcs, '_initialized', True)
        monkeypatch.setattr(gcs, '_bucket', None)
        monkeypatch.setattr(gcs, '_local_fallback_dir', lambda: str(tmp_path))

        # Create test files
        sub = tmp_path / 'debates'
        sub.mkdir()
        (sub / 'a.json').write_text('{}')
        (sub / 'b.json').write_text('{}')

        result = gcs.list_blobs('debates/')
        assert len(result) == 2

    def test_delete_blob_local(self, tmp_path, monkeypatch):
        """delete_blob should remove local file."""
        import services.gcs_service as gcs
        monkeypatch.setattr(gcs, '_initialized', True)
        monkeypatch.setattr(gcs, '_bucket', None)
        monkeypatch.setattr(gcs, '_local_fallback_dir', lambda: str(tmp_path))

        target = tmp_path / 'test.json'
        target.write_text('{}')
        assert gcs.delete_blob('test.json') is True
        assert not target.exists()

    def test_save_debate_transcript_path_format(self, tmp_path, monkeypatch):
        """save_debate_transcript should use correct path format."""
        import services.gcs_service as gcs
        monkeypatch.setattr(gcs, '_initialized', True)
        monkeypatch.setattr(gcs, '_bucket', None)
        monkeypatch.setattr(gcs, '_local_fallback_dir', lambda: str(tmp_path))

        result = gcs.save_debate_transcript('battle-123', {'topic': 'EVM'})
        assert 'debates' in result
        assert 'battle-123' in result

    def test_is_gcs_available_without_credentials(self, monkeypatch):
        """is_gcs_available should return False without credentials."""
        import services.gcs_service as gcs
        monkeypatch.setattr(gcs, '_initialized', False)
        monkeypatch.setattr(gcs, '_bucket', None)
        # Don't actually try to connect
        monkeypatch.setattr(gcs, '_initialized', True)
        assert gcs.is_gcs_available() is False


# ═══════════════════════════════════════════
# Firebase Service Tests
# ═══════════════════════════════════════════

class TestFirebaseService:
    """Test Firebase service graceful degradation."""

    def test_init_without_credentials(self, monkeypatch):
        """Firebase should not crash without credentials."""
        import services.firebase_service as fb
        monkeypatch.setattr(fb, '_initialized', False)
        monkeypatch.setattr(fb, '_firestore_db', None)
        monkeypatch.setattr(fb, '_firebase_app', None)
        # Mock Config to have no credentials
        monkeypatch.setattr('services.firebase_service.Config.FIREBASE_CREDENTIALS_PATH', '')
        monkeypatch.setattr('services.firebase_service.Config.FIREBASE_PROJECT_ID', '')
        result = fb.init_firebase()
        assert result is False

    def test_is_firebase_available_false(self, monkeypatch):
        """is_firebase_available should return False without init."""
        import services.firebase_service as fb
        monkeypatch.setattr(fb, '_initialized', True)
        monkeypatch.setattr(fb, '_firestore_db', None)
        assert fb.is_firebase_available() is False

    def test_save_agent_metric_no_crash(self, monkeypatch):
        """save_agent_metric should not crash when Firebase unavailable."""
        import services.firebase_service as fb
        monkeypatch.setattr(fb, '_initialized', True)
        monkeypatch.setattr(fb, '_firestore_db', None)
        # Should silently return without error
        fb.save_agent_metric('TestAgent', 100, 'voter', True)

    def test_save_quiz_score_no_crash(self, monkeypatch):
        """save_quiz_score should not crash when Firebase unavailable."""
        import services.firebase_service as fb
        monkeypatch.setattr(fb, '_initialized', True)
        monkeypatch.setattr(fb, '_firestore_db', None)
        fb.save_quiz_score(1, 'Test User', 5, 5, 'Expert')

    def test_get_quiz_leaderboard_empty(self, monkeypatch):
        """get_quiz_leaderboard should return empty list without Firebase."""
        import services.firebase_service as fb
        monkeypatch.setattr(fb, '_initialized', True)
        monkeypatch.setattr(fb, '_firestore_db', None)
        result = fb.get_quiz_leaderboard()
        assert result == []

    def test_save_fact_check_no_crash(self, monkeypatch):
        """save_fact_check should not crash when Firebase unavailable."""
        import services.firebase_service as fb
        monkeypatch.setattr(fb, '_initialized', True)
        monkeypatch.setattr(fb, '_firestore_db', None)
        result = fb.save_fact_check(1, 'test claim', {'verdict': 'TRUE'})
        assert result == ''

    def test_verify_firebase_token_unavailable(self, monkeypatch):
        """verify_firebase_token should return None when unavailable."""
        import services.firebase_service as fb
        monkeypatch.setattr(fb, '_initialized', True)
        monkeypatch.setattr(fb, '_firestore_db', None)
        result = fb.verify_firebase_token('fake-token')
        assert result is None


# ═══════════════════════════════════════════
# Cloud Logging Service Tests
# ═══════════════════════════════════════════

class TestCloudLogging:
    """Test Cloud Logging graceful degradation."""

    def test_init_disabled_by_default(self, monkeypatch):
        """Cloud Logging should be disabled by default."""
        import services.gcloud_logging_service as cl
        monkeypatch.setattr(cl, '_initialized', False)
        monkeypatch.setattr(cl, '_cloud_logger', None)
        monkeypatch.setattr('services.gcloud_logging_service.Config.CLOUD_LOGGING_ENABLED', False)
        result = cl.init_cloud_logging()
        assert result is False

    def test_log_event_no_crash(self, monkeypatch):
        """log_event should not crash when Cloud Logging unavailable."""
        import services.gcloud_logging_service as cl
        monkeypatch.setattr(cl, '_initialized', True)
        monkeypatch.setattr(cl, '_cloud_logger', None)
        cl.log_event('test.event', {'data': 'value'})

    def test_log_auth_event_no_crash(self, monkeypatch):
        """log_auth_event should not crash when unavailable."""
        import services.gcloud_logging_service as cl
        monkeypatch.setattr(cl, '_initialized', True)
        monkeypatch.setattr(cl, '_cloud_logger', None)
        cl.log_auth_event('test@test.com', 'login', True, '127.0.0.1')

    def test_log_security_event_no_crash(self, monkeypatch):
        """log_security_event should not crash when unavailable."""
        import services.gcloud_logging_service as cl
        monkeypatch.setattr(cl, '_initialized', True)
        monkeypatch.setattr(cl, '_cloud_logger', None)
        cl.log_security_event('test_event', {'ip': '127.0.0.1'})
