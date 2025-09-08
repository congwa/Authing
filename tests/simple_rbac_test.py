"""
简化的RBAC测试来捕获具体错误
"""
import pytest
import sys
import traceback

if __name__ == "__main__":
    # 运行单个测试并捕获详细错误
    exit_code = pytest.main([
        'tests/test_rbac.py::TestRoleAPI::test_get_role_by_id_success',
        '-v', '--tb=long', '--capture=no'
    ])
    sys.exit(exit_code)
