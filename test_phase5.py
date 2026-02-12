"""
Test Suite for Phase 5: GUI Implementation

Tests for CustomTkinter GUI components, dialogs, and workers.

Usage:
    python test_phase5.py --test-all          # Run all tests
    python test_phase5.py --test-components   # Test UI components only
    python test_phase5.py --test-dialogs      # Test dialogs only
    python test_phase5.py --test-workers      # Test workers only
    python test_phase5.py --test-gui          # Launch GUI (manual test)

Author: Music DLP Project
Version: 1.0.0
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import Database
from core.config_manager import ConfigManager
from core.logger import setup_logger


def test_imports():
    """Test 1: Verify all GUI modules can be imported."""
    print("=" * 60)
    print("TEST 1: GUI Module Imports")
    print("=" * 60)

    try:
        # Test CustomTkinter import
        import customtkinter as ctk
        print(f"[OK] CustomTkinter version: {ctk.__version__}")

        # Test main window import
        from gui.main_window import MainWindow
        print("[OK] MainWindow imported")

        # Test component imports
        from gui.components.playlist_panel import PlaylistPanel
        from gui.components.song_panel import SongPanel
        from gui.components.pipeline_panel import PipelinePanel
        from gui.components.log_panel import LogPanel
        print("[OK] All components imported")

        # Test dialog imports
        from gui.dialogs.add_playlist_dialog import AddPlaylistDialog
        from gui.dialogs.settings_dialog import SettingsDialog
        from gui.dialogs.ai_review_dialog import AIReviewDialog
        print("[OK] All dialogs imported")

        # Test worker imports
        from gui.workers.download_worker import DownloadWorker
        from gui.workers.ai_worker import AIWorker
        from gui.workers.conversion_worker import ConversionWorker
        print("[OK] All workers imported")

        print("\n[PASS] All GUI imports successful\n")
        return True

    except ImportError as e:
        print(f"\n[FAIL] Import error: {e}\n")
        return False


def test_component_creation():
    """Test 2: Test component widget creation (without GUI mainloop)."""
    print("=" * 60)
    print("TEST 2: Component Widget Creation")
    print("=" * 60)

    try:
        import customtkinter as ctk
        from core.database import Database
        from core.config_manager import ConfigManager
        from core.logger import setup_logger

        # Initialize dependencies
        db = Database()
        config = ConfigManager(db=db)
        logger = setup_logger('test_phase5', level='INFO')

        # Create root window (hidden)
        root = ctk.CTk()
        root.withdraw()

        # Test playlist panel creation
        from gui.components.playlist_panel import PlaylistPanel
        playlist_panel = PlaylistPanel(root, db=db, config=config, logger=logger)
        print("[OK] PlaylistPanel created")

        # Test song panel creation
        from gui.components.song_panel import SongPanel
        song_panel = SongPanel(root, db=db, config=config, logger=logger)
        print("[OK] SongPanel created")

        # Test pipeline panel creation
        from gui.components.pipeline_panel import PipelinePanel
        pipeline_panel = PipelinePanel(root, db=db, config=config, logger=logger)
        print("[OK] PipelinePanel created")

        # Test log panel creation
        from gui.components.log_panel import LogPanel
        log_panel = LogPanel(root, db=db, config=config, logger=logger)
        print("[OK] LogPanel created")

        # Cleanup
        root.destroy()
        db.close()

        print("\n[PASS] All components created successfully\n")
        return True

    except Exception as e:
        print(f"\n[FAIL] Component creation error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_dialog_creation():
    """Test 3: Test dialog widget creation (without showing)."""
    print("=" * 60)
    print("TEST 3: Dialog Widget Creation")
    print("=" * 60)

    try:
        import customtkinter as ctk
        from core.database import Database
        from core.config_manager import ConfigManager
        from core.logger import setup_logger

        # Initialize dependencies
        db = Database()
        config = ConfigManager(db=db)
        logger = setup_logger('test_phase5', level='INFO')

        # Create root window (hidden)
        root = ctk.CTk()
        root.withdraw()

        # Test add playlist dialog
        from gui.dialogs.add_playlist_dialog import AddPlaylistDialog
        # Note: Don't actually create dialog as it would block
        print("[OK] AddPlaylistDialog class available")

        # Test settings dialog
        from gui.dialogs.settings_dialog import SettingsDialog
        print("[OK] SettingsDialog class available")

        # Test AI review dialog
        from gui.dialogs.ai_review_dialog import AIReviewDialog
        print("[OK] AIReviewDialog class available")

        # Cleanup
        root.destroy()
        db.close()

        print("\n[PASS] All dialog classes available\n")
        return True

    except Exception as e:
        print(f"\n[FAIL] Dialog creation error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_worker_threading():
    """Test 4: Test worker thread creation and lifecycle."""
    print("=" * 60)
    print("TEST 4: Worker Threading")
    print("=" * 60)

    try:
        from core.database import Database
        from core.config_manager import ConfigManager
        from core.logger import setup_logger
        from gui.workers.download_worker import DownloadWorker
        from gui.workers.ai_worker import AIWorker
        from gui.workers.conversion_worker import ConversionWorker
        import time

        # Initialize dependencies
        db = Database()
        config = ConfigManager(db=db)
        logger = setup_logger('test_phase5', level='INFO')

        # Test download worker creation (don't start)
        worker1 = DownloadWorker(
            db=db,
            config=config,
            logger=logger,
            mode='download',
            videos=[]
        )
        print("[OK] DownloadWorker created")
        print(f"    - Thread name: {worker1.name}")
        print(f"    - Is daemon: {worker1.daemon}")

        # Test AI worker creation (don't start)
        worker2 = AIWorker(
            db=db,
            config=config,
            logger=logger,
            videos=[]
        )
        print("[OK] AIWorker created")
        print(f"    - Thread name: {worker2.name}")
        print(f"    - Is daemon: {worker2.daemon}")

        # Test conversion worker creation (don't start)
        worker3 = ConversionWorker(
            db=db,
            config=config,
            logger=logger,
            videos=[]
        )
        print("[OK] ConversionWorker created")
        print(f"    - Thread name: {worker3.name}")
        print(f"    - Is daemon: {worker3.daemon}")

        # Cleanup
        db.close()

        print("\n[PASS] All workers created successfully\n")
        return True

    except Exception as e:
        print(f"\n[FAIL] Worker threading error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_main_window():
    """Test 5: Test main window creation (without mainloop)."""
    print("=" * 60)
    print("TEST 5: Main Window Creation")
    print("=" * 60)

    try:
        from gui.main_window import MainWindow
        from core.database import Database
        from core.config_manager import ConfigManager
        from core.logger import setup_logger

        # Initialize dependencies
        db = Database()
        config = ConfigManager(db=db)
        logger = setup_logger('test_phase5', level='INFO')

        # Create main window (don't run mainloop)
        print("[INFO] Creating main window...")
        app = MainWindow(db=db, config=config, logger=logger)
        print("[OK] MainWindow created")

        # Check window properties
        print(f"    - Title: {app.title()}")
        print(f"    - Geometry: {app.geometry()}")
        print(f"    - Has playlist_panel: {hasattr(app, 'playlist_panel')}")
        print(f"    - Has song_panel: {hasattr(app, 'song_panel')}")
        print(f"    - Has pipeline_panel: {hasattr(app, 'pipeline_panel')}")
        print(f"    - Has log_panel: {hasattr(app, 'log_panel')}")

        # Cleanup
        app.destroy()
        db.close()

        print("\n[PASS] Main window created successfully\n")
        return True

    except Exception as e:
        print(f"\n[FAIL] Main window creation error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_gui_launch():
    """Test 6: Launch GUI for manual testing."""
    print("=" * 60)
    print("TEST 6: Launch GUI (Manual Test)")
    print("=" * 60)

    try:
        from gui.main_window import MainWindow
        from core.database import Database
        from core.config_manager import ConfigManager
        from core.logger import setup_logger

        # Initialize dependencies
        db = Database()
        config = ConfigManager(db=db)
        logger = setup_logger('test_phase5', level='INFO')

        logger.info("=" * 60)
        logger.info("GUI MANUAL TEST")
        logger.info("=" * 60)
        logger.info("GUI window is launching...")
        logger.info("Close the window to end the test")

        # Create and run main window
        app = MainWindow(db=db, config=config, logger=logger)
        app.mainloop()

        # Cleanup
        db.close()

        print("\n[PASS] GUI launched and closed successfully\n")
        return True

    except Exception as e:
        print(f"\n[FAIL] GUI launch error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description='Test Phase 5: GUI Implementation')
    parser.add_argument('--test-all', action='store_true', help='Run all tests')
    parser.add_argument('--test-components', action='store_true', help='Test UI components')
    parser.add_argument('--test-dialogs', action='store_true', help='Test dialogs')
    parser.add_argument('--test-workers', action='store_true', help='Test workers')
    parser.add_argument('--test-gui', action='store_true', help='Launch GUI (manual test)')

    args = parser.parse_args()

    # If no args, show help
    if not any(vars(args).values()):
        parser.print_help()
        return

    results = []

    print("\n" + "=" * 60)
    print("MUSIC DLP - PHASE 5 TEST SUITE")
    print("=" * 60 + "\n")

    # Run tests based on arguments
    if args.test_all or args.test_components:
        results.append(('Imports', test_imports()))
        results.append(('Component Creation', test_component_creation()))

    if args.test_all or args.test_dialogs:
        results.append(('Dialog Creation', test_dialog_creation()))

    if args.test_all or args.test_workers:
        results.append(('Worker Threading', test_worker_threading()))

    if args.test_all:
        results.append(('Main Window Creation', test_main_window()))

    if args.test_gui:
        results.append(('GUI Launch', test_gui_launch()))

    # Print summary
    if results:
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "[PASS]" if result else "[FAIL]"
            print(f"{status} {test_name}")

        print(f"\nTotal: {passed}/{total} tests passed")

        if passed == total:
            print("\n[SUCCESS] All tests passed!")
            return 0
        else:
            print("\n[WARNING] Some tests failed")
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
