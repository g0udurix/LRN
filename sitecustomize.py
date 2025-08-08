# Ensure project root is on sys.path so 'lrn' package is importable in tests without installation
import os, sys, sqlite3

# Ensure Python loads this module for every test run and script execution.
# Wrap sqlite3.connect so every new connection has PRAGMA foreign_keys=ON.
# Also patch sqlite3.Connection to set PRAGMA on connections created by alternative APIs.
if not hasattr(sqlite3, "_lrn_fk_wrapped"):
    _orig_sqlite3_connect = sqlite3.connect

    def _lrn_enable_fk(conn):
        try:
            conn.execute("PRAGMA foreign_keys=ON;")
        except Exception:
            pass
        return conn

    def _lrn_connect(*args, **kwargs):
        return _lrn_enable_fk(_orig_sqlite3_connect(*args, **kwargs))

    sqlite3.connect = _lrn_connect
    # Some code paths may import connect directly: from sqlite3 import connect
    setattr(sqlite3, "connect", _lrn_connect)

    # Patch Connection constructor via factory if available
    try:
        class _LRNConnection(sqlite3.Connection):
            def __init__(self, *a, **kw):
                super().__init__(*a, **kw)
                _lrn_enable_fk(self)
        sqlite3.Connection = _LRNConnection
    except Exception:
        pass

    sqlite3._lrn_fk_wrapped = True
root = os.path.dirname(os.path.abspath(__file__))
if root not in sys.path:
    sys.path.insert(0, root)