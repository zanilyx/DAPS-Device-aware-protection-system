from department import Department
from roles import Role


class Permission:
    READ = "read"
    WRITE = "write"
    DELETE = "delete"


# 1. Define the maximum allowed permissions per Department
DEPT_PERMISSIONS = {
    Department.IT: [Permission.READ, Permission.WRITE, Permission.DELETE],
    Department.HR: [Permission.READ, Permission.WRITE],
    Department.FINANCE: [Permission.READ],
}

# 2. Define the standard allowed permissions per Role
ROLE_PERMISSIONS = {
    Role.ADMIN: [Permission.READ, Permission.WRITE, Permission.DELETE],
    Role.MANAGER: [Permission.READ, Permission.WRITE],
    Role.USER: [Permission.READ],
}


def check_access(user_dept: str, user_role: str, requested_permission: str) -> bool:
    """Evaluates access by checking department capabilities first, 
    then filtering by what the role is permitted to do.
    """
    # Get the permission boundaries
    allowed_dept_perms = DEPT_PERMISSIONS.get(user_dept, [])
    allowed_role_perms = ROLE_PERMISSIONS.get(user_role, [])

    # The permission must clear the department ceiling FIRST, then the role check
    if requested_permission not in allowed_dept_perms:
        return False

    return requested_permission in allowed_role_perms


# Quick Verification Test
if __name__ == "__main__":
    # Case: Admin in Finance trying to Delete. 
    # Even though Admin has Delete rights, Finance department blocks it.
    result = check_access(Department.FINANCE, Role.ADMIN, Permission.DELETE)
    print(f"Finance Admin Delete Access: {result}")  # Expected: False

    # Case: Admin in IT trying to Delete.
    # IT allows Delete, and Admin allows Delete.
    result = check_access(Department.IT, Role.ADMIN, Permission.DELETE)
    print(f"IT Admin Delete Access: {result}")  # Expected: True